from pathlib import Path
import html
import ast
import json
from collections import Counter

def _mask_password(p: str) -> str:
    if not p:
        return ""
    if len(p) <= 2:
        return "•" * len(p)
    return "•" * (len(p) - 2) + p[-2:]

def _format_input(trap_type: str, input_data: str) -> str:
    """
    מציג את ה-input בטבלה בצורה קריאה לפי סוג הטראפ.
    לדוגמה: SSH -> Command, HTTP -> Method+Path, Phishing -> User/Pass.
    """
    text = input_data.strip()
    parsed = None

    # ננסה לפרסר dict (או JSON) אם אפשר
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = None

    if isinstance(parsed, dict):
        # טיפול ב־phishing / ftp (username+password)
        if "username" in parsed or "password" in parsed:
            uname_s = html.escape(str(parsed.get("username", "")))
            pwd_s = _mask_password(str(parsed.get("password", "")))
            return f"<b>User:</b> {uname_s} <br><b>Pass:</b> {pwd_s}"

        # טיפול ב־ssh (command)
        if "command" in parsed:
            return f"<b>Command:</b> {html.escape(str(parsed['command']))}"

        # טיפול ב־http (method + path)
        if "method" in parsed and "path" in parsed:
            return f"<b>{html.escape(parsed['method'])}</b> {html.escape(parsed['path'])}"

        # טיפול ב־open_ports / ransomware / others
        if "port" in parsed:
            return f"<b>Port:</b> {html.escape(str(parsed['port']))}"
        if "file" in parsed:
            return f"<b>File:</b> {html.escape(str(parsed['file']))}"

        # ברירת מחדל – JSON מלא
        return html.escape(json.dumps(parsed, ensure_ascii=False))

    # אם זה לא dict – מחזירים כמו שזה
    return html.escape(text)

def _trap_icon(trap_type: str) -> str:
    mapping = {
        "ssh": "🔒",
        "ftp": "📁",
        "http": "🌐",
        "admin_panel": "🛠️",
        "phishing": "🎭",
        "open_ports": "🔍",
        "ransomware": "💀",
        "iot": "📡",
    }
    return mapping.get(trap_type.lower(), "❓")

def _looks_like_csv(line: str) -> bool:
    if line.count(", ") < 3:
        return False
    if len(line) >= 19 and line[4] == "-" and line[7] == "-" and line[13] == ":" and line[16] == ":":
        return True
    return False

def generate_report():
    base_dir = Path(__file__).resolve().parents[1]
    log_path = base_dir / "logs" / "honeypot.log"

    if not log_path.exists():
        raise FileNotFoundError("לא נמצא קובץ לוג")

    with log_path.open("r", encoding="utf-8") as f:
        log_lines = f.readlines()

    rows = []
    trap_counter = Counter()

    for raw in log_lines:
        line = raw.strip()
        if not line:
            continue

        try:
            if line.startswith("[") and "]" in line and " from " in line and ": " in line:
                timestamp = line[1:20]
                rest = line[line.index("]") + 2 :].strip()
                trap_type, after_type = rest.split(" from ", 1)
                ip, input_data = after_type.split(": ", 1)

            elif _looks_like_csv(line):
                parts = [p.strip() for p in line.split(", ", 3)]
                if len(parts) < 4:
                    continue
                timestamp, trap_type, ip, input_data = parts[0], parts[1], parts[2], parts[3]

            else:
                continue

            trap_counter[trap_type] += 1
            rows.append((timestamp, trap_type, ip, input_data))

        except Exception:
            continue

    # בונים HTML
    html_lines = [
        "<html>",
        "<head><title>Honeypot Report</title>",
        "<link rel='stylesheet' href='/style.css'>",
        "<style>",
        "body { font-family: Arial; }",
        ".stats { margin: 20px 0; padding: 10px; background:#f0f0f0; border-radius:8px; }",
        ".report-table { border-collapse: collapse; width:100%; }",
        ".report-table th, .report-table td { border:1px solid #ddd; padding:8px; }",
        ".report-table th { background:#333; color:white; }",
        "</style>",
        "</head><body>",
        "<h1>📊 Honeypot Activity Summary</h1>",
    ]

    # סטטיסטיקות
    html_lines.append("<div class='stats'><h2>Summary Stats</h2><ul>")
    for trap, count in trap_counter.items():
        html_lines.append(f"<li>{_trap_icon(trap)} {trap}: <b>{count}</b></li>")
    html_lines.append("</ul></div>")

    # טבלה
    html_lines.append("<table class='report-table'>")
    html_lines.append("<tr><th>Timestamp</th><th>Trap</th><th>IP</th><th>Input</th></tr>")

    for ts, trap, ip, input_data in rows:
        pretty_input = _format_input(trap, input_data)
        html_lines.append(
            f"<tr><td>{html.escape(str(ts))}</td>"
            f"<td>{_trap_icon(trap)} {html.escape(str(trap))}</td>"
            f"<td>{html.escape(str(ip))}</td>"
            f"<td>{pretty_input}</td></tr>"
        )

    html_lines.extend(["</table>", "</body>", "</html>"])

    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    out_path = reports_dir / "summary.html"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    print(f"✅ Report generated at {out_path}")
    return out_path
