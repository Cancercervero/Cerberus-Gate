import sys
import os
import requests
import wave
import io
import time
import numpy as np
import threading

# =======================================================
# SISTEMA AUDITIVO / STT LOCAL CON FASTER-WHISPER + VAD
# =======================================================
# CARGAMOS WHISPER ANTES QUE PYQT6 PARA EVITAR COLISIONES DE DLL DE C++ (Exit code 1)
try:
    print("[*] Iniciando Motor de Inferencia Auditivo (Faster-Whisper Tiny)...")
    from faster_whisper import WhisperModel
    import sounddevice as sd
    
    WHISPER_DIR = os.path.join(os.path.dirname(__file__), "whisper_models")
    if not os.path.exists(WHISPER_DIR):
        os.makedirs(WHISPER_DIR)
        
    global_whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8", download_root=WHISPER_DIR)
    print("[+] Tracto Auditivo Inicializado...")
except ImportError:
    global_whisper_model = None
    print("[!] Faltan dependencias de Faster Whisper.")

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QLabel, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QObject, QEvent
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QPainter, QColor, QBrush, QPen, QIcon, QAction

# Añadir path al 'Brain Core' para el cliente gRPC
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'brain_core')))
from grpc_client import BrainCoreClient

# Importe del Protocolo de Adaptación Sensorial
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'host_engine')))
try:
    from dna_manager import DNAManager
except ImportError:
    DNAManager = None

# =======================================================
# PIPER TTS: AUTO-DESCARGA Y TRACTO VOCAL (CPU)
# =======================================================
try:
    from piper import PiperVoice
    import soundfile as sf
    import sounddevice as sd
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    print("[!] Faltan dependencias para Piper TTS (piper-tts, sounddevice, soundfile).")

VOICE_DIR = os.path.join(os.path.dirname(__file__), "voices")
MODEL_FILE = os.path.join(VOICE_DIR, "es_MX-ald-medium.onnx")
CONFIG_FILE = os.path.join(VOICE_DIR, "es_MX-ald-medium.onnx.json")
WHISPER_DIR = os.path.join(os.path.dirname(__file__), "whisper_models")

