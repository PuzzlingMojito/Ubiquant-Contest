import grpc
import time
import logging
import pickle
import os
import numpy as np
from math import isclose
from rpc_package import contest_pb2, question_pb2_grpc, contest_pb2_grpc, question_pb2
from google.protobuf.json_format import MessageToDict
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d-%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

question = '47.103.23.116:56701'
contest = '47.103.23.116:56702'
passwd = 'eROzSpSO'
ticker_fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}
asset_fields = ['capital', 'capital_ratio', 'long_ratio', 'short_ratio', 'exposure']


class DataHandler:
    def __init__(self):
        self.sequence = []
        self.position = []
        self.init_capital = None
        self.session_key = None
        self.tickers = {field: [] for field in ticker_fields.keys()}
        self.asset_info = {field: [] for field in asset_fields}
        self.login()

    def login(self):
        conn = grpc.insecure_channel(contest)
        client = contest_pb2_grpc.ContestStub(channel=conn)
        response = client.login(contest_pb2.LoginRequest(user_id=9, user_pin=passwd))
        self.session_key = response.session_key
        self.init_capital = response.init_capital
        if response.success:
            logging.info('login success')
        else:
            logging.info('login failed, ' + response.reason)

    def get_next(self):
        # TODO: has_next_question
        while True:
            if self.sequence:
                sequence = self.sequence[-1] + 1
            else:
                sequence = 0
            conn = grpc.insecure_channel(question)
            client = question_pb2_grpc.QuestionStub(channel=conn)
            response = client.get_question(question_pb2.QuestionRequest(user_id=9, sequence=sequence))
            if response.sequence == -1:
                time.sleep(0.1)
            else:
                self.update(response)
                break

    def update(self, response):
        info = dict()
        self.sequence.append(response.sequence)
        response = MessageToDict(response, including_default_value_fields=True)
        data = np.array([i['values'][2:] for i in response['dailystk']])
        for key, value in ticker_fields.items():
            self.tickers[key].append(data[:, value].tolist())
        if not response['positions']:
            self.position.append(np.zeros(data.shape[0]))
        else:
            self.position.append(np.array(response['positions']))
        info['capital'] = response['capital']
        info['capital_ratio'] = response['capital'] / self.init_capital
        stock_value = np.array(self.position[-1]) * self.tickers['close'][-1]
        long_value, short_abs_value = np.sum(stock_value[stock_value > 0]), abs(np.sum(stock_value[stock_value < 0]))
        info['long_ratio'] = long_value / response['capital']
        info['short_ratio'] = short_abs_value / response['capital']
        diff_occupy = abs(info['long_ratio'] - info['short_ratio'])
        total_occupy = info['long_ratio'] + info['short_ratio']
        if isclose(total_occupy, 0.0):
            info['exposure'] = 0
        else:
            info['exposure'] = diff_occupy / total_occupy
        for field in asset_fields:
            self.asset_info[field].append(info[field])
        logging.info("sequence:{}, capital_ratio:{:%}, long_ratio:{:%}, short_ratio:{:%}, exposure:{:%}"
                     .format(self.sequence[-1], info['capital_ratio'], info['long_ratio'],
                             info['short_ratio'], info['exposure']))

    def order(self, position):
        conn = grpc.insecure_channel(contest)
        client = contest_pb2_grpc.ContestStub(channel=conn)
        response = client.submit_answer(contest_pb2.AnswerRequest(user_id=9,
                                                                  user_pin=passwd,
                                                                  session_key=self.session_key,
                                                                  sequence=self.sequence[-1],
                                                                  positions=position))
        if response.accepted:
            logging.info('order accepted')
        else:
            logging.info('order failed, ' + response.reason)

    def get_price(self, field, window=10):
        return np.array(self.tickers[field][-window:])

    def get_volume(self, window=10):
        return self.get_price('volume', window)

    def get_asset_info(self, field, window=10):
        return self.asset_info[field][-window:]


if __name__ == '__main__':
    handler = DataHandler()
    handler.get_next()



