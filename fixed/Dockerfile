FROM python:3.12-slim

# Instalar Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY fixed/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fixed/app.py .
COPY fixed/nginx.conf /etc/nginx/nginx.conf

EXPOSE 5001

# Script de inicio que levanta la app Python en puerto interno 5000 y Nginx expuesto en puerto 5001
CMD nginx && gunicorn -w 2 --threads 5 -b 127.0.0.1:5000 app:app