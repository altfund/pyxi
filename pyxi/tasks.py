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
from pyxi import requestLimitOrder
from pyxi import cancelLimitOrder

#balance, cancelorder, limitorder, openorders, orderbook, json, ticker, tradefees, tradehistory,

exchanges = ['GDAX', 'KRAKEN', 'POLONIEX', 'BITFINEX']
default_limit_ask = {"order_type":"ASK","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.1","price":"10000","test":False}}
default_limit_bid = {"order_type":"BID","order_specs":{"base_currency":"ETH","quote_currency":"BTC","volume":"0.01","price":"0.0001","test": False}}


@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def balance(name, exchange):
    requestBalance(exchange)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def tradehistory(name, exchange):
    requestTradeHistory(exchange)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def openorders(name, exchange):
    requestOpenOrders(exchange)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def tradefees(name, exchange):
    requestExchange(exchange, 'tradefees')

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def ticker(name, exchange):
    requestExchange(exchange, 'ticker')

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges",
            "base_currency": "-b the base currency, e.g. BTC",
            "quote_currency": "-q the quote currency, e.g. ETH"})
def orderbook(name, exchange, base_currency, quote_currency):
    data={'exchange':exchange,'base_currency':base_currency,'quote_currency':quote_currency}
    request('orderbook', data)
    #print_report(request('orderbook', data))
    #requestExchange(exchange, 'orderbook')

def jsonendpoint(name):
    requestExchange(exchanqe, 'json')


#default_limit_ask = {"order_type":"ASK",
#"order_specs":{"base_currency":"ETH",
#"quote_currency":"BTC",
#"volume":"0.1",
#"price":"10000",
#"test":False}}
@task(help={'exchange': "-e name of EXCHANGE or all for all exchanges",
            "ordertype": "-o ASK or BID",
            "base_currency": "-b the base currency, e.g. BTC",
            "quote_currency": "-q the quote currency, e.g. ETH",
            "volume": "-v volume of base currency",
            "price": "-p price of quote currency",
            "test": "-t is test true/t runs in verify mode, or false/f runs in production mode" })
def limitorder(name, exchange, ordertype, base, quote, volume, price, test):
    #requestLimitOrder(exchange, ordertype, base, quote, volume, price, test)
    requestLimitOrder(exchange, ordertype)

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges"})
def currency(name, exchange):
    requestExchange(exchange, 'currency')

@task(help={'exchange': "give -e name of EXCHANGE or ALL for all exchanges", "order_id": "give -o id of order to cancel"})
def cancelorder(name, exchange, order_id):
    cancelLimitOrder(exchange, order_id)

@task(help={"quote": "give -q symbol of quote currency", "base": "give -b symbol of base currency", 'exchange': "give -e comma separated list of exchanges, no spaces "})
def aggregateorderbooks(name, base, quote, exchanges):
    exchanges_arr = exchanges.split(',');
    requestAggregateOrderBooks(base, quote, exchanges_arr)

@task
def ls(name):
    for x in exchanges:
        print(x)
