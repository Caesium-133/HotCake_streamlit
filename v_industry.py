import streamlit as st
import mysql.connector
import pandas as pd
from st_aggrid import AgGrid
from krwordrank.word import KRWordRank, summarize_with_keywords
from streamlit.components.v1 import html

st.title("行业数据")
st.write("选定行业，给出该行业的热门关键词，热销店铺，热销商品，行业集中度等")


@st.experimental_singleton
def connectMySql():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = connectMySql()


@st.experimental_memo(ttl=600)
def query(SQL):
    with conn.cursor() as cur:
        cur.execute(SQL)
        return cur.fetchall()


with st.sidebar:
    selectedCat = {
        "lcc": None,
        "mcc": None,
        "scc": None
    }
    catCode = ""
    lcSQL = 'SELECT DISTINCT largeCatCode, largeCatTitle FROM categories'
    lcs = query(lcSQL)
    lcDict = {lc[1]: lc[0] for lc in lcs}
    lcTitle = st.selectbox("请选择一级分类:", lcDict.keys())
    if lcTitle:
        selectedCat["lcc"] = lcDict[lcTitle]
        catCode = lcDict[lcTitle]
        mcSQL = f'SELECT DISTINCT mediumCatCode, mediumCatTitle FROM categories WHERE largeCatTitle = "{lcTitle}"'
        mcs = query(mcSQL)
        mcDict = {mc[1]: mc[0] for mc in mcs}
        mcTitles = list(mcDict.keys())
        mcTitles.append("不选")
        mcTitle = st.selectbox("请选择二级分类:", mcTitles)
        if mcTitle != "不选":
            selectedCat["mcc"] = mcDict[mcTitle]
            catCode = mcDict[mcTitle]
            scSQL = f'SELECT DISTINCT smallCatCode, smallCatTitle FROM categories WHERE largeCatTitle = "{lcTitle}" and mediumCatTitle = "{mcTitle}"'
            scs = query(scSQL)
            scDict = {sc[1]: sc[0] for sc in scs}
            scTitles = list(scDict.keys())
            scTitles.append("不选")
            scTitle = st.selectbox("请选择三级分类:", scTitles)
            if scTitle != "不选":
                selectedCat["scc"] = scDict[scTitle]
                catCode = scDict[scTitle]
choice=st.selectbox("选择：",["热销商品","热销店铺","热门关键词","行业集中度"])

if choice=="热销商品":
    num=st.slider("请选择显示数量：",1,50,20,1)
    res=query(f"SELECT goodsCode FROM bestsellersofeachcat WHERE parentLC = {selectedCat['lcc']} limit {num}")
    gclist=[re[0] for re in res]
    df = pd.DataFrame(columns=["排名","商品编号","商品名","现价","原价","店铺名"])
    for gc in gclist:
        infos=query(f"SELECT title,realPrice,originalPrice,shopTitle FROM itemInfo WHERE goodsCode={gc}")
        infolist= [len(df.index)+1,gc]
        infolist.extend(list(infos[0]))
        df.loc[len(df.index)] = infolist
    AgGrid(df,theme="material")
elif choice=="热销店铺":
    num = st.slider("请选择显示数量：", 1, 50, 20, 1)
    mcSQL=f" AND cat_2_code={selectedCat['mcc']}" if selectedCat['mcc'] else ""
    scSQL=f" AND cat_3_code={selectedCat['scc']}" if selectedCat['scc'] else ""
    res=query(f"SELECT shopTitle FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} "+mcSQL+scSQL+f" limit {num}")
    if len(res)<1:
        st.warning("该行业下店铺较少，再等等吧。")
    df = pd.DataFrame(columns=["排名", "店铺名"])
    for re in res:
        if re[0] is None:
            continue
        else:
            df.loc[len(df.index)] = [len(df.index)+1,re[0]]
    AgGrid(df,theme="material")
elif choice=="热门关键词":
    mcSQL = f" AND cat_2_code={selectedCat['mcc']}" if selectedCat['mcc'] else ""
    scSQL = f" AND cat_3_code={selectedCat['scc']}" if selectedCat['scc'] else ""
    res = query(
        f"SELECT title FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL)
    if len(res) < 1:
        st.warning("该行业下商品较少，再等等吧。")
    titleList=[]
    for re in res:
        if re[0] is None:
            continue
        else:
            titleList.append(re[0])

    min_count = 1
    max_length = 10
    wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)

    beta = 0.85
    max_iter = 10

    keywords, rank, graph = wordrank_extractor.extract(titleList, beta, max_iter)
    wordNumMax = len(keywords.items())
    if wordNumMax < 1:
        st.error("该行业下商品较少，再等等吧。")
    else:
        wordNum = st.slider("请选择要展示的词数：", 1, wordNumMax, int(0.6 * wordNumMax), 1)

        keywords = summarize_with_keywords(texts=titleList, min_count=min_count, max_length=max_length, beta=beta,
                                           max_iter=max_iter, verbose=False)

        keywordslist = []

        keys = keywords.keys()
        for key in list(keys)[:wordNum]:
            keywordslist.append(dict(text=key, value=keywords[key]))

        df = pd.DataFrame(keywordslist)
        df.columns = ["关键词", "权重"]
        st.table(df)
if choice=="行业集中度":
    st.write("使用赫芬达尔—赫希曼指数(HHI)")
    st.latex(r"HHI=\sum_i^n {s_i^2}\times \alpha")
    st.latex(r"其中s_i为第i家店铺的市场占有率. \alpha = 10000, 为便于观察所设置")

    mcSQL = f" AND cat_2_code={selectedCat['mcc']}" if selectedCat['mcc'] else ""
    scSQL = f" AND cat_3_code={selectedCat['scc']}" if selectedCat['scc'] else ""
    gcNum = query(
        f"SELECT COUNT(*) FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} ")
    gcNum=int(gcNum[0][0])
    shopInfos=query(
        f"SELECT shopTitle, COUNT(*) FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} group by shopTitle")
    hhi=0
    for si in shopInfos:
        s=float(si[1]/gcNum)**2
        hhi+=s
    st.markdown(f"#### 该行业HHI=")
    html(
        f'''
        <body>
    	<h2 align="center">{hhi*10000}</h2>
        </body>
        '''
    )

