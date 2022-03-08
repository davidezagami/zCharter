import os, random
import zGrapher
from btcstats import csv_load, get_weekday



WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

class BTCbot:
	def __init__(self, fiat_wallet, btc_wallet, name=None, live=False):
		self.fiat_wallet = fiat_wallet
		self.btc_wallet = btc_wallet
		self.name = name
		if not name:
			self.name = "bot"+str(random.randint(1000, 9999))
		self.logfile = open(os.path.join("botlogs", self.name+".log"), 'w')
		self.plotfile = os.path.join("botplots", self.name+".bmp")
		self.live = live


	def log(self, text):
		self.logfile.write(text+'\n')


	def buy_btc_specify_fiat(self, rate, fiat_amount):
		self.log("Current wallet: {:.2f} fiat, {:.8f} BTC".format(self.fiat_wallet, self.btc_wallet))
		self.log("Using {:.2f} fiat to buy {:.8f} BTC at price {:.2f} per BTC".format(fiat_amount, fiat_amount/rate, rate))

		self.fiat_wallet -= fiat_amount
		self.btc_wallet += fiat_amount/rate

		self.log("New wallet: {:.2f} fiat, {:.8f} BTC".format(self.fiat_wallet, self.btc_wallet))


	def sell_btc_specify_btc(self, rate, btc_amount):
		self.log("Current wallet: {:.2f} fiat, {:.8f} BTC".format(self.fiat_wallet, self.btc_wallet))
		self.log("Selling {:.8f} BTC at price {:.2f} per BTC to get {:.2f} fiat".format(btc_amount, rate, btc_amount*rate))

		self.btc_wallet -= btc_amount
		self.fiat_wallet += btc_amount*rate

		self.log("New wallet: {:.2f} fiat, {:.8f} BTC".format(self.fiat_wallet, self.btc_wallet))


	def wallet_fiat_value(self, rate):
		return self.fiat_wallet + self.btc_wallet*rate


	def wallet_btc_value(self, rate):
		return self.fiat_wallet/rate + self.btc_wallet


	def plot_history(self, data):
		formatted_data = dict(zip(range(len(data)), data))
		zGrapher.plot_data(formatted_data, "Days", "Funds", self.plotfile, self.live)


	def trade(self, historyfile):
		our_data = csv_load(os.path.join("CSVs", historyfile))
		bought_btc_at = 0.0
		good_sell_threshold = 1.03
		bad_sell_threshold = 0.98
		funds_history = []

		self.log("Bot starting. My thresholds are {:f} and {:f}\n\n".format(good_sell_threshold, bad_sell_threshold))
		for today in our_data:
			funds_history.append(self.wallet_fiat_value(float(today["Weighted Price"])))
			self.log(WEEKDAYS[get_weekday(today)]+" "+today["Date"])

			if get_weekday(today) == 0:
				self.log("Open: {:.2f} per BTC".format(float(today["Open"])))
				bought_btc_at = float(today["Open"])
				self.buy_btc_specify_fiat(bought_btc_at, self.fiat_wallet)
			
			self.log("High: {:.2f} per BTC".format(float(today["High"])))
			if float(today["High"])/bought_btc_at > good_sell_threshold:
				self.sell_btc_specify_btc(bought_btc_at*good_sell_threshold, self.btc_wallet)
			elif float(today["High"])/bought_btc_at < bad_sell_threshold:
				self.sell_btc_specify_btc(bought_btc_at*bad_sell_threshold, self.btc_wallet)

			self.log("")

		self.logfile.close()
		self.plot_history(funds_history)



if __name__ == "__main__":
	starting_fiat = 50.0
	starting_btc = 0.0
	for historyfile in os.listdir("CSVs"):
		if historyfile.endswith(".csv"):
			newbot = BTCbot(starting_fiat, starting_btc, historyfile[:-4])
			newbot.trade(historyfile)
			print("{} : {:.2f} fiat, {:.8f} BTC".format(historyfile, newbot.fiat_wallet, newbot.btc_wallet))
