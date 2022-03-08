from indicators import alltime_low, alltime_high
import datetime

def reformat_candle_data(candle_data, new_period):
	timestamps = list(candle_data.keys())
	timestamps.sort()
	period = timestamps[1] - timestamps[0]
	if period == new_period:
		return candle_data # untouched, was already formatted

	# remove oldest candles until we encounter a 2:00am candle
	# (for timestamp alignment purposes)
	while True:
		t = datetime.datetime.fromtimestamp(timestamps[0])
		if (t.hour == 2) and (t.minute == 0):
			break
		del timestamps[0]

	join_factor = int(new_period/period)
	new_candle_data = {}

	i = 0
	while i < len(timestamps):
		window = timestamps[i:i+join_factor]
		new_ts = window[0]
		new_low = alltime_low(candle_data, window, "low")
		new_high = alltime_high(candle_data, window, "high")
		new_open = candle_data[window[0]]["open"]
		new_close = candle_data[window[-1]]["close"]
		new_volume = sum((candle_data[ts]["volume"] for ts in window))
		new_candle_data[new_ts] = {
									"open": new_open,
									"close": new_close,
									"low": new_low,
									"high": new_high,
									"volume": new_volume,
									"date": new_ts
									}
		i += join_factor

	return new_candle_data
