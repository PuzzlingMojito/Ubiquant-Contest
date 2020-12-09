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
        self.session_key = None
        self.tickers = {field: [] for field in fields.keys()}
        self.question_conn = grpc.insecure_channel(question)
        self.contest_conn = grpc.insecure_channel(contest)

    def login(self):
        client = contest_pb2_grpc.ContestStub(channel=self.contest_conn)
        response = client.login(contest_pb2.LoginRequest(user_id=9, user_pin=passwd))
        self.session_key = response.session_key

    def get(self):
        # TODO: has_next_question
        client = question_pb2_grpc.QuestionStub(channel=self.question_conn)
        while True:
            sequence = self.sequence[-1] + 1
            response = client.get_question(question_pb2.QuestionRequest(user_id=9, sequence=sequence))
            if response.sequence == -1:
                time.sleep(0.1)
            else:
                response = MessageToDict(response)
                self.sequence.append(response['sequence'])
                self.capital.append(response['capital'])
                data = np.array([i['values'][2:] for i in response['dailystk']])
                for key, value in fields.items():
                    self.tickers[key].append(data[:, value].tolist())
                break

    def order(self, position):
        response = self.contest_client.submit_answer(contest_pb2.AnswerRequest(user_id=9,
                                                                  user_pin=passwd,
                                                                  session_key=self.session_key,
                                                                  sequence=70,
                                                                  positions=position))
        print(response)


if __name__ == '__main__':
    handler = DataHandler()
    handler.login()
    handler.get()



