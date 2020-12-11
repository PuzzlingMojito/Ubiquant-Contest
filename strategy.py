import matplotlib.pyplot as plt
import numpy as np

fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class Strategy:
    def __init__(self, data_handler):
        self.handler = data_handler

    def split_order(self, position):


    def create_position(self, factor_values):
        rank_stocks = np.array(sorted(range(len(factor_values)), key=factor_values.__getitem__))
        max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        rank_stocks = rank_stocks[max_trading_volume[rank_stocks] > 0]
        long = rank_stocks[:int(len(rank_stocks) / 10)]
        close = rank_stocks[int(len(rank_stocks) / 10): -int(len(rank_stocks) / 10)]
        short = rank_stocks[-int(len(rank_stocks) / 10)]

        select_stocks = np.append(long, short)
        max_single_stock_value = min(close[select_stocks] * max_trading_volume[select_stocks])
        position = np.zeros(len(factor_values))
        position[long] = 0.5 * max_single_stock_value / close[long]
        position[short] = 0.5 * -max_single_stock_value / close[short]
        old_position = self.handler.position[-1]
        same_direction = np.sign(old_position) == np.sign(position)
        position[same_direction] += old_position[same_direction]
        position[~same_direction] = position[~same_direction]
        return position

    def plot_pnl(self):
        plt.plot(self.handler.capital)
        plt.show()
