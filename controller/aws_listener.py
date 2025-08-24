from flask import Flask, request
from model.trap_manager import TrapManager
import os

app = Flask(__name__)
trap_manager = TrapManager()

@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.get_json()
    trap_type = data.get("trap_type")
    input_data = data.get("input")
    ip = request.remote_addr
    trap_manager.run_trap(trap_type, input_data, ip)
    return {"status": "ok"}, 200

@app.route("/health", methods=["GET"])
def health():
    return {"status": "running"}, 200

if __name__ == "__main__":
    HP_HOST = os.getenv("HP_HOST", "0.0.0.0")
    HP_PORT = int(os.getenv("HP_PORT", 80))
    SSL_CERT = os.getenv("HP_SSL_CERT")
    SSL_KEY = os.getenv("HP_SSL_KEY")
    ssl_context = (SSL_CERT, SSL_KEY) if SSL_CERT and SSL_KEY else None

    app.run(
        host=HP_HOST,
        port=HP_PORT,
        ssl_context=ssl_context
    )
