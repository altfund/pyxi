#!/bin/python3

# An adapter meant to be used to abstract away dealing with crypto
# exchanges. currently works with github.com/altfund/xchange-interface which
# relies on the knowm package and github.com/ccxt/ccxt.

import json
import requests
import random
import base64
import string
import os
import configparser

from Crypto.Cipher import AES
from .ccxt_interface import CcxtClient

#TODO
# 1. figure out what to do about the invoke/package usage . problem
# 2. take "all" call out
# 3. clean up all the extra methods, make them simpler
# 4. think through switching on calls to knowm v. ccxt
# 5. change output so it doesn't return dict with name of call... i.e.
#    separate invoke program from pyxi
# 6. make sure entire object is a dictionary so no subsequent calls to
#   json.loads are necessary.
# 7. Yell REALLY loud and specifically or just thrown an exception, when methods
#    are thrown incorrect parameters

# balance, cancelorder, limitorder, openorders, orderbook, json, ticker, tradefees, tradehistory,

exchanges_limit_order_on_ccxt = ["BINANCE"]
deprecated_exchanged = ['BTC38', 'BTCE', 'HUOBI','JUBI', 'CHBTC', 'BTER']
exchanges = ['ALL', 'BINANCE', 'GDAX', 'KRAKEN', 'POLONIEX', 'BITFINEX', 'VAULTORO', 'TRUEFX', 'QUADRIGACX', 'LUNO', 'GEMINI', 'YOBIT', 'LIVECOIN', 'VIRCUREX',  'GATECOIN', 'THEROCK', 'RIPPLE', 'QUOINE', 'TAURUS',  'MERCADOBITCOIN', 'OKCOIN', 'POLONIEX', 'PAYMIUM', 'HITBTC', 'LAKEBTC', 'INDEPENDENTRESERVE', 'ITBIT', 'GDAX', 'KRAKEN', 'EMPOEX', 'DSX', 'CRYPTONIT', 'CRYPTOPIA', 'CRYPTOFACILITIES', 'COINMATE', 'COINFLOOR', 'COINBASE',  'CEXIO', 'CCEX', 'CAMPBX',  'BTCTRADE', 'BTCMARKETS',  'BTCC',  'BLOCKCHAIN', 'BLEUTRADE', 'BITTREX', 'BITSTAMP', 'BITSO', 'BITMARKET', 'BITFINEX', 'BITCUREX', 'BITCOINIUM', 'BITCOINDE', 'BITCOINCORE', 'BITCOINCHARTS', 'BITCOINAVERAGE', 'BITBAY', 'ANX']
# exchanges = ['GDAX', 'KRAKEN', 'POLONIEX', 'BITFINEX']
default_limit_ask = {"order_type":"ASK","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.1","price":"10000","test":True}}
default_limit_bid = {"order_type":"BID","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.01","price":"0.0001","test": True}}

def send( data, method, config, json=False):
    if json:
        r = requests.get(config.get('xi_url') + "/" + method, json=data).text
    else:
        r = requests.get(config.get('xi_url') + "/" + method, params=data).text
    return r

def decrypt(payload):
    if payload is None:
        return ""
    else:
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
        
def getSettings():
    config = configparser.ConfigParser()
    config.read('config')
    try:
        stgs = dict(config['settings'])
    except:
        raise ValueError('there are no settings in config')

    return stgs

def getConfig(parameters=['xi_url','aes_key']):
    config = configparser.ConfigParser()
    config.read('config')
    if str(parameters).lower() == 'all':
        parameters = ['xi_url','aes_key','test']
    cfg = {x: os.environ.get(x.upper(),config["settings"][x]) for x in parameters}
        
    return cfg

def requestExchange(exchange, method, encrypted=True):
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
        data = send(data, method, config)

        if encrypted == True:
            data = decrypt(data)

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

