#!/bin/python3

import json
import re
import random
import base64
import string
import os
import configparser

from Crypto.Cipher import AES
from invoke import task
from pyxi import directRequest
from pyxi import requestAggregateOrderBooks
from pyxi import requestBalance
from pyxi import requestTradeHistory
from pyxi import requestOpenOrders
from pyxi import requestExchange
from pyxi import request
from pyxi import requestOrderBook
from pyxi import requestLimitOrder
from pyxi import cancelLimitOrder

#balance, cancelorder, limitorder, openorders, orderbook, json, ticker, tradefees, tradehistory,

exchanges = ['GDAX', 'KRAKEN', 'POLONIEX', 'BITFINEX']
default_limit_ask = {"order_type":"ASK","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.1","price":"10000","test":True}}
default_limit_bid = {"order_type":"BID","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.01","price":"0.0001","test": True}}

def report(data, dump=False):
    for key, value in data.items():
        #if (value == None or 'ERROR' in value or 'exception' in value or 'error' in value or re.match(r'.*error.*', value.lower()) or re.match(r'.*redacted.*', value.lower()) or len(value) < 3): response.update({"error": True})
        #    print_exchange_report(key, value, dump)
        #else:
        print("==============================================================")
        print(key)
        print("==============================================================")
        print(value)

def print_report( response, dump ):
    if dump:
        print("==============================================================")
        print("DUMP")
        print("==============================================================")
        print(response)
        print("==============================================================")
        print("END DUMP")
        print("==============================================================")
        print("")
        print("")

    print("==============================================================")
    print("START INDIVIDUAL EXCHANGES")
    print("==============================================================")
    if ('error' in response):
        failures = print_exchange_results(response, True)
        print("==============================================================")
        print("FAILURE(S): ", len(failures)/len(exchanges)*100,"%, :: ", len(failures),"/", len(exchanges))
        print(failures)
        print("==============================================================")
    else:
        print_exchange_results(response, False)
        print("==============================================================")
        print("SUCCESS")
        print("==============================================================")

def print_exchange_results(response, failure):
    failures = []
    for exchange in exchanges:
        if exchange.upper() + "ret" in response:
            print("+++++++++++++++++++++++++++++")
            print(exchange.upper())
            print("~~~~~~~~~~~~~~~~")
            print(response.get(exchange.upper()))
            if response.get(exchange.upper() + "ret"):
                print("SUCCESS")
                print(len(response.get(exchange.upper())))
            else:
                failures.append(exchange.upper())
                print("FAILURE")
            print("+++++++++++++++++++++++++++++")
    return failures

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def balance(name, exchange):
    response = requestBalance(exchange)
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def tradehistory(name, exchange):
    response = requestTradeHistory(exchange)
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def openorders(name, exchange):
    response = requestOpenOrders(exchange)
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def tradefees(name, exchange):
    response = requestExchange(exchange, 'tradefees')
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def ticker(name, exchange):
    response = requestExchange(exchange, 'ticker')
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges", "base": "-b the base currency, e.g. BTC", "quote": "-q the quote currency, e.g. ETH"})
def orderbook(name, exchange, base, quote):
    response = requestOrderBook('orderbook', exchange, base, quote)
    report(response)

def jsonendpoint(name):
    response = requestExchange(exchanqe, 'json')
    report(response)

@task(help={'exchange': "-e name of EXCHANGE or all for all exchanges", "ordertype": "-o ASK or BID", "base_currency": "-b the base currency, e.g. BTC", "quote_currency": "-q the quote currency, e.g. ETH", "volume": "-v volume of base currency", "price": "-p price of quote currency", "test": "-t is test true/t runs in verify mode, or false/f runs in production mode" })
def limitorder(name, exchange, ordertype, base, quote, volume, price, test):
    limit_order = {"order_type":ordertype.upper(),"order_specs":{"base_currency":base.upper(),"quote_currency":quote.upper(),"volume":volume,"price":price,"test":True}}
    response = requestLimitOrder(exchange,limit_order, ordertype)
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def currency(name, exchange):
    response = requestExchange(exchange, 'currency')
    report(response)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges", "order_id": "give -o id of order to cancel"})
def cancelorder(name, exchange, order_id):
    response = cancelLimitOrder(exchange, order_id)
    report(response)

@task(help={"quote": "give -q symbol of quote currency", "base": "give -b symbol of base currency", 'exchange': "give -e comma separated list of exchanges, no spaces "})
def aggregateorderbooks(name, base, quote, exchanges):
    exchanges_arr = exchanges.split(',');
    response = requestAggregateOrderBooks(base, quote, exchanges_arr)
    report(response)

@task
def ls(name):
    for x in exchanges:
        print(x)
