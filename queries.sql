/*
* Data exploration queries for NFT transactions
*/


/* Count queries */
SELECT count(*) FROM assets 

SELECT count(*) FROM collections

SELECT count(*) FROM accounts

SELECT count(*), MIN(time) AS min_date, MAX(time) AS max_date FROM nft_sales 

/* Payment symbols */
SELECT payment_symbol, count(*) FROM nft_sales 
GROUP BY payment_symbol 
ORDER BY count(*) DESC 

/* Assets most often sold in the past 2 weeks*/
SELECT count(*) AS volume, a.name AS nft, a.url, c.name AS collection FROM nft_sales s
INNER JOIN assets a ON a.id = s.asset_id 
INNER JOIN collections c ON c.id = s.collection_id 
WHERE time > NOW() - INTERVAL '2 weeks'
GROUP BY s.asset_id , a.name, a.url, c.name
ORDER BY volume DESC 
LIMIT 10

/* Time-series chart: total daily ETH volume of a given collection */
SELECT 
time_bucket('1 day', time) AS bucket, 
count(*) AS total_volume, 
sum(total_price) total_volume_eth,
count(DISTINCT asset_id) AS count_nfts 
FROM nft_sales s
INNER JOIN collections c ON c.id = s.collection_id 
WHERE payment_symbol = 'ETH' AND c.name = 'CryptoKitties'
GROUP BY bucket
ORDER BY bucket DESC 


/* Most often traded collections in the past month*/
SELECT c.name AS collection, count(*) AS sale_count, count(DISTINCT asset_id) AS nft_count
FROM nft_sales s
INNER JOIN collections c ON c.id = collection_id 
WHERE time > NOW() - INTERVAL '1 month'
GROUP BY collection_id, c.name
ORDER BY sale_count DESC
LIMIT 5



/* Time-series chart: total daily ETH volume of the most traded collections */
WITH most_traded_collections AS (
	SELECT collection_id
	FROM nft_sales s
	GROUP BY collection_id
	ORDER BY count(*) DESC
	LIMIT 5
) 
SELECT 
time_bucket('1 day', time) AS bucket,
c.name AS collection, c.url AS collection_url, 
count(*) AS trade_count, 
sum(total_price) total_volume_eth,
count(DISTINCT asset_id) AS count_nfts 
FROM nft_sales s
INNER JOIN collections c ON c.id = s.collection_id
WHERE collection_id IN (SELECT * FROM most_traded_collections) AND time > NOW() - INTERVAL '1 month'
GROUP BY bucket, c.name, c.url
ORDER BY bucket DESC


/* Time-series: Average volume per 15min */
WITH buckets AS (
	SELECT time_bucket('15 min', time) AS bucket, count(*) AS volume FROM nft_sales 
	WHERE time > NOW() - INTERVAL '1 month'
	GROUP BY bucket
)
SELECT bucket, volume FROM buckets
ORDER BY bucket


/* Time-series: amount of sales weekly in the past 3 months */
SELECT time_bucket('1 week', time) AS bucket, count(*) AS volume FROM nft_sales 
WHERE time > NOW() - INTERVAL '3 month'
GROUP BY bucket
ORDER BY bucket DESC


/* Most expensive asset sold per week in the last month */
SELECT time_bucket('1 week', time) AS bucket, MAX(total_price) AS price_paid, 
LAST(a.id , total_price) AS asset_name, LAST(a.url, total_price) AS url 
FROM nft_sales s
INNER JOIN assets a ON a.id = s.asset_id 
WHERE time > NOW() - INTERVAL '1 month' AND payment_symbol = 'ETH'
GROUP BY bucket
ORDER BY bucket DESC 


/*Time-series: daily price of the most traded asset in the past <time-period> */
WITH highest_volume_asset AS (
	SELECT asset_id FROM nft_sales
	WHERE time > NOW() - INTERVAL '1 month'
	GROUP BY asset_id
	ORDER BY count(*) DESC 
	LIMIT 1
)
SELECT a.name AS nft, a.url AS nft_url, time_bucket('1 day', time) AS bucket, LAST(total_price, time) price
FROM nft_sales s
INNER JOIN assets a ON a.id = s.asset_id
WHERE asset_id = (SELECT asset_id FROM highest_volume_asset) AND time > NOW() - INTERVAL '1 month' AND payment_symbol = 'ETH'
GROUP BY bucket, a.name, a.url
ORDER BY bucket DESC 



/* Collection continuous aggregates */
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

