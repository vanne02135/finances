import pandas as pd
import numpy as np
import scipy as sp
from scipy import optimize as opt 

import Quandl
import math
import datetime

def getMultipleLogReturns(tickers):
	# return a dataframe with log returns of abovementioned tickers

	logreturns = {}
	for ticker in tickers:
		print "Retrieving %s" % ticker
		df = Quandl.get(ticker)
		logreturns[ticker] = pd.Series((df.Close/ df.Close.shift(1)).apply(math.log))
	return pd.DataFrame(logreturns, columns = tickers)

def minimumVariancePortfolio(dataFrame):
	# calc min var portfolio weigths for dataframe with log returns
	# other room for improvement lies in the estimation of the covariance matrix, see e.g.
	# http://quantivity.wordpress.com/2011/04/17/minimum-variance-portfolios/
	# also this should be improved so that NaN in columns work. 

	Sigma = dataFrame.cov().as_matrix()
	Sigma = np.vstack([2*Sigma, [1]*dataFrame.columns.size])
	myvec = [1]*dataFrame.columns.size
	myvec.append(0)
	Sigma = np.hstack([Sigma, np.mat(myvec).T])
	myvec = [0]*(dataFrame.columns.size + 1)
	myvec[-1] = 1
	b = np.array(myvec)
	#z = np.linalg.inv(Sigma) * np.mat(b).T
	try:
		z = np.linalg.lstsq(Sigma, np.mat(b).T)[0]
		return z[0:-1]
	except np.linalg.LinAlgError:
		print "Bad condition in Sigma, returning equal weights"
		return [1.0/dataFrame.columns.size]*dataFrame.columns.size


def minimumVariancePortfolioNonneg(returnsDF):
	# use bounded fminsearch to determine weights
	# input: data frame containing returns
	# output: column weights
	def f(x):
		return (x.sum() - 1)**2 +  dfVariance(x, returnsDF)


	N = len(returnsDF.columns)
	x0 = [1.0/N]*N

	bounds = [(0, 1)]*N

 	w_nonneg = opt.fmin_l_bfgs_b(f, x0, bounds = bounds, approx_grad=True)
	

 	if w_nonneg[2]["warnflag"]:
 		print "Warning: minimization did not converge or something"

 	return w_nonneg[0]


def minVarRotation(returns, rebalancingInDays, longOnly = True):
	current = returns.index.min() + datetime.timedelta(rebalancingInDays)
	
	z = {}
	if longOnly:
		minimizationAlg = minimumVariancePortfolioNonneg 
	else:
		minimizationAlg = minimumVariancePortfolio
	while current < returns.index.max():
		z[current] = (minimizationAlg(returns[current - datetime.timedelta(rebalancingInDays):current]))
		current += datetime.timedelta(rebalancingInDays)
	return z

def calcReturns(returns, coefficients):
	keys = coefficients.keys()
	keys.sort()
	delta = keys[1] - keys[0]
	portfolioreturn = pd.Series(index=returns.index)
	portfolioreturn.fill(0.0)
	for k in keys: 
		co = coefficients[k]
		returnsSlice = returns[k:k+delta]
		for i, c in enumerate(co):
			c = float(c)
			portfolioreturn[k:k+delta] = portfolioreturn[k:k+delta].add(returnsSlice[returnsSlice.columns[i]] * c)
	return portfolioreturn


def minimumVariancePortfolio_3(dataFrame):
	# calc min var portfolio weigths for dataframe with log returns 
	# other room for improvement lies in the estimation of the covariance matrix, see e.g.
	# http://quantivity.wordpress.com/2011/04/17/minimum-variance-portfolios/
	Sigma = dataFrame.cov().as_matrix()
	Sigma = np.vstack([2*Sigma, [1, 1, 1]])
	Sigma = np.hstack([Sigma, np.mat([1, 1, 1, 0]).T])
	b = np.array([0, 0, 0, 1])
	#z = np.linalg.inv(Sigma) * np.mat(b).T
	z = np.linalg.lstsq(Sigma, np.mat(b).T)

	return z[0:3]

def dfVariance(weights, df): 
	# return variance of weights[0]*df[df.columns[0]] + ... weights[N-1]*df[df.columns[N-1]]
	a = weights[0] * df[df.columns[0]]
	for i, col in enumerate(df.columns[1:]):
		a += weights[i] * df[col]
	return a.var()



def finnishSectorRotation(rebalancingInDays):

	df = pd.DataFrame()
	df = pd.read_hdf('OP_data/miscClosePrices.h5', 'ClosePrices')
	df = df.sort()

	returns = pd.DataFrame(index = df.index)
	#tickers = ['WRT1V', 'ELI1V', 'FUM1V', 'KCR1V', 'KESBV', 'MEO1V', 'NES1V', 'NRE1V', 'OLVAS', 'OUT1V', 'SAMAS', 'STCBV', 'TIE1V', 'UPM1V', 'YTY1V']
	tickers = ['WRT1V', 'ELI1V', 'FUM1V', 'KCR1V', 'KESBV', 'MEO1V', 'NRE1V', 'OLVAS', 'OUT1V', 'SAMAS', 'STCBV', 'TIE1V', 'UPM1V', 'YTY1V']

	for ticker in tickers:
		returns[ticker] = pd.Series((df[ticker] / df[ticker].shift(1)).apply(math.log))

	minvarcoef = minVarRotation(returns, rebalancingInDays, longOnly = False)

	minvarcoefPos = minVarRotation(returns, rebalancingInDays, longOnly = True)


	eq = minvarcoef.copy()

	for k in eq.keys():
		eq[k] = [1.0 / len(tickers) ]*len(tickers)


	mvreturns = calcReturns(returns, minvarcoef)
	mvPosreturns = calcReturns(returns, minvarcoefPos)

	eqreturns = calcReturns(returns, eq)

	# plot portfolio returns
	mvreturns.cumsum().plot(label='Min Var %d' % rebalancingInDays)
	mvPosreturns.cumsum().plot(label='Min var %d long only' % rebalancingInDays)
	eqreturns.cumsum().plot(label = 'Equal weight')
	from matplotlib import pyplot
	pyplot.legend(loc='upper left')
	pyplot.title(tickers)

	# plot portfolio weights
	weights = dict()
	for k in minvarcoefPos.keys():
		weights[k] =  np.array(minvarcoefPos[k]).squeeze()

	weights = pd.DataFrame(weights.values(), index = weights.keys())
	weights.columns = tickers
	
	weights.plot()
	pyplot.legend()


