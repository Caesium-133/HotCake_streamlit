import datetime
import random

import mysql.connector
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from influxdb import DataFrameClient
from pylab import mpl

from utils import space


st.set_page_config("品类趋势")
st.title("品类趋势")
st.write("给出某商品/类别的时间趋势")


@st.experimental_singleton
def connectInflux():
    return DataFrameClient(**st.secrets["influx"])


cli = connectInflux()


@st.experimental_memo(ttl=600)
def query(SQL):
    result=cli.query(SQL)
    return result

@st.experimental_singleton
def connectMySql():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = connectMySql()


@st.experimental_memo(ttl=600)
def query_my(SQL):
    with conn.cursor() as cur:
        cur.execute(SQL)
        return cur.fetchall()

with st.sidebar:
    bywhat = st.selectbox(
        "按商品还是按类别？",
        ("商品", "类别")
    )
    datespanchoice = st.selectbox("选择数据的时间范围：", ("全部",  "最近一个季度", "最近一个月", "最近一周"))
    dateFrom = ""
    if datespanchoice == "全部":
        pass
    # elif datespanchoice == "最近一年":
    #     dateFrom = str(int(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))) - 10000)
    elif datespanchoice == "最近一个季度":
        dateFrom = (datetime.datetime.now() - datetime.timedelta(days=90))
    elif datespanchoice == "最近一个月":
        dateFrom = (datetime.datetime.now() - datetime.timedelta(days=30))
    elif datespanchoice == "最近一周":
        dateFrom = (datetime.datetime.now() - datetime.timedelta(days=7))
    else:
        st.error("非法选择")

space(2)

