import numpy as np
from scipy.stats import linregress
from data_handler import DataHandler
from strategy import Strategy


class RsRs(Strategy):
    def get_rs(self):
        high = self.get_price('high', 60)
        low = self.get_price('low', 60)
        beta, intercept, r_value, p_value, std_err = linregress(low, high)
        return beta

    def run(self):
        self.calibrate()
        try:
            while True:
                self.handler.get()
                beta = self.get_rs()
                print(beta)
        except KeyboardInterrupt:
            print('finish')


if __name__ == '__main__':
    handler = DataHandler()
    strategy = RsRs(handler, 60)
    strategy.run()

