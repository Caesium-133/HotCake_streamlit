import pandas as pd
from influxdb import DataFrameClient
import streamlit as st

def connectInflux():
    return DataFrameClient(**st.secrets["influx"])


cli = connectInflux()


def query(SQL):
    result=cli.query(SQL)
    return result

goodsCode="1568805650"
measurement="gc"+str(goodsCode)

res=query(f"SELECT * FROM {measurement}")
df=res[measurement]
print(df.describe())