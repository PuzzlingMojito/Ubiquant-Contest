import grpc
import time
import logging
import pickle
import os
import numpy as np
from rpc_package import contest_pb2, question_pb2_grpc, contest_pb2_grpc, question_pb2
from google.protobuf.json_format import MessageToDict
logging.basicConfig(level=logging.INFO)

question = '47.103.23.116:56701'
contest = '47.103.23.116:56702'
passwd = 'eROzSpSO'
fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}
filename = '/handler.pkl'


class DataHandler:
    def __init__(self):
        self.sequence = [-1]
        self.position = []
        self.capital = []
        self.total_asset = []
        self.tickers = {field: [] for field in fields.keys()}
        conn = grpc.insecure_channel(contest)
        client = contest_pb2_grpc.ContestStub(channel=conn)
        response = client.login(contest_pb2.LoginRequest(user_id=9, user_pin=passwd))
        self.session_key = response.session_key
        self.capital.append(response.init_capital)
        self.total_asset.append(response.init_capital)
        if response.success:
            logging.info('login success')
        else:
            logging.info('login failed, ' + response.reason)

    def get_next(self):
        # TODO: has_next_question
        while True:
            sequence = self.sequence[-1] + 1
            conn = grpc.insecure_channel(question)
            client = question_pb2_grpc.QuestionStub(channel=conn)
            response = client.get_question(question_pb2.QuestionRequest(user_id=9, sequence=sequence))
            if response.sequence == -1:
                time.sleep(0.1)
            else:
                self.update(response)
                logging.info('sequence:%d, total_asset_pct:%.2f%%', self.sequence[-1],
                             (self.total_asset[-1] - self.total_asset[0]) / self.total_asset[0])
                break

    def update(self, response):
        self.sequence.append(response.sequence)
        self.capital.append(response.capital)
        response = MessageToDict(response, including_default_value_fields=True)
        data = np.array([i['values'][2:] for i in response['dailystk']])
        for key, value in fields.items():
            self.tickers[key].append(data[:, value].tolist())
        if not response['positions']:
            self.position.append(np.zeros(data.shape[0]))
        else:
            self.position.append(np.array(response['positions']))
        self.total_asset.append(self.get_total_asset())

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

    def get_total_asset(self):
        stock_value = sum(np.array(self.position[-1]) * self.tickers['close'][-1])
        cash_value = self.capital[-1]
        return stock_value + cash_value


if __name__ == '__main__':
    handler = DataHandler()
    handler.get_next()



