import pandas as pd
from plotly import express as px


class NFTDatabase:
    """Fetch data from the NFT transactions database and return dataframes or 
    Plotly charts 
    """
    
    def __init__(self, conn):
        self.conn = conn
    
    
    def table_expensive_items(self):
        sql = """
            SELECT a.img_url AS nft_image
            FROM collections_daily cagg
            JOIN collections c ON cagg.collection_id = c.id
            JOIN assets a ON a.id = cagg.most_expensive_nft_id
            WHERE slug IN ('cryptopunks')
            ORDER BY cagg.max_price DESC 
            LIMIT 5"""
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return [img[0] for img in cursor.fetchall()] # pd.read_sql(sql, self.conn)

    def table_most_expensive_items(self, filters):
        sql = F"""SELECT a.img_url, a.name, MAX(s.total_price) AS price, time AS sold FROM nft_sales s
                  INNER JOIN collections c ON s.collection_id = c.id
                  INNER JOIN assets a ON s.asset_id = a.id 
                  WHERE payment_symbol = 'ETH' AND slug = '{filters['collection']}' AND time >= '{filters["start_date"]}' AND time <= '{filters["end_date"]}' 
                  GROUP BY a.id, a.name, a.img_url, time
                  ORDER BY max_price DESC
                  LIMIT 5"""
        return pd.read_sql(sql, self.conn)       
    
    def line_daily_volume_count(self, filters):
        sql = f"""SELECT bucket,
                        slug,
                        max(volume) AS "volume (count)"
                FROM public.superset_collections_daily
                WHERE slug = '{filters['collection']}' AND bucket >= '{filters["start_date"]}' AND bucket <= '{filters["end_date"]}' 
                GROUP BY slug, bucket
                ORDER BY bucket
                LIMIT 50000;"""
        df = pd.read_sql(sql, self.conn)
        return px.line(df, x="bucket", y="volume (count)")
    
    def line_daily_volume_eth(self, filters):
        sql = f"""SELECT bucket,
                        slug,
                        max(volume_eth) AS "volume (ETH)"
                FROM public.superset_collections_daily
                WHERE slug = '{filters['collection']}' AND bucket >= '{filters["start_date"]}' AND bucket <= '{filters["end_date"]}' 
                GROUP BY slug, bucket
                ORDER BY bucket
                LIMIT 50000;"""
        df = pd.read_sql(sql, self.conn)
        return px.line(df, x="bucket", y="volume (ETH)")

    def list_popular_collections(self):
        sql = """
        SELECT slug FROM collections_daily cagg
        INNER JOIN collections c ON cagg.collection_id = c.id 
        GROUP BY c.id
        ORDER BY SUM(volume) DESC 
        LIMIT 30
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return [row[0] for row in cursor.fetchall()]
