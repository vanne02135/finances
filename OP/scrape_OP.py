#!/usr/bin/python

import datetime
import urllib2
import bs4
import json
import sys

class OPStockHistory:
	def __init__(self):
		pass

	def get(self, tickername, start_date = datetime.datetime(2003, 1, 1), end_date = datetime.datetime.now()):
		# return 
		# date, close price, vaihto (eur), vaihto (kpl), avg price
		linkTemplate = "https://www.op.fi/op/henkiloasiakkaat/saastot-ja-sijoitukset/kurssit-ja-markkinat/osakekurssit?sivu=csv.html&language=fi&id=32455&sym=%s&use_corrections=1&from_year=%d&from_month=%d&from_day=%d&to_year=%d&to_month=%d&to_day=%d"

		link = linkTemplate % (tickername, start_date.year, start_date.month, start_date.day, end_date.year, end_date.month, end_date.day)
		print "Fetching %s from %s to %s" % (tickername, start_date, end_date)
		print "from %s" % link
		htmldata = urllib2.urlopen(link).read()
		open("rawhtml.txt", "w").write(htmldata)
		bs = bs4.BeautifulSoup(htmldata, "html.parser") # fails to parse large files if html.parser not specified

		pricetable = bs.findAll('table')[4]
		rows = pricetable.findAll('tr')

		dailyPrices = []

		for row in rows[1:]:
			rowItems = [cell.text for cell in row.findAll('td')]
			for k in xrange(1,len(rowItems)):
				try:
					rowItems[k] = float(rowItems[k].replace(',','.'))
				except:
					pass
			dailyPrices.append(rowItems)

		return dailyPrices

if __name__ == "__main__":
	ophist = OPStockHistory()

	stockHistory = ophist.get(sys.argv[1])
	json.dump(stockHistory, open(sys.argv[1] + ".json", "w"))

