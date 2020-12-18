import grpc
import time
import logging
import pickle
import pandas as pd
import os
import numpy as np
from math import isclose
from rpc_package import contest_pb2, question_pb2_grpc, contest_pb2_grpc, question_pb2
from google.protobuf.json_format import MessageToDict

question = '47.103.23.116:56701'
contest = '47.103.23.116:56702'
passwd = 'eROzSpSO'
ticker_fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}
asset_fields = ['positions', 'capital']
fields = ['open', 'high', 'low', 'close', 'volume']


class OfflineDataHandler:
    def __init__(self):
        self.sequence = []
        self.init_capital = None
        self.position = np.zeros(351)
        self.cash = None
        self.capital = None
        self.capitals = []
        self.benchmark = []
        self.benchmark_position = None
        self.data = {field: [] for field in list(ticker_fields.keys()) + asset_fields}
        self.provider = pd.read_csv('./notebooks/CONTEST_DATA_IN_SAMPLE_1.csv', header=None)
        self.provider.columns = ['sequence', 'code', 'open', 'high', 'low', 'close', 'volume']
        self.provider = self.provider.set_index('sequence')
        self.login()

    def login(self):
        # conn = grpc.insecure_channel(contest)
        # client = contest_pb2_grpc.ContestStub(channel=conn)
        # response = client.login(contest_pb2.LoginRequest(user_id=9, user_pin=passwd))
        self.init_capital = 5e8
        self.cash = self.init_capital
        self.capital = self.init_capital
        self.capitals.append(self.init_capital)
        self.benchmark.append(self.init_capital)
        self.benchmark_position = self.init_capital / self.provider[self.provider.index == 0]['close'].values

    def get_next(self):
        # TODO: has_next_question
        if self.sequence:
            sequence = self.sequence[-1] + 1
        else:
            sequence = 0
        self.sequence.append(sequence)
        data = self.provider[self.provider.index == sequence][fields]
        for key, value in ticker_fields.items():
            self.data[key].append(data.values[:, value].tolist())
        self.data['positions'].append(self.position)
        self.data['capital'].append(self.capital)
        amount = self.get('close', 1)[0] * self.data['positions'][-1]
        long = np.sum(amount[np.where(amount > 0)]) / self.capital
        short = -np.sum(amount[np.where(amount < 0)]) / self.capital
        logging.info('seq:{:d}, long:{:.2%}, short:{:.2%}, return:{:.2%}'
                     .format(self.sequence[-1], long, short, (self.capital / self.init_capital) - 1))

    def order(self, position):
        price = self.provider[self.provider.index == self.sequence[-1] + 1]['close'].values
        cash_change = np.sum(self.position * price - position * price)
        fees = np.sum(np.abs(position - self.position) * price) * 0.0002
        self.cash += cash_change
        self.cash -= fees
        self.capital = self.cash + np.sum(position * price)
        self.capitals.append(self.capital)
        self.benchmark.append(np.sum(self.benchmark_position * price))
        self.position = position

    def get(self, field, window=1):
        # if window == 1 then please use handler.get()[0] to get the element
        # or you will get a list which contains that element.
        if field in ticker_fields:
            return np.array(self.data[field][-window:])
        else:
            return self.data[field][-window:]

    def get_information_ratio(self):
        difference = np.array(self.capitals) - np.array(self.benchmark)
        return ((self.capital - self.benchmark[-1]) / self.init_capital) / np.std(difference)


if __name__ == '__main__':
    handler = OfflineDataHandler()




