import streamlit as st
import mysql.connector
import pandas as pd
from st_aggrid import AgGrid

st.title("选品工具")
st.write("根据您指定的属性，提供商品选择和其统计信息")


@st.experimental_singleton
def connectMySql():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = connectMySql()


@st.experimental_memo(ttl=600)
def query(SQL):
    with conn.cursor() as cur:
        cur.execute(SQL)
        return cur.fetchall()


selectedCat = {
    "lcc": None,
    "mcc": None,
    "scc": None
}
lcSQL = 'SELECT DISTINCT largeCatCode, largeCatTitle FROM categories'
lcs = query(lcSQL)
lcDict = {lc[1]: lc[0] for lc in lcs}
lcTitle = st.selectbox("一级分类:", lcDict.keys())
if lcTitle:
    selectedCat["lcc"] = lcDict[lcTitle]
    mcSQL = f'SELECT DISTINCT mediumCatCode, mediumCatTitle FROM categories WHERE largeCatTitle = "{lcTitle}"'
    mcs = query(mcSQL)
    mcDict = {mc[1]: mc[0] for mc in mcs}
    mcTitles = ["不选"]
    mcTitles.extend(list(mcDict.keys()))
    mcTitle = st.selectbox("二级分类:", mcTitles)
    if mcTitle != "不选":
        selectedCat["mcc"] = mcDict[mcTitle]
        scSQL = f'SELECT DISTINCT smallCatCode, smallCatTitle FROM categories WHERE largeCatTitle = "{lcTitle}" and mediumCatTitle = "{mcTitle}"'
        scs = query(scSQL)
        scDict = {sc[1]: sc[0] for sc in scs}
        scTitles = ["不选"]
        scTitles.extend(list(scDict.keys()))
        scTitle = st.selectbox("三级分类:", scTitles)
        if scTitle != "不选":
            selectedCat["scc"] = scDict[scTitle]
mcSQL = f" AND cat_2_code={selectedCat['mcc']}" if selectedCat['mcc'] else ""
scSQL = f" AND cat_3_code={selectedCat['scc']}" if selectedCat['scc'] else ""

with st.sidebar:
    st.subheader("请选择需要的属性:")
    needPrice = st.checkbox("价格区间", True)
    needShop = st.checkbox("店铺", True)
    needHonor = st.checkbox("商品荣誉")
    needShopHonor = st.checkbox("店铺荣誉", True)
    needBrand = st.checkbox("品牌", True)
    needProductStatus = st.checkbox("商品状况")
    needBusinessClass = st.checkbox("商业类别")
    needSource = st.checkbox("商品来源")
    needProductAndModelName = st.checkbox("产品型号")
    needManufacturerNImporter = st.checkbox("生产商或进口商")
    needCountryOfManufacture = st.checkbox("原产国")
    needMaterial = st.checkbox("材质")
    needSize = st.checkbox("大小")
    needWeight = st.checkbox("重量")
    needColour = st.checkbox("颜色")
    needBookNanme = st.checkbox("作品名称")
    needAuthor = st.checkbox("创作者")
    needPublisher = st.checkbox("出版商")

SQL = f" WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL

