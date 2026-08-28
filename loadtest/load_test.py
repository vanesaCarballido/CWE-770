#!/usr/bin/env python3
"""
Script de carga para demostrar CWE-770.

Envía ráfagas de requests concurrentes contra un servidor objetivo
(vulnerable en :5000 o mitigado en :5001) y reporta cuántas fueron
aceptadas y cuántas rechazadas, agrupadas por código de estado HTTP.

USO (desde tu VM de Kali, con docker-compose ya corriendo):

    python3 load_test.py --target http://localhost:5000 --requests 200 --concurrency 50 --payload-mb 5
    python3 load_test.py --target http://localhost:5001 --requests 200 --concurrency 50 --payload-mb 5

Mientras corre esto, en otra terminal ejecuta:

    docker stats cwe770-vulnerable cwe770-fixed

para ver en vivo el consumo de memoria/CPU de cada contenedor.
"""

import argparse
import concurrent.futures
import time
from collections import Counter
import requests


def send_one(url, payload_bytes):
    try:
        r = requests.post(url, data=payload_bytes, timeout=10)
        return r.status_code
    except requests.exceptions.RequestException:
        return "conn_error"


def main():
    parser = argparse.ArgumentParser(description="Load test para demo CWE-770")
    parser.add_argument("--target", required=True, help="Ej: http://localhost:5000")
    parser.add_argument("--requests", type=int, default=100, help="Número total de requests")
    parser.add_argument("--concurrency", type=int, default=20, help="Requests simultáneas")
    parser.add_argument("--payload-mb", type=float, default=5.0, help="Tamaño de cada request en MB")
    args = parser.parse_args()

    url = f"{args.target.rstrip('/')}/receive"
    payload_bytes = b"A" * int(args.payload_mb * 1024 * 1024)

    print(f"Objetivo:      {url}")
    print(f"Requests:      {args.requests}")
    print(f"Concurrencia:  {args.concurrency}")
    print(f"Tamaño/req:    {args.payload_mb} MB  (total ~{args.payload_mb * args.requests:.1f} MB enviados)")
    print("-" * 60)

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(send_one, url, payload_bytes) for _ in range(args.requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    total_time = time.time() - start

    counts = Counter(results)

    print(f"Tiempo total:  {total_time:.2f}s")
    for status, n in sorted(counts.items(), key=lambda kv: str(kv[0])):
        label = "error de conexión/timeout" if status == "conn_error" else f"HTTP {status}"
        print(f"  {label:<28} {n}")
    print("-" * 60)
    print("Tip: corré 'docker stats' en paralelo para ver el impacto en RAM/CPU del contenedor.")


if __name__ == "__main__":
    main()