"""
DEMO EDUCATIVA - CWE-770: Allocation of Resources Without Limits or Throttling
================================================================================
Este servidor es INTENCIONALMENTE VULNERABLE. Solo para uso en entorno
aislado (Docker local), con fines de aprendizaje sobre seguridad defensiva.

Problemas presentes a propósito:
  1. No hay límite de tamaño para el body / archivo subido (MAX_CONTENT_LENGTH).
  2. No hay límite de cantidad de requests por cliente (sin rate limiting).
  3. Cada archivo subido se guarda completo en memoria/disco sin control.
  4. No hay timeout de procesamiento.
"""

from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

UPLOAD_DIR = "/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- VULNERABLE: no MAX_CONTENT_LENGTH definido ---
# app.config['MAX_CONTENT_LENGTH'] = None  (comportamiento por defecto = sin límite)

request_count = {"total": 0}


@app.route("/health")
def health():
    return jsonify(status="ok", total_requests=request_count["total"])


@app.route("/upload", methods=["POST"])
def upload():
    """
    Endpoint vulnerable: acepta archivos de cualquier tamaño,
    sin límite de requests concurrentes ni por IP.
    """
    request_count["total"] += 1

    f = request.files.get("file")
    if not f:
        return jsonify(error="no file provided"), 400

    filename = f"upload_{request_count['total']}_{int(time.time()*1000)}.bin"
    path = os.path.join(UPLOAD_DIR, filename)

    # Guarda el archivo completo sin chequear tamaño antes ni durante
    f.save(path)
    size = os.path.getsize(path)

    return jsonify(saved_as=filename, size_bytes=size), 200


@app.route("/echo", methods=["POST"])
def echo():
    """
    Endpoint que además carga el body entero en memoria como texto,
    sin límite -> puede usarse para agotar RAM con requests grandes y repetidas.

    La pequeña espera (time.sleep) simula procesamiento real (ej. parseo,
    validación, encolado) y es lo que hace que los picos de memoria de
    requests concurrentes se solapen en vez de liberarse al instante.
    En un servidor real, cualquier procesamiento no instantáneo produce
    este mismo efecto sin necesidad de forzarlo.
    """
    request_count["total"] += 1
    data = request.get_data()  # sin límite de tamaño
    time.sleep(3)  # retiene el buffer en memoria mientras "procesa"
    return jsonify(received_bytes=len(data)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
