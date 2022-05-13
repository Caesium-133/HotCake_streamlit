import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import time
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid
from utils import space



def fillWithZero(_list,length):
    if len(_list)<length:
        while len(_list)!=length:
            _list.append(0)

st.set_page_config("关键词解析","🔑")
st.title("关键词解析")
st.write("对输入的关键词分析竞争度，同时给出简单的统计分析")

keyword=st.text_input("请输入关键词：","linear algebra")
keyword=keyword.replace(" ","+")
if keyword == "":
    st.error("请输入合法关键词")

@st.cache(suppress_st_warning=True)
def getData(keyword):
    baseurl="https://browse.gmarket.co.kr/search?keyword={}&p={}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
        "Accept": "*/*",
        "Connection":"close"
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    page=1

    totalPrice=[]
    totalDiscount=[]
    totalScore = []
    totalFeedbackCount = []
    totalPayCount = []

    webdata=requests.get(url=baseurl.format(keyword,page),headers=headers)
    soup=BeautifulSoup(webdata.text,'lxml')
    result=soup.find("div",class_="box__text-result")
    if result is None:
        st.error("返回空数据，请检查网络连接！")
    else:
        resultNum=result.find("span",class_="text text--emphasis")

        if resultNum is None:
            st.error("关键词不合法或代理IP失效")
        else:
            totalNum=int(re.findall("\d+",resultNum.get_text().replace(",",""))[0])
            if totalNum==0:
                st.success("该关键词尚未被使用，无竞争对手！")
            else:
                totalPage = int(np.ceil(totalNum / 100))
                bar = st.progress(0.0)
                while page<=totalPage:
                    try:
                        if soup is None:
                            bar.progress(page / totalPage)
                            page+=1
                            continue
                        priceboxies=soup.findAll("div",class_="box__price-seller")

                        for pricebox in priceboxies:
                            price=pricebox.find("strong",class_="text text__value") #
                            if price is None:
                                continue
                            else:
                                price=int(re.findall("\d+",price.get_text().replace(",",""))[0])
                                totalPrice.append(price)

                        discountboxies=soup.findAll("div",class_="box__discount")
                        for discountbox in discountboxies:
                            discount=discountbox.find("span",class_="text text__value")
                            if discount is None:
                                continue
                            else:
                                discount=int(re.findall("\d+",discount.get_text().replace(",",""))[0])
                                totalDiscount.append(discount)

                        informationBoxies=soup.findAll("div",class_="box__information-score")
                        for informationBox in informationBoxies:
                            scoreList=informationBox.find("li",class_="list-item list-item__awards")
                            if scoreList:
                                scoreSpan=scoreList.find("span",class_="for-a11y")
                                if scoreSpan:
                                    score=int(re.findall("\d+",scoreSpan.get_text().replace(",",""))[0])
                                    totalScore.append(score)

                            feedback_countList=informationBox.find("li,",class_="list-item list-item__feedback-count")
                            if feedback_countList:
                                fcSpan=feedback_countList.find("span",class_="text")
                                if fcSpan:
                                    fc=int(re.findall("\d+",fcSpan.get_text().replace(",",""))[0])
                                    totalFeedbackCount.append(fc)

                            pay_countList=informationBox.find("li",class_="list-item list-item__feedback-count")
                            if pay_countList:
                                pcSpan=pay_countList.find("span",class_="text")
                                if pcSpan:
                                    pc=int(re.findall("\d+",pcSpan.get_text().replace(",",""))[0])
                                    totalPayCount.append(pc)

                    except:
                        pass
                    finally:
                        time.sleep(0.5)
                        bar.progress(page / totalPage)
                        page+=1
                        webdata = requests.get(url=baseurl.format(keyword,page), headers=headers)
                        # with open("test.html","w+",encoding='utf-8') as file:
                        #     file.write(webdata.text)
                        soup = BeautifulSoup(webdata.text, 'lxml')


                supposedLen=max(len(totalPrice),len(totalDiscount),len(totalScore),len(totalFeedbackCount),len(totalPayCount))
                fillWithZero(totalPrice,supposedLen)
                fillWithZero(totalDiscount, supposedLen)
                fillWithZero(totalScore, supposedLen)
                fillWithZero(totalFeedbackCount, supposedLen)
                fillWithZero(totalPayCount, supposedLen)


                competitivity=(np.var(np.array(totalPayCount))*totalNum*100)/sum(totalPayCount)

                totalDiscount=[d/100 for d in totalDiscount]

                df=pd.DataFrame({"价格":totalPrice,"折扣":totalDiscount,"评分":totalScore,"评论数":totalFeedbackCount,"销量":totalPayCount})
                df_describe=df.style.format()
                return df,df_describe,competitivity
df,df_describe,competitivity=getData(keyword)
space(2)
st.markdown(""
            "#### 该商品竞争压力为："
            "")
st.subheader(competitivity)
st.latex(""
         r"竞争压力=\frac{商品总数\times HHI}{\sum 销量} "
         "")
space(2)
visualChoice=st.selectbox("展示简单统计数据还是全部数据？",("统计","全部"))
if visualChoice=="统计":
    st.dataframe(df.describe())
else:
    AgGrid(df,fit_columns_on_grid_load=True,theme="material")





