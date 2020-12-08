import grpc
import question_pb2, question_pb2_grpc
import contest_pb2, contest_pb2_grpc

question = '47.103.23.116:56701'
contest = '47.103.23.116:56702'


def run():
    conn = grpc.insecure_channel(contest)
    client = contest_pb2_grpc.ContestStub(channel=conn)
    response = client.login(contest_pb2.LoginRequest(user_id=9, user_pin='eROzSpSO'))
    print(response)


if __name__ == '__main__':
    run()



