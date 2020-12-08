import grpc
import time
import numpy as np
from rpc_package import contest_pb2, question_pb2_grpc, contest_pb2_grpc, question_pb2
from google.protobuf.json_format import MessageToDict

question = '47.103.23.116:56701'
contest = '47.103.23.116:56702'
passwd = 'eROzSpSO'
session_key = '8DGM2R'
fields = {'open': 0, 'high': 1, 'low': 2, 'close': 3, 'volume': 4}


class DataHandler:
    def __init__(self):
        self.sequence = [-1]
        self.capital = []
        self.tickers = {field: [] for field in fields.keys()}
        self.has_next_question = True
        self.question_client = question_pb2_grpc.QuestionStub(channel=grpc.insecure_channel(contest))
        self.contest_client = contest_pb2_grpc.ContestStub(channel=grpc.insecure_channel(question))

    def login(self):
        response = self.contest_client.login(contest_pb2.LoginRequest(user_id=9, user_pin=passwd))
        print(response)

    def get(self):
        # TODO: has_next_question
        while True:
            sequence = self.sequence[-1] + 1
            response = self.question_client.get_question(question_pb2.QuestionRequest(user_id=9, sequence=sequence))
            if response.sequence == -1:
                time.sleep(0.1)
            else:
                dict_obj = MessageToDict(response)
                self.sequence.append(dict_obj['sequence'])
                self.capital.append(dict_obj['capital'])
                data = np.array([info['values'][2:] for info in dict_obj['dailystk']])
                for key, value in fields.items():
                    self.tickers[key].append(data[:, ].tolist())
                break

    def order(self, position):
        response = self.contest_client.submit_answer(contest_pb2.AnswerRequest(user_id=9,
                                                                  user_pin=passwd,
                                                                  session_key=session_key,
                                                                  sequence=70,
                                                                  positions=position))
        print(response)


if __name__ == '__main__':
    handler = DataHandler()
    while True:
        handler.get()



