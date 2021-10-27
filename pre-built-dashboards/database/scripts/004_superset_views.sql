
/* Collections daily view for charts */
CREATE VIEW superset_collections_daily
AS SELECT cagg.bucket,
    c.slug,
    cagg.mean_price,
    cagg.median_price,
    cagg.volume,
    cagg.volume_eth,
    cagg.most_expensive_nft_id,
    cagg.max_price,
    ((('<a href="'::text || a.url) || '"><img src='::text) || a.img_url) || ' height=150></a>'::text AS nft_image
   FROM collections_daily cagg
     JOIN collections c ON cagg.collection_id = c.id
     JOIN assets a ON a.id = cagg.most_expensive_nft_id;
     
     
/* Assets daily view for charts */
CREATE VIEW superset_assets_daily
AS SELECT cagg.bucket,
    a.id AS asset_id,
    a.name AS asset_name,
    c.slug AS collection_slug,
    cagg.mean_price,
    cagg.median_price,
    cagg.volume,
    cagg.volume_eth,
    cagg.open_price,
    cagg.high_price,
    cagg.low_price,
    cagg.close_price,
    ((('<a href="'::text || a.url) || '"><img src='::text) || a.img_url) || ' height=150></a>'::text AS nft_image
   FROM assets_daily cagg
     JOIN collections c ON cagg.collection_id = c.id
     JOIN assets a ON a.id = cagg.asset_id;
