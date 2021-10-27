#!/bin/bash
set -e
echo '****************IMPORTING NFT DATA INTO TIMESCALEDB****************'
psql -v --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	\copy accounts FROM '001_accounts.csv' CSV HEADER;
	\copy collections FROM '002_collections.csv' CSV HEADER;
	\copy assets FROM '003_assets.csv' CSV HEADER;
	\copy nft_sales FROM '004_nft_sales.csv' CSV HEADER;
EOSQL