SELECT add_continuous_aggregate_policy('collections_daily',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

/* Asset continuous aggregates */
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
HAVING COUNT(*) > 1

SELECT add_continuous_aggregate_policy('assets_daily',
     start_offset => NULL,
     end_offset => INTERVAL '1 day',
     schedule_interval => INTERVAL '1 day');


/* Collections with the highest volume? */
SELECT
slug,
SUM(volume) total_volume,
SUM(volume_eth) total_volume_eth
FROM collections_daily cagg
INNER JOIN collections c ON cagg.collection_id = c.id
GROUP BY cagg.collection_id, slug
ORDER BY total_volume DESC;


/* Daily number of “CryptoKitties” NFT transactions? */

SELECT bucket, slug, volume
FROM collections_daily cagg
INNER JOIN collections c ON cagg.collection_id = c.id
WHERE slug = 'cryptokitties'
ORDER BY bucket DESC

/* Daily number of NFT transactions, "CryptoKitties" vs Ape Gang from past 3 months? */
SELECT bucket, slug, volume
FROM collections_daily cagg
INNER JOIN collections c ON cagg.collection_id = c.id
WHERE slug IN ('cryptokitties', 'ape-gang') AND bucket > NOW() - INTERVAL '3 month'
ORDER BY bucket DESC, slug;


/* Daily ETH volume of CryptoKitties NFT transactions? */
SELECT bucket, slug, volume_eth
FROM collections_daily cagg
INNER JOIN collections c ON cagg.collection_id = c.id
WHERE slug = 'cryptokitties'
ORDER BY bucket DESC 

/* Daily ETH volume of NFT transactions: CryptoKitties vs Ape Gang? */
SELECT bucket, slug, volume_eth
FROM collections_daily cagg
INNER JOIN collections c ON cagg.collection_id = c.id
WHERE slug IN ('cryptokitties', 'ape-gang') AND bucket > NOW() - INTERVAL '3 month'
ORDER BY bucket, slug DESC;


/* Mean vs median sale price of CryptoKitties? */
SELECT bucket, slug, mean_price, median_price
FROM collections_daily cagg
INNER JOIN collections c ON cagg.collection_id = c.id
WHERE slug = 'cryptokitties'
ORDER BY bucket DESC 

/* Get the image URLs of the 5 most expensive NFTs sold in the past 3 months */
SELECT url, total_price, details->>'image_url' AS image_url FROM nft_sales
INNER JOIN assets a ON a.id = nft_sales.asset_id 
WHERE payment_symbol = 'ETH' AND time > NOW() - INTERVAL '3 month'
ORDER BY total_price DESC 
LIMIT 5

/* Calculating 15-min mean and median sale prices of highest trade count NFT on 2021-10-17 */
WITH one_day AS (
    SELECT time, asset_id, total_price FROM nft_sales
    WHERE time BETWEEN '2021-10-06 00:00:00' AND '2021-10-06 23:59:59' AND payment_symbol = 'ETH'
)
SELECT time_bucket('30 min', time) AS bucket,
assets.name AS nft,
mean(percentile_agg(total_price)) AS mean_price,
approx_percentile(0.5, percentile_agg(total_price)) AS median_price
FROM one_day
INNER JOIN assets ON assets.id = one_day.asset_id
WHERE asset_id = (SELECT asset_id FROM one_day GROUP BY asset_id ORDER BY count(*) DESC LIMIT 1)
GROUP BY bucket, nft
ORDER BY DESC

/* Weekly OHLCV per asset */
SELECT time_bucket('7 day', time) AS bucket, asset_id, 
FIRST(total_price, time) AS open_price, LAST(total_price, time) AS close_price,
MIN(total_price) AS low_price, MAX(total_price) AS high_price,
count(*) AS volume
FROM nft_sales
WHERE payment_symbol = 'ETH'
GROUP BY bucket, asset_id
HAVING count(*) > 100
ORDER BY bucket


/* Daily assets sorted by biggest intraday price change in the last 6 month*/
SELECT time_bucket('1 day', time) AS bucket, a.name AS nft, a.url,
FIRST(total_price, time) AS open_price, LAST(total_price, time) AS close_price,
MAX(total_price)-MIN(total_price) AS intraday_max_change
FROM nft_sales s
INNER JOIN assets a ON a.id = s.asset_id 
WHERE payment_symbol = 'ETH' AND time > NOW() - INTERVAL '6 month'
GROUP BY bucket, asset_id, a.name, a.url
ORDER BY intraday_max_change DESC 
LIMIT 5

/* Snoop Dogg's transactions in the past 3 months aggregated */
WITH snoop_dogg AS (
	SELECT id FROM accounts 
	WHERE address = '0xce90a7949bb78892f159f428d0dc23a8e3584d75'
)
SELECT 
COUNT(*) AS trade_count,
COUNT(DISTINCT asset_id) AS nft_count,
COUNT(DISTINCT collection_id) AS collection_count,
COUNT(*) FILTER (WHERE seller_account = (SELECT id FROM snoop_dogg)) AS sale_count,
COUNT(*) FILTER (WHERE winner_account = (SELECT id FROM snoop_dogg)) AS buy_count,
SUM(total_price) AS total_volume_eth,
AVG(total_price) AS avg_price,
MIN(total_price) AS min_price,
MAX(total_price) AS max_price
FROM nft_sales
WHERE payment_symbol = 'ETH' AND ( seller_account = (SELECT id FROM snoop_dogg) OR winner_account = (SELECT id FROM snoop_dogg) )
AND time > NOW()-INTERVAL '3 months'

/* Top 5 most expensive NFTs in the CryptoKitties collection */
SELECT a.name AS nft, total_price, time, a.url  FROM nft_sales s
INNER JOIN collections c ON c.id = s.collection_id 
INNER JOIN assets a ON a.id = s.asset_id
WHERE slug = 'cryptokitties' AND payment_symbol = 'ETH'
ORDER BY total_price DESC
LIMIT 5
