import json
import os
import threading
try:
    import google.generativeai as genai
except ImportError:
    pass

class DNAManager:
    """
    Protocolo de Adaptación Sensorial (El Guante).
    Maneja la Memoria Persistente de Cerberus (User DNA).
    """
    def __init__(self):
        # El ADN se guarda en la pecera, pero es persistente al no ser purgado
        self.dna_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "brain_core", "user_dna.json")
        self.lock = threading.Lock()
        
        # Opcional: Para resumir/extraer lecciones de conversaciones largas
        self.gemini_analyzer = None
        try:
            self.gemini_analyzer = genai.GenerativeModel('gemini-2.5-flash')
        except:
            pass

    def _asegurar_adn(self):
        if not os.path.exists(self.dna_path):
            with open(self.dna_path, 'w', encoding='utf-8') as f:
                json.dump({"lecciones_aprendidas": []}, f)

    def leer_adn_completo(self) -> dict:
        """Retorna el diccionario estructurado del ADN."""
        with self.lock:
            self._asegurar_adn()
            with open(self.dna_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {"lecciones_aprendidas": []}

    def inyectar_adn_en_prompt(self, base_system_prompt: str) -> str:
        """
        El CEO llama a esta función para compilar el System Prompt de cualquier nuevo agente,
        asegurando que nazca sabiendo cómo operamos.
        """
        dna = self.leer_adn_completo()
        
        perfil = dna.get("perfil_empresa", {})
        prefs = dna.get("preferencias_comandante", {})
        lecciones = dna.get("lecciones_aprendidas", [])
        
        contexto_adn = "\n\n--- [PROTOCOLO EL GUANTE: MEMORIA ADN DEL COMANDANTE] ---\n"
        if perfil:
            contexto_adn += f"Empresa: {perfil.get('nombre', 'CC IA Consultores')}. "
            contexto_adn += f"Proyectos Insignia: {', '.join(perfil.get('proyectos_insignia', []))}.\n"
        
        if prefs:
            contexto_adn += "Preferencias Base:\n"
            for k, v in prefs.items():
                contexto_adn += f"- {k.upper()}: {' '.join(v) if isinstance(v, list) else v}\n"
                
        if lecciones:
            contexto_adn += "Directrices Históricas Estrictas (Lecciones Aprendidas):\n"
            for lec in lecciones[-10:]: # Inyectar máximo las últimas 10 lecciones más frescas
                contexto_adn += f"- {lec}\n"
                
        contexto_adn += "------------------------------------------------------\n\n"
        
        return base_system_prompt + contexto_adn

    def actualizar_adn(self, contexto_feedback: str, es_critico: bool = False):
        """
        Extrae la esencia operativa de un feedback/corrección del comandante 
        y la graba en el JSON de ADN local permanentemente.
        """
        def _hilo_procesamiento():
            if not self.gemini_analyzer:
                print("[-] Inyector de ADN: Falla por falta de Gema AI.")
                return

            try:
                # Instruimos a Gemini que extraiga la regla desnuda
                prompt = (
                    "Eres el Analista de Memoria ADN del Ecosistema Cerberus.\n"
                    "El Comandante acaba de dar una instrucción correctiva o un feedback sobre nuestro trabajo.\n"
                    "Tu trabajo es destilar esto en UNA SOLA FRASE directa de 'Directriz Operativa', sin explicaciones extras.\n"
                    f"Feedback del Comandante: '{contexto_feedback}'"
                )
                
                res = self.gemini_analyzer.generate_content(prompt)
                leccion_destilada = res.text.strip().replace("\"", "").replace("- ", "")
                
                with self.lock:
                    dna = self.leer_adn_completo()
                    if "lecciones_aprendidas" not in dna:
                        dna["lecciones_aprendidas"] = []
                        
                    # Prevenir duplicados groseros
                    if leccion_destilada not in dna["lecciones_aprendidas"]:
                        dna["lecciones_aprendidas"].append(leccion_destilada)
                        
                        with open(self.dna_path, 'w', encoding='utf-8') as f:
                            json.dump(dna, f, indent=2, ensure_ascii=False)
                            
                print(f"\n[🧬 ADAPTACIÓN SENSORIAL (EL GUANTE)] Nueva Lección inyectada en el ADN: '{leccion_destilada}'")
                
            except Exception as e:
                print(f"[-] Falla al actualizar el ADN: {e}")

        # Lo ejecutamos en background para no bloquear el flujo del Orbe
        threading.Thread(target=_hilo_procesamiento, daemon=True).start()

if __name__ == "__main__":
    manager = DNAManager()
    # Mock Test
    print("[*] Simulando feedback del Comandante...")
    manager.actualizar_adn("No uses variables con una sola letra, ponles nombres descriptivos carajo.")
    
    # Simular lectura del prompt inyectado
    import time
    time.sleep(3) # Esperar a que el hilo termine
    test_prompt = manager.inyectar_adn_en_prompt("Eres un agente programador en Python.")
    print("\n--------- TEST DE PROMPT FINAL ---------")
    print(test_prompt)
