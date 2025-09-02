# FILE: controller/api_controller.py
from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file
from pathlib import Path
import sys, os, json, urllib.request

# --- הגדרות בסיס ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = Path(__file__).resolve().parents[1]

# --- GeoIP (שימוש בקובץ MaxMind) ---
from model.geoip_resolver import resolve_ip

# --- יבוא טראפים ומנג'ר ---
from model.trap_manager import TrapManager
from model.open_ports_trap import OpenPortsTrap
from model.ransomware_trap import RansomwareTrap
from model.phishing_trap import PhishingTrap
from model.ssh_trap import SshTrap
from model.http_trap import HTTPTrap
from model.ftp_trap import FTPTrap
from model.admin_panel_trap import AdminPanelTrap
from model.iot_router_trap import IoTRouterTrap

try:
    from model.logger import log_interaction
except Exception:
    log_interaction = None

from model.report_generator import generate_report

# --- Flask app ---
app = Flask(__name__)

# --- CORS (גם אם Flask-Cors לא מותקן) ---
try:
    from flask_cors import CORS
    CORS(app)
except Exception:
    @app.after_request
    def add_cors_headers(resp):
        resp.headers.setdefault("Access-Control-Allow-Origin", "*")
        resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization")
        resp.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return resp

# --- Manager + רישום טראפים ---
manager = TrapManager()
manager.add_trap("open_ports", OpenPortsTrap())
manager.add_trap("ransomware", RansomwareTrap())
manager.add_trap("phishing", PhishingTrap())
manager.add_trap("ssh", SshTrap())
manager.add_trap("http", HTTPTrap())
manager.add_trap("ftp", FTPTrap())
manager.add_trap("admin_panel", AdminPanelTrap())
manager.add_trap("iot_router", IoTRouterTrap())

# ---------- Health ----------
@app.route("/health", methods=["GET"])
def health():
    return {"status": "running"}, 200

# ---------- Routes בסיס ----------
@app.route("/")
def home():
    return "Honeypot is live"

# ---------- Dashboard / Static ----------
@app.route("/dashboard")
def dashboard():
    with open(BASE_DIR / "view" / "dashboard.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

@app.route("/report")
def show_report():
    try:
        out_path = generate_report()
        return send_file(str(out_path), mimetype="text/html")
    except FileNotFoundError:
        return "<h1>אין דוח זמין</h1><p>לא נמצאו קבצי לוג ליצירת דוח.</p>", 404
    except Exception as e:
        return f"<h1>שגיאה ביצירת הדוח</h1><pre>{e}</pre>", 500

@app.route("/summary")
def summary():
    return show_report()

@app.route("/style.css")
def style():
    return send_from_directory(str(BASE_DIR / "view"), "style.css")

# ---------- Views (UI) ----------
@app.route("/admin_panel.html")
def admin_panel():
    return send_from_directory(str(BASE_DIR / "view"), "admin_panel.html")

@app.route("/phishing.html")
def phishing():
    return send_from_directory(str(BASE_DIR / "view"), "phishing.html")

@app.route("/router_ui.html")
def router_ui():
    return send_from_directory(str(BASE_DIR / "view"), "router_ui.html")

# ---------- Traps (API) ----------
@app.route("/trap/phishing", methods=["POST"])
def trap_phishing():
    trap = manager.get_trap("phishing")
    data = request.form.to_dict() or request.get_json(silent=True) or {}
    ip = request.remote_addr
    result = trap.simulate_interaction(data, ip)
    if log_interaction:
        try:
            log_interaction("phishing", ip, data)
        except Exception:
            pass
    return jsonify(result)

@app.route("/trap/admin_panel", methods=["POST"])
def trap_admin_panel():
    trap = manager.get_trap("admin_panel")
    data = request.form.to_dict() or request.get_json(silent=True) or {}
    ip = request.remote_addr
    result = trap.simulate_interaction(data, ip)
    if log_interaction:
        try:
            log_interaction("admin_panel", ip, data)
        except Exception:
            pass
    return jsonify(result)

@app.route("/trap/iot_router", methods=["GET", "POST"])
def trap_iot_router():
    if request.method == "GET":
        return send_from_directory(str(BASE_DIR / "view"), "router_ui.html")

    trap = manager.get_trap("iot_router")
    data = request.form.to_dict() or request.get_json(silent=True) or {}
    ip = request.remote_addr
    result = trap.simulate_interaction(data, ip)

    response_data = data.copy()
    response_data.update(result.get("data", {}))

    if log_interaction:
        try:
            log_interaction("iot_router", ip, data)
        except Exception:
            pass

    return jsonify({"status": "ok", "data": response_data})

# --- helpers: נרמול שמות טראפים / כינויים ---
_TRAP_ALIASES = {
    "http": "http",
    "https": "http",
    "web": "http",
    "ftp": "ftp",
    "ssh": "ssh",
    "phishing": "phishing",
    "admin": "admin_panel",
    "admin-panel": "admin_panel",
    "admin_panel": "admin_panel",
    "open-ports": "open_ports",
    "open_ports": "open_ports",
    "open ports": "open_ports",
    "iot": "iot_router",
    "router": "iot_router",
    "iot_router": "iot_router",
}
def _normalize_trap_name(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("-", "_").replace(" ", "_")
    return _TRAP_ALIASES.get(s, s)

# ---------- Generic simulation endpoint ----------
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}
    trap_type_raw = str(data.get("trap_type", ""))
    trap_type = _normalize_trap_name(trap_type_raw)
    input_data = data.get("input", {}) or {}
    if isinstance(input_data, str):
        input_data = {"raw": input_data}
    ip = data.get("ip") or request.headers.get("X-Forwarded-For", request.remote_addr)
    if not trap_type:
        return jsonify({"error": "Missing trap_type"}), 400
    if not ip:
        return jsonify({"error": "Missing ip"}), 400
    try:
        result = manager.run_trap(trap_type, input_data, ip)
        if log_interaction:
            try:
                log_interaction(trap_type, ip, input_data)
            except Exception:
                pass
        return jsonify(result), 200
    except KeyError:
        try:
            available = sorted(list(getattr(manager, "_traps", {}).keys()))
        except Exception:
            available = []
        return jsonify({
            "error": f"Trap '{trap_type_raw}' not found",
            "normalized": trap_type,
            "available_traps": available,
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- GeoIP (מבוסס MaxMind) ----------
@app.route("/geoip/<ip>", methods=["GET"])
def geoip_lookup(ip):
    return jsonify(resolve_ip(ip))

# ---------- Run app ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
