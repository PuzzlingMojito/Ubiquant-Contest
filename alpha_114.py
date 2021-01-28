import numpy as np
from scipy.stats import linregress
from scipy.stats import spearmanr
from offline_data_handler import OfflineDataHandler
from data_handler import DataHandler
from execution import Executor
from math import isclose
import logging
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.basicConfig(
    filename='offline_alpha_104.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d-%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def intersection(a, b):
    return list(set(a).intersection(set(b)))


class Alpha104:
    def __init__(self, data_handler, ext):
        self.handler = data_handler
        self.executor = ext
        self.alpha = []

    def calculate_alpha(self, window):
        high = self.handler.get('close', window)
        low = self.handler.get('high', window)
        volume = self.handler.get('volume', window)
        ts_max = np.zeros((8, high.shape[1]))
        for i in range(8):
            ts_max[i, :] = np.maximum(low[i, :], low[i+1, :])
        std_volume = np.zeros((8, high.shape[1]))
        for i in range(8):
            std_volume[i, :] = np.std(volume[i:i+10, :], axis=0)
        rank_high = np.zeros((11, high.shape[1]))
        rank_low = np.zeros((11, high.shape[1]))
        for i in range(11):
            rank_high[i, :] = np.argsort(high[i, :])
            rank_low[i, :] = np.argsort(low[i, :])
        rank_sub = rank_high - rank_low
        cov = np.zeros((8, high.shape[1]))
        for i in range(8):
            for j in range(high.shape[1]):
                cov[i, j] = spearmanr(rank_sub[i:i+3, j], ts_max[i:i+3, j])[0]
        alpha = np.std(cov - std_volume, axis=0)
        self.alpha.append(alpha)

    def get_stocks_dict(self, holding_window):
        positions = self.handler.get('positions', window=holding_window)
        today = np.sign(positions[-1])
        holding = np.sum(np.abs(np.sign(positions)), axis=0)
        valid_stocks = np.argwhere(np.logical_or(today == 0.0, holding >= holding_window)).reshape(-1).tolist()
        rank = list(np.argsort(-self.alpha[-1]))
        long = intersection(rank[:int(len(rank) / 10)], valid_stocks)
        short = intersection(rank[-int(len(rank) / 10):], valid_stocks)
        close = intersection(rank[int(len(rank) / 10): -int(len(rank) / 10)], valid_stocks)
        logging.info('      l:{:d}, s:{:d}, c:{:d}, v:{:d}'
                     .format(len(long), len(short), len(close), len(valid_stocks)))
        return {'long': long, 'close': close, 'short': short}

    def run(self, window, holding_window):
        while True:
            self.handler.get_next()
            self.executor.update(price=self.handler.get('close')[0],
                                 volume=self.handler.get('volume')[0],
                                 capital=self.handler.get('capital')[0],
                                 position=self.handler.get('positions')[0])
            if len(self.handler.sequence) > window:
                self.calculate_alpha(window)
            if len(self.alpha) > 0:
                stocks_dict = self.get_stocks_dict(holding_window)
                self.executor.add_order(stocks_dict)
                self.executor.calculate_target()
                if not self.executor.check():
                    self.handler.order(self.executor.target_position)


if __name__ == '__main__':
    handler = OfflineDataHandler()
    executor = Executor()
    alpha = Alpha104(handler, executor)
    try:
        alpha.run(20, 5)
    except ValueError:
        import matplotlib.pyplot as plt
        plt.plot(handler.capitals)
        plt.show()

