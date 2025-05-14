import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import argrelextrema
# from tqdm import tqdm


def fit(x, y, order):
    try:
        values = curve_fit(f=poly, p0=np.ones(order), xdata=x, ydata=y)[0]  # bounds=([0, 50, 0, 0], [1e5, 5e3, 2, 1e5])
    except RuntimeError:
        # print("Fit problem! Ignoring...")
        values = [1, 1, 1, 1]
    return poly(x, *values), values


def poly(x, *args):
    y = 0
    for i, arg in enumerate(args):
        y = y + (arg * (x ** i))
    return y

# def lorentzian(x, gamma, x0, c, a)
# values = curve_fit(f=lorentzian, xdata=x, ydata=y, bounds=([0, 50, 0, 0], [1e5, 5e3, 2, 1e5]))[0]


