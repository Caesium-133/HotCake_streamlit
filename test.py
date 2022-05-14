from influxdb import DataFrameClient
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def connectInflux():
    return DataFrameClient(host= "8.142.74.245",
                            username= "root",
                            password="123root456",
                            database="itemExample2")


cli = connectInflux()


def query(SQL):
    result=cli.query(SQL)
    return result

goodsCode="232558632"
measurement="gc"+str(goodsCode)

res=query(f"SELECT * FROM {measurement}")
df=res[measurement]

fig=plt.figure()
plt.plot(df["price"].astype(float))
plt.show()


