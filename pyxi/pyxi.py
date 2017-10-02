#!/bin/python3

import json
import re
import requests
import random
import base64
import string
import os
import configparser

from Crypto.Cipher import AES
from invoke import task

#balance, cancelorder, limitorder, openorders, orderbook, json, ticker, tradefees, tradehistory,

exchanges = ['ALL', 'GDAX', 'KRAKEN', 'POLONIEX', 'BITFINEX', 'VAULTORO', 'TRUEFX', 'QUADRIGACX', 'LUNO', 'GEMINI', 'YOBIT', 'LIVECOIN', 'VIRCUREX', 'HUOBI', 'GATECOIN', 'THEROCK', 'RIPPLE', 'QUOINE', 'TAURUS', 'JUBI', 'MERCADOBITCOIN', 'OKCOIN', 'POLONIEX', 'PAYMIUM', 'HITBTC', 'LAKEBTC', 'INDEPENDENTRESERVE', 'ITBIT', 'GDAX', 'KRAKEN', 'EMPOEX', 'DSX', 'CRYPTONIT', 'CRYPTOPIA', 'CRYPTOFACILITIES', 'COINMATE', 'COINFLOOR', 'COINBASE', 'CHBTC', 'CEXIO', 'CCEX', 'CAMPBX', 'BTER', 'BTCTRADE', 'BTCMARKETS', 'BTCE', 'BTCC', 'BTC38', 'BLOCKCHAIN', 'BLEUTRADE', 'BITTREX', 'BITSTAMP', 'BITSO', 'BITMARKET', 'BITFINEX', 'BITCUREX', 'BITCOINIUM', 'BITCOINDE', 'BITCOINCORE', 'BITCOINCHARTS', 'BITCOINAVERAGE', 'BITBAY', 'ANX']
default_limit_ask = {"order_type":"ASK","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.1","price":"10000","test":True}}
default_limit_bid = {"order_type":"BID","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.01","price":"0.0001","test": True}}

def send( data, method, config, json=False):
    if json:
        r = requests.get(config.get('xi_url') + "/" + method, json=data).text
    else:
        r = requests.get(config.get('xi_url') + "/" + method, params=data).text
    return r

def decrypt(payload):
    config = getConfig()
    payload = json.loads(payload)
    plain_text = ""
#    try:
    init_vector = payload['iv']
    encrypted_data = payload['encrypted_data']
    init_vector = base64.b64decode(init_vector)
    encrypted_data = base64.b64decode(encrypted_data)
    encryption_suite = AES.new(config['aes_key'], AES.MODE_CFB, init_vector)

    plain_text = encryption_suite.decrypt(encrypted_data).decode('utf-8')
    #plain_text = plain_text.decode('utf-8')
    #except:
    #    plain_text = json.dumps(payload)

    return plain_text

def encrypt( data, config):
    #https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
    init_vector = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(16))

    #encryption_suite = AES.new(key, AES.MODE_CFB, init_vector, segment_size=128)
    encryption_suite = AES.new(config['aes_key'], AES.MODE_CFB, init_vector)
    json_data = json.dumps(data)

    # encrypt returns an encrypted byte string
    cipher_text = encryption_suite.encrypt(json_data)

    # encrypted byte string is base 64 encoded for message passing
    base64_cipher_byte_string = base64.b64encode(cipher_text)

    # base 64 byte string is decoded to utf-8 encoded string for json serialization
    base64_cipher_string = base64_cipher_byte_string.decode('utf-8')

    encrypted_request = {"iv": init_vector,
            "encrypted_data": base64_cipher_string}
    return encrypted_request

def getCreds(exchange):
    exchange = exchange.upper()
    config = configparser.ConfigParser()
    config.read('config')
    try:
        creds = {
                "exchange": exchange.lower(),
                "key": config[exchange]['key'],
                "secret": config[exchange]['secret']
                }
    except:
        raise ValueError('exchange ' + exchange.lower() + ' does not have credentials')

    try:
        passphrase = config[exchange]['passphrase']
        creds.update({"passphrase":  passphrase})
        return creds
    except:
        return creds

def getConfig():
    config = configparser.ConfigParser()
    config.read('config')
    cfg = { "xi_url": os.environ.get("XI_URL", None),
            "aes_key": os.environ.get("AES_KEY", None)
            }
    if cfg['aes_key'] is None:
        cfg['aes_key'] = config["settings"]['aes_key']
    if cfg['xi_url'] is None:
        cfg['xi_url'] = config["settings"]['xi_url']
    return cfg

