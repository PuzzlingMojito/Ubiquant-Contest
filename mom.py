import numpy as np
from scipy.stats import linregress
from data_handler import DataHandler
from execution import Executor
from math import isclose
import logging
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


def intersection(a, b):
    return list(set(a).intersection(set(b)))


class Momentum:
    def __init__(self, data_handler, ext):
        self.handler = data_handler
        self.executor = ext
        self.mom = []

    def calculate_mom(self, window):
        if len(self.handler.sequence) > window:
            price = self.handler.get('close', window)
            ret = np.diff(price, axis=0) / price[:-1, :]
            self.mom.append(np.sum(ret, axis=0) - 50 * np.var(ret, axis=0))

    def get_stocks_dict(self, window=40):
        positions = self.handler.get('positions', window=window)
        today = np.sign(positions[-1])
        holding = np.sum(np.abs(np.sign(positions)), axis=0)
        valid_stocks = np.argwhere(np.logical_or(today == 0.0, holding >= window)).reshape(-1).tolist()
        rank = list(np.argsort(self.mom[-1]))
        short = intersection(rank[:int(len(rank) / 20)], valid_stocks)
        long = intersection(rank[-int(len(rank) / 20):], valid_stocks)
        close = intersection(rank[int(len(rank) / 20): -int(len(rank) / 20)], valid_stocks)
        logging.info('      l:{:d}, s:{:d}, c:{:d}, v:{:d}'
                     .format(len(long), len(short), len(close), len(valid_stocks)))
        return {'long': long, 'close': close, 'short': short}

    def run(self, window):
        while True:
            self.handler.get_next()
            self.executor.update(price=self.handler.get('close')[0],
                                 volume=self.handler.get('volume')[0],
                                 capital=self.handler.get('capital')[0],
                                 position=self.handler.get('positions')[0])
            if len(self.handler.sequence) > window:
                self.calculate_mom(window)
            if len(self.mom) > 0:
                stocks_dict = self.get_stocks_dict()
                self.executor.add_order(stocks_dict)
                self.executor.calculate_target()
                if not self.executor.check():
                    self.handler.order(self.executor.target_position)


if __name__ == '__main__':
    handler = DataHandler()
    executor = Executor()
    mom = Momentum(handler, executor)
    mom.run(60)

