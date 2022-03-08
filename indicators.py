# All time low calculator
def alltime_low(data, subset, field=None):
	lowest = 1e+8
	for ts in subset:
		if field == None:
			lowest = min(lowest, data[ts])
		else:
			lowest = min(lowest, data[ts][field])
	return lowest


# All time high calculator
def alltime_high(data, subset, field=None):
	highest = 1e-8
	for ts in subset:
		if field == None:
			highest = max(highest, data[ts])
		else:
			highest = max(highest, data[ts][field])
	return highest


# Simple Moving Average calculator
def SMA(candle_data, period, field="close"):
	timestamps = list(candle_data.keys())
	timestamps.sort()
	SMA_data = list((0 for i in range(period-1)))
	first_SMA = sum((candle_data[ts][field] for ts in timestamps[:period]))/period
	SMA_data.append(first_SMA)
	i = period
	while i < len(timestamps):
		current_ts = timestamps[i]
		tail_ts = timestamps[i-period]
		prev_SMA = SMA_data[-1]
		this_SMA = prev_SMA + (candle_data[current_ts][field] - candle_data[tail_ts][field])/period
		SMA_data.append(this_SMA)
		i+=1
	return dict(zip(timestamps, SMA_data))


# Exponential Moving Average calculator
def EMA(candle_data, period, field="close"):
	timestamps = list(candle_data.keys())
	timestamps.sort()
	EMA_data = list((0 for i in range(period-1)))
	first_EMA = sum((candle_data[ts][field] for ts in timestamps[:period]))/period
	EMA_data.append(first_EMA)
	multiplier = (2 / (period + 1) )
	i = period
	while i < len(timestamps):
		current_ts = timestamps[i]
		prev_EMA = EMA_data[-1]
		this_EMA = (candle_data[current_ts][field] - prev_EMA) * multiplier + prev_EMA
		EMA_data.append(this_EMA)
		i+=1
	return dict(zip(timestamps, EMA_data))


# MACD calculator
def MACD(candle_data, periods, field="close"):
	short_period, long_period, signal_period = periods
	short_data = EMA(candle_data, short_period, field)
	long_data = EMA(candle_data, long_period, field)
	MACD_data = {}
	for ts in short_data:
		# insert a dict with 'field' key to make the structure compatible with above functions
		MACD_data[ts] = { field: short_data[ts] - long_data[ts] }
	signal_data = EMA(MACD_data, signal_period, field)
	for ts in MACD_data:
		# then remove the field for simplicity's sake
		MACD_data[ts] = MACD_data[ts][field]
	histogram_data = {}
	for ts in MACD_data:
		histogram_data[ts] = MACD_data[ts] - signal_data[ts]
	return MACD_data, signal_data, histogram_data


# RSI calculator
def RSI(candle_data, period):
	timestamps = list(candle_data.keys())
	timestamps.sort()
	prev = timestamps[0]
	U_series = {}
	D_series = {}
	U_series[prev] = 0
	D_series[prev] = 0

	change = candle_data[prev]["close"] - candle_data[prev]["open"]
	if change >= 0:
		U_series[prev] = change
	else:
		D_series[prev] = -change

	for now in timestamps:
		U_series[now] = 0
		D_series[now] = 0

		change = candle_data[now]["close"] - candle_data[prev]["close"]
		if change >= 0:
			U_series[prev] = change
		else:
			D_series[prev] = -change

		prev = now

	for ts in timestamps:
		# insert a dict with 'close' key to make the structure compatible with above functions
		U_series[ts] = { "close": U_series[ts] }
		D_series[ts] = { "close": D_series[ts] }
	EMA_U_series = EMA(U_series, period, "close")
	EMA_D_series = EMA(D_series, period, "close")

	RSI_data = {}
	for ts in timestamps:
		EMA_U = EMA_U_series[ts]
		EMA_D = EMA_D_series[ts]
		RS = EMA_U/EMA_D if EMA_D else 100 # avoid division by zero errors
		RSI = 100 - 100/(1+RS)
		RSI_data[ts] = RSI

	return RSI_data


# Standard Deviation calculator
def std_dev(data, subset, cursor, period):
	mean = sum((data[ts]["close"] for ts in subset[cursor-period:cursor]))/period
	variance = sum(((data[ts]["close"]-mean)**2 for ts in subset[cursor-period:cursor]))/period
	standard_deviation = variance**0.5
	return mean, standard_deviation


# Bollinger Bands calculator
def BBANDS(candle_data, period, deviations):
	timestamps = list(candle_data.keys())
	timestamps.sort()
	upper_band = list((0 for i in range(period-1)))
	central_line = list((0 for i in range(period-1)))
	lower_band = list((0 for i in range(period-1)))
	i = period
	while i <= len(candle_data):
		mean, dev = std_dev(candle_data, timestamps, i, period)
		upper_band.append(mean + deviations*dev)
		central_line.append(mean)
		lower_band.append(mean - deviations*dev)
		i+=1
	upper_band = dict(zip(timestamps, upper_band))
	central_line = dict(zip(timestamps, central_line))
	lower_band = dict(zip(timestamps, lower_band))
	return upper_band, central_line, lower_band


# Channel Breakout calculator
def CHBRK(candle_data, period):
	timestamps = list(candle_data.keys())
	timestamps.sort()
	highs = list((0 for i in range(period-1)))
	lows = list((0 for i in range(period-1)))
	i = period
	while i <= len(candle_data):
		last_n_candles = timestamps[i-period:i]
		high = alltime_high(candle_data, last_n_candles, "high")
		low = alltime_low(candle_data, last_n_candles, "low")
		highs.append(high)
		lows.append(low)
		i+=1
	lows = dict(zip(timestamps, lows))
	highs = dict(zip(timestamps, highs))
	return lows, highs
