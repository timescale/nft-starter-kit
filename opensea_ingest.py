import requests
import json
import psycopg2
from psycopg2.extras import execute_values
import time
from datetime import datetime, timezone
import config


def write_json(json_obj, file_name):
    with open(file_name, 'wb') as f:
        f.write(json_obj)


def _insert_accounts(cursor):
    sql = """
        INSERT INTO accounts (user_name, address, details)
        SELECT * FROM (
            SELECT account_seller_user_name, account_seller_address, account_seller_details::JSONB 
            FROM temp_table
            UNION
            SELECT account_winner_user_name, account_winner_address, account_winner_details::JSONB 
            FROM temp_table
            UNION
            SELECT account_from_user_name, account_from_address, account_from_details::JSONB
            FROM temp_table
            UNION
            SELECT account_to_user_name, account_to_address, account_to_details::JSONB 
            FROM temp_table
            UNION
            SELECT account_owner_user_name, account_owner_address, account_owner_details::JSONB 
            FROM temp_table
        ) s
        WHERE account_seller_address IS NOT NULL 
        ON CONFLICT DO NOTHING;
    """
    cursor.execute(sql)
    

def _insert_collections(cursor):
    sql = """
        INSERT INTO collections (slug, name, url, details)
        SELECT collection_slug, collection_name, collection_url, collection_details::JSONB FROM temp_table
        ON CONFLICT DO NOTHING;
    """
    cursor.execute(sql)
    
    
def _insert_assets(cursor):
    sql = """
        INSERT INTO assets (id, name, collection_id, description, contract_date, url, img_url, owner_id, details)
        SELECT asset_id::BIGINT, asset_name, c.id, asset_description, asset_contract_date::TIMESTAMPTZ, asset_url, asset_img_url, a.id, asset_details::JSONB 
        FROM temp_table t
        INNER JOIN collections c ON c.slug = t.collection_slug 
        INNER JOIN accounts a ON a.address = t.account_owner_address 
        ON CONFLICT DO NOTHING;
    """
    cursor.execute(sql)

def _insert_nft_sales(cursor):
    sql = """
        INSERT INTO nft_sales (id, time, asset_id, auction_type, contract_address, quantity, payment_symbol, total_price, 
        seller_account, from_account, to_account, winner_account, collection_id)
        SELECT event_id::BIGINT, event_time::TIMESTAMPTZ, a.id, event_auction_type::auction, event_contract_address, event_quantity::NUMERIC, event_payment_symbol, 
        event_total_price::DOUBLE PRECISION, seller_acc.id, from_acc.id, to_acc.id, winner_acc.id, a.collection_id 
        FROM temp_table t
        INNER JOIN assets a ON a.id = t.asset_id::BIGINT
        LEFT JOIN accounts seller_acc ON seller_acc.address = t.account_seller_address 
        LEFT JOIN accounts from_acc ON from_acc.address = t.account_from_address 
        LEFT JOIN accounts to_acc ON to_acc.address = t.account_to_address 
        LEFT JOIN accounts winner_acc ON winner_acc.address = t.account_winner_address 
        ON CONFLICT DO NOTHING;
    """
    cursor.execute(sql)


def zero_gen(n):
    """Returns n amount of zeros (0) in string format, eg n=3 => "000"
    """
    zeros = ""
    for i in range(0, n):
        zeros = zeros + "0"
    return zeros


def fetch_opensea_json(occurred_before, occurred_after=None, limit=300, offset=0, json_file="", event_type=''):
    url = "https://api.opensea.io/api/v1/events"
    querystring = {"only_opensea":"false", 
                   "offset":"{}".format(offset), 
                   "limit":"{}".format(limit), 
                   "occurred_before": "{}".format(occurred_before),
                   "occurred_after": "{}".format(occurred_after)}
    
    if event_type != '':
        querystring['event_type'] = event_type

    apikey = config.OPENSEA_APIKEY
    headers = None if apikey == "" else {"X-API-KEY": apikey}
    response = requests.request("GET", url, headers=headers, params=querystring)
    
    # write the response to a JSON file
    if json_file != "":
        write_json(response.content, json_file)
        
    if "<!doctype html>" in response.text[:20].lower():
        return None # blocked request
    return response.json()


