import re
import sqlite3
import hmac
import hashlib
import time
import requests

response = requests.get("https://api.exchange.coinbase.com/products")


def crypto_available():
    """get a list of all available cryptocurrencies and display it"""
    response = requests.get('https://api.exchange.coinbase.com/currencies').json()   # request.get method sends a get request to the api url specify, and .json() returns a JSON object of the result
    for i in range(len(response)):
        print(response[i]['id'], ":", response[i]['name'])
    print("\nThere is %d cryptocurrencies\n\n"%i)
#crypto_available()


def getDepth(direction="ask", pair="BTC-USD"):
    response = requests.get('https://api.exchange.coinbase.com/products/'+pair+'/book?level=1').json()
    
    if direction == 'ask' : print('Best ask : ',response['asks'])
    elif direction == 'bid': print('Best bid : ',response['bids'])
    else : print("You need to ask for ask, or bid, but not")
# getDepth()

def getOrderBook(direction="ask", pair="BTC-USD"):
    getDepth()
    getDepth("bid")
#getOrderBook()

# def refreshDataCandle(pair="BTC-USD",duration="5m"):
#     time = "".join(re.findall("[\d)]+",duration))
#     duration = 60*int(time)
#     if duration not in [60, 300, 900, 3600, 21600, 86400]:
#         print("Error: Invalid duration")
#     else:
#         response = requests.get('https://api.exchange.coinbase.com/products/' + pair + '/candles?granularity=' + str(duration)).json()
#         for i in range(1,6,1):
#             print("candle",i,":",response[i])
#refreshDataCandle()

def create_sqlite_table():
    # Connect to the database (/creating it if it doesn't exist)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create the data_candles table
    cursor.execute(
        "CREATE TABLE  data_candles(id INTEGER PRIMARY KEY AUTOINCREMENT, date INT, high REAL, low REAL, open REAL, close REAL, volume REAL)"
    )
    # Create the data_full table
    cursor.execute(
        "CREATE TABLE if not exists data_full(id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, traded_crypto REAL, price REAL, created_at INT, side TEXT)"
    )
    # Create the temp table
    cursor.execute(
        "CREATE TABLE if not exists temp(id INTEGER PRIMARY KEY AUTOINCREMENT, cex TEXT, trading_pair TEXT, duration TEXT, table_name TEXT, last_check INT, startdate INT, last_id INT)"
    )
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
# create_sqlite_table()


def refreshDataCandle(pair, duration):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    time = "".join(re.findall("[\d)]+",duration))
    duration = 60*int(time)

    if duration not in [60, 300, 900, 3600, 21600, 86400]:
        print("Error: Invalid duration")
    else:

        response = requests.get('https://api.exchange.coinbase.com/products/' + pair + '/candles?granularity=' + str(duration)).json()

        for candle in response:
            cursor.execute(
                "INSERT OR REPLACE INTO data_candles (date, high, low, open, close, volume) VALUES (?,?,?,?,?,?)",
                (candle[0], candle[2], candle[3], candle[4], candle[1], candle[5])
            )
    conn.commit()
    conn.close()
#You may ask why this order candle 0, candle 2, candle 3, candle 4, candle 1, candle 5?
#The reason for this is that the values in the candle list represent different data points for each candle. The format of the candle data returned by the Coinbase API is as follows:
#   timestamp,   0 - The timestamp for the start of the candle period
#   low,         1 - The lowest price during the candle period
#   high,        2 - The highest price during the candle period
#   open,        3 - The opening price for the candle period
#   close,       4 - The closing price for the candle period
#   volume       5 - The volume of trades during the candle period
# Therefore, the values in the VALUES clause are specified in the order that corresponds to the columns in the data_candles table

# refreshDataCandle("BTC-USD", "5m")

def refreshData(pair='BTC-USD'):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    response = requests.get(f'https://api.exchange.coinbase.com/products/{pair}/trades')

    if response.status_code == 200:
        data = response.json()
        for trade in data:
            print(trade)
            #id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, traded_crypto REAL, price REAL, created_at INT, side TEXT)
            cursor.execute(
                "INSERT OR REPLACE INTO data_full (uuid, traded_crypto, price, created_at, side) VALUES (?,?,?,?,?)",
                (trade["trade_id"], trade["size"], pair, trade["time"], trade["side"])
            ) 
            conn.commit()
    else:
        print("An error occurred:", response.status_code)
    conn.close()
# refreshData()

def createOrder(api_key, secret_key, direction, price, amount, pair='BTC-USD', orderType='LimitOrder'):
    params = {
        'product_id': pair,
        'side': direction,
        'price': price,
        'size': amount,
        'type': orderType,
    }

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CoinbaseAPI/1.0',
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-TIMESTAMP': str(time.time()),
        'CB-ACCESS-SIGN': hmac.new(secret_key.encode(), ''.join(
            [
                'POST',
                '/orders',
                '',
                'Content-Type: application/json',
                'User-Agent: CoinbaseAPI/1.0',
                'CB-ACCESS-KEY:' + api_key,
                'CB-ACCESS-TIMESTAMP:' + str(time.time()),
            ]
        ).encode(), hashlib.sha256).hexdigest()
    }

    response = requests.post('https://api.exchange.coinbase.com/orders', json=params, headers=headers)

    if response.status_code == 200:
        print(response.json())
    else:
        print(f'An error occurred: {response.status_code}')
# to call this function you will need you api_key and secret_key, i can't give you mine because it's a secret :)

import hmac
import hashlib
import requests
import time

def cancelOrder(api_key, secret_key, uuid):
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CoinbaseAPI/1.0',
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-TIMESTAMP': str(time.time()),
        'CB-ACCESS-SIGN': hmac.new(secret_key.encode(), ''.join(
            [
                'DELETE',
                '/orders/' + uuid,
                '',
                'Content-Type: application/json',
                'User-Agent: CoinbaseAPI/1.0',
                'CB-ACCESS-KEY:' + api_key,
                'CB-ACCESS-TIMESTAMP:' + str(time.time()),
            ]
        ).encode(), hashlib.sha256).hexdigest()
    }

    response = requests.delete(f'https://api.exchange.coinbase.com/orders/{uuid}', headers=headers)

    if response.status_code == 200:
        print(response.json())
    else:
        print(f'An error occurred: {response.status_code}')
#Same as above, you will need your api_key and secret_key