def download_file(url, dest):
    print(f"[*] Descargando {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"[+] Descarga completada: {dest}")

def check_and_download_voice():
    if not os.path.exists(VOICE_DIR):
        os.makedirs(VOICE_DIR)
    model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx"
    config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx.json"
    if not os.path.exists(MODEL_FILE): download_file(model_url, MODEL_FILE)
    if not os.path.exists(CONFIG_FILE): download_file(config_url, CONFIG_FILE)

class AudioThread(QThread):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        if not PIPER_AVAILABLE: return
        try:
            voice = PiperVoice.load(MODEL_FILE, CONFIG_FILE)
            wav_bytes = io.BytesIO()
            with wave.open(wav_bytes, 'wb') as wav_file:
                voice.synthesize(self.text, wav_file)
            wav_bytes.seek(0)
            data, fs = sf.read(wav_bytes)
            sd.play(data, fs)
            sd.wait()
        except Exception as e:
            print(f"[!] Error crítico en tracto vocal: {e}")

# =======================================================
# SISTEMA AUDITIVO / STT LOCAL CON FASTER-WHISPER + VAD
# =======================================================
class SpeechListenerThread(QObject):
    recording_started = pyqtSignal()   # Se detectó voz y empezamos a grabar
    recording_stopped = pyqtSignal()   # Fin de habla, procesando whisper
    speech_transcribed = pyqtSignal(str) # Resultado del STT
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.thread = threading.Thread(target=self._run_process, daemon=True)
        
    def is_speech_energy(self, audio_chunk, threshold=500):
        # VAD casero basado en Root-Mean-Square (RMS) Energy (Bypass a WebRTCVAD)
        rms = np.sqrt(np.mean(np.square(audio_chunk.astype(np.float32))))
        return rms > threshold

    def _get_float32_array(self, int16_frames):
        # Whisper requiere float32 np.ndarray de 1D
        data = np.concatenate(int16_frames).flatten()
        return data.astype(np.float32) / 32768.0
        
    def start(self):
        self.thread.start()

    def _run_process(self):
        try:
            import sounddevice as sd
            
            if global_whisper_model is None:
                self.error_occurred.emit(f"[!] Tracto auditivo no disponible. Falta Faster Whisper.")
                return

            print("[+] Tracto Auditivo Activo y escuchando.")
            
            RATE = 16000
            CHANNELS = 1
            CHUNK_FRAMES = int(RATE * 0.03) # 30ms
            MAX_SILENCE_CHUNKS = 40 # 1.2 segundos aprox sin habla = corte
            
            with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16') as stream:
                listening = False
                frames = []
                silence_chunks = 0
                
                while self.running:
                    chunk, overflowed = stream.read(CHUNK_FRAMES)
                    is_speech = self.is_speech_energy(chunk, threshold=500)
                    
                    if not listening:
                        # Si no estábamos escuchando y de pronto hay ruido de habla
                        if is_speech:
                            listening = True
                            frames = [chunk]
                            silence_chunks = 0
                            self.recording_started.emit()
                    else:
                        # Si ya estábamos grabando
                        frames.append(chunk)
                        if not is_speech:
                            silence_chunks += 1
                        else:
                            silence_chunks = 0
                        
                        # Si acumulamos mucho silencio, cortamos la grabación y transcribimos
                        if silence_chunks > MAX_SILENCE_CHUNKS:
                            listening = False
                            self.recording_stopped.emit()
                            
                            # Procesar dictado solo si dura más de 1 segundo (evitar ruidos secos aislados)
                            if len(frames) > 33: 
                                audio_fp32 = self._get_float32_array(frames)
                                segments, _ = global_whisper_model.transcribe(audio_fp32, beam_size=5, language="es")
                                text = " ".join([seg.text for seg in segments]).strip()
                                
                                if text:
                                    self.speech_transcribed.emit(text)
                                
                            frames = []
                            silence_chunks = 0

        except Exception as e:
            self.error_occurred.emit(f"[!] Error del sistema auditivo: {str(e)}")
            
    def stop(self):
        self.running = False


# =======================================================
# MÚSCULO TONTO / GPRC THREAD
# =======================================================
class GRPCTaskThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            client = BrainCoreClient(host="localhost", port=50052)
            formatted_prompt = f"<|im_start|>system\nEres CERBERUS. Responde de forma precisa.<|im_end|>\n<|im_start|>user\n{self.prompt}<|im_end|>\n<|im_start|>assistant\n"
            response = client.think(formatted_prompt, max_tokens=250)
            if response:
                self.response_received.emit(response.strip())
            else:
                self.error_occurred.emit("[!] Error: Sin respuesta del Muro")
        except Exception as e:
            self.error_occurred.emit(f"[!] Excepción gRPC: {str(e)}")


# =======================================================
# ESTADO PASIVO (ORBE CENTINELA)
# =======================================================
class OrbeCentinela(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(60, 60)
        
        self.drag_pos = QPoint()
        self.start_pos = QPoint()
        self.is_recording = False
        
        # Parpadeo suave
        self.glow_alpha = 160
        self.glow_increasing = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_glow)
        self.timer.start(50)
        
        # --- PILAR 1: System Tray Integration ---
        self.tray_icon = QSystemTrayIcon(self)
        
        # Generate a dynamic fallback icon if we don't have one on disk yet to prevent crash
        pixmap = QPainter()
        icon_fallback = QIcon()
        
        self.tray_icon.setIcon(icon_fallback) # Needs an actual icon to render in Windows
        
        tray_menu = QMenu()
        show_action = QAction("👁️ Descender Orbe", self)
        show_action.triggered.connect(self.show)
        
        hide_action = QAction("👻 Ocultar (Modo Fantasma)", self)
        hide_action.triggered.connect(self.hide)
        
        quit_action = QAction("🛑 Apagar Sistema Cerbero", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def update_glow(self):
        if self.is_recording:
            if self.glow_increasing:
                self.glow_alpha += 15
                if self.glow_alpha >= 255: self.glow_increasing = False
            else:
                self.glow_alpha -= 15
                if self.glow_alpha <= 100: self.glow_increasing = True
            self.update()

    def set_recording_state(self, state: bool):
        self.is_recording = state
        self.glow_alpha = 160 if not state else 255
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Color dinámico (Rojo si escucha voz, Naranja normal)
        r, g, b = (255, 0, 0) if self.is_recording else (255, 140, 0)
        
        # Halo Translúcido
        brush = QBrush(QColor(r, g, b, self.glow_alpha)) 
        painter.setBrush(brush)
        pen = QPen(QColor(r, max(0, g + 60), b, 255), 2)
        painter.setPen(pen)
        painter.drawEllipse(5, 5, 50, 50)
        
        # Núcleo "Mecánico" Ardiente
        core_r = 255
        core_g = 0 if self.is_recording else 60
        core_b = 0
        painter.setBrush(QBrush(QColor(core_r, core_g, core_b, 255)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(20, 20, 20, 20)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.start_pos = event.globalPosition().toPoint()
            self.main_app.show_hud()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            diff = event.globalPosition().toPoint() - self.start_pos
            if diff.manhattanLength() < 5:
                self.clicked.emit()
            event.accept()


# =======================================================
# ESTADO ACTIVO (HUD EXPANDIDO)
# =======================================================
class HUDExpandido(QWidget):
    switch_to_orbe = pyqtSignal()
    submit_query = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.drag_pos = QPoint()
        self.is_recording = False
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # UI dinámica por propiedades QSS
        self.setStyleSheet("""
            QWidget#MainContainer {
                background-color: rgba(18, 18, 24, 0.95);
                border-radius: 20px;
                border: 1px solid rgba(255, 140, 0, 0.2);
            }
            QWidget#MainContainer[recording="true"] {
                border: 1px solid rgba(255, 50, 50, 0.6);
                background-color: rgba(30, 15, 15, 0.95);
            }
            QTextEdit {
                color: #e0e0e0;
                background-color: transparent;
                border: none;
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 14px;
                padding: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 140, 0, 0.3);
                border-radius: 2px;
            }
            QLineEdit {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 10px;
                padding: 12px 15px;
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 14px;
            }
            QLineEdit:focus { 
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)

        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.container.setProperty("recording", "false")
        
        inner_layout = QVBoxLayout(self.container)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.append("<span style='color:#00ff00;'>[SISTEMA] COREA DEL SUR ONLINE (Modo Activo)</span>")
        self.chat_display.append("<span style='color:#00ff00;'>[SISTEMA] Micrófono Abierto: Háblame al Orbe - El Sistema Auditivo (Faster-Whisper) está activo.</span><br>")
        inner_layout.addWidget(self.chat_display)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Comando manual [Enter] o háblale al Orbe (VAD Automático). [Esc para colapsar]")
        self.input_field.returnPressed.connect(self.manual_send)
        inner_layout.addWidget(self.input_field)

        layout.addWidget(self.container)
        self.setLayout(layout)
        self.resize(800, 500)
        
        self.shortcut_esc = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_esc.activated.connect(self.contract)

    def set_recording_state(self, state: bool):
        self.is_recording = state
        self.container.setProperty("recording", "true" if state else "false")
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        
        if state:
            self.input_field.setPlaceholderText("🔴 * ESCUCHANDO VOZ... * 🔴")
        else:
            self.input_field.setPlaceholderText("Comando manual [Enter] o háblale al Orbe (VAD Automático). [Esc para colapsar]")

    def contract(self):
        self.switch_to_orbe.emit()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.contract()
        super().changeEvent(event)

    def manual_send(self):
        txt = self.input_field.text().strip()
        if txt:
            self.input_field.clear()
            self.submit_query.emit(txt)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()


# =======================================================
# CORE CONTROL DE ESTADOS Y EVENTOS
# =======================================================
class MainApp:
    def __init__(self):
        print("[*] Verificando dependencias fonéticas...")
        check_and_download_voice()

        self.orbe = OrbeCentinela(self)
        self.hud = HUDExpandido()

        # Vinculaciones GUI
        self.orbe.clicked.connect(self.show_hud)
        self.hud.switch_to_orbe.connect(self.show_orbe)
        self.hud.submit_query.connect(self.process_query)

        self.audio_thread = None
        self.grpc_worker = None
        
        # Iniciar Gestor de ADN (Protocolo El Guante)
        self.dna_manager = DNAManager() if DNAManager else None
        
        # Iniciar Tracto Auditivo (Escucha VAD Asíncrona)
        self.listener = SpeechListenerThread()
        self.listener.recording_started.connect(self.on_recording_start)
        self.listener.recording_stopped.connect(self.on_recording_stop)
        self.listener.speech_transcribed.connect(self.on_speech_transcribed)
        self.listener.error_occurred.connect(self.on_system_error)
        self.listener.start()

        # Centrar el Orbe en la pantalla
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.orbe.width()) // 2
        y = (screen.height() - self.orbe.height()) // 2
        self.orbe.move(x, y)

        # Vista por defecto: Mini-Widget (Orbe Flotante)
        self.show_orbe()
        
        self.shortcut_quit_orbe = QShortcut(QKeySequence("Ctrl+Q"), self.orbe)
        self.shortcut_quit_orbe.activated.connect(self.shutdown)
        
    def show_hud(self):
        self.hud.move(self.orbe.pos().x() - 400 + 30, self.orbe.pos().y() - 250 + 30)
        self.hud.show()
        self.orbe.hide()
        self.hud.input_field.setFocus()

    def show_orbe(self):
        self.orbe.move(self.hud.pos().x() + 400 - 30, self.hud.pos().y() + 250 - 30)
        self.orbe.show()
        self.hud.hide()

    # Eventos de Audio y Dictado
    def on_recording_start(self):
        self.orbe.set_recording_state(True)
        self.hud.set_recording_state(True)

    def on_recording_stop(self):
        self.orbe.set_recording_state(False)
        self.hud.set_recording_state(False)

    def on_speech_transcribed(self, text):
        if not text: return
        
        # --- FILTRO WAKE WORD (Palabra de Activación) ---
        wake_words = ["cerberus", "sistema", "orbe", "cerbero", "orv"]
        text_lower = text.lower()
        
        if not any(word in text_lower for word in wake_words):
            # Es ruido de fondo o alguien hablando con otra persona, lo ignoramos.
            print(f"[-] Ruido de fondo ignorado: {text}")
            return
            
        # Insertar texto dictado en la interfaz y procesarlo
        self.hud.chat_display.append(f"<span style='color:#00ffff;'>[Voz]: {text}</span>")
        self.process_query(text, is_voice=True)
        
    def process_query(self, user_text, is_voice=False):
        if not user_text: return
        
        # Trigger Especial: Diario de Guerra
        if user_text.lower() in ["cerberus, compila mi día", "cerbero, compila mi día"]:
            self.hud.chat_display.append("<span style='color:#ff8c00;'>[Orbe]: Compilando Diario de Guerra...</span><br>")
            self._trigger_digest()
            return

        # Trigger Especial: Adaptación Sensorial (El Guante) ADN
        # Palabras clave heurísticas que indican una directriz permanente o regaño
        lower_txt = user_text.lower()
        if any(keyword in lower_txt for keyword in ["regaño", "corrección", "acostúmbrate a", "prefiero que", "siempre usa", "a partir de ahora", "regla estricta", "no antiguo", "no antigravity"]):
            if self.dna_manager:
                self.hud.chat_display.append("<span style='color:#ff00ff;'>[🧬 ADN]: Absorbiendo corrección operativa en la Memoria Persistente...</span><br>")
                self.dna_manager.actualizar_adn(user_text, es_critico=True)

        self.hud.input_field.setEnabled(False)
        
        # Imprimir "[Tú]" si viene de teclado manual
        if not is_voice:
             self.hud.chat_display.append(f"<span style='color:#00ff00;'>[Tú]: {user_text}</span>")
             
        self._log_interaction("user", user_text)
             
        self.hud.chat_display.append("<span style='color:#666666;'><i>[...] Derivando tráfico por gRPC al Muro Blindado...</i></span>")

        # Llamada gRPC a la GPU
        self.grpc_worker = GRPCTaskThread(user_text)
        self.grpc_worker.response_received.connect(self.handle_grpc_response)
        self.grpc_worker.error_occurred.connect(self.on_system_error)
        self.grpc_worker.start()

    def handle_grpc_response(self, response_text):
        cleaned_text = response_text.replace('\n', '<br>')
        self.hud.chat_display.append(f"<span style='color:#ff8c00;'>[CERBERUS]:</span><br><span style='color:#ffaa44;'>{cleaned_text}</span><br>")
        self._log_interaction("assistant", response_text)
        
        self.hud.input_field.setEnabled(True)
        self.hud.input_field.setFocus()
        
        # Auto-Scroll
        scrollbar = self.hud.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Tracto Vocal
        if PIPER_AVAILABLE:
            self.audio_thread = AudioThread(response_text)
            self.audio_thread.start()

    def on_system_error(self, error_msg):
        self.hud.chat_display.append(f"<span style='color:#ff0000;'>{error_msg}</span><br>")
        self.hud.input_field.setEnabled(True)
        self.hud.input_field.setFocus()
        
    # --- RUTINAS DEL DIARIO DE GUERRA ---
    def _log_interaction(self, role, content):
        """Guarda la interacción asíncronamente en el JSON de hoy."""
        date_str = time.strftime("%Y_%m_%d")
        log_dir = os.path.join(os.path.dirname(__file__), "..", "host_engine", "vault", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"temp_log_{date_str}.json")
        
        def append_log():
            import json
            try:
                data = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                data.append({
                    "time": time.strftime("%H:%M:%S"),
                    "role": role,
                    "content": content
                })
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"[!] Error logging a JSON: {e}")
                
        threading.Thread(target=append_log).start()
        
    def _trigger_digest(self):
        """Solicita a Corea del Sur compilar el Markdown del día."""
        date_str = time.strftime("%Y_%m_%d")
        
        def trigger():
            try:
                import orange_pb2
                import orange_pb2_grpc
                import grpc
                
                # Asumimos que el Proxy (La Pecera) está en localhost:50052
                channel = grpc.insecure_channel('localhost:50052')
                stub = orange_pb2_grpc.OrangeInferenceStub(channel)
                res = stub.CompileDailyDigest(orange_pb2.DigestRequest(date=date_str))
                
                # Reportar al HUD (Print local, luego usar signal si se desea pintar en Qt)
                if res.success:
                    print(f"[+] Digest compilado existosamente: {res.message}")
                    # Pequeño hack para pintar en HUD desde otro hilo sería usar señales,
                    # por simplicidad imprimimos en terminal.
                else:
                    print(f"[-] Fallo el Digest: {res.message}")
            except Exception as e:
                print(f"[!] Error gRPC al compilar: {e}")
                
        threading.Thread(target=trigger).start()
        
    def shutdown(self):
        print("[*] Cerrando Sistema Auditivo...")
        if self.listener:
            self.listener.stop()
            self.listener.wait()
        QApplication.instance().quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = MainApp()
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        controller.shutdown()
        print("[!] Saliendo...")
