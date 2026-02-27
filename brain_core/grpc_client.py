import grpc
import sys
import os
import re
import socket
from concurrent import futures

# En Docker (La Pecera), los archivos pb2 estarán en la misma carpeta
import orange_pb2
import orange_pb2_grpc
from sandbox_tools import execute_python_code
import time

class BrainCoreClient:
    """
    Cliente gRPC usado SOLAMENTE por el HUD en Windows.
    Se conecta al proxy de La Pecera mapeado en localhost:50052.
    """
    def __init__(self, host="localhost", port=50052):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = orange_pb2_grpc.OrangeInferenceStub(self.channel)

    def think(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        print(f"[ 🧠 Cliente ] Solicitando cálculo a La Pecera...")
        request = orange_pb2.InferenceRequest(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        try:
            response = self.stub.RunDeduction(request)
            return response.text
        except grpc.RpcError as e:
            msg = f"\n[!] ERROR: La Pecera no responde en el puerto 50052.\nDetalle: {e.details()}"
            print(msg)
            return msg

class BrainCoreServicer(orange_pb2_grpc.OrangeInferenceServicer):
    """
    Servidor gRPC dentro de Docker (La Pecera).
    Filtra los requests del HUD, ejecuta lógica agéntica (Sandbox) y retransmite al Host.
    """
    def __init__(self, host="host.docker.internal", port=50051):
        try:
            # Forzar resolución IPv4 para evadir el agujero negro de IPv6 (WSL2)
            ipv4_host = socket.gethostbyname(host)
            target = f"{ipv4_host}:{port}"
            print(f"[*] DNS forzado: {host} -> {ipv4_host} (IPv4)")
        except Exception as e:
            target = f"{host}:{port}"
            print(f"[!] Fallo al resolver {host}: {e}")
            
        self.channel = grpc.insecure_channel(target)
        self.gpu_stub = orange_pb2_grpc.OrangeInferenceStub(self.channel)
        print(f"[*] Brain Proxy conectado al Host GPU en {target}")

    def RunDeduction(self, request, context):
        print(f"\n[ 🧠 Cerebro Táctico ] Interceptado prompt del HUD. Solicitando modelo Qwen a la GPU en Host...")
        
        gpu_request = orange_pb2.InferenceRequest(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        try:
            response = self.gpu_stub.RunDeduction(gpu_request)
            text = response.text
            
            # 🕵️ LÓGICA AGÉNTICA (El Sandbox en Acción)
            # Buscamos si el LLM decidió escribir bloques de código Python
            code_blocks = re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)
            if code_blocks:
                print(f"[!] {len(code_blocks)} Bloque(s) de Código Python detectado(s). Ejecutando en La Pecera de Linux...")
                execution_results = ""
                for code in code_blocks:
                    res = execute_python_code(code)
                    execution_results += f"\n\n```text\n[Resultado de Ejecución en Sandbox (Linux)]:\n{res}\n```"
                
                # Adjuntamos el subproducto de la ejecución al final de lo que lee el usuario
                text += execution_results

            return orange_pb2.InferenceResponse(
                text=text,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens
            )
            
        except grpc.RpcError as e:
            msg = f"[!] ERROR FATAL intentando alcanzar Windows desde Docker: {e.details()}"
            print(msg)
            return orange_pb2.InferenceResponse(text=msg)

    # Proxy para el resto de endpoints
    def CompileDailyDigest(self, request, context):
        print("[*] Proxying Digest Request to Host.")
        return self.gpu_stub.CompileDailyDigest(request)
            
    def RequestAction(self, request, context):
        return self.gpu_stub.RequestAction(request)
            
    def UpdateUserProfile(self, request, context):
        return self.gpu_stub.UpdateUserProfile(request)

    # ------------------ PILAR 4: LA PECERA EXECUTOR ------------------
    def ExecutePythonCode(self, request, context):
        print("\n[ 🔒 LA PECERA ] ==============================================")
        print(f"[*] Recibiendo carga destructiva/analítica desde Windows Router:")
        print(f"[{time.strftime('%H:%M:%S')}] Ejecutando bloque de {len(request.code.splitlines())} líneas en Sandbox Asilado...")
        
        # Le delegamos la plomería de stdout a sandbox_tools
        resultado_plano = execute_python_code(request.code)
        
        print("\n[✔] Ejecución Aislada Completada. Devolviendo StdOut al Host.")
        print("===============================================================\n")
        return orange_pb2.PythonCodeResponse(stdout=resultado_plano)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orange_pb2_grpc.add_OrangeInferenceServicer_to_server(BrainCoreServicer(), server)
    server.add_insecure_port('0.0.0.0:50051')
    print("=======================================================")
    print("[+] Cerebro Táctico (La Pecera) en línea y Asilado.")
    print("[+] Escuchando peticiones del HUD en 0.0.0.0:50051 (interno de Docker)")
    print("=======================================================")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
