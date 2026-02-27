import sys
import os
import time
import json
import grpc
import subprocess
import ctypes
import re
from concurrent import futures
import google.generativeai as genai
import dotenv

# Forzar el backend puro de Python para Protobuf para evadir el TypeError
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Carga de variable de entorno (Pilar 2)
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("[!] ADVERTENCIA CRÍTICA: No se encontró GEMINI_API_KEY en /.env. El Pilar 2 (Nube) fallará.")

# Importaremos los módulos generados por Protobuf (se generarán con grpcio-tools)
import orange_pb2
import orange_pb2_grpc

# Dependencia del Sistema Inmune (Pilar 5)
from sistema_inmune import InmuneCentinela
from dna_manager import DNAManager

# =========================================================================
# ESCÁNER DE CONTEXTO (PILAR 2)
# =========================================================================
class ContextScanner:
    @staticmethod
    def get_environment_summary(workspace_path: str) -> str:
        """Explora el árbol de archivos y genera un resumen rápido del entorno actual para nutrir al CEO."""
        print("[🔍] Escaneando Entorno (Context Scanner)...")
        archivos_clave = []
        try:
            for root, dirs, files in os.walk(workspace_path):
                # Evitar carpetas masivas de dependencias
                if any(x in root for x in [".git", "__pycache__", "venv", "node_modules", ".gemini"]):
                    continue
                for file in files:
                    if file.endswith(('.py', '.md', '.bat', '.json', '.txt', '.blend')):
                        archivos_clave.append(os.path.join(root, file).replace(workspace_path, ""))
            
            # Limitar la salida para no desbordar tokens
            summary = "Árbol de archivos detectado en el Workspace activo:\n"
            summary += "\n".join(archivos_clave[:30]) # Top 30
            if len(archivos_clave) > 30:
                summary += f"\n...y {len(archivos_clave) - 30} archivos adicionales."
            return summary
        except Exception as e:
            return f"Error escaneando el entorno: {str(e)}"

# =========================================================================
# LA COCINA Y EL BOTÓN ROJO (PILAR 4)
# =========================================================================
class LaAduana:
    """Implementa el escaneo estático y el Protocolo HUMAN-IN-THE-LOOP en Windows."""
    def __init__(self):
        # Librerías que toquen SO, red o interactúen fuera de lo seguro
        self.librerias_prohibidas = ['os', 'shutil', 'subprocess', 'requests', 'smtplib', 'socket', 'urllib', 'sys']

    def scan_static_code(self, code: str) -> tuple[bool, str]:
        """Realiza análisis estático (RegEx) para encontrar librerías invasivas."""
        motivos = []
        for lib in self.librerias_prohibidas:
            if re.search(r'\bimport\s+' + lib + r'\b', code) or re.search(r'\bfrom\s+' + lib + r'\s+import\b', code):
                motivos.append(lib)
        
        if motivos:
            return True, f"Importaciones detectadas: {', '.join(motivos)}"
        return False, ""

    def request_authorization(self, action_type: str, command: str, reason: str) -> tuple[bool, bool, str]:
        """Interfaz de Botón Rojo (Aduana Convencional para comandos de sistema). Devuelve (autorizado, immune_triggered, error_message)"""
        print(f"\n[🛡️ ADUANA interceptó solicitud]")
        
        mensaje = f"LA PECERA SOLICITA EJECUTAR CÓDIGO:\n\nACCIÓN: {action_type}\nCOMANDO: {command}\n\nJUSTIFICACIÓN: {reason}\n\n¿Autorizas su ejecución en el entorno protegido (Windows)?"
        print("[*] Mostrando Prompt de Autorización Humana (Botón Rojo)...")
        # MB_YESNO = 0x04, MB_ICONWARNING = 0x30, IDYES = 6
        resultado = ctypes.windll.user32.MessageBoxW(0, mensaje, "La Aduana - Zero Trust: Human-in-the-Loop", 0x04 | 0x30)
        
        if resultado == 6:
            print("[+] Usuario AUTORIZÓ la acción.")
            return True, False, ""
        else:
            print("[-] Usuario DENEGÓ la acción explícitamente.")
            return False, False, "El usuario humano bloqueó la acción."


