# Usamos una imagen ligera de Python 3.11
FROM python:3.11-slim

# Evitar que los archivos pyc se escriban a disco y desactivar el buffer de logs de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Creamos un usuario non-root para mejorar The Frontier
RUN useradd -m pecera_user

# Directorio de trabajo
WORKDIR /app

# Copiamos primero los requerimientos (optimizando la caché de Docker)
# Copiamos directamente de la máquina Windows a La Pecera.
COPY brain_core/requirements.txt /app/

# Instalamos gRPC y otras dependencias básicas
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de brain_core (grpc_client, tools, y el orange_pb2 generado)
COPY brain_core/ /app/

# Opcional (Dependiendo de si el host debe inyectar el proto):
# En un escenario real compilaríamos el proto aquí o usaríamos el pb2 precompilado
# COPY ../proto/orange.proto /app/

# Cambiamos al usuario sin privilegios
USER pecera_user

# Al iniciar el contenedor, mantendremos vivo el cliente o ejecutaremos un script principal
CMD ["python", "grpc_client.py"]
