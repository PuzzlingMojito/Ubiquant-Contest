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
        self.capital = []
        self.position = []
        self.session_key = None
        self.tickers = {field: [] for field in fields.keys()}

    def login(self):
        conn = grpc.insecure_channel(contest)
        client = contest_pb2_grpc.ContestStub(channel=self.conn)
        response = client.login(contest_pb2.LoginRequest(user_id=9, user_pin=passwd))
        self.session_key = response.session_key

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
                self.sequence.append(response.sequence)
                self.capital.append(response.capital)
                response = MessageToDict(response, including_default_value_fields=True)
                self.position.append(response['positions'])
                data = np.array([i['values'][2:] for i in response['dailystk']])
                for key, value in fields.items():
                    self.tickers[key].append(data[:, value].tolist())
                logging.info(self.sequence[-1])
                break

    def order(self, position):
        conn = grpc.insecure_channel(contest)
        client = contest_pb2_grpc.ContestStub(channel=conn)
        response = client.submit_answer(contest_pb2.AnswerRequest(user_id=9,
                                                                  user_pin=passwd,
                                                                  session_key=self.session_key,
                                                                  sequence=70,
                                                                  positions=position))
        print(response)

    def get_price(self, field, window=10):
        return np.array(self.tickers[field][-window:])

    def calibrate(self, calibrate_window):
        while len(self.sequence) < calibrate_window:
            self.get_next()

    # def save(self):
    #     f = open(os.getcwd() + filename, 'wb')
    #     pickle.dump(self, f)


# def create_handler(calibrate_window):
#     if os.path.exists(os.getcwd() + filename):
#         f = open(os.getcwd() + filename, 'rb')
#         handler = pickle.load(f)
#     else:
#         handler = DataHandler(calibrate_window)
#     handler.calibrate()
#     return handler


if __name__ == '__main__':
    print(os.getcwd())