def requestExchange( exchange, method):
    config = getConfig()
    response = {}
    if exchange.lower() == 'all':
        for an_exchange in exchanges:
            data = {"exchange": an_exchange.lower()}
            r = send(data, method, config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        data = {"exchange": exchange.lower()}
        r = send(data, method, config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def directRequest( method, data=None):
    response = {}
    config = getConfig()
    r = send(data, method, config, True)
    data = decrypt(r)
    response.update({method: data})
    return response

def request( method, data=None):
    config = getConfig()
    response = {}
    if data['exchange'].lower() == 'all':
        for an_exchange in exchanges:
            data.update({"exchange": an_exchange.lower()})
            r = send(data, method, config)
            data = decrypt(r)
            response.update({an_exchange.upper(): data})
    else:
        r = send(data, method, config)
        data = decrypt(r)
        response.update({data['exchange'].upper(): data})
    return response

def requestOrderBook(method, exchange, base, quote):
    config = getConfig()
    response = {}
    if exchange.lower() == 'all':
        for an_exchange in exchanges:
            data = {'exchange':an_exchange,'base_currency':base,'quote_currency':quote}
            r = send(encrypt(data, config), method, config)
            data = decrypt(r)
            response.update({an_exchange.upper(): data})
    else:
        data = {'exchange':exchange,'base_currency':base,'quote_currency':quote}
        r = send(encrypt(data, config), method, config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def requestLimitOrder( exchange, limitorder, ordertype):
    order = ""
    if ordertype.lower() == 'ask':
        order = 'ask'
    elif ordertype.lower() == 'bid':
        order = 'bid'
    else:
        order = ""

    if order == "":
        print("Must set order type to ASK or BID");
    else:
        config = getConfig()
        response = {}
        if exchange.lower() == 'all':
            for exchange in exchanges:
                creds = getCreds(exchange)
                limitorder.update({"exchange_credentials":creds})
                r = send(encrypt(limitorder, config), "limitorder", config)
                data = decrypt(r)
                response.update({exchange.upper(): data})
        else:
            creds = getCreds(exchange)
            limitorder.update({"exchange_credentials":creds})
            r = send(encrypt(limitorder, config), "limitorder", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    return response

def requestInterExchangeArbitrage(orders):
    config = getConfig()
    response = {}

    index = 0
    modified_orders = []

    while (index < len(orders)):
        exchange = orders[index]['exchange']
        creds = getCreds(exchange)
        orders[index]['order'].update({"exchange_credentials": creds})
        modified_orders.append(orders[index]['order'])
        index = index + 1

    r = send(encrypt(modified_orders, config), "interexchangearbitrage", config)
    data = decrypt(r)
    response.update({"interexchangearbitrage": data})
    return response


def requestOpenOrders( exchange):
    config = getConfig()
    response = {}
    temp = {}
    if exchange.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            r = send(encrypt(creds, config), "openorders", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        creds = getCreds(exchange)
        r = send(encrypt(creds, config), "openorders", config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def requestTradeHistory( exchange):
    config = getConfig()
    response = {}
    temp = {}
    history_req = {}
    temp.update({"page_length": "10"});
    history_req.update({"trade_params": temp});
    if exchange.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            history_req.update({"exchange_credentials": creds});
            r = send(encrypt(history_req, config), "tradehistory", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        creds = getCreds(exchange)
        history_req.update({"exchange_credentials": creds});
        r = send(encrypt(history_req, config), "tradehistory", config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def cancelLimitOrder( exchange, order_id):
    config = getConfig()
    response = {}
    order_to_cancel = {}
    if exchange.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            order_to_cancel.update({"exchange_credentials": creds});
            order_to_cancel.update({"order_id": order_id});
            r = send(encrypt(order_to_cancel, config), "cancelorder", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        creds = getCreds(exchange)
        order_to_cancel.update({"exchange_credentials": creds});
        order_to_cancel.update({"order_id": order_id});
        r = send(encrypt(order_to_cancel, config), "cancelorder", config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def requestBalance(exchange):
    config = getConfig()
    response = {}
    if exchange.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            r = send(encrypt(creds, config), "balance", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        creds = getCreds(exchange)
        r = send(encrypt(creds, config), "balance", config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def requestAggregateOrderBooks(base, quote, exchanges):
    data = {'base_currency':base,'quote_currency':quote,'exchanges':exchanges}
    config = getConfig()
    response = {}
    r = send(encrypt(data, config), "aggregateorderbooks", config, True)
    data = decrypt(r);
    response.update({"aggregateorderbooks": data})
    return response

def requestAvailableMarkets(coe_list):
    config = getConfig()
    response = {}
    r = send(encrypt(coe_list, config), "availablemarkets", config, False)
    data = decrypt(r);
    response.update({"availablemarkets": data})
    return response
