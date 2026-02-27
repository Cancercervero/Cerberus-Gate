import sys
import os
import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), 'brain_core'))
from grpc_client import BrainCoreClient

def test_grpc():
    client = BrainCoreClient(host="localhost", port=50052)
    prompt = "naranja, mis cuchas."
    formatted_prompt = f"<|im_start|>system\nEres la Naranja Mecánica. Responde de forma precisa.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    print("Enviando prompt formateado a Docker en 50052...")
    resp = client.think(formatted_prompt, max_tokens=250)
    print("Respuesta recibida:", resp)

if __name__ == '__main__':
    test_grpc()
