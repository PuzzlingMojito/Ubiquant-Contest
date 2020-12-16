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
        self.executor = ext
        self.betas = []
        self.r_2 = []
        self.z_scores = []
        self.rs = []

    def calculate_beta_r2(self, window):
        # calculate one day's beta and r_2
        if len(self.handler.sequence) < window:
            return
        high = self.handler.get('high', window)
        low = self.handler.get('low', window)
        beta = []
        r_2 = []
        for i in range(high.shape[1]):
            slope, intercept, r_value, p_value, std_err = linregress(low[:, i], high[:, i])
            beta.append(slope)
            r_2.append(r_value**2)
        self.betas.append(beta)
        self.r_2.append(r_2)

    def calculate_rs(self, window):
        if len(self.betas) < window and len(self.r_2) < window:
            return
        betas, r_2 = np.array(self.betas[-window:]), np.array(self.r_2[-1])
        z_score = (betas[-1] - betas.mean(axis=0)) / betas.std(axis=0)
        self.rs.append(z_score * r_2 * betas[-1])

    # def calculate_ma(self, window=20):
    #     price = self.handler.get('close', window + 3)
    #     ma_0 = np.mean(price[-20:])
    #     ma_3 = np.mean(price[-23:-3])
    #     return ma_0 > ma_3, ma_0 < ma_3

    def get_stocks_dict(self):
        if len(self.rs) == 0:
            return {'long': [], 'short': [], 'close': []}
        # ma_long_signal, ma_short_signal = self.calculate_ma()
        # rs_long_signal = self.rs[-1] > 0.7
        # rs_short_signal = self.rs[-1] < -0.7
        # close = np.argwhere(np.logical_or(rs_long_signal, rs_short_signal))
        # long = np.argwhere(np.logical_and(ma_long_signal, rs_long_signal))
        # short = np.argwhere(np.logical_and(ma_short_signal, rs_short_signal))
        long = np.argwhere(self.rs[-1] > 0.7).reshape(-1).tolist()
        short = np.argwhere(self.rs[-1] < -0.7).reshape(-1).tolist()
        close = []
        logging.info('len_l:{:d}, len_s:{:d}'.format(len(long), len(short)))
        stock_dict = {'long': long,
                      'close': close,
                      'short': short}
        return stock_dict

    def run(self, window_1, window_2):
        while True:
            self.handler.get_next()
            self.executor.update(price=self.handler.get('close')[0],
                                 volume=self.handler.get('volume')[0],
                                 capital=self.handler.get('capital')[0],
                                 position=self.handler.get('positions')[0])
            self.calculate_beta_r2(window_1)
            self.calculate_rs(window_2)
            self.executor.add(self.get_stocks_dict())
            if not self.executor.check():
                self.handler.order(self.executor.target_position)


if __name__ == '__main__':
    handler = DataHandler()
    executor = Executor(max_pct=0.5)
    strategy = RsRs(handler, executor)
    strategy.run(300, 16)

