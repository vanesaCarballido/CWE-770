"""
DEMO - CWE-770: Allocation of Resources Without Limits or Throttling

Problemas presentes:
  1. No hay límite de tamaño para el body / archivo subido (MAX_CONTENT_LENGTH).
  2. No hay límite de cantidad de requests por cliente (sin rate limiting).
  3. Cada archivo subido se guarda completo en memoria/disco sin control.
  4. No hay timeout de procesamiento.
  
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# VULNERABLE: no MAX_CONTENT_LENGTH
# app.config['MAX_CONTENT_LENGTH'] = None  (comportamiento por defecto = sin límite)

request_count = {"total": 0}


@app.route("/health")
def health():
    return jsonify(status="ok", total_requests=request_count["total"])


@app.route("/receive", methods=["POST"])
def receive():
    request_count["total"] += 1
    data = request.get_data()
    return jsonify(received_bytes=len(data)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
