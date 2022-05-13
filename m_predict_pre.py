import streamlit as st
import mysql.connector
import pandas as pd
from st_aggrid import AgGrid

st.set_page_config(page_title="热销预测-高级版",page_icon="🥞")
st.title("热销预测-高级版")
st.write("在原版的基础上，展示排名增加到了50，且展示分类，允许筛选。")


@st.experimental_singleton
def connectMySql():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = connectMySql()


@st.experimental_memo(ttl=600)
def query(SQL):
    with conn.cursor() as cur:
        cur.execute(SQL)
        return cur.fetchall()

res=query("select * from predictedHotCake order by score desc")
df=pd.DataFrame(columns=["排名","商品编号","一级分类","二级分类","三级分类","得分","链接"])
for r in res:
    gc=r[0]
    infolist = [len(df.index) + 1]
    infolist.extend(list(r))
    infolist.append(f"http://item.gmarket.co.kr/Item?goodsCode={gc}")
    df.loc[len(df.index)] = infolist
AgGrid(df)
st.write("tips:")
st.write("点按属性名可进行排序和筛选。")