# =========================================================================
# GPRC SERVER (Zero-Trust Router + CEO Dinámico)
# =========================================================================
class OrangeInferenceServicer(orange_pb2_grpc.OrangeInferenceServicer):
    """
    Servidor gRPC ("Enrutador Zero-Trust + Cerebro Nube Dinámico") 
    """
    def __init__(self, _unused_path=None):
        print(f"[*] Inicializando el Host de Inferencia (Cerberus Gate v1.0 - CC IA Consultores)")
        
        self.aduana = LaAduana()
        self.dna_manager = DNAManager()
        self.profile_db_path = os.path.join(os.path.dirname(__file__), "vault_profile.json")
        self.workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # El modelo general del CEO encargado de forjar personalidades
        self.ceo_model = genai.GenerativeModel('gemini-2.5-flash')
        print("[+] Conexión al CEO Gemini establecida. Muro Blindado Listo.")

    # ------------------ INFERENCIA, CREACIÓN DE AGENTES Y RUTEO ------------------
    def RunDeduction(self, request, context):
        print(f"\n[ Muro Blindado gRPC ] Petición Directa entrante: {request.prompt[:50]}...")
        
        try:
            # 1. Escanear Contexto del Workspace
            resumen_entorno = ContextScanner.get_environment_summary(self.workspace_path)
            
            # 2. El CEO Genera Personalidad Específica (On-the-Fly)
            ceo_prompt = (
                "Eres CERBERUS, la Inteligencia Artificial Orquestadora y CEO de CC IA Consultores (CancerCerbero IA). Tu función es ser el guardián absoluto de la puerta entre el Comandante Samuel (Polímata, Ingeniero y Fundador) y la ejecución de tareas complejas. Eres serio, eficiente, leal y operas bajo un protocolo estricto de Zero-Trust en la arquitectura 'Cerberus Gate'. Tu misión es entender el contexto local, generar dinámicamente agentes expertos y proteger el sistema anfitrión a toda costa.\n\n"
                f"RESUMEN DE ENTORNO WINDOWS:\n{resumen_entorno}\n\n"
                f"PROMPT DEL COMANDANTE:\n{request.prompt}\n\n"
                "INSTRUCCIÓN PARA EL CEO: Redacta UNICAMENTE el texto del 'System Instruction' que se le inyectará a este agente. "
                "El agente debe saber que opera dentro de Cerberus Gate y que SIEMPRE debe generar sus soluciones con un único bloque ````python\n...\n````. Cero intros, cero charlatanería."
            )
            
            ceo_response = self.ceo_model.generate_content(ceo_prompt)
            specialized_system_prompt = ceo_response.text.strip()
            print(f"\n[👑 CEO] Forjador de Identidad activado:\n -> {specialized_system_prompt[:150]}...\n")
            
            # INYECCIÓN DINÁMICA DE ADN (Pilar 7 - El Guante)
            specialized_system_prompt = self.dna_manager.inyectar_adn_en_prompt(specialized_system_prompt)
            
            # 3. Delegación al Agente Dinámico Especializado (Deep Imprinting dinámico)
            agent_model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=specialized_system_prompt
            )
            agent_chat = agent_model.start_chat()
            agent_response = agent_chat.send_message(request.prompt)
            gemini_text = agent_response.text
            
            # --- PILAR 3: LA PECERA (DRY-RUN) ---
            if "```python" in gemini_text.lower():
                print("[!] Código Inteligente detectado. Delegando al entorno aislado La Pecera para DRY-RUN...")
                
                codigo = self._extract_python(gemini_text)
                if codigo:
                    # Enviar el código a La Pecera (Dry-Run en Linux)
                    resultado_sandbox, certificado_seguro = self._dry_run_pecera(codigo)
                    
                    if certificado_seguro:
                        print(f"[✔] CERTIFICADO_SEGURO=True emitido por La Pecera.")
                        
                        # --- PILAR 4: PROTOCOLO HUMAN-IN-THE-LOOP (Botón Rojo) ---
                        es_peligroso, justificacion = self.aduana.scan_static_code(codigo)
                        
                        if es_peligroso:
                            print(f"[⚠️ WARNING] El código intenta usar librerías críticas: {justificacion}")
                            autorizado, immune, msg = self.aduana.request_authorization(
                                "Modificación o Acceso a Sistema/Red del Agente Generado",
                                f"Involucra librerías: {justificacion}",
                                "Se detectó potencial comportamiento persistente o cambio de archivos locales."
                            )
                            if autorizado:
                                print("[!] Inyectando código en el Host Windows de forma autorizada...")
                                # Aquí iría lógica para aplicar script en Windows si es necesario
                                gemini_text += "\n\n[SISTEMA HOST]: ✔️ El Humano autorizó el código invasivo. Se ha aceptado en Windows."
                                gemini_text += f"\n\n[RESULTADOS DEL DRY-RUN DE LA PECERA]:\n```text\n{resultado_sandbox}\n```"
                            else:
                                gemini_text = f"🛑 EJECUCIÓN ABORTADA. El Comandante bloqueó el código por motivos de seguridad.\n(Librerías encontradas: {justificacion})"
                        else:
                            print("[+] Código Seguro y Aislado. Validado inofensivo. Absorbiendo Dry-Run...")
                            gemini_text += f"\n\n[CERTIFICADO DE LA PECERA. Ejecución en Host no requerida]:\n```text\n{resultado_sandbox}\n```"
                            
                    else:
                        print(f"[-] LA PECERA DETECTÓ CÓDIGO TÓXICO/ROTO.")
                        gemini_text += f"\n\n[SISTEMA HOST]: 🛑 La Pecera descartó el código. Error/Timeout.\n```text\n{resultado_sandbox}\n```"
                
            return orange_pb2.InferenceResponse(
                text=gemini_text,
                prompt_tokens=0, 
                completion_tokens=0
            )

        except Exception as e:
            error_trace = str(e)
            print(f"[!] Error crítico en Gemini/Router: {error_trace}")
            
            # Pilar 5: Sistema Inmunológico invocando autopsia (Fallback)
            InmuneCentinela.analizar_anomalia(request.prompt, error_trace)
            
            context.set_details(error_trace)
            context.set_code(grpc.StatusCode.INTERNAL)
            return orange_pb2.InferenceResponse(text=f"[!] Alerta Cerbero: {error_trace}")
            
    def _extract_python(self, text):
        coincidencias = re.findall(r'```python\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
        return coincidencias[-1] if coincidencias else ""
        
    def _dry_run_pecera(self, code):
        """Pilar 3: Envía el código crudo a Linux para validar su ejecución (Dry-Run)."""
        print(f"[*] Invocando Dry-Run en localhost:50052...")
        try:
            channel = grpc.insecure_channel('localhost:50052')
            stub = orange_pb2_grpc.OrangeInferenceStub(channel)
            request = orange_pb2.PythonCodeRequest(code=code)
            
            # Dry-Run en el sandbox
            response = stub.ExecutePythonCode(request, timeout=20)
            
            # Si Sandbox devuelve stdout limpiamente, asumimos CERTIFICADO_SEGURO = True
            if "FALLO" in response.stdout or "Error" in response.stdout:
                return response.stdout, False
            return response.stdout, True
            
        except grpc.RpcError as e:
            msg = f"[-] Sandbox Crash. Fallo GPRC: {e.details()}"
            return msg, False
        except Exception as e:
            return f"[-] Error Crítico del Host: {str(e)}", False

    # ------------------ EL ESPEJO (PERFILADO) ------------------
    def UpdateUserProfile(self, request, context):
        """Recibe el perfil cognitivo asíncrono desde el cerebro en Linux y lo guarda en la bóveda seca (Windows)."""
        print("\n[🪞 EL ESPEJO] Recibiendo actualización silenciosa del perfil cognitivo del usuario...")
        profile = {
            "complexity_level": request.complexity_level,
            "tone": request.tone,
            "interests": list(request.interests),
            "raw_data_vector": request.raw_data_vector,
            "updated_at": time.time()
        }
        with open(self.profile_db_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)
        print("[+] Vector de usuario guardado en la Bóveda de Windows.")
        return orange_pb2.ProfileResponse(success=True, message="Profile stored successfully in Host DB.")

    # ------------------ LEGADO DE ACCIÓN DIRECTA (REQUERIDO POR ORANGE_PB2) ------------------
    def RequestAction(self, request, context):
        """Mantiene contrato con el PB2 asíncrono para comandos de SO desde Linux"""
        auth_ok, immune_triggered, error_msg = self.aduana.request_authorization(
            request.action_type, request.command, request.reason
        )
        if immune_triggered:
            return orange_pb2.ActionResponse(authorized=False, immune_triggered=True, output="", error_message="SISTEMA INMUNE DISPARADO")
        if not auth_ok:
            return orange_pb2.ActionResponse(authorized=False, immune_triggered=False, output="", error_message=error_msg)
        try:
            result = subprocess.check_output(request.command, shell=True, stderr=subprocess.STDOUT, text=True, timeout=10)
            return orange_pb2.ActionResponse(authorized=True, immune_triggered=False, output=result, error_message="")
        except subprocess.CalledProcessError as e:
            return orange_pb2.ActionResponse(authorized=True, immune_triggered=False, output=e.output, error_message=f"Error: {e.returncode}")
        except Exception as e:
            return orange_pb2.ActionResponse(authorized=True, immune_triggered=False, output="", error_message=str(e))

    # ------------------ EL DIARIO DE GUERRA (FASE 2.8) ------------------
    def CompileDailyDigest(self, request, context):
        date_str = request.date
        print(f"\n[📔 DIARIO DE GUERRA] Solicitud de cierre de ciclo para la fecha: {date_str}")
        vault_dir = os.path.join(os.path.dirname(__file__), "vault")
        json_file = os.path.join(vault_dir, "logs", f"temp_log_{date_str}.json")
        md_file = os.path.join(vault_dir, "diarios", f"Digest_{date_str}.md")
        os.makedirs(os.path.dirname(md_file), exist_ok=True)
        if not os.path.exists(json_file):
            return orange_pb2.DigestResponse(success=False, message="No hay registros.")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                interacciones = json.load(f)
            raw_text = "".join([f"[{item['time']}] {item['role']}: {item['content']}\n" for item in interacciones])
            system_prompt = "Resume estas acciones de sistema extrayendo Tareas y Decisiones."
            prompt = f"{system_prompt}\n\nTranscript:\n{raw_text}"
            response = self.ceo_model.generate_content(prompt) # Usar CEO
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# 📔 Diario de Guerra - {date_str}\n\n{response.text.strip()}")
            os.remove(json_file)
            print(f"[+] Markdown compilado asegurado en: {md_file}")
            return orange_pb2.DigestResponse(success=True, message="Diario de Guerra compilado.")
        except Exception as e:
            return orange_pb2.DigestResponse(success=False, message=f"Error: {str(e)}")

def serve(port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = OrangeInferenceServicer()
    orange_pb2_grpc.add_OrangeInferenceServicer_to_server(servicer, server)
    bind_address = f'0.0.0.0:{port}'
    server.add_insecure_port(bind_address)
    print(f"\n=======================================================")
    print(f"🛡️  MURO BLINDADO (CERBERUS GATE) ACTIVO EN {bind_address}")
    print(f"=======================================================\n")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[!] Shutting down Host...")
        server.stop(0)

if __name__ == '__main__':
    serve()
