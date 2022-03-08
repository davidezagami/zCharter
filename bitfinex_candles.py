"""
See https://docs.bitfinex.com/v2/reference#rest-public-candles
"""

try:
	from urllib import urlencode
except ImportError:
	from urllib.parse import urlencode
import requests


def get_candles(pair, interval, section="hist", options=None):
	request_url = 'https://api.bitfinex.com/v2/candles/trade:%s:t%s/%s?'%(interval, pair, section)
	if options != None:
		request_url += urlencode(options)
	return requests.get(request_url).json()


if __name__ == '__main__':
	r = get_candles("BTCUSD", "1D")
	# r is array of array entries[MTS, OPEN, CLOSE, HIGH, LOW, VOLUME]
	candlestick_data = {}
	for c in r:
		ts = c[0]
		candle = {"date":ts}
		candle["open"] = float(c[1])
		candle["close"] = float(c[2])
		candle["high"] = float(c[3])
		candle["low"] = float(c[4])
		candle["volume"] = float(c[5])
		candlestick_data[ts] = candle

	print(str(candlestick_data))
