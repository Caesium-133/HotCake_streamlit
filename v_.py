import streamlit as st
from influxdb import DataFrameClient


st.title("品类趋势")


@st.experimental_singleton
def connectInflux():
    return DataFrameClient(**st.secrets["influx"])


cli = connectInflux()


@st.experimental_memo(ttl=600)
def query(SQL):
    result=cli.query(SQL)
    return result

goodsCode="1568805650"
measurement="gc"+str(goodsCode)

res=query(f"SELECT * FROM {measurement}")
df=res[measurement]
print(df.describe())


