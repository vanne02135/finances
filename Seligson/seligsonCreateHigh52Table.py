#!/usr/bin/python

from SeligsonData import SeligsonData
import datetime as dt
import csv

data = SeligsonData().download()


now = dt.datetime.now()

print "Fund\t\tDate\t\tLatest price\t\tHigh 52\t\tDown from high52"
csvw = csv.writer(open("seligsonHigh52.csv", "w"))
csvw.writerow(["Fund", "Latest Date", "Latest Price", "High 52", "Down from high52"])
for fundname in data.keys():
	fund = data[fundname]
	yearAgo = now - dt.timedelta(365)
	lastYear = fund[yearAgo:]
	lastYearHigh = lastYear.max()
	latest = fund.dropna()[-1]
	latestDate = fund.dropna().index[-1]
	
	downFromHigh52 =  (lastYearHigh - latest) / lastYearHigh
	print "%s \t\t %s \t\t %f\t\t %f\t\t %f " % (fundname, latestDate, latest, lastYearHigh, downFromHigh52)
	csvw.writerow([fundname, str(latestDate), latest, lastYearHigh, downFromHigh52])
