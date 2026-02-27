from faster_whisper import WhisperModel
import threading

def thread_func():
    print("Iniciando hilo...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("Modelo cargado")

print("Main thread")
t = threading.Thread(target=thread_func)
t.start()
t.join()
print("Terminado")
