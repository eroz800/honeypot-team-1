from flask import Flask, request
from model.trap_manager import TrapManager

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
    app.run(host="0.0.0.0", port=80)
