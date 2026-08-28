FROM python:3.12-slim

WORKDIR /app

# Instalar las librerías de Python
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del dashboard
COPY dashboard/app.py /app/app.py
COPY dashboard/templates /app/templates

# Copiar el script load_test.py a la ruta esperada por app.py
COPY loadtest/load_test.py /app/load_test.py

EXPOSE 8000

CMD ["python", "app.py"]