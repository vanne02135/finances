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


def drawdowns_example(funds):
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

if __name__ == "__main__":
    np.random.seed(0)
    n = 100
    s = pd.Series(np.random.randn(n).cumsum())

    window_length = 10

    rolling_dd = pd.rolling_apply(s, window_length, max_dd, min_periods=0)
    df = pd.concat([s, rolling_dd], axis=1)
    df.columns = ['s', 'rol_dd_%d' % window_length]
    df.plot(linewidth=3, alpha=0.4)

    my_rmdd = rolling_max_dd(s.values, window_length, min_periods=1)
    plt.plot(my_rmdd, 'g.')

    plt.show()