if needPrice:
    prices = query(
        "SELECT min(realprice), max(realprice) FROM itemInfo" + f" WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL)
    minp = int(prices[0][0])
    maxp = int(prices[0][1])
    st.write(minp)
    st.write(maxp)
    priceSpan = st.slider("价格区间：",min_value=minp,max_value=maxp, value=(5000 if minp<5000 else int(minp*1.8), int(maxp * 0.8)),step=100)
    SQL += f" and realprice >= {priceSpan[0]} and realprice <= {priceSpan[1]} "
if needHonor:
    honors = st.multiselect("商品荣誉：", ["Best", "Official", "SmileDelivery", "ExpressShop"], ["Best"])
    # SQL+=" and isBest=1" if "Best" in honors else ""
    # SQL+=" and isOfficial=1" if "Official" in honors else ""
    # SQL += " and isSmileDelivery=1" if "SmileDelivery" in honors else ""
    # SQL += " and isExpressShop=1" if "ExpressShop" in honors else ""
    for h in honors:
        SQL += f" and is{h}=1"

if needShop:
    shopSQL = f"SELECT DISTINCT shopTitle FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL
    shopsL = query(shopSQL)
    shopList = [st[0] for st in shopsL]
    shopMaxes = query(
        f"SELECT shopTitle, COUNT(*) FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL + " Group by shopTitle order by COUNT(*) desc LIMIT 3")
    shopMax = [sm[0] for sm in shopMaxes]

    shops = st.multiselect(f"店铺: (共{len(shopList)}个)", shopList, shopMax)
    # SQL += f" and shopTitle in {shops[0]}" if len(shops)>0 else ""
    # if len(shops)>1:
    #     for shop in shops[1:]:
    #         SQL+=f"or shopTitle={shop}"
    if len(shops) > 0:
        SQL += f" and shopTitle in ({shops})"

if needShopHonor:
    shopHornor = st.multiselect("店铺荣誉:", ["파워딜러", "고객만족우수"], ["파워딜러"])
    if "파워딜러" in shopHornor:
        SQL += f" and isPowerDealer=1"
    if "고객만족우수" in shopHornor:
        SQL += f" and isInterestShop=1"


# if needBrand:
#     brandsList=query(f"SELECT DISTINCT brand FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL+ " AND brand<>\"\" GROUP BY brand ORDER BY COUNT(*) DESC")
#     if len(brandsList)>0:
#         brands=st.multiselect("品牌名",brandsList,brandsList[0])
#         SQL+=f" and brand in ({brands})"

def otherAttr(word, zh, count=False):
    nlist = query(
        f"SELECT DISTINCT {word} FROM itemInfo WHERE cat_1_code={selectedCat['lcc']} " + mcSQL + scSQL + f" AND {word}<>\"\" GROUP BY {word} ORDER BY COUNT(*) DESC")
    if len(nlist) > 0:
        nsl = [nl[0] for nl in nlist]
        if count:
            ns = st.multiselect(zh + f": (共{len(nsl)}个)", nsl, nsl[:3])
        else:
            ns = st.multiselect(zh + ":", nsl, nsl[:3])
        if len(ns) > 0:
            return f" and {word} in ({(ns)})"
    return ""


if needBrand:
    SQL += otherAttr("brand", "品牌名", count=True)
if needProductStatus:
    SQL += otherAttr("productStatus", "产品状况")
if needBusinessClass:
    SQL += otherAttr("businessClassification", "商业类别")
if needSource:
    SQL += otherAttr("source", "商品来源")
if needProductAndModelName:
    SQL += otherAttr("productAndModelName", "产品型号")
if needManufacturerNImporter:
    SQL += otherAttr("ManufacturerNImporter", "生产商或进口商")
if needCountryOfManufacture:
    SQL += otherAttr("countryOfManufacture", "原产国")
if needMaterial:
    SQL += otherAttr("material", "材质")
if needSize:
    SQL += otherAttr("size", "大小")
if needWeight:
    SQL += otherAttr("weight", "重量")
if needColour:
    SQL += otherAttr("color", "颜色")
if needBookNanme:
    SQL += otherAttr("bookName", "作品名称")
if needAuthor:
    SQL += otherAttr("author", "创作者")
if needPublisher:
    SQL += otherAttr("publisher", "出版商")

if st.button("确定"):
    finalSQL = "SELECT goodsCode, title, realPrice, brand, shopTitle FROM itemInfo" + SQL
    finalSQL = finalSQL.replace("[", "").replace("]", "")
    finRes = query(finalSQL)
    df = pd.DataFrame(columns=["排名", "商品编号", "商品名", "现价", "品牌", "店铺名", "商品链接"])
    for fr in finRes:
        gc = fr[0]
        infolist = [len(df.index) + 1]
        infolist.extend(list(fr))
        infolist.append(f"http://item.gmarket.co.kr/Item?goodsCode={gc}")
        df.loc[len(df.index)] = infolist
    AgGrid(df, theme="material")
