CREATE EXTENSION timescaledb_toolkit;

/* Asset caggs */
CREATE MATERIALIZED VIEW assets_daily 
WITH (timescaledb.continuous) AS 
SELECT time_bucket('1 day', time) AS bucket,
asset_id,
collection_id, 
mean(percentile_agg(total_price)) AS mean_price,
approx_percentile(0.5, percentile_agg(total_price)) AS median_price,
COUNT(*) AS volume,
SUM(total_price) AS volume_eth,
FIRST(total_price, time) AS open_price,
MAX(total_price) AS high_price,
MIN(total_price) AS low_price,
LAST(total_price, time) AS close_price
FROM nft_sales
WHERE payment_symbol = 'ETH'
GROUP BY bucket, asset_id, collection_id
HAVING COUNT(*) > 1;


/* Collection caggs */
CREATE MATERIALIZED VIEW collections_daily
WITH (timescaledb.continuous) AS
SELECT
collection_id,
time_bucket('1 day', time) AS bucket,
mean(percentile_agg(total_price)) AS mean_price,
approx_percentile(0.5, percentile_agg(total_price)) AS median_price,
COUNT(*) AS volume,
SUM(total_price) AS volume_eth,
LAST(asset_id, total_price) AS most_expensive_nft_id,
MAX(total_price) AS max_price
FROM nft_sales
GROUP BY bucket, collection_id;


