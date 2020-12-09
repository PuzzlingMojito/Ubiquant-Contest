from data_handler import DataHandler
import numpy as np
import matplotlib.pyplot as plt

fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class Strategy:
    def __init__(self, data_handler):
        self.handler = data_handler

    def plot_pnl(self):
        plt.plot(self.handler.capital)
        plt.show()
