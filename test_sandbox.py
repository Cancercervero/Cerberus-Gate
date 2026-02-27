import sys
import os

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
sys.path.append(os.path.join(os.path.dirname(__file__), 'host_engine'))

import grpc
import orange_pb2
import orange_pb2_grpc

def test_sandbox():
    print("[*] Testeando delegación Zero-Trust hacia Linux...")
    try:
        # Forzar IPv4 explícito porque 'localhost' resuelve a ::1 y falla en Docker WSL2
        channel = grpc.insecure_channel('127.0.0.1:50052')
        stub = orange_pb2_grpc.OrangeInferenceStub(channel)
        
        test_code = (
            "import os\n"
            "import platform\n"
            "print('Hello from Sandbox!')\n"
            "print('OS:', os.name, platform.system())\n"
        )
        request = orange_pb2.PythonCodeRequest(code=test_code)
        
        response = stub.ExecutePythonCode(request, timeout=5)
        print("\n--- STDOUT de La Pecera ---")
        print(response.stdout)
        print("---------------------------")
        
    except Exception as e:
        print("[-] Fallo de conexión o ejecución:", e)

if __name__ == '__main__':
    test_sandbox()
