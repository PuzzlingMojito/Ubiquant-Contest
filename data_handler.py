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
    filename='mom.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d-%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

question = '47.103.23.116:56701'
contest = '47.103.23.116:56702'
passwd = 'eROzSpSO'
ticker_fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}
asset_fields = ['positions', 'capital']


class DataHandler:
    def __init__(self):
        self.sequence = []
        self.init_capital = None
        self.session_key = None
        self.data = {field: [] for field in list(ticker_fields.keys()) + asset_fields}
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
                self.sequence.append(response.sequence)
                response = MessageToDict(response, including_default_value_fields=True)
                data = np.array([i['values'][2:] for i in response['dailystk']])
                for key, value in ticker_fields.items():
                    self.data[key].append(data[:, value].tolist())
                if not response['positions']:
                    self.data['positions'].append(np.zeros(data.shape[0]))
                else:
                    self.data['positions'].append(np.array(response['positions']))
                self.data['capital'].append(response['capital'])
                amount = self.get('close', 1)[0] * self.data['positions'][-1]
                long = np.sum(amount[np.where(amount > 0)]) / response['capital']
                short = -np.sum(amount[np.where(amount < 0)]) / response['capital']
                logging.info('seq:{:d}, long:{:.2%}, short:{:.2%}, return:{:.2%}'
                             .format(self.sequence[-1], long, short, (response['capital'] / self.init_capital) - 1))
                break

    def order(self, position):
        conn = grpc.insecure_channel(contest)
        client = contest_pb2_grpc.ContestStub(channel=conn)
        response = client.submit_answer(contest_pb2.AnswerRequest(user_id=9,
                                                                  user_pin=passwd,
                                                                  session_key=self.session_key,
                                                                  sequence=self.sequence[-1],
                                                                  positions=position))
        if response.accepted:
            logging.info('seq:{:d}, order accepted'.format(self.sequence[-1]))
        else:
            logging.info('seq:{:d}, order failed, {}'.format(self.sequence[-1], response.reason))

    def get(self, field, window=1):
        # if window == 1 then please use handler.get()[0] to get the element
        # or you will get a list which contains that element.
        if field in ticker_fields:
            return np.array(self.data[field][-window:])
        else:
            return self.data[field][-window:]


if __name__ == '__main__':
    handler = DataHandler()



