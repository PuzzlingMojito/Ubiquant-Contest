import numpy as np
from math import isclose
import logging


def change_position(old, delta):
    if np.sign(old) == np.sign(delta):
        return old + delta
    else:
        if abs(old) > abs(delta):
            return np.sign(old) * (abs(old) - abs(delta))
        else:
            return np.sign(delta) * (abs(delta) - abs(old))


def close_position(old, max_trading_volume):
    if abs(old) > max_trading_volume:
        return np.sign(old) * (abs(old) - max_trading_volume)
    else:
        return 0


class Executor:
    def __init__(self, max_pct=0.5):
        self.price = None
        self.volume = None
        self.capital = None
        self.position = None
        self.max_pct = max_pct
        self.target_position = None

    def add(self, stocks_dict):
        self.target_position = np.copy(self.position)
        self.long(stocks_dict['long'], self.volume[stocks_dict['long']])
        self.short(stocks_dict['short'], self.volume[stocks_dict['short']])
        self.close(stocks_dict['close'], self.volume[stocks_dict['short']])
        self.adjust()
        self.direction_change()

    def direction_change(self):
        direction_change = np.sign(self.position) == np.sign(self.position)
        logging.info('change list:{}'.format(np.argwhere(~direction_change).reshape(-1).tolist()))

    def long(self, stocks, position):
        # position is unsigned
        if not stocks:
            return
        op = np.vectorize(change_position)
        self.target_position[stocks] = op(self.position[stocks], position)

    def short(self, stocks, position):
        # position is unsigned
        if not stocks:
            return
        op = np.vectorize(change_position)
        self.target_position[stocks] = op(self.position[stocks], -position)

    def close(self, stocks, max_trading_volume):
        # position is unsigned
        if not stocks:
            return
        op = np.vectorize(close_position)
        self.target_position[stocks] = op(self.position[stocks], max_trading_volume)

    def check(self):
        return np.all(np.isclose(self.position, self.target_position, rtol=0.1))

    def adjust(self):
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
        self.target_position[long_stocks] = position[long_stocks]
        self.target_position[short_stocks] = -position[short_stocks]
        estimate_amount = np.sum(np.abs(self.target_position) * self.price)
        if estimate_amount > self.capital:
            self.target_position *= (self.capital / estimate_amount)

    def update(self, price, volume, capital, position):
        self.price = price
        self.volume = volume
        self.capital = capital
        self.position = position
