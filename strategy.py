import matplotlib.pyplot as plt
import numpy as np
fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class Strategy:
    def __init__(self, data_handler):
        self.handler = data_handler
        self.max_single_stock = 10e4

    def create_position(self, factor_values, ):
        rank = np.array(sorted(range(len(factor_values)), key=factor_values.__getitem__))
        max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        rank = rank[volume[rank] > 0]
        long, short = rank[:int(len(rank) / 10)], rank[-int(len(rank) / 10):]
        close = self.handler.get_price('close', 1)[0]
        max_long_volume, max_short_volume = max_trading_volume[long], max_trading_volume[short]

        ratio = sum(close[long] * max_long_volume) / sum(close[short] * max_short_volume)
        long_volume, short_volume = max_long_volume * 0.001

    def plot_pnl(self):
        plt.plot(self.handler.capital)
        plt.show()
