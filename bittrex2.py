"""
   See https://bittrex.com/Home/Api
"""

import time
import hmac
import hashlib
try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import urljoin
import requests


BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

BASE_URL = 'https://bittrex.com/api/v1.1/%s/'
BASE_URL2 = "https://bittrex.com/Api/v2.0/pub/market/"

MARKET_SET = {'getopenorders', 'cancel', 'sellmarket', 'selllimit', 'buymarket', 'buylimit'}

ACCOUNT_SET = {'getbalances', 'getbalance', 'getdepositaddress', 'withdraw', 'getorderhistory', "getorder"}

UNDOCUMENTED_SET = {"getChartData"}


class Bittrex2(object):
    """
    Used for requesting Bittrex with API key and API secret
    """
    def __init__(self, api_key, api_secret):
        self.api_key = str(api_key) if api_key is not None else ''
        self.api_secret = str(api_secret) if api_secret is not None else ''


    def api_query(self, method, options=None):
        """
        (for API 1.1)
        Queries Bittrex with given method and options

        :param method: Query method for getting info
        :type method: str

        :param options: Extra options for query
        :type options: dict

        :return: JSON response from Bittrex
        :rtype : dict
        """
        if not options:
            options = {}
        nonce = str(int(time.time() * 1000))
        method_set = 'public'

        if method in MARKET_SET:
            method_set = 'market'
        elif method in ACCOUNT_SET:
            method_set = 'account'

        request_url = (BASE_URL % method_set) + method + '?'

        if method_set != 'public':
            request_url += 'apikey=' + self.api_key + "&nonce=" + nonce + '&'

        request_url += urlencode(options)

        return requests.get(
            request_url,
            headers={"apisign": hmac.new(self.api_secret.encode(), request_url.encode(), hashlib.sha512).hexdigest()}
        ).json()


    def api_query2(self, method, options=None):
        """
        (for API 2.0 undocumented)
        Queries Bittrex with given method and options

        :param method: Query method for getting info
        :type method: str

        :param options: Extra options for query
        :type options: dict

        :return: JSON response from Bittrex
        :rtype : dict
        """
        if not options:
            options = {}
        nonce = str(int(time.time() * 1000))

        request_url = BASE_URL2 + method + '?'

        request_url += urlencode(options)

        return requests.get(request_url).json()


    def getChartData(self, marketName, tickInterval):
        """
        Used to get Bittrex historical data (api 2.0 beta undocumented)

        :param market: String literal for the market (ex: BTC-LTC)
        :param tickInterval: String literal for candle interval;
                            valid values: oneMin, fiveMin, thirtyMin, hour, day

        :return: Historical data info in JSON
        :rtype : dict
        """
        return self.api_query2("GetTicks", {"marketName": marketName, "tickInterval": tickInterval})


    def getmarkets(self):
        """
        Used to get the open and available trading markets
        at Bittrex along with other meta data.

        :return: Available market info in JSON
        :rtype : dict
        """
        return self.api_query('getmarkets')


    def getcurrencies(self):
        """
        Used to get all supported currencies at Bittrex
        along with other meta data.

        :return: Supported currencies info in JSON
        :rtype : dict
        """
        return self.api_query('getcurrencies')


    def getticker(self, market):
        """
        Used to get the current tick values for a market.

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :return: Current values for given market in JSON
        :rtype : dict
        """
        return self.api_query('getticker', {'market': market})


    def getmarketsummaries(self):
        """
        Used to get the last 24 hour summary of all active exchanges

        :return: Summaries of active exchanges in JSON
        :rtype : dict
        """
        return self.api_query('getmarketsummaries')


    def getmarketsummary(self, market):
        """
        Used to get the last 24 hour summary of one particular active exchange

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :return: Summaries of active exchanges in JSON
        :rtype : dict
        """
        return self.api_query('getmarketsummary', {'market': market})


    def getorderbook(self, market, depth_type, depth=20):
        """
        Used to get retrieve the orderbook for a given market

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param depth_type: buy, sell or both to identify the type of orderbook to return.
            Use constants BUY_ORDERBOOK, SELL_ORDERBOOK, BOTH_ORDERBOOK
        :type depth_type: str

        :param depth: how deep of an order book to retrieve. Max is 100, default is 20
        :type depth: int

        :return: Orderbook of market in JSON
        :rtype : dict
        """
        return self.api_query('getorderbook', {'market': market, 'type': depth_type, 'depth': depth})


    def getmarkethistory(self, market, count):
        """
        Used to retrieve the latest trades that have occurred for a
        specific market.

        /market/getmarkethistory

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param count: Number between 1-100 for the number of entries to return (default = 20)
        :type count: int

        :return: Market history in JSON
        :rtype : dict
        """
        return self.api_query('getmarkethistory', {'market': market, 'count': count})


    def buymarket(self, market, quantity):
        """
        Used to place a buy order in a specific market. Use buymarket to
        place market orders. Make sure you have the proper permissions
        set on your API keys for this call to work

        /market/buymarket

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        return self.api_query('buymarket', {'market': market, 'quantity': quantity})


    def buylimit(self, market, quantity, rate):
        """
        Used to place a buy order in a specific market. Use buylimit to place
        limit orders Make sure you have the proper permissions set on your
        API keys for this call to work

        /market/buylimit

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        return self.api_query('buylimit', {'market': market, 'quantity': quantity, 'rate': rate})


    def sellmarket(self, market, quantity):
        """
        Used to place a sell order in a specific market. Use sellmarket to place
        market orders. Make sure you have the proper permissions set on your
        API keys for this call to work

        /market/sellmarket

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        return self.api_query('sellmarket', {'market': market, 'quantity': quantity})


    def selllimit(self, market, quantity, rate):
        """
        Used to place a sell order in a specific market. Use selllimit to place
        limit orders Make sure you have the proper permissions set on your
        API keys for this call to work

        /market/selllimit

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str

        :param quantity: The amount to purchase
        :type quantity: float

        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float

        :return:
        :rtype : dict
        """
        return self.api_query('selllimit', {'market': market, 'quantity': quantity, 'rate': rate})


    def cancel(self, uuid):
        """
        Used to cancel a buy or sell order

        /market/cancel

        :param uuid: uuid of buy or sell order
        :type uuid: str

        :return:
        :rtype : dict
        """
        return self.api_query('cancel', {'uuid': uuid})


    def getopenorders(self, market):
        """
        Get all orders that you currently have opened. A specific market can be requested

        /market/getopenorders

        :param market: String literal for the market (ie. BTC-LTC)
        :type market: str

        :return: Open orders info in JSON
        :rtype : dict
        """
        return self.api_query('getopenorders', {'market': market})


    def getbalances(self):
        """
        Used to retrieve all balances from your account

        /account/getbalances

        :return: Balances info in JSON
        :rtype : dict
        """
        return self.api_query('getbalances', {})


    def getbalance(self, currency):
        """
        Used to retrieve the balance from your account for a specific currency

        /account/getbalance

        :param currency: String literal for the currency (ex: LTC)
        :type currency: str

        :return: Balance info in JSON
        :rtype : dict
        """
        return self.api_query('getbalance', {'currency': currency})


    def getdepositaddress(self, currency):
        """
        Used to generate or retrieve an address for a specific currency

        /account/getdepositaddress

        :param currency: String literal for the currency (ie. BTC)
        :type currency: str

        :return: Address info in JSON
        :rtype : dict
        """
        return self.api_query('getdepositaddress', {'currency': currency})


    def withdraw(self, currency, quantity, address):
        """
        Used to withdraw funds from your account

        /account/withdraw

        :param currency: String literal for the currency (ie. BTC)
        :type currency: str

        :param quantity: The quantity of coins to withdraw
        :type quantity: float

        :param address: The address where to send the funds.
        :type address: str

        :return:
        :rtype : dict
        """
        return self.api_query('withdraw', {'currency': currency, 'quantity': quantity, 'address': address})


    def getorderhistory(self, market, count):
        """
        Used to reterieve order trade history of account

        /account/getorderhistory

        :param market: optional a string literal for the market (ie. BTC-LTC). If ommited, will return for all markets
        :type market: str

        :param count: optional 	the number of records to return
        :type count: int

        :return: order history in JSON
        :rtype : dict

        """
        return self.api_query('getorderhistory', {'market':market, 'count': count})


    def getorder(self, uuid):
        return self.api_query("getorder", {"uuid": uuid})
