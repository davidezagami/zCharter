"""
	See https://poloniex.com/support/api/
"""

import urllib
import urllib.request
import json
import time
import hmac,hashlib



def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
	return time.mktime(time.strptime(datestr, format))



class Poloniex:
	def __init__(self, APIKey, Secret):
		self.APIKey = APIKey
		self.Secret = Secret


	def post_process(self, before):
		after = before

		# Add timestamps if there isnt one but is a datetime
		if('return' in after):
			if(isinstance(after['return'], list)):
				for x in xrange(0, len(after['return'])):
					if(isinstance(after['return'][x], dict)):
						if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
							after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))

		return after


	def api_query(self, command, req={}):

		if(command == "returnTicker" or command == "return24hVolume"):
			ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command))
			return json.loads(ret.read().decode('utf-8'))
		elif(command == "returnOrderBook"):
			ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])))
			return json.loads(ret.read().decode('utf-8'))
		elif(command == "returnMarketTradeHistory"):
			ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(req['currencyPair'])))
			return json.loads(ret.read().decode('utf-8'))
		else:
			req['command'] = command
			req['nonce'] = int(time.time()*1000)
			post_data = urllib.parse.urlencode(req)

			sign = hmac.new(self.Secret.encode(), post_data.encode(), hashlib.sha512).hexdigest()
			headers = {
				'Sign': sign,
				'Key': self.APIKey
			}

			ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/tradingApi', post_data.encode(), headers))
			jsonRet = json.loads(ret.read().decode('utf-8'))
			return self.post_process(jsonRet)


	# Returns the ticker for all markets.
	def returnTicker(self):
		return self.api_query("returnTicker")


	# Returns the 24-hour volume for all markets, plus totals for primary currencies.
	def return24hVolume(self):
		return self.api_query("return24hVolume")


	# Returns the order book for a given market, as well as a sequence number for use with the Push API and an indicator
	# specifying whether the market is frozen. You may set currencyPair to "all" to get the order books of all markets.
	def returnOrderBook (self, currencyPair):
		return self.api_query("returnOrderBook", {'currencyPair': currencyPair})


	# Returns the past 200 trades for a given market, or up to 50,000 trades between a range specified in
	# UNIX timestamps by the "start" and "end" GET parameters.
	def returnMarketTradeHistory (self, currencyPair):
		return self.api_query("returnMarketTradeHistory", {'currencyPair': currencyPair})


	# Returns candlestick chart data. Required GET parameters are:
	# "currencyPair"
	# "period" (candlestick period in seconds; valid values are 300, 900, 1800, 7200, 14400, and 86400)
	# "start" and "end" are given in UNIX timestamp format and used to specify the date range for the data returned.
	def returnChartData(self, currencyPair, period, start, end):
		return self.api_query("returnChartData", {'currencyPair': currencyPair, "period": period, "start": start, "end": end})


	# Returns information about currencies.
	def returnCurrencies(self):
		return self.api_query("returnCurrencies")


	# Returns all of your available balances (exchange account).
	def returnBalances(self):
		return self.api_query('returnBalances')


	# Returns your open orders for a given market, specified by the "currencyPair"
	# Set "currencyPair" to "all" to return open orders for all markets.
	def returnOpenOrders(self, currencyPair):
		return self.api_query('returnOpenOrders', {"currencyPair":currencyPair})


	# Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
	# You may specify "all" as the currencyPair to receive your trade history for all markets.
	# You may optionally specify a range via "start" and/or "end" POST parameters, given in UNIX timestamp format;
	# if you do not specify a range, it will be limited to one day.
	def returnTradeHistory(self, currencyPair):
		return self.api_query('returnTradeHistory', {"currencyPair":currencyPair})


	# Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
	# If successful, the method will return the order number.
	# You may optionally set "fillOrKill", "immediateOrCancel", "postOnly" to 1.
	# A fill-or-kill order will either fill in its entirety or be completely aborted.
	# An immediate-or-cancel order can be partially or completely filled, but any portion of the order that
	# cannot be filled immediately will be canceled rather than left on the order book.
	# A post-only order will only be placed if no portion of it fills immediately;
	# this guarantees you will never pay the taker fee on any part of the order that fills.
	def buy(self, currencyPair, rate, amount):
		return self.api_query('buy', {"currencyPair":currencyPair, "rate":rate, "amount":amount})


	# Places a sell order in a given market. Parameters and output are the same as for the buy method.
	def sell(self, currencyPair, rate, amount):
		return self.api_query('sell', {"currencyPair":currencyPair, "rate":rate, "amount":amount})


	# Cancels an order you have placed in a given market. Required POST parameter is "orderNumber".
	# If successful, the method will return: {"success":1}
	def cancelOrder(self, currencyPair, orderNumber):
		return self.api_query('cancelOrder', {"currencyPair":currencyPair, "orderNumber":orderNumber})


	# Returns your balances sorted by account. You may optionally specify the "account" POST parameter
	# if you wish to fetch only the balances of one account. Please note that balances in your margin account
	# may not be accessible if you have any open margin positions or orders.
	def returnAvailableAccountBalances(self):
		return self.api_query("returnAvailableAccountBalances")


	# Returns your current tradable balances for each currency in each market for which margin trading is enabled.
	# Please note that these balances may vary continually with market conditions. 
	def returnTradableBalances(self):
		return self.api_query("returnTradableBalances")


	# Returns a summary of your entire margin account.
	# This is the same information you will find in the Margin Account section of the Margin Trading page, under the Markets list.
	def returnMarginAccountSummary(self):
		return self.api_query("returnMarginAccountSummary")


	# Places a margin buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
	# You may optionally specify a maximum lending rate using the "lendingRate" parameter.
	# If successful, the method will return the order number and any trades immediately resulting from your order.
	def marginBuy(self, currencyPair, rate, amount, lendingRate):
		return self.api_query('marginBuy', {"currencyPair":currencyPair, "rate":rate, "amount":amount, "lendingRate":lendingRate})


	# Places a margin sell order in a given market. Parameters and output are the same as for the marginBuy method.
	def marginSell(self, currencyPair, rate, amount, lendingRate):
		return self.api_query('marginSell', {"currencyPair":currencyPair, "rate":rate, "amount":amount, "lendingRate":lendingRate})


	# Returns information about your margin position in a given market, specified by the "currencyPair" POST parameter.
	# You may set "currencyPair" to "all" if you wish to fetch all of your margin positions at once.
	# If you have no margin position in the specified market, "type" will be set to "none". "liquidationPrice" is an estimate,
	# and does not necessarily represent the price at which an actual forced liquidation will occur.
	# If you have no liquidation price, the value will be -1.
	def getMarginPosition(self, currencyPair):
		return self.api_query("getMarginPosition", {'currencyPair': currencyPair})


	# Closes your margin position in a given market (specified by the "currencyPair" POST parameter) using a market order.
	# This call will also return success if you do not have an open position in the specified market.
	def closeMarginPosition(self, currencyPair):
		return self.api_query("closeMarginPosition", {'currencyPair': currencyPair})


	# Immediately places a withdrawal for a given currency, with no email confirmation.
	# In order to use this method, the withdrawal privilege must be enabled for your API key.
	# Required POST parameters are "currency", "amount", and "address". For XMR withdrawals, you may optionally specify "paymentId".
	def withdraw(self, currency, amount, address):
		return self.api_query('withdraw',{"currency":currency, "amount":amount, "address":address})
