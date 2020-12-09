import numpy as np
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

    def calculate_rs(self, window):
        betas, r_2 = np.array(self.betas[-window:]), np.array(self.r_2[-1])
        z_score = (betas[-1] - betas.mean(axis=0)) / betas.std(axis=0)
        self.rs.append(z_score * r_2)

    def run(self, window_1, window_2):
        for i in range(window_1):
            self.handler.get_next()
        for i in range(window_2):
            self.handler.get_next()
            self.calculate_beta_r2(10)
        for i in range(100):
            self.handler.get_next()
            self.calculate_beta_r2(10)
            if i % 10 == 0:
                self.calculate_rs(10)
                self.handler.order(self.create_position(self.rs[-1]))


if __name__ == '__main__':
    handler = DataHandler()
    strategy = RsRs(handler)
    strategy.run(10, 10)

