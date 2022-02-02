import streamlit as st
from db import NFTDatabase
import psycopg2
from datetime import datetime

st.set_page_config(page_title="NFT dashboard - Powered by TimescaleDB",
                   page_icon=None,
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={
                        'About': "https://github.com/timescale/nft-starter-kit"
                    })


def init_connection():
    return psycopg2.connect(**st.secrets["NFT_DATABASE"])


db = NFTDatabase(init_connection())

col1, col2 = st.columns(2)
with col1:
    st.title('NFT collection sales dashboard')
    st.info(
        """Want to build your own NFT dashboard with TimescaleDB? 
        Check out the [NFT Starter Kit on GitHub!](https://github.com/timescale/nft-starter-kit)"""
    )

filters = {"start_date": datetime(2021, 8, 1),
           "end_date": datetime(2021, 10, 12),
           "collection": ""}

col1, col2 = st.columns(2)
with col1:
    with st.expander("Filters"):
        st.write("""
            Use these filters to change the analyzed time range or the collection(s)
        """)
        
        min_date = datetime(2021, 1, 1)
        max_date = datetime(2021, 10, 12)
        
        filters["start_date"] = st.date_input("Start date: ", value=filters["start_date"], min_value=min_date, max_value=max_date)
        filters["end_date"] = st.date_input("End date: ", value=filters["end_date"], min_value=min_date, max_value=max_date)
        
        filters["collection"] = st.selectbox("Select a collection", db.list_popular_collections())

with col2:
    st.subheader(f"Most expensive items sold - {filters['collection']}")
    df = db.table_most_expensive_items(filters=filters)
    image_urls = []
    for index, row in df.iterrows():
        if row["img_url"]:
            image_urls.append((row["img_url"]))
    with st.expander("Items"):
        st.image(image_urls, width=140)
    st.table(df[["name", "price", "sold"]])


col1, col2 = st.columns(2)
with col1:
    st.subheader(f"Daily number of NFT transactions - {filters['collection']}")
    chart = db.line_daily_volume_count(filters=filters)
    st.plotly_chart(chart)

with col2:
    st.subheader(f"Daily ETH volume of NFT transactions - {filters['collection']}")
    chart = db.line_daily_volume_eth(filters=filters)
    st.plotly_chart(chart)

