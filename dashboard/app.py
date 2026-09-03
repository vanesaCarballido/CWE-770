import json
import subprocess
import time
from flask import Flask, render_template, Response, request
import docker

app = Flask(__name__)

# Conexión nativa al socket de Docker (/var/run/docker.sock)
try:
    docker_client = docker.from_env()
except Exception:
    docker_client = None


def get_container_status(container_name):
    if not docker_client:
        return "offline"
    try:
        # Consulta el contenedor directo al motor de Docker
        container = docker_client.containers.get(container_name)
        container.reload()
        return container.status  # Retorna 'running', 'exited', etc.
    except Exception:
        return "offline"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status_api():
    vulnerable_status = get_container_status("cwe770-vulnerable")
    fixed_status = get_container_status("cwe770-fixed")
    return {"vulnerable": vulnerable_status, "fixed": fixed_status}


@app.route("/api/restart", methods=["POST"])
def restart_containers():
    if not docker_client:
        return {"success": False, "message": "No se pudo conectar al socket de Docker"}, 500

    try:
        # Reinicia los contenedores directamente vía API de Docker
        for cname in ["cwe770-vulnerable", "cwe770-fixed"]:
            try:
                container = docker_client.containers.get(cname)
                container.restart()
            except docker.errors.NotFound:
                pass

        return {"success": True, "message": "Contenedores reiniciados exitosamente."}
    except Exception as e:
        return {"success": False, "message": str(e)}, 500


@app.route("/api/run-test")
def run_test():
    
    target_port = request.args.get("port", "5000")
    requests_cnt = request.args.get("requests", "150")
    concurrency = request.args.get("concurrency", "60")
    payload_mb = request.args.get("payload", "6")

    # Mapeo de puerto a nombre de servicio para la red interna de Docker
    host_target = "vulnerable" if target_port == "5000" else "fixed"
    url = f"http://{host_target}:{target_port}"

    def generate():
        cmd = [
            "python3",
            "-u",
            "/app/load_test.py",
            "--target",
            url,
            "--requests",
            str(requests_cnt),
            "--concurrency",
            str(concurrency),
            "--payload-mb",
            str(payload_mb),
        ]

        yield f"data: {json.dumps({'log': f'>>> Ejecutando prueba contra {url}...\n'})}\n\n"

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            for line in iter(process.stdout.readline, ""):
                yield f"data: {json.dumps({'log': line})}\n\n"

            process.stdout.close()
            process.wait()
            yield f"data: {json.dumps({'log': '>>> Pruebas finalizadas.\n', 'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'log': f'>>> Error ejecutando la prueba: {e}\n', 'done': True})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)