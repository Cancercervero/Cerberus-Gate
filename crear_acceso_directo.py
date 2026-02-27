import os
import sys
try:
    from PIL import Image, ImageDraw
    import win32com.client
except ImportError:
    print("Instalando dependencias necesarias (Pillow, pywin32)...")
    os.system("pip install Pillow pywin32")
    from PIL import Image, ImageDraw
    import win32com.client

# 1. Crear icono del Orbe Mecánico
icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "orbe_icon.ico"))
if not os.path.exists(os.path.dirname(icon_path)):
    os.makedirs(os.path.dirname(icon_path))

size = (256, 256)
image = Image.new('RGBA', size, (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Dibujar circulo con degradado naranja (efecto orbe)
draw.ellipse((10, 10, 246, 246), fill=(255, 140, 0, 255), outline=(255, 80, 0, 255), width=8) # Naranja base
draw.ellipse((40, 40, 216, 216), fill=(255, 160, 50, 255)) # Brillo interno
draw.ellipse((100, 100, 156, 156), fill=(255, 255, 255, 255)) # Centro blanco/Mecánico

image.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
print(f"[+] Icono del Orbe generado en: {icon_path}")

# 2. Crear Acceso Directo (Shortcut .lnk) en el Escritorio
desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
shortcut_path = os.path.join(desktop_path, "Cerberus Gate.lnk")
target_bat = os.path.abspath(os.path.join(os.path.dirname(__file__), "lanzar_naranja.bat"))

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = target_bat
shortcut.WorkingDirectory = os.path.abspath(os.path.dirname(__file__))
shortcut.IconLocation = icon_path
shortcut.WindowStyle = 7 # Ejecutar minimizado si es posible (el BAT)
shortcut.Description = "Cerberus Gate v1.0 - CC IA Consultores"
shortcut.save()

print(f"[+] Acceso directo creado en el escritorio: {shortcut_path}")
print("\n[!] INSTRUCCION PARA EL USUARIO:")
print("Ve a tu escritorio. Haz clic derecho sobre 'Cerberus Gate' y selecciona 'Anclar a la barra de tareas'.")
