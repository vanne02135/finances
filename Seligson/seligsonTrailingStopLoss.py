#!/usr/bin/python
# coding=UTF-8

# Testing trailing stop loss strategies with Seligson Index Funds

from SeligsonData import SeligsonData
import cPickle
import datetime
import pandas as pd

class NewPortfolio: 
	def __init__(self, initCash = 10000.0, startDate=datetime.datetime.now()):
		self.assets = pd.DataFrame(index=[datetime.datetime.now()], columns = ["cash", "taxesDue", "taxesPaid", "transactionFee"])
		self.assets["cash"][0] = initCash
	
	def buy(self, assetName, units, priceDataFrame):
		# buy number of units of assetName and use price from priceDataFrame
		pass

	def sell(self, assetName, units, priceDataFrame):
		# buy number of units of assetName and use price from priceDataFrame
		# Taxes are accounted in assets["taxesDue"] and at next year's end the taxesDue are moved to assets["taxesPaid"] and deducted from cash
		pass

	def evaluatePerformance(priceDataFrame):
		# Evaluate portfolio performance. Input should be dataFrame including 
		# the per day price information for assets in the Portfolio.assets dataframe
		# Return: performance per year, taxes per year, fees per year 
		# total performance p.a. 
		raise Exception("Not implemented yet")
		pass 

class OldPortfolio:
	# Simple portfolio class without short selling 

	# TODO: create a pandas DataFrame of assets, would be easy to visualize
	# You have to store the order assets were bought in since oldest are sold first
	# Take taxes and fees into account
	# Tax: at the end of each year taxes are deducted from cash. If there are losses,
	# they can be deducted from profits for 3 years. 

	# Pitäisikö rakenne olla jotain tällaista:
	# transactions[date] = (BUY|SELL, ASSET, AMOUNT_OF_ASSETS, FEE)
	# Miten tehdään kassan lisäys? Onko portfoliossa transaktioiden lisäksi
	# cash sekä aina vuoden lopussa ulos maksettava vero ja mahdollisesti edellisiltä
	# vuosilta kertyneet tappiot?

	def __init__(self, initCash = 10000.0):
		self.initCash = initCash
		self.assets = {}
		self.assets["cash"] = initCash

		self.log = {}

	def buy(self, date, asset, unitPrice, totalSum):
		if totalSum > self.assets["cash"]:
			raise Exception("Not enough cash")

		self.assets["cash"] -= totalSum

		if asset in self.assets.keys():
			self.assets[asset] += totalSum / unitPrice
		else:
			self.assets[asset] = totalSum / unitPrice

		self.log[date] = { "buy": (asset, unitPrice, totalSum)}

	def sell(self, date, asset, unitPrice, totalSum):
		if asset not in self.assets.keys():
			raise Exception("Short selling not allowed")
		
		if self.assets[asset] * unitPrice > totalSum:
			raise Exception("Short selling not allowed")

		self.assets["cash"] += totalSum

		self.assets[asset] -= totalSum / unitPrice

		self.log[date] = { "sell": (asset, unitPrice, totalSum)}

	def sellAll(self, date, asset, unitPrice):
		if asset not in self.assets.keys():
			raise Exception("Asset not in portfolio")

		totalSum = self.assets[asset] * unitPrice
		self.assets["cash"] += totalSum

		self.assets[asset] = 0 

		self.log[date] = { "sell": (asset, unitPrice, totalSum)}

	def buyAll(self, date, asset, unitPrice):
		totalSum = self.assets["cash"]
		if asset in self.assets.keys():
			self.assets[asset] += totalSum / unitPrice
		else:
			self.assets[asset] = totalSum / unitPrice

		self.assets["cash"] = 0.0
		self.log[date] = { "buy": (asset, unitPrice, totalSum)}


def testPortfolio():

	myPortfolio = OldPortfolio()

	myPortfolio.buy(datetime.datetime.now(), "EUROOPPA", 2, 10000)

	assert myPortfolio.assets["cash"] == 0.0


	myPortfolio.sell(datetime.datetime.now()+datetime.timedelta(10), "EUROOPPA", 2.5, 12500)

	assert myPortfolio.assets["EUROOPPA"] == 0

	assert myPortfolio.assets["cash"] == 12500

	print myPortfolio.log

def getHistory():
	try:
		data = cPickle.load(open("seligsonCache.pickle"))
		print "Loaded cached data from seligsonCache.pickle"
	except:
		print "Downloading fresh data from Seligson"
		data = SeligsonData().download()
		cPickle.dump(data, open("seligsonCache.pickle", "w"))

	return data


def testTrailingStopLoss(data, asset = "eurooppa"):
	trailing_days = 260

	transActionThreshold = -0.15

	pf = OldPortfolio()

	for k in range(trailing_days, len(data.eurooppa)):
		currentDate = data.index[k]
		highValue = data[asset][k-trailing_days:k+1].max()
		currentValue = data[asset][k]
		if len(data[asset][k-10:k].dropna()) > 0:
 			previousValue = data[asset][k-10:k].dropna().values[-1]
 		else:
 			continue

		changeFromHigh = (currentValue - highValue) / highValue
		if changeFromHigh > transActionThreshold and currentValue > previousValue and pf.assets["cash"] > 0.0:
			pf.buyAll(currentDate, asset, currentValue)
		elif changeFromHigh < transActionThreshold and currentValue < previousValue and pf.assets[asset] > 0:
			pf.sellAll(currentDate, asset, currentValue)


	pf.sellAll(data.index[-1], asset, currentValue)

	cash = pf.assets["cash"]
	
	BHreturn = (data[asset].dropna().values[-1] - data[asset].dropna().values[0]) / data[asset].dropna().values[0] * 100 

	#print pf.log
	print "ASSET: %s" % asset
	print "Trailing days: %d, action threshold: %.2f %%, return: %.2f %% (compare to B-H %.2f %%)" % (trailing_days, transActionThreshold*100, (cash - 10000.0)/10000.0 * 100, BHreturn)



if __name__ == "__main__":
	testPortfolio()

	data = getHistory()
	testTrailingStopLoss(data, "eurooppa")
	testTrailingStopLoss(data, "pohjoisamerikka")
	testTrailingStopLoss(data, "suomi")

	eurooppa_drawdown = []
	trailing_days = 260

	for k in range(trailing_days, len(data.eurooppa)):
		highValue = data.eurooppa[k-trailing_days:k].max()
		eurooppa_drawdown.append((data.eurooppa[k] - highValue)/highValue)
   
	pohjoisamerikka_drawdown = []
	for k in range(trailing_days, len(data.pohjoisamerikka)):
		highValue = data.pohjoisamerikka[k-trailing_days:k].max()
		pohjoisamerikka_drawdown.append((data.pohjoisamerikka[k] - highValue)/highValue)

