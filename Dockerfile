# Usamos la imagen oficial de Playwright que ya tiene Python y los browsers
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Directorio de trabajo
WORKDIR /app

# Copiamos los archivos de requerimientos primero (para aprovechar el cache)
COPY requirements.txt .

# Instalamos las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del bot
COPY . .

# Comando para arrancar el bot
CMD ["python", "main.py"]