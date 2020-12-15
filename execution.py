from data_handler import DataHandler
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


class Position:
    def __init__(self, array):
        self.position = array

    def long(self, stocks, position):
        # position is unsigned
        op = np.vectorize(change_position)
        self.position[stocks] = op(self.position[stocks], position)

    def short(self, stocks, position):
        # position is unsigned
        op = np.vectorize(change_position)
        self.position[stocks] = op(self.position[stocks], -position)

    def close(self, stocks, max_trading_volume):
        # position is unsigned
        op = np.vectorize(close_position)
        self.position[stocks] = op(self.position[stocks], max_trading_volume)

    def check(self, stocks_dict, price, amount):
        return np.all(self.position[stocks_dict['long']] > 0) and \
               np.all(self.position[stocks_dict['short']] < 0) and \
               np.all(self.position[stocks_dict['close']] == 0) and \
               np.abs(self.position) * price >= amount

    def adjust(self, price):
        long_stocks = np.where(self.position > 0)
        short_stocks = np.where(self.position < 0)
        position = abs(self.position)
        amount = position * price
        while True:
            if np.max(amount) > 0.1 * np.sum(amount) and not isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1):
                # logging.info('single:{}'.format(np.max(amount) - 0.1 * np.sum(amount)))
                amount[amount > 0.1 * np.sum(amount)] = 0.1 * np.sum(amount)
                position = amount / price
            amount_long = np.sum(amount[long_stocks])
            amount_short = np.sum(amount[short_stocks])
            if not isclose(amount_long, amount_short, abs_tol=1):
                # logging.info('exposure:{}'.format(abs(amount_long - amount_short) / (amount_long + amount_short)))
                if amount_long > amount_short:
                    position[long_stocks] *= (amount_short / amount_long)
                else:
                    position[short_stocks] *= (amount_long / amount_short)
                amount = position * price
            if (np.max(amount) < 0.1 * np.sum(amount) or isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1)) and \
                    isclose(np.sum(amount[long_stocks]), np.sum(amount[short_stocks]), abs_tol=1):
                break
        self.position[long_stocks] = position[long_stocks]
        self.position[short_stocks] = -position[short_stocks]


class Executor:
    def __init__(self, data_handler):
        self.handler = data_handler
        self.max_ratio = 0.5
        self.order_list = []

    def add_order(self, stocks_dict):
        self.order_list.append(stocks_dict)

    def trade(self):
        capital = self.handler.get_asset_info('capital', 1)[0]
        price = self.handler.get_price('close', 1)[0]
        position = Position(self.handler.position[-1])
        if len(self.order_list) > 0:
            if position.check(stocks_dict=self.order_list[-1], price=price, amount=self.max_ratio * capital):
                self.order_list.pop(-1)
            else:
                max_trading_volume = self.handler.get_volume(1)[0]
                position.long(self.order_list[-1]['long'], max_trading_volume[self.order_list[-1]['long']])
                position.short(self.order_list[-1]['short'], max_trading_volume[self.order_list[-1]['short']])
                position.close(self.order_list[-1]['close'], max_trading_volume[self.order_list[-1]['close']])
                position.adjust(price=price)
                self.handler.order(position.position)
