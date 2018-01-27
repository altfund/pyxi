import ccxt


class CcxtClient(object):

    def __init__(self, exchange_account):
        self.exchange_name = exchange_account['exchange_credentials']['exchange']
        self.apiKey = exchange_account['exchange_credentials']['key']
        self.secret = exchange_account['exchange_credentials']['secret']
        self.password = exchange_account['exchange_credentials']['passphrase']

        try:
            self.exchange_class = getattr(ccxt, self.exchange_name)()
        except Exception:
            self.exchange_class = None
        else:
            self.exchange_class.apiKey = self.apiKey
            self.exchange_class.secret = self.secret
            if self.password:
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
