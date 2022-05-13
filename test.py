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


evaDF=pd.DataFrame
evaDF_std=pd.DataFrame
W=pd.DataFrame()

# 熵权法
# 标准化
for i in evaDF.columns:
    Max = np.max(evaDF[i])
    Min = np.min(evaDF[i])
    #     if (i=='严重失信次数') or (i=='供货稳定性'):
    #         evaDF[i]=(Max-evaDF[i])/(Max-Min)
    #     else:
    evaDF[i] = (evaDF[i] - Min) / (Max - Min)

evaDF_std = evaDF

# 计算指标比重
for i in evaDF.columns:
    sigma_xij = sum(evaDF[i])
    evaDF[i] = evaDF[i].apply(lambda x_ij: x_ij / sigma_xij if x_ij / sigma_xij != 0 else 1e-6)

# 求熵值
k = 1 / np.log(401)
E_j = (-k) * np.array([sum([pij * np.log(pij) for pij in evaDF[column]]) for column in evaDF.columns])
E = pd.Series(E_j, index=evaDF.columns, name='指标的熵值')

# 差异系数
G = pd.Series(1 - E_j, index=evaDF.columns, name='差异系数')

# 权重
W = G / sum(G)
W.name = '权重指标'

print(W)


#TOPSIS
#数据归一化
Y=np.array(evaDF_std)
mms=MinMaxScaler()
Y=mms.fit_transform(Y)

#确定最优方案和最劣方案
Z=np.zeros((401,5))
for i in range(401):
    for j in range(5):
        Z[i,j]=Y[i,j]*W.iloc[j]
Imax=Z.max(axis=0)
Imin=Z.min(axis=0)
I=pd.DataFrame([Imax,Imin],index=['最优解','最劣解'])

#计算各评价对象与最优方案、最烈方案的接近程度
Dmax=Z.copy()
Dmin=Z.copy()
for i in range(401):
    for j in range(5):
        Dmax[i][j]=(Imax[j]-Z[i][j])**2
        Dmin[i][j]=(Imin[j]-Z[i][j])**2
Dmax=Dmax.sum(axis=1)**0.5
Dmin=Dmin.sum(axis=1)**0.5

#给出综合评价
C=Dmin/(Dmin+Dmax)
Dmax=pd.Series(Dmax,name='最优解')
Dmin=pd.Series(Dmin,name='最劣解')
C=pd.Series(C,name='综合评价')

C.to_excel("熵权Topsis综合评价_bsoa_220410_220501.xls")

