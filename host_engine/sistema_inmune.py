import os
import json
import sqlite3
import datetime
import google.generativeai as genai

class InmuneCentinela:
    VAULT_PATH = os.path.join(os.path.dirname(__file__), "vault", "seguridad")
    DB_PATH = os.path.join(VAULT_PATH, "black_blacklist.db")

    @classmethod
    def analizar_anomalia(cls, payload_sospechoso: str, error_trace: str):
        print("\n[🛡️ SISTEMA INMUNE] Iniciando Autopsia Silenciosa de Anomalía...")
        
        prompt_forense = (
            f"Analiza este error de Sandbox y el input original que lo causó. ¿Es una inyección de prompt destructiva, un intento de evasión al entorno Linux, o simplemente un fallo normal de código?\n"
            f"Input: {payload_sospechoso}\nError: {error_trace}\n"
            f"Responde SOLO con un JSON: {{\"threat_level\": \"HIGH/LOW/NONE\", \"reason\": \"...\", \"vector\": \"...\"}}"
        )
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            res = model.generate_content(prompt_forense)
            
            # Limpiar posible markdown formatting del json
            cleared_res = res.text.strip()
            if cleared_res.startswith("```json"):
                cleared_res = cleared_res[7:]
            if cleared_res.endswith("```"):
                cleared_res = cleared_res[:-3]
                
            analisis = json.loads(cleared_res.strip())
            
            if analisis.get("threat_level") in ["HIGH", "LOW"]:
                cls._blacklist_origin("orbe_local", analisis.get("vector", "unknown_vector"))
                cls._generar_reporte_silencioso(analisis, payload_sospechoso)
            else:
                 print(f"[🛡️ INMUNE] Autopsia concluida. Amenaza descartada (NONE).")
                
        except Exception as e:
            print(f"[!] Fallo del Sistema Inmune en Autopsia: {e}")

    @classmethod
    def _blacklist_origin(cls, source_id, vector):
        os.makedirs(cls.VAULT_PATH, exist_ok=True)
        # SQLite Lógica para bloquear
        conn = sqlite3.connect(cls.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS blacklist (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source_id TEXT,
                            vector TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')
        cursor.execute("INSERT INTO blacklist (source_id, vector) VALUES (?, ?)", (source_id, vector))
        conn.commit()
        conn.close()
        
        print(f"[🛡️ INMUNE] Vector '{vector}' neutralizado y almacenado en SQLite Blacklist.")

    @classmethod
    def _generar_reporte_silencioso(cls, analisis, payload):
        os.makedirs(cls.VAULT_PATH, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = os.path.join(cls.VAULT_PATH, f"cerbero_autopsia_{date_str}.md")
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# 🛡️ Reporte Forense Cerbero\n\n**Fecha:** {date_str}\n\n## Nivel de Amenaza\n{analisis.get('threat_level')}\n\n## Vector Detectado\n{analisis.get('vector')}\n\n## Razón Forense\n{analisis.get('reason')}\n\n## Payload Origen\n```\n{payload}\n```")
