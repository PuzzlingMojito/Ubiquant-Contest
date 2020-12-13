import numpy as np
from scipy.stats import linregress
from data_handler import DataHandler
import logging


class RsRs:
    def __init__(self, data_handler):
        self.handler = data_handler
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
        self.rs.append(z_score * r_2)

    def create_position(self, factor_values):
        rank_stocks = np.array(sorted(range(len(factor_values)), key=factor_values.__getitem__))
        max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        # logging.info('max_volume:{}, min_volume:{}'.format(max(max_trading_volume),
        #                                                    min(max_trading_volume[max_trading_volume > 0])))
        # volume_limit = np.sort(max_trading_volume)[int(len(max_trading_volume) / 10)]
        rank_stocks = rank_stocks[max_trading_volume[rank_stocks] > 0]
        long = rank_stocks[:int(len(rank_stocks) / 10)]
        short = rank_stocks[-int(len(rank_stocks) / 10):]
        select_stocks = np.append(long, short)
        # logging.info('10%:{}, 25%:{}, 50%:{}, 75%{}'.format(np.percentile(vol, 10), np.percentile(vol, 25),
        #                                                     np.percentile(vol, 50), np.percentile(vol, 75)))
        close = self.handler.get_price('close', 1)[0]

        # max_single_stock_value = min(close[select_stocks] * max_trading_volume[select_stocks])
        position = np.zeros(len(factor_values))
        amount_long = sum(max_trading_volume[long] * close[long])
        amount_short = sum(max_trading_volume[short] * close[short])
        if amount_long > amount_short:
            position[long] = max_trading_volume[long] / (amount_long / amount_short)
            position[short] = max_trading_volume[short]
        else:
            position[short] = max_trading_volume[short] / (amount_short / amount_long)
            position[long] = max_trading_volume[long]
        return position

    def run(self, window_1, window_2):
        for i in range(window_1):
            self.handler.get_next()
        for i in range(window_2):
            self.handler.get_next()
            self.calculate_beta_r2(10)
        for i in range(100):
            self.handler.get_next()
            self.calculate_beta_r2(10)
            self.calculate_rs(10)
            self.handler.order(self.create_position(self.rs[-1]))


if __name__ == '__main__':
    handler = DataHandler()
    strategy = RsRs(handler)
    strategy.run(10, 10)

