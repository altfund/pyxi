import ccxt
from ccxt.base.errors import NetworkError
from ccxt.base.errors import OrderNotFound
import uuid

class CcxtClient(object):
    def __init__(self, exchange_account):
        if 'exchange' in exchange_account['exchange_credentials']:
            self.exchange_name = exchange_account['exchange_credentials']['exchange']
        if 'key' in exchange_account['exchange_credentials']:
            self.apiKey = exchange_account['exchange_credentials']['key']
        if 'secret' in exchange_account['exchange_credentials']:
            self.secret = exchange_account['exchange_credentials']['secret']
        if 'passphrase' in exchange_account['exchange_credentials']:
            self.password = exchange_account['exchange_credentials']['passphrase']

        try:
            self.exchange_class = getattr(ccxt, self.exchange_name.lower())()
        except Exception as e:
            print("Exception on init: ", e)
            self.exchange_class = None
        else:
            self.exchange_class.apiKey = self.apiKey
            self.exchange_class.secret = self.secret
            #if self.password:
            if 'passphrase' in exchange_account['exchange_credentials']:
                self.exchange_class.password = self.password

    def get_account_balance(self):
        if not self.exchange_class:
            return False, {}

        try:
            all_balances = self.exchange_class.fetch_balance()
        except Exception as e:
            return True, {"ERROR": e}

        return True, self.parse_balance_response(all_balances)

    def parse_balance_response(self, balances):
        final_response = {
            "wallet": {},
        }
        all_currency = balances.get('total', {}).keys()
        for currency in all_currency:
            currency_data = balances.get(currency)
            if currency_data:
                data = {}
                data['availableForWithdraw'] = currency_data['free']
                data['available'] = currency_data['free']
                data['total'] = currency_data['total']
                data['frozen'] = currency_data['used']
                final_response['wallet'][currency] = data
        return final_response

    def submit_limit_order(self, limit_order, order_type):
        if not self.exchange_class:
            return False, {}
        try:
            order = self.parse_limit_order_request(limit_order, order_type)
            self.set_precision(order)
            if order["type"].lower() == "bid":
                order_response = self.exchange_class.create_limit_buy_order(order["symbol"], order["amount"], order["price"])
            elif order["type"].lower() == "ask":
                order_response = self.exchange_class.create_limit_sell_order(order["symbol"], order["amount"], order["price"])
        except Exception as e:
            return True, {"ERROR": e}

        return True, self.parse_order_response(order_response, limit_order, order_type)

    def parse_limit_order_request(self, limit_order, order_type):
        if "order_specs" in limit_order and "test" in limit_order['order_specs']:
            is_test = limit_order['order_specs']['test']
            if type(is_test) == str and test_value.lower() is "true":
                is_test = True
            if is_test:
                raise NotImplementedError("This call uses ccxt which does not yet support (either actually or b/c we haven't yet implemented it) orders in test")

        order = {}
        if order_type.lower() == "bid" or order_type.lower() == "ask":
            order["type"] = order_type.lower()
        else:
            raise ValueError("order_type must be of string value of buy or sell")

        if "order_specs" in limit_order:
            order_specs = limit_order["order_specs"]
            if "base_currency" in order_specs:
                order["symbol"] = order_specs["base_currency"].upper()
            else:
                raise ValueError("order_specs must have base currency")
            if "quote_currency" in order_specs:
                order["symbol"] = order["symbol"] + "/" + order_specs["quote_currency"].upper()
            else:
                raise ValueError("order_specs must have quote currency")
            if "price" in order_specs:
                order["price"] = order_specs["price"]
            else:
                raise ValueError("order_specs must have price")
            if "volume" in order_specs:
                order["amount"] = order_specs["volume"]
            else:
                raise ValueError("order_specs must have volume")
        else:
            raise ValueError("must submit order_specs")
        return order

    def parse_order_response(self, order_response, submitted_order, order_type):
        """ orig knowm output
        {"orderResponseId":"341d5806-3b8c-426c-9a68-881417a7bfdd",
        "orderSpec":{"base_currency":"XRP",
                        "quote_currency":"ETH",
                        "volume":7.829133395691334,
                        "price":0.0013993488765157466,
                        "test":false},
        "orderType":"BID",
        "orderId":null,
        "altfundId":"6e140d63313a49b498c5d4ff2a5d7720",
        "orderStatus":{"orderStatusType":"UNKNOWN_ERROR",
        "orderStatusPhrase":"org.knowm.xchange.binance.dto.BinanceException :: -1013: Filter failure: LOT_SIZE","maxLength":0},
        "timestamp":{"dayOfYear":25,"dayOfWeek":"THURSDAY","month":"JANUARY","dayOfMonth":25,"year":2018,"monthValue":1,"hour":12,"minute":57,"second":26,"nano":780000000,"chronology":{"calendarType":"iso8601","id":"ISO"}}}
        """
        """ new ccxt out
        {'info':
            {'symbol': 'LTCETH', 'orderId': 5353234,
            'clientOrderId': 'rRBqTuttN6uXm2GAeYVZx4',
            'transactTime': 1517352994792,
            'price': '0.05665000',
            'origQty': '1.00000000',
            'executedQty': '0.00000000',
            'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY'},
        'id': '5353234', 'timestamp': 1517352994792, 'datetime': '2
        018-01-30T22:56:35.792Z', 'symbol': 'LTC/ETH', 'type': 'limit', 'side': 'buy', 'price': 0.05665, 'amount': 1.0, 'cost': 0.05665, 'filled': 0.0, 'remaining': 1.0, 'statu
        s': 'open', 'fee': None}
        """
        new_order_response = {
                    "orderResponseId": order_response.get('id', order_response.get('info', {}).get('orderId')),
                    "orderSpec": submitted_order["order_specs"],
                    "orderType": order_type,
                    "orderId": order_response.get('id', order_response.get('info', {}).get('orderId')),
                    "altfundId": uuid.uuid4().hex,
                    "orderStatus": {
                        "orderStatusType": order_response.get('status', order_response.get('info', {}).get('status')),
                        "orderStatusPhrase": ""
                        },
                    "timestamp": order_response.get('status', order_response.get('info', {}).get('status')),
                    "api": "ccxt",
                    "rawOut": order_response
                }
        return new_order_response

    def set_precision(self, order):
        def set_precision(value, precision):
            value = float(value)
            format_str = "{0:." + str(precision) + "f}"
            format_str.format(value)
            return value

        self.exchange_class.load_markets()
        market_metadata = self.exchange_class.market(order["symbol"])
        if "precision" in market_metadata:
            precision = market_metadata["precision"]
            if "price" in precision:
                order["price"] = set_precision(order["price"], precision["price"])
            if "amount" in precision:
                order["amount"] = set_precision(order["amount"], precision["amount"])

    def cancel_limit_order(self, order_id, symbol):
        if not self.exchange_class:
            return False, {}
        for attempt in range(5):
            try:
                order_canceled = self.exchange_class.cancel_order(order_id, symbol)
            except NetworkError as e:
                continue
            except OrderNotFound as e:
                return True, True
            else:
                return True, True
        else:
            raise CancelOrderException("Failed to cancel order in production")

    def request_open_orders(self, base, quote):
        if not self.exchange_class:
            return False, {}
        for attempt in range(5):
            try:
                symbol = base + "/" + quote
                order_res = self.exchange_class.fetch_open_orders(symbol=symbol)
            except NetworkError as e:
                continue
            else:
                return True, order_res
