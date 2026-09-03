"""
DEMO - CWE-770: Versión MITIGADA
================================================================================
Controles de asignación de recursos:
  1. MAX_CONTENT_LENGTH: limita el tamaño máximo de cada request/archivo.
  2. Rate limiting (flask-limiter): limita requests por cliente (IP).
  3. Respuestas 413 / 429 / 503 claras.
"""

import threading
import time
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# --- MITIGACIÓN 1: Límite máximo de tamaño de request (2 MB) ---
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

# --- MITIGACIÓN 2: Rate limiting por IP ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    storage_uri="memory://",
)

request_count = {"total": 0}

# --- MANEJADORES DE ERROR ---
@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify(error="payload too large, max 2MB"), 413

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify(error="rate limit exceeded, slow down"), 429

# --- RUTAS ---
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