def cancelLimitOrder(exchange, order_id, symbol=""):
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
        if exchange.upper() in exchanges_limit_order_on_ccxt:
            ccxtclient = CcxtClient(order_to_cancel)
            status, response = ccxtclient.cancel_limit_order(order_id, symbol)
            if not status:
                print("status", status)
                print("response", response)
                return "ERROR"
            else:
                print("response", response)
                return response
        else:
            r = send(encrypt(order_to_cancel, config), "cancelorder", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    return response

def amCancelLimitOrder(exchange_dict, order_id, symbol=""):
    print("PARAMS TO AM CANCEL LIMIT ORDER")
    print("exchange_dict", exchange_dict)
    print("order_id", order_id)
    print("symbol", symbol)
    config = getConfig()
    exchange_dict.update({"order_id": order_id});
    exchange_name = exchange_dict['exchange_credentials']['exchange']
    if exchange_name.upper() in exchanges_limit_order_on_ccxt:
        ccxtclient = CcxtClient(exchange_dict)
        status, response = ccxtclient.cancel_limit_order(order_id, symbol)
        if not status:
            print("status", status)
            print("response", response)
            return "ERROR"
        else:
            print("response", response)
            return response
    else:
        r = send(encrypt(exchange_dict, config), "cancelorder", config)
        data = decrypt(r)
    if data == "true":
        return True;
    else:
        return json.loads(data)

def requestLimitOrder(exchange, limitorder, ordertype):
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
        if exchange.upper() in exchanges_limit_order_on_ccxt:
            ccxtclient = CcxtClient(limitorder)
            status, response = ccxtclient.submit_limit_order(limitorder, ordertype)
            if not status:
                print("status", status)
                print("response", response)
                return "ERROR"
            else:
                return response
        else:
            response = {}
            #if exchange.lower() == 'all':
            #    for exchange in exchanges:
            #        creds = getCreds(exchange)
            #        limitorder.update({"exchange_credentials":creds})
            #        r = send(encrypt(limitorder, config), "limitorder", config)
            #       data = decrypt(r)
            #       response.update({exchange.upper(): data})
            #else:
            r = send(encrypt(limitorder, config), "limitorder", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    return response


def requestFillOrKill(orders):
    config = getConfig()
    response = {}

    index = 0
    modified_orders = []

    while (index < len(orders)):
        if not orders[index].get('exchange_credentials'):
            exchange = orders[index]['exchange']
            creds = getCreds(exchange)
            orders[index].update({"exchange_credentials": creds})

        modified_orders.append(orders[index])
        index = index + 1

    r = send(encrypt(modified_orders, config), "fillorkill", config)
    data = decrypt(r)
    response.update({"fillorkill": data})
    return response


def requestInterExchangeArbitrage(orders, external_creds=None):
    config = getConfig()
    response = {}

    index = 0
    modified_orders = []

    if (external_creds==None):
        while (index < len(orders)):
            exchange = orders[index]['exchange']
            creds = getCreds(exchange)
            orders[index]['order'].update({"exchange_credentials": creds})
            modified_orders.append(orders[index]['order'])
            index = index + 1
            r = send(encrypt(modified_orders, config), "interexchangearbitrage", config)

    r = send(encrypt(orders, config), "interexchangearbitrage", config)
    data = decrypt(r)
    response.update({"interexchangearbitrage": data})
    return response


def requestBalance(exchange):
    config = getConfig()
    response = {}

    if isinstance(exchange, dict):
        exchange_name = exchange['exchange_credentials']['exchange']
        exchange = exchange['exchange_credentials']
    else:
        exchange_name = exchange

    if exchange_name.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            r = send(encrypt(creds, config), "balance", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        # creds = getCreds(exchange)
        r = send(encrypt(exchange, config), "balance", config)
        data = decrypt(r)
        # response.update({exchange.upper(): data})
        response = json.loads(data)
    return response


def requestExchangeAccountBalance(exchange):

    response = {}
    ccxtclient = CcxtClient(exchange)
    status, response = ccxtclient.get_account_balance()
    # Status Show Ccxt Exchange Class Exist or not
    if not status:
        return requestBalance(exchange)
    else:
        return response


def requestOpenOrders(exchange, base="", quote=""):
    config = getConfig()
    response = {}
    temp = {}
    history_req = {}
    temp.update({"page_length": "10"})
    history_req.update({"trade_params": temp})

    if isinstance(exchange, dict):
        exchange_name = exchange['exchange_credentials']['exchange']
        exchange = exchange['exchange_credentials']
    else:
        exchange_name = exchange
        exchange = {}
        exchange['exchange_credentials'] = getCreds(exchange_name)
        exchange['exchange_credentials']['exchange'] = exchange_name
        exchange = exchange['exchange_credentials']

    if exchange_name.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            r = send(encrypt(creds, config), "openorders", config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        """
        if exchange_name.upper() in exchanges_limit_order_on_ccxt:
            ccxtclient = CcxtClient(exchange)
            status, response = ccxtclient.request_open_orders(base, quote)
            if not status:
                return "ERROR"
            else:
                return response
        else:
        """
        # creds = getCreds(exchange)
        r = send(encrypt(exchange, config), "openorders", config)
        data = decrypt(r)
        # response.update({exchange.upper(): data})
        response = data
    return response


def requestFundingHistory( exchange, method="fundinghistory"):
    config = getConfig()
    response = {}
    temp = {}
    history_req = {}
    temp.update({"page_length": "10"});
    history_req.update({"trade_params": temp});

    if isinstance(exchange,dict):
        exchange_name = exchange['exchange_credentials']['exchange']
    else:
        exchange_name = exchange

    if exchange_name.lower() == 'all':
        for exchange in exchanges:
            creds = getCreds(exchange)
            history_req.update({"exchange_credentials": creds});
            r = send(encrypt(history_req, config), method, config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        #creds = getCreds(exchange)
        r = send(encrypt(exchange, config), method, config)
        data = decrypt(r)
        #response.update({exchange.upper(): data})
        response = data
    return response


def requestAmTradeHistroy(exchange):
    config = getConfig()
    response = {}
    if not exchange.get('trade_params'):
        temp = {}
        temp.update({"page_length": "10"})
        exchange.update({"trade_params": temp})

    r = send(encrypt(exchange, config), "tradehistory", config)
    data = decrypt(r)
    return data


def requestAmFundingHistroy(exchange):
    print('calling funding history with', exchange)
    config = getConfig()
    response = {}
    if not exchange.get('trade_params'):
        temp = {}
        temp.update({"page_length": "10"})
        exchange.update({"trade_params": temp})

    r = send(encrypt(exchange, config), "fundinghistory", config)
    data = decrypt(r)
    return data


def requestTradeHistory(exchange, method="tradehistory"):
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
            r = send(encrypt(history_req, config), method, config)
            data = decrypt(r)
            response.update({exchange.upper(): data})
    else:
        creds = getCreds(exchange)
        history_req.update({"exchange_credentials": creds});
        r = send(encrypt(history_req, config), method, config)
        data = decrypt(r)
        response.update({exchange.upper(): data})
    return response

def requestOrders(exchange, orders):
    creds = getCreds(exchange)
    data = {'exchange_credentials':creds,'order_ids':orders}
    config = getConfig()
    response = {}
    r = send(encrypt(data, config), "getorders", config, False)
    data = decrypt(r);
    response.update({"getorders": data})
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

def localRequestBalance(exchange):
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
        print("the data and it's damn shape", data)
        response.update({exchange.upper(): data})
    return response
