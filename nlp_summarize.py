import random

import matplotlib.pyplot as plt
import streamlit as st
from konlpy.tag import Okt
from textrankr import TextRank
import mysql.connector
from krwordrank.word import KRWordRank, summarize_with_keywords
import streamlit_wordcloud as sw
import pandas as pd
import datetime
from sentiment_analysis.predict import predict
from utils import space

st.set_page_config("评论解析","💬")
st.title("评论解析")
st.write("使用自然语言处理算法，分析给定评论。")


@st.experimental_singleton
def connectMySql():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = connectMySql()


@st.experimental_memo(ttl=600)
def query(SQL):
    with conn.cursor() as cur:
        cur.execute(SQL)
        return cur.fetchall()

# def predict(sentence):
#     if random.random()<0.83:
#         return 1
#     else:
#         return 0


with st.sidebar:
    bywhat = st.selectbox(
        "按商品还是按类别？",
        ("商品", "类别")
    )

if bywhat == "商品":

    goodsCode = st.text_input("请输入商品编码(goodsCode)：", "208041573")
    if goodsCode == "":
        st.error("请输入商品编码！")

    datespanchoice = st.selectbox("选择数据的时间范围：", ("全部", "最近一年", "最近一季度", "最近一个月", "最近一周"))
    dateFrom = ""
    if datespanchoice == "全部":
        pass
    elif datespanchoice == "最近一年":
        dateFrom = str(int(str(datetime.datetime.now().strftime("%Y%m%d"))) - 10000)
    elif datespanchoice == "最近一个季度":
        dateFrom = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y%m%d")
    elif datespanchoice == "最近一个月":
        dateFrom = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y%m%d")
    elif datespanchoice == "最近一周":
        dateFrom = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d")
    else:
        st.error("非法选择")

    dateSql = f' AND reviewDate > "{dateFrom}"' if datespanchoice != "全部" else ""

    preSQL = f"SELECT reviewTitle,reviewContent FROM premiumreview WHERE goodsCode = {goodsCode} " + dateSql
    comSQL = f"SELECT reviewContent FROM commonreview WHERE goodsCode = {goodsCode} " + dateSql

    pres = query(preSQL)
    pretext = [pre[0] + ". " + pre[1] for pre in pres]

    coms = query(comSQL)
    comtext = [com[0] for com in coms]

    textList = pretext + comtext
    text = ""
    for sentence in textList:
        text += sentence

    if text == "":
        st.error("该商品没有评论或暂未收录。")

    st.subheader("关键词提取")
    st.text(""
            "利用wordrank算法分析评论中的关键词，按权重列出"
            "")

    if len(textList) < 5:
        st.warning("评论数过少，再等等吧。")
    else:
        visualMethod = st.radio("请选择关键词显示方式：", ("词云", "列表"))
        swordlist = []
        # if st.button("过滤指定词"):
        swords = st.text_area("请输入过滤词，以换行分隔：")
        if swords is not None:
            swords_split = swords.splitlines()
            for w in swords_split:
                swordlist.append(str(w))
        min_count = 1
        max_length = 10
        wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)

        beta = 0.85
        max_iter = 10

        keywords, rank, graph = wordrank_extractor.extract(textList, beta, max_iter)
        wordNumMax = len(keywords.items())
        if wordNumMax < 1:
            st.error("评论太过分散，换个商品或者再等等吧。")
        else:
            wordNum = st.slider("请选择要展示的词数：", 1, wordNumMax, int(0.6 * wordNumMax), 1)

            # for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True)[:wordNum]:
            # print('%8s:\t%.4f' % (word, r))

            keywords = summarize_with_keywords(texts=textList, min_count=min_count, max_length=max_length, beta=beta,
                                               max_iter=max_iter, verbose=False, stopwords=set(swordlist))

            # font_path="S:/Downloads/gowun-batang/GowunBatang-Regular.ttf"
            # krwordrank_cloud=WordCloud(
            #     font_path=font_path,
            #     width=800,
            #     height=800,
            #     background_color="white"
            # )
            # krwordrank_cloud=krwordrank_cloud.generate_from_frequencies(keywords)
            #
            # fig=plt.figure()

            keywordslist = []

            keys = keywords.keys()
            for key in list(keys)[:wordNum]:
                keywordslist.append(dict(text=key, value=keywords[key]))

            if visualMethod == "词云":
                return_object = sw.visualize(keywordslist, tooltip_data_fields={'text': '关键词', 'value': '权重'},
                                             width="1000", height="1000")
            else:
                df = pd.DataFrame(keywordslist)
                df.columns = ["关键词", "权重"]
                st.table(df)

    st.subheader("评论情绪分析")
    st.text("使用进行过韩语优化的kobert-multiligual模型对评论内容进行情绪分析。")

    if len(textList)<1:
        st.error("评论太少了！")
    else:
        good_rate = 0
        bad_rate=0
        sabar=st.progress(0)
        sap=0
        saList = []
        for text in textList:
            pr=predict(text)
            if pr==1:#good
                good_rate+=1
            else:
                bad_rate+=1
            sap+=1
            sabar.progress(sap / len(textList))


        piefig = plt.figure(figsize=(10,1))


        plt.xticks([])
        plt.yticks([])
        plt.axis("off")
        plt.barh(0,good_rate,0.1,color=(255/255,75/255,75/255),label="satisfied")
        plt.barh(0,bad_rate,0.1,left=good_rate,color="#00BFFF",label="unsatisfied")
        plt.legend()
        # plt.pie([good_rate,bad_rate],labels=["satisfied","unsatisfied"],colors=["#fce38a","#3fc1c9"])
        # plt.axis('equal')
        st.pyplot(piefig)


    st.subheader("评论摘要")
    st.text(""
            "利用textrank算法提取评论摘要"
            "")


    class OktTokenizerPos:
        okt = Okt()

        def __call__(self, text: str):
            tokentpl = self.okt.pos(text, norm=True, stem=True)
            tokens = [tp[0] for tp in tokentpl]
            return tokens


    if len(textList) < 5:
        st.warning("评论数过少，再等等吧。")
    else:
        sentenceNumMax = len(textList)
        sentenceNum = st.slider("请选择要展示的摘要句数：", 1, sentenceNumMax, 3 if sentenceNumMax > 3 else sentenceNumMax, 1)

        mytokenizer = OktTokenizerPos()

        textrank = TextRank(mytokenizer)

        k = sentenceNum

        summarized = textrank.summarize(text, k)

        st.code(summarized)

    st.subheader("评级统计")
    st.write("统计一般评论中顾客对于商品和快递的评级")
    grades=query(f"select goodsGrade, deliveryGrade from commonreview where goodsCode={goodsCode}")
    if len(grades)<1:
        st.warning("该商品一般评论数太少，再等等吧")
    else:
        goodsGrades={
            "a":0,
            "b":0,
            "c":0,
            "d":0
        }
        deliveryGrades={
            "a":0,
            "b":0,
            "c":0,
            "d":0
        }
        space(2)
        for grade in grades:
            goodsGrades[grade[0]]+=1
            deliveryGrades[grade[1]]+=1
        gpiefig = plt.figure()
        plt.pie([i for i in goodsGrades.values()], labels=[i for i in goodsGrades.keys()],
                colors=["#ffedb2", "#ffbf87", "#ff9867", "#ff4545"])
        plt.axis('equal')
        st.pyplot(gpiefig)
        st.write(goodsGrades)
        space(2)
        dpiefig = plt.figure()
        plt.pie([i for i in deliveryGrades.values()], labels=[i for i in deliveryGrades.keys()], colors=["#e2eff1", "#b6d5e1","#65799b","#555273"])
        plt.axis('equal')
        st.pyplot(dpiefig)
        st.write(deliveryGrades)




