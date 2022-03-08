import zGUI
import poloniex, bittrex2, krakenOHLC, bitfinex_candles, indicators
from reformat_candle_data import reformat_candle_data
import pygame, json, time, sys
from pygame.locals import *



SCREEN_SIZE = SCREEN_X, SCREEN_Y = (1800, 900)
CHART_SIZE = (SCREEN_X-340, SCREEN_Y*0.9)
CHART_POS = (20, SCREEN_Y*0.05)
WALLETSPANEL_POS = (SCREEN_X-300, SCREEN_Y*0.05)
WALLETSPANEL_SIZE = (240, SCREEN_Y*0.18)
NEWORDERPANEL_POS = (SCREEN_X-300, SCREEN_Y*0.25)
NEWORDERPANEL_SIZE = (240, SCREEN_Y*0.29)
DETAILSPANEL_POS = (SCREEN_X-300, SCREEN_Y*0.56)
DETAILSPANEL_SIZE = (240, SCREEN_Y*0.23)
POSITIONSPANEL_POS = (SCREEN_X-300, SCREEN_Y*0.81)
POSITIONSPANEL_SIZE = (240, SCREEN_Y*0.18)
LOGPANEL_POS = (20, SCREEN_Y*0.96)
LOGPANEL_SIZE = (SCREEN_X-340, SCREEN_Y*0.03)
REGULAR_FONT = "LiberationMono-Regular.ttf"
BOLD_FONT = "LiberationMono-Bold.ttf"
F_SIZE = 12
CROSSCOLOR = (255,255,255,128)
BACKGROUNDCOLOR = zGUI.DARKERBLUE
PANELCOLOR = zGUI.DARKBLUE
FIELDBORDERCOLOR = zGUI.DARKESTBLUE
FIELDBACKGROUNDCOLOR = zGUI.MEDIUMBLUE
TEXTCOLOR = zGUI.WHITE
EPSILON = 1e-4



class dummyChart(zGUI.zWidget):
	def __init__(self, engine):
		super(dummyChart, self).__init__(engine)


	def back_in_time(self, numcandles):
		return "No chart data"


	def forward_in_time(self, numcandles):
		return "No chart data"


	def travel_to(self, targettime):
		return "No chart data"


	def get_current_price_from_data(self):
		return 0.0


	def update(self, event):
		pass


	def draw(self, dest_surface=None):
		pass



