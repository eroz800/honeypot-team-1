# controller/aws_listener.py
from flask import Flask, request, jsonify, Request
from model.trap_manager import TrapManager
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

app = Flask(__name__)
trap_manager = TrapManager()


def _client_ip(req: Request) -> str:
    """
    מחזיר את כתובת ה-IP של הלקוח.
    אם נהיה מאחורי Nginx, ניקח מ-X-Forwarded-For; אחרת מ-remote_addr.
    """
    fwd = req.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else req.remote_addr


@app.route("/ingest", methods=["POST"])
def ingest():
    """
    מצפה ל-JSON:
    {
      "trap_type": "open_ports" | "ssh" | "http" | ...,
      "input": <string or object>,
      "ip": (לא חובה)
    }
    """
    data = request.get_json(silent=True) or {}

    trap_type = data.get("trap_type")
    input_data = data.get("input")
    ip = data.get("ip") or _client_ip(request)

    if not trap_type or input_data is None:
        return jsonify({"error": "trap_type and input are required"}), 400

    try:
        trap_manager.run_trap(trap_type, input_data, ip)
        return jsonify({"status": "ok"}), 200
    except Exception:
        return jsonify({"status": "error"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200


if __name__ == "__main__":
    # ריצה על HTTPS בפורט 8443 עם TLS
    app.run(host="0.0.0.0", port=8443, ssl_context=("certs/cert.pem", "certs/key.pem"))
