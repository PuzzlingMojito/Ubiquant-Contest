import numpy as np
from math import isclose
import logging


def change_position(old, target, volume):
    if np.sign(old) == np.sign(target):
        change = abs(target - old)
        if change > volume:
            return np.sign(old) * (abs(old) + volume)
    else:
        change = abs(target) + abs(old)
        if change > volume:
            if abs(old) > 0:
                return np.sign(old) * (abs(old) - volume)
            else:
                return np.sign(target) * volume
    return target


class Executor:
    def __init__(self, max_pct=0.8):
        self.price = None
        self.volume = None
        self.capital = None
        self.order = {'long': [], 'short': [], 'close': []}
        self.max_pct = max_pct
        self.position = np.array([])
        self.target_position = np.array([])

    def add_order(self, order):
        self.order = order

    def calculate_target(self):
        direction = np.sign(self.position)
        direction[self.order['long']] = 1.0
        direction[self.order['short']] = -1.0
        direction[self.order['close']] = 0.0
        long = np.argwhere(direction > 0).reshape(-1).tolist()
        short = np.argwhere(direction < 0).reshape(-1).tolist()
        target = np.zeros(len(self.position))
        if len(long) != 0 and len(short) != 0:
            target[long] = ((self.max_pct * 0.5 * self.capital) / len(long)) / self.price[long]
            target[short] = (-(self.max_pct * 0.5 * self.capital) / len(short)) / self.price[short]
        # if len(long) != 0:
        #     target[long] = ((self.max_pct * 0.5 * self.capital) / len(long)) / self.price[long]
        op = np.vectorize(change_position)
        self.target_position = op(self.position, target, self.volume)
        self.adjust()

    def check(self):
        if len(self.target_position) == 0:
            return True
        else:
            return np.all(np.isclose(self.position, self.target_position, rtol=0.1))

    def adjust(self):
        # logging.info('      adjust...')
        long_stocks = np.where(self.target_position > 0)
        short_stocks = np.where(self.target_position < 0)
        position = abs(self.target_position)
        amount = position * self.price
        while True:
            if np.max(amount) > 0.1 * np.sum(amount) and not isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1):
                # logging.info('single:{}'.format(np.max(amount) - 0.1 * np.sum(amount)))
                amount[amount > 0.1 * np.sum(amount)] = 0.1 * np.sum(amount)
                position = amount / self.price
            amount_long = np.sum(amount[long_stocks])
            amount_short = np.sum(amount[short_stocks])
            if not isclose(amount_long, amount_short, abs_tol=1):
                # logging.info('exposure:{}'.format(abs(amount_long - amount_short) / (amount_long + amount_short)))
                if amount_long > amount_short:
                    position[long_stocks] *= (amount_short / amount_long)
                else:
                    position[short_stocks] *= (amount_long / amount_short)
                amount = position * self.price
            if (np.max(amount) < 0.1 * np.sum(amount) or isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1)) and \
                    isclose(np.sum(amount[long_stocks]), np.sum(amount[short_stocks]), abs_tol=1):
                break
            # if np.max(amount) < 0.1 * np.sum(amount) or isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1):
            #     break
        # logging.info('      adjust finished!')
        self.target_position[long_stocks] = position[long_stocks]
        self.target_position[short_stocks] = -position[short_stocks]

    def update(self, price, volume, capital, position):
        self.price = price
        self.volume = volume
        self.capital = capital
        self.position = position

