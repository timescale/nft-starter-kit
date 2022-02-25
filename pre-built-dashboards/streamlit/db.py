import pandas as pd
import psycopg2.extras


class NFTDatabase:
    """Fetch data from the NFT transactions database and return dataframes or 
    Plotly charts 
    """
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()
        
    def table_cagg_collections_daily(self, filters):
        sql = f"""
        SELECT bucket, slug, volume AS "volume (count)", volume_eth AS "volume (ETH)", max_price AS "max price", median_price AS "median price"
        FROM streamlit_collections_daily cagg
        INNER JOIN collections c ON c.id = cagg.collection_id
        WHERE slug IN ('{filters["collection_one"]}', '{filters["collection_two"]}') AND bucket >= '{filters["start_date"]}' AND bucket <= '{filters["end_date"]}' 
        ORDER BY bucket
        """
        return pd.read_sql(sql, self.conn)

    def table_most_expensive_items(self, filters):
        sql = F"""SELECT a.img_url, a.name, MAX(s.total_price) AS price, time AS sold FROM nft_sales s
                  INNER JOIN collections c ON s.collection_id = c.id
                  INNER JOIN assets a ON s.asset_id = a.id 
                  WHERE payment_symbol = 'ETH' AND slug = '{filters["collection_one"]}' AND time <= '{filters["end_date"]}' 
                  GROUP BY a.id, a.name, a.img_url, time
                  ORDER BY price DESC
                  LIMIT 5"""
        return pd.read_sql(sql, self.conn)       

    def list_popular_collections(self, filters):
        sql = f"""
        SELECT slug FROM streamlit_collections_daily cagg
        INNER JOIN collections c ON cagg.collection_id = c.id 
        WHERE bucket >= '{filters["start_date"]}' AND bucket <= '{filters["end_date"]}' 
        GROUP BY c.id
        ORDER BY SUM(volume) DESC 
        LIMIT 30
        """
        self.cursor.execute(sql)
        return [row[0] for row in self.cursor.fetchall()]

    def collection_info(self, filters):
        sql = f"""
        SELECT name, url, 
        details->>'image_url' AS image_url, 
        details->>'discord_url' AS discord_url,
        details->>'created_date' AS created_date,
        details->>'external_url' AS web_url,
        details->>'twitter_username' AS twitter_user,
        slug
        FROM collections
        WHERE slug IN ('{filters["collection_one"]}', '{filters["collection_two"]}')
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql)
        return cur.fetchall()

