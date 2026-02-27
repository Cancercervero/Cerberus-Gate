import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'host_engine'))
from llama_cpp import Llama

def test_inference():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "host_engine", "model", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
    system_prompt = "Eres La Naranja Mecánica."
    try:
        llm = Llama(model_path=model_path, n_ctx=4096, verbose=True)
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\nNaranja, reporta tu sistema.\n<|im_end|>\n<|im_start|>assistant\n"
        output = llm(prompt, max_tokens=1024, temperature=0.7, echo=False)
        print("Success:", output['choices'][0]['text'])
    except Exception as e:
        print("CRITICAL ERROR:", e)

if __name__ == '__main__':
    test_inference()