class zChart(zGUI.zWidget):

	border_width = 1
	shadow_width = 1

	def __init__(self, engine, data, area, position):
		super(zChart, self).__init__(engine)
		# CHART DATA
		self.all_candle_data = data
		self.all_timestamps = list(self.all_candle_data.keys())
		self.all_timestamps.sort()
		self.all_timestamps.reverse()
		self.current_candle_data = self.all_candle_data.copy()
		self.candle_ends = (1e+4, 1e-8)
		self.volume_ends = (1e+4, 1e-8)
		self.SMA_period = 40
		self.SMA_offset = -20
		self.EMA_period = 10
		self.EMA_offset = 0
		self.BBANDS_period = 20
		self.BBANDS_deviations = 3.0
		self.CHBRK_period = 20
		self.MACD_periods = (12, 26, 9)
		self.MACD_ends = (1e+4, 1e-8)
		self.RSI_period = 14
		self.overbought = 75
		self.oversold = 25
		self.recompute_indicators()

		# GRAPHICS
		self.candle_width = 5
		self.down_candle_color = zGUI.RED
		self.up_candle_color = zGUI.GREEN
		self.down_volume_color = zGUI.DARKRED
		self.up_volume_color = zGUI.DARKGREEN
		self.SMA_color = zGUI.CYAN
		self.EMA_color = zGUI.YELLOW
		self.upper_band_color = zGUI.MEDIUMBLUE
		self.central_line_color = zGUI.MEDIUMRED
		self.lower_band_color = zGUI.MEDIUMBLUE
		self.channel_color = zGUI.DARKBLUE
		self.histogram_color = zGUI.CYAN
		self.MACD_color = zGUI.MAGENTA
		self.signal_color = zGUI.WHITE
		self.RSI_color = zGUI.WHITE
		self.overbought_color = zGUI.RED
		self.oversold_color = zGUI.GREEN

		# SECTORS
		self.position = position
		self.area = area
		self.prices_area = (100, 0)
		self.timestamps_area = (area[0]-self.prices_area[0], 50)
		self.MACD_area = (self.timestamps_area[0], 100)
		self.RSI_area = (self.timestamps_area[0] , 100)
		self.prices_area = (self.prices_area[0], self.area[1]-self.timestamps_area[1]-self.MACD_area[1]-self.RSI_area[1])
		self.graph_area = (self.timestamps_area[0], area[1]-self.timestamps_area[1]-self.MACD_area[1]-self.RSI_area[1])
		self.volume_area = (self.timestamps_area[0], int(self.graph_area[1]/4))
		self.Rect = pygame.Rect(position, area)

		# INTERACTIVITY
		self.skipped_candles = 0
		self.panning = False
		self.panning_begin = None
		self.surface = None
		self.final_surface = None
		self.refresh_surface()


	def recompute_indicators(self):
		self.current_timestamps = list(self.current_candle_data.keys())
		self.current_timestamps.sort()
		self.current_timestamps.reverse()
		self.period = self.get_period_from_data()
		self.current_price = self.get_current_price_from_data()
		self.SMA_data = indicators.SMA(self.current_candle_data, self.SMA_period)
		self.EMA_data = indicators.EMA(self.current_candle_data, self.EMA_period)
		self.BBANDS_data = indicators.BBANDS(self.current_candle_data, self.BBANDS_period, self.BBANDS_deviations)
		self.CHBRK_data = indicators.CHBRK(self.current_candle_data, self.CHBRK_period)
		self.MACD = indicators.MACD(self.current_candle_data, self.MACD_periods)
		self.RSI = indicators.RSI(self.current_candle_data, self.RSI_period)


	def back_in_time(self, numcandles):
		try:
			for i in range(numcandles):
				del self.current_candle_data[self.current_timestamps[i]]
		except IndexError:
			return "Time travel error: limit reached"
		self.recompute_indicators()
		self.refresh_surface()
		return "Time traveled back {:d} candles".format(numcandles)


	def forward_in_time(self, numcandles):
		for i in range(numcandles):
			try:
				futurecandlets = self.all_timestamps[-len(self.current_timestamps)-1-i]
			except IndexError:
				return "Time travel error: limit reached"
			self.current_candle_data[futurecandlets] = self.all_candle_data[futurecandlets]
		self.recompute_indicators()
		self.refresh_surface()
		return "Time traveled forward {:d} candles".format(numcandles)


	def travel_to(self, targettime):
		ts = int(time.mktime(time.strptime(targettime, "%d-%m-%Y")))
		self.current_candle_data = self.all_candle_data.copy()
		self.current_timestamps = self.all_timestamps.copy()
		try:
			while self.current_timestamps[0] > ts:
				del self.current_candle_data[self.current_timestamps[0]]
				del self.current_timestamps[0]
			self.recompute_indicators()
			self.refresh_surface()
		except IndexError:
			return "Time travel error: limit reached"
		return "Traveled to " + targettime


	def get_period_from_data(self):
		timestamps = list(self.current_candle_data.keys())
		timestamps.sort()
		return timestamps[1] - timestamps[0]


	def get_current_price_from_data(self):
		lastcandle = self.current_candle_data[self.current_timestamps[0]]
		return lastcandle["close"]


	def price_to_surface_y(self, price, lowest, highest, graph_height):
		return int( graph_height - graph_height*(price-lowest)/(highest-lowest) )


	def surface_to_price_y(self, tick_height, lowest, highest, graph_height):
		return lowest + (highest-lowest)*(graph_height-tick_height)/graph_height


	def draw_ticks_and_borders(self):
		lowest = self.candle_ends[0]
		highest = self.candle_ends[1]

		# candles-MACD border
		height = self.graph_area[1]+self.timestamps_area[1]
		pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, height), (self.area[0], height), 2)
		# MACD-RSI border
		height = self.graph_area[1]+self.timestamps_area[1]+self.MACD_area[1]
		pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, height), (self.area[0], height), 2)

		# price boundaries
		pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, self.graph_area[1]), (self.graph_area[0]+10, self.graph_area[1]), 1)
		zGUI.z_text_draw(self.surface, "{:.8f}".format(lowest), F_SIZE, (self.graph_area[0]+15, self.graph_area[1]-5), font=BOLD_FONT, color=zGUI.GRAY)
		pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, 1), (self.graph_area[0]+10, 1), 1)
		zGUI.z_text_draw(self.surface, "{:.8f}".format(highest), F_SIZE, (self.graph_area[0]+15, 1), font=BOLD_FONT, color=zGUI.GRAY)

		# price ticks
		i=1
		step = self.prices_area[1]/9
		while i<=8:
			height = i*step
			pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, height), (self.graph_area[0]+10, height), 1)
			value = self.surface_to_price_y(height, lowest, highest, self.prices_area[1])
			zGUI.z_text_draw(self.surface, "{:.8f}".format(value), F_SIZE, (self.graph_area[0]+15, height-5), font=BOLD_FONT, color=zGUI.GRAY)
			i+=1

		# RSI overbought tick
		height = self.graph_area[1] + self.timestamps_area[1] + self.MACD_area[1] + 100 - self.overbought
		pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, height), (self.graph_area[0]+10, height), 1)
		zGUI.z_text_draw(self.surface, "{:.7f}".format(self.overbought), F_SIZE, (self.graph_area[0]+15, height-5), font=BOLD_FONT, color=zGUI.GRAY)

		# RSI oversold tick
		height = self.graph_area[1] + self.timestamps_area[1] + self.MACD_area[1] + 100 - self.oversold
		pygame.draw.line(self.surface, zGUI.DARKGRAY, (0, height), (self.graph_area[0]+10, height), 1)
		zGUI.z_text_draw(self.surface, "{:.7f}".format(self.oversold), F_SIZE, (self.graph_area[0]+15, height-5), font=BOLD_FONT, color=zGUI.GRAY)


	def draw_ts(self, candle, cursor):
		# draw a ts once every this many pixels away from vertical axis
		ts_step = self.candle_width*int(self.graph_area[0]/min(7*self.candle_width, self.graph_area[0]))
		dist = self.graph_area[0] - cursor - self.candle_width
		if dist%ts_step == 0:
			offset = self.candle_width/2
			pygame.draw.line(self.surface, zGUI.DARKGRAY, (cursor+offset, 0), (cursor+offset, self.graph_area[1]+15), 1)
			value = time.strftime("%d-%m-%Y", time.localtime(candle["date"]))
			zGUI.z_text_draw(self.surface, value, F_SIZE, (cursor+offset-36, self.graph_area[1]+20), font=BOLD_FONT, color=zGUI.GRAY)
			value = time.strftime("%H:%M", time.localtime(candle["date"]))
			zGUI.z_text_draw(self.surface, value, F_SIZE, (cursor+offset-18, self.graph_area[1]+32), font=BOLD_FONT, color=zGUI.GRAY)
			pygame.draw.line(self.surface, zGUI.DARKGRAY, (cursor+offset, self.graph_area[1]+self.timestamps_area[1]-5), (cursor+offset, self.area[1]), 1)


	def draw_volumes(self, timestamps, cursor):
		lowest, highest = self.volume_ends
		for ts in timestamps:
			volume = self.current_candle_data[ts]["volume"]
			s_volume = self.price_to_surface_y(volume, lowest, highest, self.volume_area[1])
			s_volume += self.graph_area[1] - self.volume_area[1]
			cursor -= self.candle_width
			self.draw_ts(self.current_candle_data[ts], cursor)

			p_open = self.current_candle_data[ts]["open"]
			p_close = self.current_candle_data[ts]["close"]
			bar_color = self.up_volume_color if p_close>=p_open else self.down_volume_color
			# draw body
			top = s_volume
			bot = self.graph_area[1]
			bar_rect = pygame.Rect(cursor, top, self.candle_width, bot-top)
			pygame.draw.rect(self.surface, bar_color, bar_rect)


	def draw_candles(self, timestamps, cursor):
		lowest, highest = self.candle_ends
		for ts in timestamps:
			p_open = self.current_candle_data[ts]["open"]
			p_close = self.current_candle_data[ts]["close"]
			p_low = self.current_candle_data[ts]["low"]
			p_high = self.current_candle_data[ts]["high"]

			s_open = self.price_to_surface_y(p_open, lowest, highest, self.graph_area[1])
			s_close = self.price_to_surface_y(p_close, lowest, highest, self.graph_area[1])
			s_low = self.price_to_surface_y(p_low, lowest, highest, self.graph_area[1])
			s_high = self.price_to_surface_y(p_high, lowest, highest, self.graph_area[1])

			cursor -= self.candle_width

			candle_color = self.up_candle_color if p_close>=p_open else self.down_candle_color
			# draw shadow
			offset = self.candle_width/2
			pygame.draw.line(self.surface, candle_color, (cursor+offset, s_low), (cursor+offset, s_high), zChart.shadow_width)
			# draw body
			top = min(s_close, s_open)
			bot = max(s_close, s_open)
			candle_rect = pygame.Rect(cursor+1, top, self.candle_width-2, bot-top)
			pygame.draw.rect(self.surface, candle_color, candle_rect)


	def draw_SMA(self, timestamps, cursor):
		lowest = self.candle_ends[0]
		highest = self.candle_ends[1]
		offset = self.candle_width/2
		cursor += self.candle_width*self.SMA_offset
		pointlist = []
		for ts in timestamps:
			SMA = self.SMA_data[ts]
			s_SMA = self.price_to_surface_y(SMA, lowest, highest, self.graph_area[1])
			cursor -= self.candle_width
			pointlist.append((cursor+offset, s_SMA))
		if len(pointlist) > 1:
			pygame.draw.lines(self.surface, self.SMA_color, False, pointlist, 2)


	def draw_EMA(self, timestamps, cursor):
		lowest = self.candle_ends[0]
		highest = self.candle_ends[1]
		offset = self.candle_width/2
		cursor += self.candle_width*self.EMA_offset
		pointlist = []
		for ts in timestamps:
			EMA = self.EMA_data[ts]
			s_EMA = self.price_to_surface_y(EMA, lowest, highest, self.graph_area[1])
			cursor -= self.candle_width
			pointlist.append((cursor+offset, s_EMA))
		if len(pointlist) > 1:
			pygame.draw.lines(self.surface, self.EMA_color, False, pointlist, 2)


	def draw_BBANDS(self, timestamps, cursor):
		lowest = self.candle_ends[0]
		highest = self.candle_ends[1]
		offset = self.candle_width/2
		upperlist = []
		centrallist = []
		lowerlist = []
		for ts in timestamps:
			upper = self.BBANDS_data[0][ts]
			central = self.BBANDS_data[1][ts]
			lower = self.BBANDS_data[2][ts]
			s_upper = self.price_to_surface_y(upper, lowest, highest, self.graph_area[1])
			s_central = self.price_to_surface_y(central, lowest, highest, self.graph_area[1])
			s_lower = self.price_to_surface_y(lower, lowest, highest, self.graph_area[1])
			cursor -= self.candle_width
			upperlist.append((cursor+offset, s_upper))
			centrallist.append((cursor+offset, s_central))
			lowerlist.append((cursor+offset, s_lower))
		if len(upperlist) > 1:
			pygame.draw.lines(self.surface, self.upper_band_color, False, upperlist, 1)
			pygame.draw.lines(self.surface, self.central_line_color, False, centrallist, 1)
			pygame.draw.lines(self.surface, self.lower_band_color, False, lowerlist, 1)


	def draw_channel(self, timestamps, cursor):
		lowest = self.candle_ends[0]
		highest = self.candle_ends[1]
		offset = self.candle_width/2
		highslist = []
		lowslist = []
		for ts in timestamps:
			high = self.CHBRK_data[1][ts]
			low = self.CHBRK_data[0][ts]
			s_high = self.price_to_surface_y(high, lowest, highest, self.graph_area[1])
			s_low = self.price_to_surface_y(low, lowest, highest, self.graph_area[1])
			cursor -= self.candle_width
			highslist.append((cursor+offset, s_high))
			lowslist.append((cursor+offset, s_low))
		if len(highslist) > 1:
			pygame.draw.lines(self.surface, self.channel_color, False, highslist, 4)
			pygame.draw.lines(self.surface, self.channel_color, False, lowslist, 4)


	def draw_histogram(self, timestamps, cursor):
		lowest, highest = self.MACD_ends
		zero_value = self.price_to_surface_y(0, lowest, highest, self.MACD_area[1])
		for ts in timestamps:
			h_value = self.MACD[2][ts]

			cursor -= self.candle_width
			s_value = self.price_to_surface_y(h_value, lowest, highest, self.MACD_area[1])

			top = s_value
			bot = zero_value
			h_rect = pygame.Rect(cursor+1, self.graph_area[1]+self.timestamps_area[1]+top, self.candle_width-2, bot-top)
			pygame.draw.rect(self.surface, self.histogram_color, h_rect)


	def draw_MACD_line(self, timestamps, cursor):
		lowest, highest = self.MACD_ends
		offset = self.candle_width/2
		zero_value = self.price_to_surface_y(0, lowest, highest, self.MACD_area[1])
		pointlist = []
		for ts in timestamps:
			MACD = self.MACD[0][ts]
			s_MACD = self.price_to_surface_y(MACD, lowest, highest, self.MACD_area[1])
			cursor -= self.candle_width
			pointlist.append((cursor+offset, self.graph_area[1]+self.timestamps_area[1]+s_MACD))
		if len(pointlist) > 1:
			pygame.draw.lines(self.surface, self.MACD_color, False, pointlist, 1)


	def draw_signal_line(self, timestamps, cursor):
		lowest, highest = self.MACD_ends
		offset = self.candle_width/2
		zero_value = self.price_to_surface_y(0, lowest, highest, self.MACD_area[1])
		pointlist = []
		for ts in timestamps:
			signal = self.MACD[1][ts]
			s_signal = self.price_to_surface_y(signal, lowest, highest, self.MACD_area[1])
			cursor -= self.candle_width
			pointlist.append((cursor+offset, self.graph_area[1]+self.timestamps_area[1]+s_signal))
		if len(pointlist) > 1:
			pygame.draw.lines(self.surface, self.signal_color, False, pointlist, 1)


	def draw_MACD(self, timestamps, cursor):
		#histogram = {k:v for k,v in self.MACD[2].items() if k in timestamps}
		#MACD_line = {k:v for k,v in self.MACD[0].items() if k in timestamps}
		#signal_line = {k:v for k,v in self.MACD[1].items() if k in timestamps}
		l1 = indicators.alltime_low(self.MACD[2], timestamps)
		l2 = indicators.alltime_low(self.MACD[0], timestamps)
		l3 = indicators.alltime_low(self.MACD[1], timestamps)
		lowest = min(l1, l2, l3)
		h1 = indicators.alltime_high(self.MACD[2], timestamps)
		h2 = indicators.alltime_high(self.MACD[0], timestamps)
		h3 = indicators.alltime_high(self.MACD[1], timestamps)
		highest = max(h1, h2, h3)
		self.MACD_ends = (lowest, highest)
		self.draw_histogram(timestamps, cursor)
		self.draw_MACD_line(timestamps, cursor)
		self.draw_signal_line(timestamps, cursor)


	def draw_RSI(self, timestamps, cursor):
		sy = self.graph_area[1]+self.timestamps_area[1]+self.MACD_area[1]
		# overbought line
		start = (0, sy+100-self.overbought)
		end = (cursor, sy+100-self.overbought)
		pygame.draw.line(self.surface, self.overbought_color, start, end, 1)

		# 50 line
		start = (0, sy+50)
		end = (cursor, sy+50)
		pygame.draw.line(self.surface, zGUI.LIGHTGRAY, start, end, 1)

		# oversold line
		start = (0, sy+100-self.oversold)
		end = (cursor, sy+100-self.oversold)
		pygame.draw.line(self.surface, self.oversold_color, start, end, 1)

		# RSI graph
		offset = self.candle_width/2
		pointlist = []
		for ts in timestamps:
			s_RSI = 100-self.RSI[ts]
			cursor -= self.candle_width
			pointlist.append((cursor+offset, sy+s_RSI))
		if len(pointlist) > 1:
			pygame.draw.lines(self.surface, self.RSI_color, False, pointlist, 2)


	def refresh_surface(self):
		#print(time.time(), "redrawing...")
		self.surface = pygame.Surface(self.area)
		self.surface.fill(zGUI.BLACK)

		cursor = self.graph_area[0]

		timestamps = self.current_timestamps
		if self.skipped_candles < 0:
			cursor += self.candle_width*self.skipped_candles
		else:
			timestamps = timestamps[self.skipped_candles:]

		displayed_candles = int((cursor)/self.candle_width)
		timestamps = timestamps[:displayed_candles]
		l1 = indicators.alltime_low(self.current_candle_data, timestamps, "low")
		l2 = indicators.alltime_low(self.BBANDS_data[2], timestamps)
		h1 = indicators.alltime_high(self.current_candle_data, timestamps, "high")
		h2 = indicators.alltime_high(self.BBANDS_data[0], timestamps)
		self.candle_ends = (min(l1,l2), max(h1,h2))
		lowest = indicators.alltime_low(self.current_candle_data, timestamps, "volume")
		highest = indicators.alltime_high(self.current_candle_data, timestamps, "volume")
		self.volume_ends = (lowest, highest)
		self.first_ts = timestamps[0] if timestamps else 0

		self.draw_ticks_and_borders()
		self.draw_volumes(timestamps, cursor)
		#self.draw_channel(timestamps, cursor)
		self.draw_BBANDS(timestamps, cursor)
		self.draw_candles(timestamps, cursor)
		#self.draw_SMA(timestamps, cursor)
		self.draw_EMA(timestamps, cursor)
		self.draw_MACD(timestamps, cursor)
		self.draw_RSI(timestamps, cursor)
		#self.final_surface = self.surface.copy()


	def update(self, event):
		if self.panning:
			panning_end = pygame.mouse.get_pos()[0]
			candles_to_skip = int( (self.panning_begin - panning_end)/self.candle_width )
			if candles_to_skip != 0:
				self.panning_begin = panning_end
				self.skipped_candles -= candles_to_skip
				candles_to_skip = 0
				self.refresh_surface()
		if event.type == MOUSEBUTTONDOWN:
			if self.Rect.collidepoint(pygame.mouse.get_pos()):
				if event.button == 1:
					self.panning = True
					self.panning_begin = pygame.mouse.get_pos()[0]
				if event.button == 4:
					self.candle_width += 1
				if event.button == 5:
					self.candle_width -= 1
					if self.candle_width < 3:
						self.candle_width = 3
						return
				self.refresh_surface()
		elif event.type == MOUSEBUTTONUP:
			if event.button == 1:
				self.panning = False
				self.panning_begin = None


	def draw_crossair(self):
		self.final_surface = self.surface.copy()
		mx, my = pygame.mouse.get_pos()
		if self.Rect.collidepoint((mx, my)):
			pygame.mouse.set_visible(False)
			sx, sy = self.position
			mx, my = (mx-sx, my-sy)
			# HORIZONTAL LINE
			#pygame.draw.line(self.final_surface, CROSSCOLOR, (0, my), (self.graph_area[0]+10, my), 1)
			zGUI.draw_alpha_line(self.final_surface, CROSSCOLOR, (0, my), (self.graph_area[0]+10, my), 1)
			# VALUE TAG
			if my < self.graph_area[1] + self.timestamps_area[1]:
				# PRICE TAG
				lowest, highest = self.candle_ends
				value = self.surface_to_price_y(my, lowest, highest, self.graph_area[1])
				value = "{:.8f}".format(value)
			elif my < self.graph_area[1] + self.timestamps_area[1] + self.MACD_area[1]:
				# MACD TAG
				lowest, highest = self.MACD_ends
				value = self.surface_to_price_y(my-self.graph_area[1]-self.timestamps_area[1], lowest, highest, self.MACD_area[1])
				value = "{:+.8f}".format(value)
			else:
				# RSI TAG
				value = 100 - (my - self.graph_area[1] - self.timestamps_area[1] - self.MACD_area[1])
				value = "{:.7f}".format(value)
			tag_rect = pygame.Rect(self.graph_area[0]+13, my-7, 80, 16)
			pygame.draw.rect(self.final_surface, zGUI.DARKGRAY, tag_rect)
			zGUI.z_text_draw(self.final_surface, value, F_SIZE, (self.graph_area[0]+15, my-5), font=BOLD_FONT, color=zGUI.WHITE)

			halfcandle = int(self.candle_width/2)+1
			actual_x = self.graph_area[0]-halfcandle - self.candle_width*int((self.graph_area[0]-mx)/self.candle_width)
			# VERTICAL LINE
			#pygame.draw.line(self.final_surface, CROSSCOLOR, (actual_x, 0), (actual_x, self.area[1]), 1)
			zGUI.draw_alpha_line(self.final_surface, CROSSCOLOR, (actual_x, 0), (actual_x, self.area[1]), 1)
			# TIMESTAMP TAG
			candle_no = int((self.graph_area[0]-mx)/self.candle_width) + min(self.skipped_candles, 0)
			tag_rect = pygame.Rect(actual_x-42, self.graph_area[1]+18, 80, 28)
			pygame.draw.rect(self.final_surface, zGUI.DARKGRAY, tag_rect)
			value_ts = self.first_ts - candle_no*self.period
			value = time.strftime("%d-%m-%Y", time.localtime(value_ts))
			zGUI.z_text_draw(self.final_surface, value, F_SIZE, (actual_x-36, self.graph_area[1]+20), font=BOLD_FONT, color=zGUI.WHITE)
			value = time.strftime("%H:%M", time.localtime(value_ts))
			zGUI.z_text_draw(self.final_surface, value, F_SIZE, (actual_x-18, self.graph_area[1]+32), font=BOLD_FONT, color=zGUI.WHITE)
		else:
			pygame.mouse.set_visible(True)


	def draw(self, dest_surface=None):
		if dest_surface == None:
			dest_surface = self.target_surface
		self.draw_crossair()
		dest_surface.blit(self.final_surface, self.position)



