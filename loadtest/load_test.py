#!/usr/bin/env python3
"""
Script de carga para demostrar CWE-770.

Envía ráfagas de requests concurrentes contra un servidor objetivo
(vulnerable en :5000 o mitigado en :5001) y reporta cuántas fueron
aceptadas, rechazadas (413/429) o fallaron por timeout/conexión caída.

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
import requests


def send_one(target, payload_bytes, endpoint="/upload"):
    url = f"{target.rstrip('/')}{endpoint}"
    try:
        t0 = time.time()
        if endpoint == "/upload":
            files = {"file": ("payload.bin", payload_bytes)}
            r = requests.post(url, files=files, timeout=10)
        else:
            r = requests.post(url, data=payload_bytes, timeout=10)
        elapsed = time.time() - t0
        return {"status": r.status_code, "elapsed": elapsed, "error": None}
    except requests.exceptions.RequestException as e:
        return {"status": None, "elapsed": None, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Load test para demo CWE-770")
    parser.add_argument("--target", required=True, help="Ej: http://localhost:5000")
    parser.add_argument("--requests", type=int, default=100, help="Número total de requests")
    parser.add_argument("--concurrency", type=int, default=20, help="Requests simultáneas")
    parser.add_argument("--payload-mb", type=float, default=5.0, help="Tamaño de cada archivo en MB")
    parser.add_argument("--endpoint", default="/upload", choices=["/upload", "/echo"])
    args = parser.parse_args()

    payload_bytes = b"A" * int(args.payload_mb * 1024 * 1024)

    print(f"Objetivo:      {args.target}{args.endpoint}")
    print(f"Requests:      {args.requests}")
    print(f"Concurrencia:  {args.concurrency}")
    print(f"Tamaño/req:    {args.payload_mb} MB  (total ~{args.payload_mb * args.requests:.1f} MB enviados)")
    print("-" * 60)

    results = []
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(send_one, args.target, payload_bytes, args.endpoint)
            for _ in range(args.requests)
        ]
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    total_time = time.time() - start

    ok = sum(1 for r in results if r["status"] and 200 <= r["status"] < 300)
    rejected_413 = sum(1 for r in results if r["status"] == 413)
    rejected_429 = sum(1 for r in results if r["status"] == 429)
    other_status = sum(
        1 for r in results
        if r["status"] and r["status"] not in (413, 429) and not (200 <= r["status"] < 300)
    )
    conn_errors = sum(1 for r in results if r["error"] is not None)

    print(f"Tiempo total:              {total_time:.2f}s")
    print(f"Exitosas (2xx):            {ok}")
    print(f"Rechazadas por tamaño(413):{rejected_413}")
    print(f"Rechazadas por rate(429):  {rejected_429}")
    print(f"Otros status:              {other_status}")
    print(f"Errores de conexión/timeout: {conn_errors}")
    print("-" * 60)
    print("Tip: corré 'docker stats' en paralelo para ver el impacto en RAM/CPU del contenedor.")


if __name__ == "__main__":
    main()
