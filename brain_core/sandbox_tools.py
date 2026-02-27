import subprocess
import sys

def execute_python_code(code_string: str, timeout: int = 15) -> str:
    """
    Ejecuta un bloque de código Python usando un subproceso supervisado.
    Como esto está dentro del contenedor (La Pecera), la destrucción o error
    no afecta el sistema operativo Host (Windows).
    """
    try:
        print("[🔧] Sandbox interceptando y ejecutando código Python de la IA...")
        
        # Ejecutamos con python -c y capturamos stdout/stderr
        result = subprocess.run(
            [sys.executable, "-c", code_string],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = ""
        if result.stdout:
            output += f"--- STDOUT ---\n{result.stdout}\n"
        if result.stderr:
            output += f"--- STDERR ---\n{result.stderr}\n"
            
        if result.returncode == 0:
            return f"[+] Ejecución Exitosa:\n{output}" if output else "[+] Código ejecutado sin salida estándar."
        else:
            return f"[-] Error de Ejecución (Exit Code {result.returncode}):\n{output}"
            
    except subprocess.TimeoutExpired:
        return "[-] Error: Se excedió el tiempo límite de ejecución (Timeout 15s). Posible bucle infinito evitado."
    except Exception as e:
        return f"[-] Error Fatal del Sandbox: {str(e)}"