def coin_to_fiat(coin_field, fiat_field, conversion_rate):
	try:
		fiat_field.set_text("%.8f"%(float(coin_field.text)*conversion_rate))
	except ValueError:
		fiat_field.set_text("0.0")

def fiat_to_coin(fiat_field, coin_field, conversion_rate):
	try:
		coin_field.set_text("%.8f"%(float(fiat_field.text)/conversion_rate))
	except ValueError:
		coin_field.set_text("0.0")



period_in_seconds =  {"5m":300, "15m":900, "30m":1800, "1h":3600, "2h":7200, "3h":10800,
						"4h":14400, "5h":18000, "6h":21600, "8h":28800, "10h":36000,
						"12h":43200, "1d":86400}

bittrex_unit =  {"5m":300, "15m":300, "30m":1800, "1h":3600, "2h":3600, "3h":3600,
					"4h":3600, "5h":3600, "6h":3600, "8h":3600, "10h":3600,
					"12h":3600, "1d":86400}

bittrex_conversion = {300:"fiveMin", 1800:"thirtyMin", 3600:"hour", 86400:"day"}

poloniex_unit =  {"5m":300, "15m":900, "30m":1800, "1h":1800, "2h":7200, "3h":1800,
					"4h":14400, "5h":1800, "6h":7200, "8h":14400, "10h":7200,
					"12h":14400, "1d":14400}

