# Streamlit NFT sales dashboard - powered by TimescaleDB

## Install requirements

We recommend to create a separate virtual environment for this project and
install the requirements there:

```bash
virtualenv env && source env/bin/activate
pip install -r requirements.txt
```

## Modify database secrets
1. Open the `.streamlit/secrets.toml` file
1. Modify the secrets so Streamlit can connect to your database
    ```text
    [NFT_DATABASE]
    dbname="tsdb"    
    host="xxxxxxxxxxxxxx.tsdb.cloud.timescale.com"
    user="tsdbadmin"
    password="xxxxxxx"
    port=33333    
    ```

## Run the app
```bash
streamlit run app.py
```