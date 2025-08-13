# controller/api_controller.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]

from flask import Flask, request, jsonify, send_from_directory, render_template_string, make_response, send_file
from model.trap_manager import TrapManager
try:
    from model.logger import log_interaction  # אם קיים – נשתמש; אם לא, נתעלם בשקט
except Exception:
    log_interaction = None

# ייבוא הפונקציה שמייצרת את הדוח ומחזירה נתיב מוחלט
from model.report_generator import generate_report

app = Flask(__name__)
manager = TrapManager()


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
    """
    מייצר את הדוח בכל בקשה ומגיש את הקובץ המלא ישירות לדפדפן.
    זה עוקף בעיות נתיב/סביבת ריצה כי משתמשים בנתיב המוחלט שהפונקציה מחזירה.
    """
    try:
        out_path = generate_report()  # Path אובייקט מוחלט ל-reports/summary.html
        return send_file(str(out_path), mimetype="text/html")
    except FileNotFoundError:
        return "<h1>אין דוח זמין</h1><p>לא נמצאו קבצי לוג ליצירת דוח.</p>", 404
    except Exception as e:
        return f"<h1>שגיאה ביצירת הדוח</h1><pre>{e}</pre>", 500

@app.route("/style.css")
def style():
    return send_from_directory(str(BASE_DIR / "view"), "style.css")


# (לא חובה יותר, אבל משאיר כנתיב ידני במידה וצריך)
@app.route("/summary")
def summary():
    out_path = generate_report()
    with out_path.open("r", encoding="utf-8") as f:
        return render_template_string(f.read())


# ---------- Generic simulation endpoint ----------
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}

    trap_type = (data.get("trap_type") or "").strip().lower()
    input_data = data.get("input")  # יכול להיות dict (http/ftp) או str (ssh)
    ip = data.get("ip") or request.headers.get("X-Forwarded-For", request.remote_addr)

    if not trap_type:
        return jsonify({"error": "Missing trap_type"}), 400
    if not ip:
        return jsonify({"error": "Missing ip"}), 400
    if input_data is None:
        input_data = {}

    try:
        result = manager.run_trap(trap_type, input_data, ip)

        # לוג אם זמין
        if log_interaction:
            try:
                log_interaction(trap_type, ip, input_data)
            except Exception:
                pass

        # מחזירים אך ורק את התוצאה של ה-Manager, בלי עטיפה נוספת
        return jsonify(result), 200

    except KeyError:
        return jsonify({"error": f"Trap '{trap_type}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- (אופציונלי) פרוקסי ל-HTTPTrap לבדיקות אמיתיות ב-GET/POST ----------
@app.route("/trap/http", defaults={"req_path": ""}, methods=["GET", "POST"])
@app.route("/trap/http/<path:req_path>", methods=["GET", "POST"])
def http_trap_proxy(req_path):
    method = request.method
    path = "/" + req_path

    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.get_data(as_text=True) or ""

    input_data = {"method": method, "path": path, "payload": payload}
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    try:
        result = manager.run_trap("http", input_data, ip) or {}

        # תמיכה גם כשה-Manager מחזיר עטיפה וגם כשהתוצאה כבר "שטוחה"
        inner = result.get("result", result)
        data  = inner.get("data", inner)

        status = int(data.get("status", 200))
        body = data.get("body", "")
        content_type = data.get("content_type", "text/html")

        resp = make_response(body, status)
        resp.headers["Content-Type"] = content_type
        return resp
    except Exception as e:
        return make_response(f"HTTPTrap error: {e}", 500)


if __name__ == "__main__":
    app.run(debug=True)
