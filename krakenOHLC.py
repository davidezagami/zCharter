"""
See https://www.kraken.com/en-us/help/api
"""

try:
	from urllib import urlencode
except ImportError:
	from urllib.parse import urlencode
import requests


def getOHLCdata(pair, interval, since=None):
	request_url = 'https://api.kraken.com/0/public/OHLC?'
	options = {"pair":pair, "interval":interval}
	if since != None:
		options["since"] = since
	request_url += urlencode(options)

	return requests.get(request_url).json()


if __name__ == '__main__':
	r = getOHLCdata("XBTEUR", 30, 1505556000)
	cs = None
	for k in r["result"]:
		if k != "last":
			cs = r["result"][k]
			break

	# cs is array of array entries(<time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>)
	candlestick_data = {}
	for c in cs:
		ts = c[0]
		candle = {"date":ts}
		candle["open"] = float(c[1])
		candle["high"] = float(c[2])
		candle["low"] = float(c[3])
		candle["close"] = float(c[4])
		candle["volume"] = float(c[6])
		candlestick_data[ts] = candle

	print(str(candlestick_data))