def _get_price_value(event, price_key, decimals=18):
    if event.get(price_key) == None:
        return None
    if event.get('payment_token') != None and event.get('payment_token').get('decimals') != None:
        decimals = event.get('payment_token').get('decimals')
        
    amount_str = event.get(price_key)
    if len(amount_str) < 18:
        needed_zeros = 18-len(amount_str)
        amount_str =  "0." + zero_gen(needed_zeros)  + amount_str
        return float(amount_str)
    return float(amount_str[:-decimals] + "." + amount_str[len(amount_str)-decimals:])
    
    
def _get_account_item(event, key):
    account = {}
    if event.get(key) != None:
        account['address'] = event[key].get('address')
        account['json'] = json.dumps(event[key])
        if event[key].get('user') != None:
            account['user'] = event[key]['user'].get('username')
    return account


def _clean_collection(asset):  
    return {
        'collection_slug': asset['collection']['slug'],
        'collection_name': asset['collection']['name'],
        'collection_url': "https://opensea.io/collection/" + asset['collection']['slug'],
        'collection_details': json.dumps(asset['collection'])
    }


def _clean_account(event, account_key):
    account_item = _get_account_item(event, account_key)
    if account_key == 'owner': 
        return {
            'account_owner_user_name': account_item.get('user'),
            'account_owner_address': account_item.get('address'),
            'account_owner_details': account_item.get('json')}
    elif account_key == 'winner_account':
        return {
            'account_winner_user_name': account_item.get('user'),
            'account_winner_address': account_item.get('address'),
            'account_winner_details': account_item.get('json')}
    elif account_key == 'to_account':
        return {
            'account_to_user_name': account_item.get('user'),
            'account_to_address': account_item.get('address'),
            'account_to_details': account_item.get('json')}
    elif account_key == 'from_account':
        return {
            'account_from_user_name': account_item.get('user'),
            'account_from_address': account_item.get('address'),
            'account_from_details': account_item.get('json')}
    elif account_key == 'seller':
        return {
            'account_seller_user_name': account_item.get('user'),
            'account_seller_address': account_item.get('address'),
            'account_seller_details': account_item.get('json')}


def _clean_asset(asset):
    return {
        'asset_id': asset['id'],
        'asset_name': asset['name'],
        'asset_description': asset['description'],
        'asset_contract_date': asset['asset_contract']['created_date'],
        'asset_url': asset['permalink'],
        'asset_img_url': asset['image_url'],
        'asset_details': json.dumps(asset)
    }
    
    
def _clean_event(event):
    return {
            'event_id': event['id'],
            'event_time': event.get('created_date'),
            'event_auction_type': event.get('auction_type'),
            'event_contract_address': event.get('contract_address'),
            'event_quantity': event.get('quantity'),
            'event_payment_symbol': None if event.get('payment_token') == None else event.get('payment_token').get('symbol'),
            'event_total_price': _get_price_value(event, price_key='total_price')
            }


def insert_values(cursor, list_of_dicts):
    columns = list_of_dicts[0].keys()

    # create temp table to insert to
    sql_temp = "DROP TABLE IF EXISTS temp_table; CREATE TEMPORARY TABLE temp_table ({}".format(' TEXT, '.join(columns)) + " TEXT);"
    cursor.execute(sql_temp)
    
    # batch insert to temp table
    sql_insert = "INSERT INTO temp_table ({}) VALUES %s".format(','.join(columns))
    values = [[value for value in item.values()] for item in list_of_dicts]
    execute_values(cursor, sql_insert, values)
    print("Data loaded into temp table!")
    
    # insert into tables (order matters!)
    _insert_accounts(cursor)
    _insert_collections(cursor)
    _insert_assets(cursor)
    _insert_nft_sales(cursor)
    conn.commit()
    print("Data ingested!")


