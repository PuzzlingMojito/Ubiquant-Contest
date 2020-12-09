import numpy as np
import os
from scipy.stats import linregress
from data_handler import DataHandler
from strategy import Strategy


class RsRs(Strategy):
    def __init__(self, data_handler):
        Strategy.__init__(self, data_handler)
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
        for i in range(500):
            slope, intercept, r_value, p_value, std_err = linregress(low[:, i], high[:, i])
            beta.append(slope)
            r_2.append(r_value**2)
        self.betas.append(beta)
        self.r_2.append(r_2)

    def get_beta_r2(self, window):
        return np.array(self.betas[-window:]), np.array(self.r_2[-window:])

    def get_rs(self, window):
        betas, r_2 = self.get_beta_r2(window)
        z_score = (betas[-1] - beta.mean()) / betas.std()
        self.rs.append(z_score * r_2)

    def run(self):
        for i in range(100):
            self.handler.get_next()
            self.calculate_beta_r2(10)
            if i % 10 == 0:
                self.get_rs(10)


if __name__ == '__main__':
    handler = DataHandler()
    handler.calibrate(30)
    strategy = RsRs(handler)
    strategy.run()

