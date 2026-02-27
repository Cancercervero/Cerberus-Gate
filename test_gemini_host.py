import sys
import os

# Forzar backend puro de python para Protobuf antes de cargar nada
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Append the directory containing host_engine to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'host_engine'))

import grpc
import orange_pb2
import orange_pb2_grpc

def run():
    print("Testing Host Engine (Gemini API)...")
    channel = grpc.insecure_channel('localhost:50051')
    stub = orange_pb2_grpc.OrangeInferenceStub(channel)
    request = orange_pb2.InferenceRequest(prompt="Comandante Samuel autoriza: Dame un script de python simple para imprimir hola mundo.", max_tokens=200, temperature=0.7)
    try:
        response = stub.RunDeduction(request)
        print("\nResponse from Server:\n", response.text)
    except Exception as e:
        print("\nError:", e)

if __name__ == '__main__':
    run()
