
from flask import (
    Flask, request, jsonify, send_from_directory,
    render_template_string, send_file, Response
)
from pathlib import Path
import sys, os, json, urllib.request

# הגדרות בסיס 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = Path(__file__).resolve().parents[1]

# יבוא טראפים ומנג'ר 
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

# CSV/PDF + events
from model import report_generator

# Flask app 
app = Flask(__name__)

# CORS 
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

# Manager + רישום טראפים 
manager = TrapManager()
manager.add_trap("open_ports", OpenPortsTrap())
manager.add_trap("ransomware", RansomwareTrap())
manager.add_trap("phishing", PhishingTrap())
manager.add_trap("ssh", SshTrap())
manager.add_trap("http", HTTPTrap())
manager.add_trap("ftp", FTPTrap())
manager.add_trap("admin_panel", AdminPanelTrap())
manager.add_trap("iot_router", IoTRouterTrap())

# Health 
@app.route("/health", methods=["GET"])
def health():
    return {"status": "running"}, 200

# Routes בסיס 
@app.route("/")
def home():
    return "Honeypot is live"

# Dashboard / Static 
@app.route("/dashboard")
def dashboard():
    with open(BASE_DIR / "view" / "dashboard.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

# Reports & Data Export (CSV / PDF / HTML)
@app.route("/report")
def report_html():
    """מציג את דוח האירועים בעמוד HTML שמוגדר ב-reports/summary.html"""
    try:
        events = report_generator.get_events_for_report()
        html_path = BASE_DIR / "reports" / "summary.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_src = f.read()
        return render_template_string(html_src, events=events)
    except FileNotFoundError:
        return "<h1>אין תבנית דוח</h1><p>חסר reports/summary.html</p>", 404
    except Exception as e:
        return f"<h1>שגיאה בטעינת הדוח</h1><pre>{e}</pre>", 500

# קישור ישן אם משתמשים בו – מפנה לאותו הדוח
@app.route("/summary")
def summary():
    return report_html()

# ייצוא CSV
@app.route("/reports.csv")
def report_csv():
    try:
        csv_str = report_generator.export_csv()
        return Response(
            csv_str,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=honeypot_report.csv"},
        )
    except Exception as e:
        return f"CSV export error: {e}", 500

# ייצוא PDF
@app.route("/reports.pdf")
def report_pdf():
    try:
        pdf_bytes = report_generator.export_pdf()
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=honeypot_report.pdf"},
        )
    except Exception as e:
        return f"PDF export error: {e}", 500

@app.route("/style.css")
def style():
    return send_from_directory(str(BASE_DIR / "view"), "style.css")

# Views (UI)
@app.route("/admin_panel.html")
def admin_panel():
    return send_from_directory(str(BASE_DIR / "view"), "admin_panel.html")

@app.route("/phishing.html")
def phishing():
    return send_from_directory(str(BASE_DIR / "view"), "phishing.html")

@app.route("/router_ui.html")
def router_ui():
    return send_from_directory(str(BASE_DIR / "view"), "router_ui.html")

# Traps (API) 
@app.route("/trap/phishing", methods=["POST"])
def trap_phishing():
    trap = manager.get_trap("phishing")
    data = request.form.to_dict() or request.get_json(silent=True) or {}
    ip = request.remote_addr
    result = trap.simulate_interaction(data, ip)
    return jsonify(result)

@app.route("/trap/admin_panel", methods=["POST"])
def trap_admin_panel():
    trap = manager.get_trap("admin_panel")
    data = request.form.to_dict() or request.get_json(silent=True) or {}
    ip = request.remote_addr
    result = trap.simulate_interaction(data, ip)
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

    return jsonify({"status": "ok", "data": response_data})


# helpers: נרמול שמות טראפים / כינויים 
_TRAP_ALIASES = {
    "http": "http", "https": "http", "web": "http",
    "ftp": "ftp", "ssh": "ssh", "phishing": "phishing",
    "admin": "admin_panel", "admin-panel": "admin_panel", "admin_panel": "admin_panel",
    "open-ports": "open_ports", "open_ports": "open_ports", "open ports": "open_ports",
    "iot": "iot_router", "router": "iot_router", "iot_router": "iot_router",
}
def _normalize_trap_name(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("-", "_").replace(" ", "_")
    return _TRAP_ALIASES.get(s, s)

# Generic simulation endpoint 
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

# GeoIP 
@app.route("/geoip", methods=["GET"])
def geoip():
    ip = (request.args.get("ip") or "").strip()
    if not ip:
        return jsonify({"error": "missing ip"}), 400
    try:
        url = f"https://ipapi.co/{ip}/json/"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))

        out = {
            "ip": ip,
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name") or data.get("country"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "org": data.get("org") or data.get("asn"),
        }
        return jsonify(out), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 502

# Reports Export
@app.route("/reports.csv", methods=["GET"])
def export_csv():
    from flask import Response
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # כותרות
    writer.writerow(["Timestamp", "Trap", "IP", "Input"])

   
    sample_data = [
        ("2025-09-01T12:00:00Z", "http", "1.2.3.4", "GET /"),
        ("2025-09-01T12:05:00Z", "ftp", "5.6.7.8", "USER test"),
    ]
    for row in sample_data:
        writer.writerow(row)

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=reports.csv"},
    )


@app.route("/reports.pdf", methods=["GET"])
def export_pdf():
    from flask import Response
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 750, "Honeypot Activity Report")
    pdf.drawString(100, 730, "Example Data:")
    pdf.drawString(100, 710, "Timestamp: 2025-09-01T12:00:00Z")
    pdf.drawString(100, 690, "Trap: http, IP: 1.2.3.4, Input: GET /")
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return Response(
        buffer,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reports.pdf"},
    )
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
