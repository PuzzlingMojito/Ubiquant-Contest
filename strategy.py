import matplotlib.pyplot as plt
import numpy as np
fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class Strategy:
    def __init__(self, data_handler):
        self.handler = data_handler
        self.max_single_stock = 10e4

    def create_position(self, factor_values):
        rank_stocks = np.array(sorted(range(len(factor_values)), key=factor_values.__getitem__))
        max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        rank_stocks = rank_stocks[max_trading_volume[rank_stocks] > 0]
        long, short = rank_stocks[:int(len(rank_stocks) / 10)], rank_stocks[-int(len(rank_stocks) / 10):]
        close = self.handler.get_price('close', 1)[0]
        select_stocks = np.append(long, short)
        max_single_stock_value = min(close[select_stocks] * max_trading_volume[select_stocks])
        position = np.zeros(len(factor_values))
        position[long] = 0.1 * max_single_stock_value / close[long]
        position[short] = 0.1 * -max_single_stock_value / close[short]
        return position

    def plot_pnl(self):
        plt.plot(self.handler.capital)
        plt.show()
