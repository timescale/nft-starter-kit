# Timescale NFT starter kit

This repository containes the code for the NFT starter kit. Read the tutorial here.

Project components:

* 1
* 2
* 3

## Running the ingestion script
...

## Running the pre-built Superset dashboard
...

### Ingest the sample data
...

Connect to the database
```bash
psql -x "postgres://host:port/tsdb?sslmode=require"
```

Import the CSV files in this order:
```bash
\copy accounts FROM accounts.csv CSV HEADER;
\copy collections FROM collections.csv CSV HEADER;
\copy assets FROM assets.csv CSV HEADER;
\copy nft_sales FROM nft_sales.csv CSV HEADER;
```
