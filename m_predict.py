import streamlit as st
import mysql.connector
import pandas as pd

st.set_page_config(page_title="热销预测-普通版",page_icon="🥞")
st.title("热销预测")
st.write("根据原创模型对商品进行评分，得分越高，越有可能再接下来一段时间内热销。")
st.write("这是普通预测，仅展示第5-10名。")


@st.experimental_singleton
def connectMySql():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = connectMySql()


@st.experimental_memo(ttl=600)
def query(SQL):
    with conn.cursor() as cur:
        cur.execute(SQL)
        return cur.fetchall()

res=query("select goodsCode,score from predictedHotCake order by score desc limit 4,6")
df=pd.DataFrame(columns=["排名","商品编号","得分","链接"])
for r in res:
    gc=r[0]
    infolist = [len(df.index) + 5]
    infolist.extend(list(r))
    infolist.append(f"http://item.gmarket.co.kr/Item?goodsCode={gc}")
    df.loc[len(df.index)] = infolist
st.table(df)