poloniex_conversion = {300:300, 900:900, 1800:1800, 7200:7200, 14400:14400}

kraken_unit =  {"5m":300, "15m":900, "30m":1800, "1h":3600, "2h":3600, "3h":3600,
					"4h":14400, "5h":3600, "6h":3600, "8h":14400, "10h":3600,
					"12h":14400, "1d":86400}

kraken_conversion = {300:5, 900:15, 1800:30, 3600:60, 14400:240, 86400:1440}

bitfinex_unit =  {"5m":300, "15m":900, "30m":1800, "1h":3600, "2h":3600, "3h":10800,
					"4h":3600, "5h":3600, "6h":21600, "8h":3600, "10h":3600,
					"12h":43200, "1d":86400}

bitfinex_conversion = {300:"5m", 900:"15m", 1800:"30m", 3600:"1h", 10800:"3h", 21600:"6h",
						43200:"12h", 86400:"1D"}



class zSimTrader(object):
	def __init__(self):
		super(zSimTrader, self).__init__()
		self.wallets = {"YYY":0.0}
		self.positions = {"XXX-YYY": None}
		sample_position = {"type":"long", "market":"XXX-YYY", "amount":0.0, "price":0.0, "invested":0.0}
		self.positions["XXX-YYY"] = sample_position
		self.selected_market = "XXX-YYY"


	def edit_position(self, amount, price, market=None):
		if market is None:
			market = self.selected_market
		wallet = market.split('-')[1]
		self.wallets[wallet] -= amount*price
		oldamount = self.positions[market]["amount"]
		self.positions[market]["amount"] += amount
		newamount = self.positions[market]["amount"]
		signchanged = oldamount*newamount < 0
		if abs(self.positions[market]["amount"]) < EPSILON:
			self.positions[market]["amount"] = 0.0
		self.positions[market]["type"] = "long" if newamount>=0 else "short"
		if self.positions[market]["amount"] != 0.0:
			if signchanged:
				self.positions[market]["invested"] = newamount*price
				self.positions[market]["price"] = price
			else:
				self.positions[market]["invested"] += amount*price
				self.positions[market]["price"] = abs(self.positions[market]["invested"]/self.positions[market]["amount"])
		else:
			self.positions[market]["invested"] = 0.0
			self.positions[market]["price"] = 0.0
		return "Balance: {:+.8f}, Position: {:s}".format(self.wallets[wallet], str(self.positions[market]))


	def switch_to_market(self, market):
		if not (market in self.positions):
			new_position = {"type":"long", "market":market, "amount":0.0, "price":0.0, "invested":0.0}
			self.positions[market] = new_position
		if not (market.split('-')[1] in self.wallets):
			self.wallets[market.split('-')[1]] = 0.0
		self.selected_market = market


	def get_balance(self, wallet=None):
		if wallet is None:
			wallet = self.selected_market.split('-')[1]
		return self.wallets[wallet]


	def get_amount(self, market=None):
		if market is None:
			market = self.selected_market
		return self.positions[market]["amount"]


	def get_price(self, market=None):
		if market is None:
			market = self.selected_market
		return self.positions[market]["price"]


	def get_invested(self, market=None):
		if market is None:
			market = self.selected_market
		return self.positions[market]["invested"]



