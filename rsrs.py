import numpy as np
from scipy.stats import linregress
from data_handler import DataHandler
from execution import Executor
from math import isclose
import logging
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


class RsRs:
    def __init__(self, data_handler, ext):
        self.handler = data_handler
        self.executor = executor
        self.betas = []
        self.r_2 = []
        self.z_scores = []
        self.rs = []

    def calculate_beta_r2(self, window):
        # calculate one day's beta and r_2
        high = self.handler.get_price('high', window)
        low = self.handler.get_price('low', window)
        beta = []
        r_2 = []
        for i in range(high.shape[1]):
            slope, intercept, r_value, p_value, std_err = linregress(low[:, i], high[:, i])
            beta.append(slope)
            r_2.append(r_value**2)
        self.betas.append(beta)
        self.r_2.append(r_2)

    def calculate_rs(self, window):
        betas, r_2 = np.array(self.betas[-window:]), np.array(self.r_2[-1])
        z_score = (betas[-1] - betas.mean(axis=0)) / betas.std(axis=0)
        self.rs.append(z_score * r_2 * betas[-1])

    def get_stock_dict(self):
        rank = np.argsort(-self.rs[-1])
        # max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        # rank = rank[max_trading_volume[rank] > np.percentile(max_trading_volume, 20)]
        stock_dict = {'long': rank[:int(len(rank) / 10)],
                      'close': rank[int(len(rank) / 10): -int(len(rank) / 10)],
                      'short': rank[-int(len(rank) / 10):]}
        return stock_dict

    def run(self, window_1, window_2):
        for i in range(window_1):
            self.handler.get_next()
        for i in range(window_2):
            self.handler.get_next()
            self.calculate_beta_r2(window_1)
        for i in range(400):
            self.handler.get_next()
            self.calculate_beta_r2(window_1)
            self.calculate_rs(window_2)
            if i % 100 == 10:
                self.executor.add_order(self.get_stock_dict())
            self.executor.trade()


if __name__ == '__main__':
    handler = DataHandler()
    executor = Executor(handler)
    strategy = RsRs(handler, executor)
    strategy.run(5, 5)

