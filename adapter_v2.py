#!/usr/bin/python3
import random
import time
import json
import hmac
import hashlib
import requests
from urllib.parse import urljoin, urlencode
from binance import Client
import pandas as pd
from requests_toolbelt.adapters import source

source_adapt = source.SourceAddressAdapter('192.168.100.2')

print(f'Source ip adress: {source_adapt.source_address[0]}')

def create_order(params):  # Func for creating order
    counter = 1
    try_N = 0
    print('Creating order')
    PATH = '/api/v3/order'
    params['timestamp'] = int(time.time() * 1000)

    orders = []
    timing = []

    query_string = urlencode(params)
    print('Query to: ', query_string)
    params['signature'] = hmac.new(secret_Key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(BASE_URL, PATH)
    print(url)
    with requests.Session() as session:
        session.mount('https://', source_adapt)
        print(source_adapt.source_address[0])
        r = session.post(url, headers=headers, params=params)


    del params['signature']
    if r.status_code == 200:
        data_from_api = client.get_open_orders()
        a = json.dumps(data_from_api)
        c = json.loads(a)
        order_id = c[0]['orderId']
        print(f'order_id {order_id}\n')
        params['cancelOrderId'] = order_id
        params['cancelReplaceMode'] = 'STOP_ON_FAILURE'
        move_order(params, counter, try_N, orders, timing)

    else:
        print(r)
        print(r.status_code, r.json())
    return params

def move_order(params, counter, try_N, orders, timing): # Func for move order
    try_N += 1
    if try_N <= tryes_limit:
        print(f'Number of try: {try_N}')
        PATH = '/api/v3/order/cancelReplace'
        params['timestamp'] = int(time.time() * 1000)
        a = random.randint(0, 1)  # Random selection to change quantity or price
        if a == 0:
            counter += 1
            if counter % 2 == 0:
                params['price'] = params['price'] - 10
            else:
                params['price'] = params['price'] + 10
        elif a == 1:
            counter += 1
            if counter % 2 == 0:
                params['quantity'] = round((params['quantity'] + 0.001), 3)
            else:
                params['quantity'] = round((params['quantity'] - 0.001), 3)
        else:
            print('Something went wrong...')
            cancel_order(params, orders, timing)

        query_string = urlencode(params)
        print('Query to : ', query_string)
        params['signature'] = hmac.new(secret_Key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        url = urljoin(BASE_URL, PATH)

        with requests.Session() as session:
            session.mount('https://', source_adapt)
            print(source_adapt.source_address[0])
            r = session.post(url, headers=headers, params=params)

        elapsed_time = r.elapsed.total_seconds()
        timing.append(str(elapsed_time))
        del params['signature']
        print('Save time on moving the order...')
        orders.append(params['cancelOrderId'])

        if r.status_code == 200:
            data_from_api = client.get_open_orders()
            a = json.dumps(data_from_api)
            c = json.loads(a)
            new_order_id = c[0]['orderId']
            params['cancelOrderId'] = new_order_id
            print(f'New order_id : {new_order_id}')
        else:
            print(r)
            print(r.status_code, r.json())
            cancel_order(params, orders, timing)

        repeat_moving(params, counter, try_N, orders, timing)

    else:
        cancel_order(params, orders, timing)

def cancel_order(params, orders, timing):
    PATH = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    params1 = {
        'symbol': params['symbol'],
        'orderId': params['cancelOrderId'],
        'recvWindow': 60000,
        'timestamp': timestamp
    }

    data_from_api = client.get_open_orders()
    a = json.dumps(data_from_api)
    c = json.loads(a)
    order_id = c[0]['orderId']
    params1['orderId'] = order_id

    query_string = urlencode(params1)
    params1['signature'] = hmac.new(secret_Key.encode('utf-8'), query_string.encode('utf-8'),
                                    hashlib.sha256).hexdigest()

    url = urljoin(BASE_URL, PATH)
    with requests.Session() as session:
        session.mount('https://', source_adapt)
        print(source_adapt.source_address[0])
        r = session.delete(url, headers=headers, params=params1)
    print('dssadsa', params1)
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))
        print('\nResult saved to "OrderId_Timings.csv"')

        df = pd.DataFrame([orders, timing]).T
        df.rename(columns={0: 'order_id', 1: 'time in sec'}, inplace=True)
        with open('OrderId_Timings.csv', 'w') as OrderId_Timings_file:
            df.to_csv('OrderId_Timings.csv', index=False)

    else:
        print(r.status_code, r.json())
        print('Something went wrong. Cancellation Failed')

def repeat_moving(params, counter, try_N, orders, timing): # Func for continuous Movement of order
    print(f'Going to sleep {time_to_sleep} milliseconds & start moving order...\n')
    time.sleep(time_to_sleep/1000)
    move_order(params, counter, try_N,orders, timing)

def Get_Price(params, offset):  # Func for get latest price
    PATH = '/api/v3/ticker/price'
    params['timestamp'] = int(time.time() * 1000)
    params1 = {
        'symbol': params['symbol']
    }

    url = urljoin(BASE_URL, PATH)
    r = requests.get(url, headers=headers, params=params1)

    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    else:
        print(r)
        print(r.status_code, r.json(), '\n')
    price = round(float(r.json()['price']), 2)
    print('Order Price : ', price + offset, '$')
    params['price'] = price + offset
    create_order(params)
    return params

if __name__ == "__main__":

    api_Key = 'LCksWnlYiLrkh4lTgpPud82v4kjHQwPCFt98I9Fb9jM3SyekNuhsyr49z7l6PJGs'
    secret_Key = 'amZpjt6z4imaJUF1e8WUUllDjH01udQ52GKfDbIbwijozrkwVztEKl9bAls8SwOP'
    time_to_sleep = 300
    tryes_limit = 3
    symbol = 'ETHUSDT'
    side = 'SELL'
    offset = 200.0
    quantity = 0.008

    client = Client(api_Key, secret_Key)

    BASE_URL = 'https://api.binance.com'
    headers = {
        'X-MBX-APIKEY': api_Key
    }

    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': '',
        'recvWindow': 60000,
        'timestamp': int()
    }

    Get_Price(params, offset)
