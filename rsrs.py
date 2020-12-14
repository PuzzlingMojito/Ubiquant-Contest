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

    def create_position(self, factor_values):
        rank_stocks = np.array(sorted(range(len(factor_values)), key=factor_values.__getitem__))
        max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        rank_stocks = rank_stocks[max_trading_volume[rank_stocks] > 0]
        long = rank_stocks[:int(len(rank_stocks) / 10)]
        short = rank_stocks[-int(len(rank_stocks) / 10):]
        close = self.handler.get_price('close', 1)[0]
        position = np.zeros(close.shape[0])
        position[long] = max_trading_volume[long]
        position[short] = max_trading_volume[short]
        amount = close * position
        while True:
            if np.max(amount) > 0.1 * np.sum(amount) and not isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1):
                logging.info('single:{}'.format(np.max(amount) - 0.1 * np.sum(amount)))
                amount[amount > 0.1 * np.sum(amount)] = 0.1 * np.sum(amount)
                position = amount / close
            amount_long = np.sum(amount[long])
            amount_short = np.sum(amount[short])
            if not isclose(amount_long, amount_short, abs_tol=1):
                logging.info('exposure:{}'.format(abs(amount_long - amount_short) / (amount_long + amount_short)))
                if amount_long > amount_short:
                    position[long] *= (amount_short / amount_long)
                else:
                    position[short] *= (amount_long / amount_short)
                amount = close * position
            if (np.max(amount) < 0.1 * np.sum(amount) or isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1)) \
                    and isclose(np.sum(amount[long]), np.sum(amount[short]), abs_tol=1):
                break
        position[short] *= -1
        return position

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
            self.executor.execute(self.rs[-1])


if __name__ == '__main__':
    handler = DataHandler()
    executor = Executor(handler)
    strategy = RsRs(handler, executor)
    strategy.run(2, 2)