class zCharter(object):
	def __init__(self, trader):
		super(zCharter, self).__init__()
		self.our_engine = zGUI.zEngine(SCREEN_SIZE, "zCharter")
		self.our_engine.get_window().set_refresh_behaviour(1, BACKGROUNDCOLOR)
		self.clock = pygame.time.Clock()
		self.trader = trader
		self.current_date = time.strftime("%d-%m-%Y", time.localtime())
		self.build_GUI()
		self.chart = dummyChart(self.our_engine)


	def log(self, tolog):
		print("[LOG] " + tolog)
		self.log_label.set_text("[LOG] " + tolog)


	def make_chart(self, targettime, exchange, market, period_name):
		if not isinstance(self.chart, dummyChart):
			self.our_engine.delete_zID(self.chart.zID)
			self.chart = dummyChart(self.our_engine)

		exchange = exchange.lower()
		try:
			secrets_file = open(exchange+"_secrets.json")
			secrets = json.load(secrets_file)
			secrets_file.close()
		except FileNotFoundError:
			secrets = {"api_key":None, "api_secret":None}

		api = None
		if exchange == "poloniex":
			api = poloniex.Poloniex(secrets["api_key"] , secrets["api_secret"])
		elif exchange == "bittrex":
			api = bittrex2.Bittrex2(secrets["api_key"] , secrets["api_secret"])
		elif exchange == "kraken":
			api = krakenOHLC
		elif exchange == "bitfinex":
			api = bitfinex_candles
		else:
			self.log("Invalid exchange")
			sys.exit(1)

		# "currencyPair"
		# "period" (candlestick period in seconds; valid values are 300, 900, 1800, 7200, 14400, and 86400)
		# "start" and "end" are given in UNIX timestamp format and used to specify the date range for the data returned.
		now = int(time.time()) #seconds
		start = now - int(500*24*3600) #seconds
		market = market.upper()
		period_name = period_name.lower()
		self.trader.switch_to_market(market)

		r = None
		cs = []
		if exchange == "poloniex":
			period_u = poloniex_unit[period_name]

			if not (period_u in poloniex_conversion):
				self.log("Invalid period for poloniex")
				sys.exit(1)
			period_c = poloniex_conversion[period_u]
			pair = '_'.join(market.split('-')[::-1])
			r = api.returnChartData(pair, period_c, start, now)
			cs = r["candleStick"]

		elif exchange == "bittrex":
			period_u = bittrex_unit[period_name]

			if not (period_u in bittrex_conversion):
				self.log("Invalid period for bittrex")
				sys.exit(1)
			period_c = bittrex_conversion[period_u]
			pair = '-'.join(market.split('-')[::-1])
			r = api.getChartData(pair, period_c)
			cs_t = r["result"]

			for candle in cs_t:
				converted = {}
				converted["open"] = candle["O"]
				converted["close"] = candle["C"]
				converted["high"] = candle["H"]
				converted["low"] = candle["L"]
				converted["volume"] = candle["BV"]
				ttt = candle["T"]
				strt = time.strptime(ttt, "%Y-%m-%dT%H:%M:%S")
				converted["date"] = time.mktime(strt) + 7200 # +2h for local time
				cs.append(converted)

		elif exchange == "kraken":
			period_u = kraken_unit[period_name]

			if not (period_u in kraken_conversion):
				self.log("Invalid period for poloniex")
				sys.exit(1)
			period_c = kraken_conversion[period_u]
			pair = ''.join(market.split('-'))
			r = api.getOHLCdata(pair, period_c, start)
			cs_t = None
			for k in r["result"]:
				if k != "last":
					cs_t = r["result"][k]
					break

			# cs_t is array of array entries(<time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>)
			for c in cs_t:
				ts = c[0]
				candle = {"date":ts}
				candle["open"] = float(c[1])
				candle["high"] = float(c[2])
				candle["low"] = float(c[3])
				candle["close"] = float(c[4])
				candle["volume"] = float(c[6])
				cs.append(candle)

		elif exchange == "bitfinex":
			period_u = bitfinex_unit[period_name]

			if not (period_u in bitfinex_conversion):
				self.log("Invalid period for bitfinex")
				sys.exit(1)
			period_c = bitfinex_conversion[period_u]
			pair = ''.join(market.split('-'))
			r = api.get_candles(pair, period_c, options={"limit":1000})
			for c in r:
				ts = int(c[0])//1000
				candle = {"date":ts}
				candle["open"] = float(c[1])
				candle["close"] = float(c[2])
				candle["high"] = float(c[3])
				candle["low"] = float(c[4])
				candle["volume"] = float(c[5])
				cs.append(candle)

		candlestick_data = {}
		for candle in cs:
			candlestick_data[candle["date"]] = candle
		candlestick_data = reformat_candle_data(candlestick_data, period_in_seconds[period_name])

		self.chart = zChart(self.our_engine, candlestick_data, CHART_SIZE, CHART_POS)
		return self.chart.travel_to(targettime)


	def get_chart(self, targettime, exchange, pair, interval, coinamt_label, fiatamt_label):
		try:
			tolog = self.make_chart(targettime, exchange, pair, interval)
			coinamt_label.set_text("AMOUNT "+pair.split('-')[0].upper())
			fiatamt_label.set_text("AMOUNT "+pair.split('-')[1].upper())
			self.log("Price history OK --- " + tolog)
		except Exception as e:
			self.log("Can't get price history: {:s}".format(repr(e)))


	def build_GUI(self):
		exchange_textfield = zGUI.zTextField(self.our_engine, (120, 30), font=BOLD_FONT, foreground=TEXTCOLOR, background=FIELDBACKGROUNDCOLOR, border=FIELDBORDERCOLOR)
		exchange_textfield.set_pos((SCREEN_X*0.05, 10))

		pair_textfield = zGUI.zTextField(self.our_engine, (120, 30), font=BOLD_FONT, foreground=TEXTCOLOR, background=FIELDBACKGROUNDCOLOR, border=FIELDBORDERCOLOR)
		pair_textfield.set_pos((SCREEN_X*0.05+130, 10))

		interval_textfield = zGUI.zTextField(self.our_engine, (60, 30), font=BOLD_FONT, foreground=TEXTCOLOR, background=FIELDBACKGROUNDCOLOR, border=FIELDBORDERCOLOR)
		interval_textfield.set_pos((SCREEN_X*0.05+260, 10))

		timetravel_label = zGUI.zLabel(self.our_engine, "Time travel:", 24, font=REGULAR_FONT, color=TEXTCOLOR)
		timetravel_label.set_pos((SCREEN_X-850, 14))

		timetravel_textfield = zGUI.zTextField(self.our_engine, (120, 30), font=BOLD_FONT, foreground=TEXTCOLOR, background=FIELDBACKGROUNDCOLOR, border=FIELDBORDERCOLOR)
		timetravel_textfield.set_pos((SCREEN_X-680, 10))
		timetravel_textfield.set_text(self.current_date)

		self.setdate_button = zGUI.zButton(self.our_engine, (40, 30), zGUI.DARKYELLOW, zGUI.YELLOW, zGUI.MEDIUMYELLOW)
		self.setdate_button.set_pos((SCREEN_X-550, 10))
		self.setdate_button.action_performer(lambda: self.log(self.chart.travel_to(timetravel_textfield.text)))

		fastbackintime_button = zGUI.zButton(self.our_engine, (40, 30), zGUI.GRAY, zGUI.GRAY, zGUI.GRAY)
		fastbackintime_button.set_pos((SCREEN_X-495, 10))
		fastbackintime_button.action_performer(lambda: self.log(self.chart.back_in_time(15)))

		backintime_button = zGUI.zButton(self.our_engine, (40, 30), zGUI.GRAY, zGUI.GRAY, zGUI.GRAY)
		backintime_button.set_pos((SCREEN_X-450, 10))
		backintime_button.action_performer(lambda: self.log(self.chart.back_in_time(1)))

		forwardintime_button = zGUI.zButton(self.our_engine, (40, 30), zGUI.DARKGRAY, zGUI.DARKGRAY, zGUI.DARKGRAY)
		forwardintime_button.set_pos((SCREEN_X-405, 10))
		forwardintime_button.action_performer(lambda: self.log(self.chart.forward_in_time(1)))

		fastforwardintime_button = zGUI.zButton(self.our_engine, (40, 30), zGUI.DARKGRAY, zGUI.DARKGRAY, zGUI.DARKGRAY)
		fastforwardintime_button.set_pos((SCREEN_X-360, 10))
		fastforwardintime_button.action_performer(lambda: self.log(self.chart.forward_in_time(15)))

		fps_label = zGUI.zDynamicLabel(self.our_engine, 20, font=REGULAR_FONT, color=TEXTCOLOR)
		fps_label.set_pos((SCREEN_X*0.9, 10))
		fps_label.set_dynamic_text(lambda: "%.1f FPS"%(self.clock.get_fps()))

		nochart = zGUI.zImage(self.our_engine, CHART_SIZE, zGUI.BLACK)
		nochart.set_pos(CHART_POS)

		wallets_panel = zGUI.zPanel(self.our_engine, WALLETSPANEL_SIZE)
		wallets_panel.set_refresh_behaviour(1, PANELCOLOR)

		self.wallets_table = zGUI.zTable(self.our_engine, 16, font=REGULAR_FONT, color=TEXTCOLOR, columns=["BALANCES:"])
		wallets_panel.add_widget(self.wallets_table)
		self.wallets_table.set_pos((10, 10))

		wallets_panel.set_pos(WALLETSPANEL_POS)

		neworder_panel = zGUI.zPanel(self.our_engine, NEWORDERPANEL_SIZE)
		neworder_panel.set_refresh_behaviour(1, PANELCOLOR)

		neworder_label = zGUI.zLabel(self.our_engine, "New order", 30, font=REGULAR_FONT, color=TEXTCOLOR)
		neworder_panel.add_widget(neworder_label)
		neworder_label.set_pos((10, 10))

		coinamt_label = zGUI.zLabel(self.our_engine, "AMOUNT COIN", 18, font=REGULAR_FONT, color=TEXTCOLOR)
		neworder_panel.add_widget(coinamt_label)
		coinamt_label.set_pos((10, 70))

		coinamt_textfield = zGUI.zTextField(self.our_engine, (200, 30), font=REGULAR_FONT, foreground=TEXTCOLOR, background=FIELDBACKGROUNDCOLOR, border=FIELDBORDERCOLOR)
		neworder_panel.add_widget(coinamt_textfield)
		coinamt_textfield.set_pos((10, 100))

		fiatamt_label = zGUI.zLabel(self.our_engine, "AMOUNT FIAT", 18, font=REGULAR_FONT, color=TEXTCOLOR)
		neworder_panel.add_widget(fiatamt_label)
		fiatamt_label.set_pos((10, 150))

		fiatamt_textfield = zGUI.zTextField(self.our_engine, (200, 30), font=REGULAR_FONT, foreground=TEXTCOLOR, background=FIELDBACKGROUNDCOLOR, border=FIELDBORDERCOLOR)
		neworder_panel.add_widget(fiatamt_textfield)
		fiatamt_textfield.set_pos((10, 180))

		getchart_button = zGUI.zButton(self.our_engine, (40, 30), zGUI.DARKYELLOW, zGUI.YELLOW, zGUI.MEDIUMYELLOW)
		getchart_button.set_pos((SCREEN_X*0.05+330, 10))
		getchart_button.action_performer(lambda: self.get_chart(timetravel_textfield.text, exchange_textfield.text, pair_textfield.text, interval_textfield.text, coinamt_label, fiatamt_label))

		coinamt_textfield.action_performer(lambda: coin_to_fiat(coinamt_textfield, fiatamt_textfield, self.chart.get_current_price_from_data()))
		fiatamt_textfield.action_performer(lambda: fiat_to_coin(fiatamt_textfield, coinamt_textfield, self.chart.get_current_price_from_data()))

		long_button = zGUI.zButton(self.our_engine, (90, 30), zGUI.DARKGREEN, zGUI.GREEN, zGUI.MEDIUMGREEN)
		neworder_panel.add_widget(long_button)
		long_button.set_pos((15, 220))
		long_button.action_performer(lambda: self.open_position(float(coinamt_textfield.text)))

		short_button = zGUI.zButton(self.our_engine, (90, 30), zGUI.DARKRED, zGUI.RED, zGUI.MEDIUMRED)
		neworder_panel.add_widget(short_button)
		short_button.set_pos((115, 220))
		short_button.action_performer(lambda: self.open_position(-float(coinamt_textfield.text)))

		neworder_panel.set_pos(NEWORDERPANEL_POS)

		details_panel = zGUI.zPanel(self.our_engine, DETAILSPANEL_SIZE)
		details_panel.set_refresh_behaviour(1, PANELCOLOR)

		thisposition_label = zGUI.zDynamicLabel(self.our_engine, 20, font=REGULAR_FONT, color=TEXTCOLOR)
		details_panel.add_widget(thisposition_label)
		thisposition_label.set_pos((10, 10))
		thisposition_label.set_dynamic_text(lambda: "{:s} position:".format(self.trader.selected_market))

		coinposition_label = zGUI.zDynamicLabel(self.our_engine, 16, font=REGULAR_FONT, color=TEXTCOLOR)
		details_panel.add_widget(coinposition_label)
		coinposition_label.set_pos((10, 40))
		coinposition_label.set_dynamic_text(lambda: "{:+.8f} {:s}".format(self.trader.get_amount(), self.trader.selected_market.split('-')[0]))

		priceposition_label = zGUI.zDynamicLabel(self.our_engine, 16, font=REGULAR_FONT, color=TEXTCOLOR)
		details_panel.add_widget(priceposition_label)
		priceposition_label.set_pos((10, 70))
		priceposition_label.set_dynamic_text(lambda: "@ {:.8f} {:s}".format(self.trader.get_price(), self.trader.selected_market.split('-')[1]))

		pricenow_label = zGUI.zLabel(self.our_engine, "Price now:", 20, font=REGULAR_FONT, color=TEXTCOLOR)
		details_panel.add_widget(pricenow_label)
		pricenow_label.set_pos((10, 120))

		change_label = zGUI.zDynamicLabel(self.our_engine, 14, font=REGULAR_FONT, color=TEXTCOLOR)
		details_panel.add_widget(change_label)
		change_label.set_pos((10, 150))
		change_label.set_dynamic_text(lambda: "{:.8f} {:s} ({:+.2f}%)".format(self.chart.get_current_price_from_data(), self.trader.selected_market.split('-')[1], 100*self.chart.get_current_price_from_data()/self.trader.get_price()-100 if abs(self.trader.get_price())>EPSILON else 0.0))

		profitloss_label = zGUI.zDynamicLabel(self.our_engine, 14, font=REGULAR_FONT, color=TEXTCOLOR)
		details_panel.add_widget(profitloss_label)
		profitloss_label.set_pos((10, 180))
		profitloss_label.set_dynamic_text(lambda: "P/L: {:+.8f} {:s}".format(self.trader.get_amount()*self.chart.get_current_price_from_data()-self.trader.get_invested(), self.trader.selected_market.split('-')[1]))

		details_panel.set_pos(DETAILSPANEL_POS)

		log_panel = zGUI.zPanel(self.our_engine, LOGPANEL_SIZE)
		log_panel.set_refresh_behaviour(1, PANELCOLOR)

		self.log_label = zGUI.zLabel(self.our_engine, "[LOG] Start OK", 15, font=REGULAR_FONT, color=TEXTCOLOR)
		log_panel.add_widget(self.log_label)
		self.log_label.set_pos((5, 5))

		log_panel.set_pos(LOGPANEL_POS)

		positions_panel = zGUI.zPanel(self.our_engine, POSITIONSPANEL_SIZE)
		positions_panel.set_refresh_behaviour(1, PANELCOLOR)

		openpositions_label = zGUI.zLabel(self.our_engine, "Open positions", 20, font=REGULAR_FONT, color=TEXTCOLOR)
		positions_panel.add_widget(openpositions_label)
		openpositions_label.set_pos((10, 10))

		self.positions_table = zGUI.zTable(self.our_engine, 14, font=REGULAR_FONT, color=TEXTCOLOR, columns=["MARKET", "INVESTED"])
		positions_panel.add_widget(self.positions_table)
		self.positions_table.set_pos((10, 40))

		positions_panel.set_pos(POSITIONSPANEL_POS)


	def open_position(self, amount):
		try:
			price = self.chart.get_current_price_from_data()
			self.log(self.trader.edit_position(amount, price))
		except Exception as e:
			self.log("Can't open position: {:s}".format(repr(e)))
		self.positions_table.clear_rows()
		for pos in self.trader.positions:
			if self.trader.get_invested(pos) != 0.0:
				self.positions_table.add_row([pos, "{:+.8f} {:s}".format(self.trader.get_invested(pos), pos.split('-')[1])], pos)
		self.wallets_table.clear_rows()
		for w in self.trader.wallets:
			if self.trader.get_balance(w) != 0.0:
				self.wallets_table.add_row(["{:+.8f} {:s}".format(self.trader.get_balance(w), w)], w)


	def go(self):
		RUN = True
		while RUN:
			self.clock.tick(20)
			RUN = self.our_engine.handle_events()
			self.our_engine.handle_draws()



if __name__ == '__main__':
	charter_app = zCharter(zSimTrader())
	charter_app.go()
