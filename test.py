from influxdb import DataFrameClient
import matplotlib.pyplot as plt

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

