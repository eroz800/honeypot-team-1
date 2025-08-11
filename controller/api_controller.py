from flask import Flask, request, jsonify, send_from_directory, render_template_string, make_response
from model.trap_manager import TrapManager

app = Flask(__name__)

# Init manager (הרישום של המלכודות נעשה בתוך TrapManager)
manager = TrapManager()


# Home route
@app.route("/")
def home():
    return "Honeypot is live"


# -------- Helper for HTTP trap --------
def _run_http_trap_and_get_response(path: str) -> tuple[int, str, str]:
    """
    מריץ את מלכודת ה-HTTP ומחזיר (status, content_type, body)
    """
    # בונים input_data בדיוק לפי הפורמט של HTTPTrap.simulate_interaction
    if request.method == "POST":
        body = request.get_data(as_text=True) or ""
        input_data = f"POST /{path}\n{body}"
    else:
        input_data = f"GET /{path}"

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    manager.run_trap("http", input_data, ip)

    # שולפים את התגובה האחרונה מה-HTTPTrap (שמור כ־_last_response)
    http_trap = manager.get_trap("http")
    last = getattr(http_trap, "_last_response", None) or {"status": 200, "body": ""}

    status = int(last.get("status", 200))
    body_text = last.get("body", "")
    # טיפוס תוכן פשוט: JSON ל-health, אחרת HTML
    content_type = "application/json" if str(path).startswith("api/health") else "text/html"
    return status, content_type, body_text


# -------- Public HTTP trap endpoints (GET/POST אמיתיים) --------
@app.route("/trap/http", methods=["GET", "POST"])
def http_root():
    status, ctype, body = _run_http_trap_and_get_response("")
    resp = make_response(body, status)
    resp.headers["Content-Type"] = ctype
    return resp


@app.route("/trap/http/<path:req_path>", methods=["GET", "POST"])
def http_with_path(req_path):
    status, ctype, body = _run_http_trap_and_get_response(req_path)
    resp = make_response(body, status)
    resp.headers["Content-Type"] = ctype
    return resp


# -------- Generic simulation endpoint --------
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}
    trap_type = data.get("trap_type")
    input_data = data.get("input")
    ip = data.get("ip") or request.headers.get("X-Forwarded-For", request.remote_addr)

    if not all([trap_type, input_data, ip]):
        return jsonify({"error": "Missing parameters"}), 400

    # הפעלה דרך TrapManager
    manager.run_trap(trap_type, input_data, ip)

    # אם זו מלכודת HTTP
    if trap_type == "http":
        http_trap = manager.get_trap("http")
        last = getattr(http_trap, "_last_response", None) or {}
        return jsonify({"status": "ok", "last_response": last}), 200

    # אם זו מלכודת FTP
    if trap_type == "ftp":
        ftp_trap = manager.get_trap("ftp")
        last = ftp_trap.simulate_interaction(input_data, ip)
        return jsonify({"status": "ok", "response": last.get("response")}), 200

    return jsonify({"status": "ok"}), 200


# -------- Dashboard HTML --------
@app.route("/dashboard")
def dashboard():
    with open("view/dashboard.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())


@app.route("/summary")
def summary():
    with open("reports/summary.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())


# -------- CSS static --------
@app.route("/style.css")
def serve_css():
    return send_from_directory("view", "style.css")


# -------- Run app (local) --------
if __name__ == "__main__":
    app.run(debug=True)
