import matplotlib.pyplot as plt
import numpy as np
fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class Strategy:
    def __init__(self, data_handler):
        self.handler = data_handler

    def create_position(self, factor_values):
        length = len(factor_values)
        rank = np.array(sorted(range(len(factor_values)), key=factor_values.__getitem__))
        max_volume = self.handler.get_volume(1)[0]
        rank = rank[max_volume[rank] > 0]
        position = max_volume * 0.05
        position[rank[:int(length / 10)]] *= 0.001
        position[rank[-int(length / 10):]] *= -0.001
        return position

    def plot_pnl(self):
        plt.plot(self.handler.capital)
        plt.show()