else:

    lcc = st.text_input("请输入类别编码：", "100000048")
    if lcc == "":
        st.error("请输入类别编码！")

    preSQL = f"SELECT reviewTitle,reviewContent FROM premiumreview WHERE goodsCode in (SELECT goodsCode FROM bestsellersofeachcat WHERE parentLC={lcc})"
    comSQL = f"SELECT reviewContent FROM commonreview WHERE goodsCode in (SELECT goodsCode FROM bestsellersofeachcat WHERE parentLC={lcc})"

    pres = query(preSQL)
    pretext = [pre[0] + ". " + pre[1] for pre in pres]

    coms = query(comSQL)
    comtext = [com[0] for com in coms]

    textList = pretext + comtext
    text = ""
    for sentence in textList:
        text += sentence

    if text == "":
        st.error("该品类商品没有评论或暂未收录。")

    st.subheader("关键词提取")
    st.text(""
            "利用wordrank算法分析评论中的关键词，按权重列出"
            "")

    if len(textList) < 5:
        st.warning("评论数过少，再等等吧。")
    else:
        visualMethod = st.radio("请选择关键词显示方式：", ("词云", "列表"))
        swordlist = []
        # if st.button("过滤指定词"):
        swords = st.text_area("请输入过滤词，以换行分隔：")
        if swords is not None:
            swords_split = swords.splitlines()
            for w in swords_split:
                swordlist.append(str(w))
        min_count = 1
        max_length = 10
        wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)

        beta = 0.85
        max_iter = 10

        keywords, rank, graph = wordrank_extractor.extract(textList, beta, max_iter)
        wordNumMax = len(keywords.items())
        if wordNumMax < 1:
            st.error("评论太过分散，换个商品或者再等等吧。")
        else:
            wordNum = st.slider("请选择要展示的词数：", 1, wordNumMax, int(0.3 * wordNumMax), 1)

            # for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True)[:wordNum]:
            # print('%8s:\t%.4f' % (word, r))

            keywords = summarize_with_keywords(texts=textList, min_count=min_count, max_length=max_length, beta=beta,
                                               max_iter=max_iter, verbose=False, stopwords=set(swordlist))

            # font_path="S:/Downloads/gowun-batang/GowunBatang-Regular.ttf"
            # krwordrank_cloud=WordCloud(
            #     font_path=font_path,
            #     width=800,
            #     height=800,
            #     background_color="white"
            # )
            # krwordrank_cloud=krwordrank_cloud.generate_from_frequencies(keywords)
            #
            # fig=plt.figure()

            keywordslist = []

            keys = keywords.keys()
            for key in list(keys)[:wordNum]:
                keywordslist.append(dict(text=key, value=keywords[key]))

            if visualMethod == "词云":
                return_object = sw.visualize(keywordslist, tooltip_data_fields={'text': '关键词', 'value': '权重'})
            else:
                df = pd.DataFrame(keywordslist)
                df.columns = ["关键词", "权重"]
                st.table(df)

    st.subheader("评论情绪分析")
    st.text("使用进行过韩语优化的kobert-multiligual模型对评论内容进行情绪分析。")


    if len(textList) < 1:
        st.error("评论太少了！")
    else:
        good_rate = 0
        bad_rate = 0
        sabar = st.progress(0)
        sap = 0
        saList = []
        for text in textList:
            pr = predict(text)
            if pr == 1:  # good
                good_rate += 1
            else:
                bad_rate += 1
            sap += 1
            sabar.progress(sap / len(textList))

        piefig = plt.figure(figsize=(10, 1))
        plt.xticks([])
        plt.yticks([])
        plt.axis("off")
        plt.barh(0, good_rate, 0.1, color=(255 / 255, 75 / 255, 75 / 255), label="satisfied")
        plt.barh(0, bad_rate, 0.1, left=good_rate, color="#00BFFF", label="unsatisfied")
        plt.legend()
        # plt.pie([good_rate,bad_rate],labels=["satisfied","unsatisfied"],colors=["#fce38a","#3fc1c9"])
        # plt.axis('equal')
        st.pyplot(piefig)

    st.subheader("评论摘要")
    st.text(""
            "利用textrank算法提取评论摘要"
            "")


    class OktTokenizerPos:
        okt = Okt()

        def __call__(self, text: str):
            tokentpl = self.okt.pos(text, norm=True, stem=True)
            tokens = [tp[0] for tp in tokentpl]
            return tokens


    if len(textList) < 5:
        st.warning("评论数过少，再等等吧。")
    else:
        sentenceNumMax = len(textList)
        sentenceNum = st.slider("请选择要展示的摘要句数：", 1, sentenceNumMax, 3 if sentenceNumMax > 3 else sentenceNumMax, 1)

        mytokenizer = OktTokenizerPos()

        textrank = TextRank(mytokenizer)

        k = sentenceNum

        summarized = textrank.summarize(text, k)

        st.code(summarized)

        space(1)

        st.subheader("评级统计")
        st.write("统计一般评论中顾客对于商品和快递的评级")
        grades = query(f"select goodsGrade, deliveryGrade from commonreview where goodsCode in (select goodsCode from itemInfo where cat_1_code={lcc})")
        if len(grades) < 1:
            st.warning("该商品一般评论数太少，再等等吧")
        else:
            goodsGrades = {
                "a": 0,
                "b": 0,
                "c": 0,
                "d": 0
            }
            deliveryGrades = {
                "a": 0,
                "b": 0,
                "c": 0,
                "d": 0
            }
            space(2)
            for grade in grades:
                goodsGrades[grade[0]] += 1
                deliveryGrades[grade[1]] += 1
            gpiefig = plt.figure()
            plt.pie([i for i in goodsGrades.values()], labels=[i for i in goodsGrades.keys()],
                    colors=["#ffedb2", "#ffbf87", "#ff9867", "#ff4545"])
            plt.axis('equal')
            st.pyplot(gpiefig)
            st.write(goodsGrades)
            space(2)
            dpiefig = plt.figure()
            plt.pie([i for i in deliveryGrades.values()], labels=[i for i in deliveryGrades.keys()],
                    colors=["#e2eff1", "#b6d5e1", "#65799b", "#555273"])
            plt.axis('equal')
            st.pyplot(dpiefig)
            st.write(deliveryGrades)


