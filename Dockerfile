# Usamos imagen oficial de Python
FROM python:3.13-slim

# Establecemos directorio de trabajo
WORKDIR /app

# Instalamos dependencias del sistema necesarias para OpenCV/YOLO
# NOTA: Cambiamos libgl1-mesa-glx por libgl1
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiamos los archivos del bot
COPY . /app

# Instalamos dependencias de Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el bot
CMD ["python", "bot.py"]