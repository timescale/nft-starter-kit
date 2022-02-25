import streamlit as st
from db import NFTDatabase
import psycopg2
from datetime import datetime
from plotly import express as px

st.set_page_config(page_title="NFT dashboard - Powered by TimescaleDB",
                   page_icon=None,
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={
                        'About': "https://github.com/timescale/nft-starter-kit"
                    })

@st.experimental_singleton
def init_connection():
    return psycopg2.connect(**st.secrets["NFT_DATABASE"])

db = NFTDatabase(init_connection())


st.markdown(
"""
<style>
.css-zbg2rx {
    background-color: #fdb515;
}
</style>
""", unsafe_allow_html=True)



col1, col2, col3 = st.columns(3)
with col2:
    st.image("https://www.timescale.com/static/6b397f5b4e91bc728827d24975941e3d/TimescaleLogoHorizontal1Png.png")
    


st.title('NFT collection sales dashboard - TimescaleDB demo')
    
st.info(
        """Want to build your own NFT dashboard with TimescaleDB? 
        Check out the [NFT Starter Kit on GitHub!](https://github.com/timescale/nft-starter-kit)"""
    )
    

filters = {"start_date": datetime(2021, 9, 1),
           "end_date": datetime(2021, 10, 12),
           "collection_one": "",
           "collection_two": ""}

collections_info = None

with st.sidebar:
    # display filters
    min_date = datetime(2021, 1, 1)
    max_date = datetime(2021, 10, 12)
    filters["start_date"] = st.date_input("Start date: ", value=filters["start_date"], min_value=min_date, max_value=max_date)
    filters["end_date"] = st.date_input("End date: ", value=filters["end_date"], min_value=min_date, max_value=max_date)
    collections_options = db.list_popular_collections(filters=filters)
    filters["collection_one"] = st.selectbox("Collection", collections_options, 0)
    filters["collection_two"] = st.selectbox("compare to", collections_options, 1)
    
    # display collection images in the correct order
    collections_info = db.collection_info(filters=filters)
    swap = None
    if collections_info[0][7] != filters["collection_one"]:
        swap = collections_info[0]
        collections_info[0] = collections_info[1]
        collections_info[1] = swap
    
    st.image(collections_info[0][2])
    if len(collections_info) > 1:
        st.image(collections_info[1][2])
        

# @st.experimental_memo
def cagg_collections_daily(filters):
    return db.table_cagg_collections_daily(filters)

cagg_df = cagg_collections_daily(filters)


col1, col2 = st.columns(2)
with col1:
    info = collections_info[0]
    st.subheader(f"Selected collection: {info[0]}")
    collection_img = info[2]
    md = f"""
    | OpenSea | <a href="{info[1]}">{info[0]}</a>  |
    |:-------:|---|
    | created | {info[4]} |
    | twitter | <a href="https://twitter.com/{info[6]}"> {"" if info[6] is None else f"@{info[6]}"}  |
    | discord | {"" if info[3] is None else info[3]} |
    | web | {"" if info[5] is None else info[5]} |
    """
    st.markdown(md, unsafe_allow_html=True)


with col2:
    st.subheader(f"Most expensive items sold")
    df = db.table_most_expensive_items(filters=filters)
    image_urls = []
    for index, row in df.iterrows():
        if row["img_url"]:
            image_urls.append((row["img_url"]))
    if len(image_urls) > 0:
        with st.expander("Items"):
            st.image(image_urls, width=110)
    st.table(df[["name", "price", "sold"]])


st.subheader(f"Daily median price")
chart = px.line(cagg_df, x="bucket", y=["median price"], color="slug",
                template="simple_white", markers=True)
st.plotly_chart(chart, use_container_width=True)


col1, col2 = st.columns(2)
with col1:
    st.subheader(f"Daily number of NFT transactions")
    chart = px.line(cagg_df, x="bucket", y="volume (count)", color="slug",
                    template="simple_white", markers=True)
    st.plotly_chart(chart)

with col2:
    st.subheader(f"Daily ETH volume of NFT transactions")
    chart = px.line(cagg_df, x="bucket", y="volume (ETH)", color="slug",
                    template="simple_white", markers=True)
    st.plotly_chart(chart)