# turns the opensea response into a list of dicts that contain all needed data fields in a denormalized fashion
def clean_response(opensea_event_response):
    event_items = opensea_event_response['asset_events']
    denormalized_items = []
    for event in event_items:    
        asset_item = event.get('asset')
        
        # check if asset item exists
        if event.get('asset') == None:
            continue # if there's no asset that means it's not a single NFT transaction so skip this item
        
        # accounts
        cleaned_seller = _clean_account(event, 'seller')
        cleaned_winner = _clean_account(event, 'winner_account')
        cleaned_from_acc = _clean_account(event, 'from_account')
        cleaned_to_acc = _clean_account(event, 'to_account')
        cleaned_owner_acc = _clean_account(asset_item, 'owner')
        # event
        cleaned_event = _clean_event(event)
        # asset
        cleaned_asset = _clean_asset(asset_item)
        # collection
        cleaned_collection = _clean_collection(asset_item)
        # everything denormalized
        denormalized_item = {**cleaned_seller, **cleaned_winner, **cleaned_from_acc, 
                             **cleaned_to_acc, **cleaned_event, **cleaned_asset, 
                             **cleaned_collection, **cleaned_owner_acc}
        # add item to the list
        denormalized_items.append(denormalized_item)
    return denormalized_items
    

def fetch_multiple_events(start_date, end_date, rate_limiting=None, event_type="successful"):
    # these values are the maximum that the OpenSea API allows per request
    MAX_API_ITEMS = 300
    MAX_OFFSET = 10000
    
    i = 0
    MAX_ITERATIONS = MAX_OFFSET/MAX_API_ITEMS
    while i < MAX_ITERATIONS:
        # rate limiting
        if rate_limiting != None:
            time.sleep(rate_limiting)
        print("---\nFetching transactions from OpenSea...")
        opensea_response = fetch_opensea_json(occurred_before=int(end_date.timestamp()), 
                                        occurred_after=int(start_date.timestamp()), 
                                        limit=MAX_API_ITEMS, 
                                        offset=i*MAX_API_ITEMS, 
                                        event_type=event_type, 
                                        json_file='latest_item.json')
        
        # if request is blocked by the API, wait then retry
        if opensea_response == None:
            print("Request blocked... retrying...")
            time.sleep(6) # wait a little then continue with the same loop
            continue
            
        # iterate
        i += 1
        
        cleaned_response = clean_response(opensea_response)
        if len(cleaned_response) > 0:
            yield cleaned_response
        else:
            yield None

                
def fetch_earliest_date(conn):
    sql = "SELECT time FROM nft_sales ORDER BY time ASC LIMIT 1;"
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor.fetchone()[0].replace(tzinfo=timezone.utc)


def start_ingest(start_date, end_date, rate_limiting=2):
    """Ingests NFT transactions (backfilling) from the defined time period.

    Args:
        start_date ([type]): first timestamp when the ingestion should start from
        end_date ([type]): final timestamp when the ingestion should finish at
        rate_limiting (int, optional): Rate limit for the API. Defaults to 2.
    """
    cursor = conn.cursor()
    keep_ingesting = True
    print("Start ingesting data between {} and {}".format(start_date, end_date))
    while keep_ingesting:
        multiple_events = fetch_multiple_events(start_date, end_date, rate_limiting=rate_limiting)
        for one_batch in multiple_events:
            if one_batch != None:
                # check if batch is in the correct time period
                current_batch_time = datetime.fromisoformat(one_batch[-1]['event_time']).replace(tzinfo=timezone.utc)
                if len(one_batch) > 0 and current_batch_time >= start_date:
                    insert_values(cursor, one_batch)
                    print("Data has been backfilled until this time: {}".format(current_batch_time))
                else:
                    keep_ingesting = False
                    break
            else:
                keep_ingesting = False
                break
        end_date = fetch_earliest_date(conn)
    print("All rows have been inserted from the defined time period!")

conn = psycopg2.connect(database=config.DB_NAME, 
                        host=config.DB_HOST, 
                        user=config.DB_USER, 
                        password=config.DB_PASS, 
                        port=config.DB_PORT)

# insert OpenSea data from a defined time period
# all transactions will be inserted between the start_date and end_date timestamps
start_date = datetime.fromisoformat(config.OPENSEA_START_DATE).replace(tzinfo=timezone.utc)
end_date = datetime.fromisoformat(config.OPENSEA_END_DATE).replace(tzinfo=timezone.utc)
start_ingest(start_date, end_date)

# You can also define dates like this:
# start_date = datetime(2021, 10, 5, 3, 20, tzinfo=timezone.utc)
# end_date = datetime(2021, 10, 7, 3, 21,  tzinfo=timezone.utc)
