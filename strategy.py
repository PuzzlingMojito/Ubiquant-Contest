from data_handler import DataHandler
import numpy as np
import matplotlib.pyplot as plt

fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class Strategy:
    def __init__(self, data_handler, calibrate_window=20):
        self.handler = data_handler
        self.calibrate_window = calibrate_window

    def get_price(self, field, window=20):
        return np.array(self.handler[field][-window:])

    def calibrate(self):
        while len(self.handler.sequence) < self.calibrate_window:
            self.handler.get()

    def plot_pnl(self):
        plt.plot(self.handler.capital)
        plt.show()