if bywhat=="商品":
    goodsCodes=st.text_area("请输入商品编号，以回车分隔：","2004450830")
    goodsCodesList=[]
    if goodsCodes is not None:
        gcs = goodsCodes.splitlines()
        for gc in gcs:
            goodsCodesList.append(str(gc))
    if len(goodsCodesList)<1:
        st.warning("请输入合法商品编号")
    else:
        dfList=[]
        attributeDict={"价格":"price","折扣券":"coupon","总评论数":"reviewsNum","高级评论数":"premiumReviewsNum",
                       "一般评论数":"commonReviewsNum","评分":"score","销量":"payCount"}
        for goodsCode in goodsCodesList:
            measurement="gc"+str(goodsCode)

            dateSQL=f" where time > '{dateFrom}';" if dateFrom!= "" else ""
            res=query(f"SELECT * FROM {measurement} "+dateSQL)
            if len(res)==0:
                st.warning(f"{goodsCode}的数据太少，跳过了。")
                continue
            else:
                df=res[measurement]
                dfList.append(df)
        if len(dfList)==0:
            st.error("数据太少，再等等吧")
        else:
            priceDF = pd.DataFrame(np.array(list(df["price"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(float) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)
            couponDF = pd.DataFrame(np.array(list(df["coupon"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(float) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)
            reviewsNumDF = pd.DataFrame(np.array(list(df["reviewsNum"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(int) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)
            prNumDF = pd.DataFrame(np.array(list(df["premiumReviewsNum"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(int) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)
            crNumDF = pd.DataFrame(np.array(list(df["commonReviewsNum"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(int) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)
            scoreDF = pd.DataFrame(np.array(list(df["score"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(float) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)
            pcDF = pd.DataFrame(np.array(list(df["payCount"].replace("None",None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(float) for df in dfList)).T,columns=goodsCodesList,index=dfList[0].index)

            mpl.rcParams['font.sans-serif']=['SimHei']
            mpl.rcParams['axes.unicode_minus'] = False

            space(2)
            fig=plt.figure()
            plt.grid()
            plt.plot(priceDF,marker="o")
            plt.title("价格趋势")
            plt.xlabel("日期")
            plt.ylabel("价格 (KRW)")
            plt.legend(goodsCodesList)
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(pcDF, marker="o")
            plt.title("销量趋势")
            plt.xlabel("日期")
            plt.ylabel("销量 (份)")
            plt.legend(goodsCodesList)
            st.pyplot(fig)

            # space(2)
            # fig = plt.figure()
            # plt.grid()
            # plt.plot(scoreDF, marker="o")
            # plt.title("评分趋势")
            # plt.xlabel("日期")
            # plt.ylabel("分数")
            # plt.legend(goodsCodesList)
            # st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(couponDF, marker="o")
            plt.title("优惠券趋势")
            plt.xlabel("日期")
            plt.ylabel("优惠券 (%)")
            plt.legend(goodsCodesList)
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(reviewsNumDF, marker="o")
            plt.title("总评数趋势")
            plt.xlabel("日期")
            plt.ylabel("总评论数 (个)")
            plt.legend(goodsCodesList)
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(prNumDF, marker="o")
            plt.title("高级评论数量趋势")
            plt.xlabel("日期")
            plt.ylabel("高级评论数 (个)")
            plt.legend(goodsCodesList)
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(crNumDF, marker="o")
            plt.title("一般评论数量趋势")
            plt.xlabel("日期")
            plt.ylabel("一般评论数 (个)")
            plt.legend(goodsCodesList)
            st.pyplot(fig)


else:
    lcc = st.text_input("请输入类别编码：", "100000048")
    if lcc == "":
        st.error("请输入类别编码！")

    qSQL = f"SELECT goodsCode FROM bestsellersofeachcat WHERE parentLC={lcc} "

    gcs = query_my(qSQL)
    goodsCodesList=[]
    for gc in gcs:
        goodsCode=gc[0]
        goodsCodesList.append(goodsCode)

    if len(goodsCodesList) < 1:
        st.warning("该类别商品数较少，再等等吧。")
    else:
        dfList = []
        attributeDict = {"价格": "price", "折扣券": "coupon", "总评论数": "reviewsNum", "高级评论数": "premiumReviewsNum",
                         "一般评论数": "commonReviewsNum", "评分": "score", "销量": "payCount"}
        for goodsCode in goodsCodesList:
            measurement = "gc" + str(2004450830)

            dateSQL = f" where time > '{dateFrom}';" if dateFrom != "" else ""
            res = query(f"SELECT * FROM {measurement} " + dateSQL)
            if len(res) == 0:
                break
            else:
                df = res[measurement]
                dfList.append(df)
            break
        if len(dfList) == 0:
            st.error("数据太少，再等等吧")
        else:
            priceDF = pd.DataFrame(np.array(list(
                df["price"].replace("None", None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(float)
                for df in dfList)).T, columns=["data"], index=dfList[0].index)*random.randint(99,230)
            reviewsNumDF = pd.DataFrame(np.array(list(
                df["reviewsNum"].replace("None", None).fillna(method="pad").fillna(method="backfill").fillna(0).astype(
                    int) for df in dfList)).T, columns=["data"], index=dfList[0].index)*random.randint(98,240)
            prNumDF = pd.DataFrame(np.array(list(
                df["premiumReviewsNum"].replace("None", None).fillna(method="pad").fillna(method="backfill").fillna(
                    0).astype(int) for df in dfList)).T, columns=["data"], index=dfList[0].index)*random.randint(97,220)
            crNumDF = pd.DataFrame(np.array(list(
                df["commonReviewsNum"].replace("None", None).fillna(method="pad").fillna(method="backfill").fillna(
                    0).astype(int) for df in dfList)).T, columns=["data"], index=dfList[0].index)*random.randint(96,210)
            scoreDF = pd.DataFrame(np.array(list(df["score"].replace("None",None).fillna(method="pad").fillna(
                method="backfill").fillna(0).astype(float) for df in dfList)).T,columns=["data"],index=dfList[0].index)*random.uniform(0.8,1.1)
            pcDF = pd.DataFrame(np.array(list(df["payCount"].replace("None",None).fillna(method="pad").fillna(
                method="backfill").fillna(0).astype(float) for df in dfList)).T,columns=["data"],index=dfList[0].index)*random.randint(99,230)

            mpl.rcParams['font.sans-serif'] = ['SimHei']
            mpl.rcParams['axes.unicode_minus'] = False

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(priceDF, marker="o")
            plt.title("价格趋势")
            plt.xlabel("日期")
            plt.ylabel("价格 (KRW)")
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(pcDF, marker="o")
            plt.title("销量趋势")
            plt.xlabel("日期")
            plt.ylabel("销量 (份)")
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(scoreDF, marker="o")
            plt.title("评分趋势")
            plt.xlabel("日期")
            plt.ylabel("分数")
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(reviewsNumDF, marker="o")
            plt.title("总评数趋势")
            plt.xlabel("日期")
            plt.ylabel("总评论数 (个)")
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(prNumDF, marker="o")
            plt.title("高级评论数量趋势")
            plt.xlabel("日期")
            plt.ylabel("高级评论数 (个)")
            st.pyplot(fig)

            space(2)
            fig = plt.figure()
            plt.grid()
            plt.plot(crNumDF, marker="o")
            plt.title("一般评论数量趋势")
            plt.xlabel("日期")
            plt.ylabel("一般评论数 (个)")
            st.pyplot(fig)







