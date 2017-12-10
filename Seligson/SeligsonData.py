import urllib2
import pandas as pd
import datetime
import StringIO

class SeligsonData:
	def __init__(self):
		self.urls = ["www.seligson.fi/graafit/rahamarkkina.csv",
"www.seligson.fi/graafit/eurocorporate.csv",
"www.seligson.fi/graafit/euroobligaatio.csv",
"www.seligson.fi/graafit/eurooppa.csv",
"www.seligson.fi/graafit/global-brands.csv",
"www.seligson.fi/graafit/global-pharma.csv",
"www.seligson.fi/graafit/japani.csv", 
"www.seligson.fi/graafit/pharos.csv",
"www.seligson.fi/graafit/phoenix.csv",
"www.seligson.fi/graafit/phoebus.csv",
"www.seligson.fi/graafit/pohjoisamerikka.csv",
"www.seligson.fi/graafit/russia.csv",
"www.seligson.fi/graafit/kehittyva.csv",
"www.seligson.fi/graafit/suomi.csv",
"www.seligson.fi/graafit/aasia.csv"]
		

	def mydateparser(self, mystr):
		(day, month, year) = mystr.split('.')
		return datetime.datetime(int(year), int(month), int(day))
	
	def download(self):
		url = self.urls[0]
		csvdata = urllib2.urlopen("http://" + url).read()
		df = pd.io.parsers.read_csv(StringIO.StringIO(csvdata), sep=";", parse_dates=[0], date_parser=self.mydateparser, names=["Date", url.split("/")[-1].split('.')[0]], index_col=0)

		for url in self.urls[1:]:
			csvdata = urllib2.urlopen("http://" + url).read()
			if "ei valitettavasti" in csvdata:
				continue
			df2 = pd.io.parsers.read_csv(StringIO.StringIO(csvdata), sep=";", parse_dates=[0], date_parser=self.mydateparser, names=["Date", url.split("/")[-1].split('.')[0]], index_col=0)
			df = df.join(df2)

		return df
