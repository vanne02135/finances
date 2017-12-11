# Calculating signal drawdowns & max drawdowns
# See also https://stackoverflow.com/questions/21058333/compute-rolling-maximum-drawdown-of-pandas-series

import numpy as np
from numpy.lib.stride_tricks import as_strided
import pandas as pd
import matplotlib.pyplot as plt


def windowed_view(x, window_size):
    """Creat a 2d windowed view of a 1d array.

    `x` must be a 1d numpy array.

    `numpy.lib.stride_tricks.as_strided` is used to create the view.
    The data is not copied.

    Example:

    >>> x = np.array([1, 2, 3, 4, 5, 6])
    >>> windowed_view(x, 3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5],
           [4, 5, 6]])
    """
    y = as_strided(x, shape=(x.size - window_size + 1, window_size),
                   strides=(x.strides[0], x.strides[0]))
    return y


def rolling_max_dd(x, window_size, min_periods=1):
    """Compute the rolling maximum drawdown of `x`.

    `x` must be a 1d numpy array.
    `min_periods` should satisfy `1 <= min_periods <= window_size`.

    Returns an 1d array with length `len(x) - min_periods + 1`.
    """
    if min_periods < window_size:
        pad = np.empty(window_size - min_periods)
        pad.fill(x[0])
        x = np.concatenate((pad, x))
    y = windowed_view(x, window_size)
    running_max_y = np.maximum.accumulate(y, axis=1)
    dd = y - running_max_y
    return dd.min(axis=1)


def max_dd(ser):
    max2here = pd.expanding_max(ser)
    dd2here = ser - max2here
    return dd2here.min()

def drawdown(ser):
    max2here = pd.expanding_max(ser)
    dd2here = ser - max2here
    return dd2here[-1]

def rolling_dd(signal, window_length):
    return pd.rolling_apply(signal, window_length, drawdown, min_periods=0)

def rolling_max(signal, window_length):
    return pd.rolling_apply(signal, window_length, max, min_periods=0)


def drawdowns_example_plot(funds):
    # funds = SeligsonData().download()
    windowDays = 365

    fundnames = funds.keys()
    drawdowns = funds.copy()
    for name in fundnames:
        print "Processing %s" % name
        rollmax = rolling_max(funds[name].values, windowDays)
        rolldd = rolling_dd(funds[name].values, windowDays)
        drawdowns[name] = (rollmax - rolldd) / rollmax * 100 - 100
    print "...done. Plotting"
    for name in fundnames:
        plt.figure()
        ax1 = funds[name].plot()
        ax2 = drawdowns[name].plot(secondary_y=True)
        ax1.set_title("Seligson %s Fund" % name)
        ax1.grid()
        ax1.set_ylabel("Price (EUR, blue)")
        ax2.set_ylabel("52wk drawdown (%, green)")
        plt.show()

def drawdowns_strategy_backtest(funds, stoploss_thresholds=[10, 15, 20, 25]):
    # funds = SeligsonData().download()
    # stoploss_thresholds: long position, when stoploss is under threshold 
    windowDays = 365  # drawdown window size in days

    fundnames = funds.keys()

    drawdowns = funds.copy()
    for name in fundnames:
        print "Calculating drawdowns %s" % name
        rollmax = rolling_max(funds[name].values, windowDays)
        rolldd = rolling_dd(funds[name].values, windowDays)
        drawdowns[name] = (rollmax - rolldd) / rollmax * 100 - 100
    print "...done. Backtesting"
    returns = funds.copy()
    for name in fundnames:
        # Use log returns
        returns[name] = np.log(funds[name] / funds[name].shift(1))
        cols = [name]
        for stoploss in stoploss_thresholds:
            col = "stoploss_%d" % stoploss
            # long position, when drawdown (in %) more than stoploss threshold value
            returns[col] = returns[name] * (drawdowns[name].shift(1).values < stoploss) * 1.0
            cols.append(col)
        returns[cols].dropna().cumsum().apply(np.exp).plot()
        plt.legend(cols, loc="best")
        plt.show()        
        #plt.figure()
        #ax1 = funds[name].plot()
        #ax2 = drawdowns[name].plot(secondary_y=True)
        #ax1.set_title("Seligson %s Fund" % name)
        #ax1.grid()
        #ax1.set_ylabel("Price (EUR, blue)")
        #ax2.set_ylabel("52wk drawdown (%, green)")
        #plt.show()


if __name__ == "__main__":
    import SeligsonData
    funds = SeligsonData.SeligsonData().download()

    # Test long position on suomi fund, when 52wk drawdown is less than
    # 13, 16, 19 % on different times
    drawdowns_strategy_backtest(funds[["suomi"]], [13, 16, 19])    

    drawdowns_strategy_backtest(funds[["suomi"]][2012:], [13, 16, 19])
