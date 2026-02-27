import sys
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication
from faster_whisper import WhisperModel

class TestThread(QThread):
    def run(self):
        print("Iniciando Hilo PyQt6...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Modelo cargado")

app = QApplication(sys.argv)
t = TestThread()
t.start()
t.wait()
print("Terminado")
