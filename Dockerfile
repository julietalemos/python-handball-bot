# Usamos Python 3.13 (tu versión)
FROM python:3.13-slim

WORKDIR /app

# Instalamos las librerías de Python primero
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# INSTALACIÓN MÁGICA: 
# Instalamos playwright y le pedimos que instale el browser Y sus dependencias de sistema
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

CMD ["python", "main.py"]