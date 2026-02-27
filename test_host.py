import sys
import os
import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), 'host_engine'))
import orange_pb2
import orange_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = orange_pb2_grpc.OrangeInferenceStub(channel)
    request = orange_pb2.InferenceRequest(prompt="Naranja, reporta tu sistema.", max_tokens=10, temperature=0.7)
    try:
        response = stub.RunDeduction(request)
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    run()
