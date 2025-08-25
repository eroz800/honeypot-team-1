from pathlib import Path
import html
import ast
import json
from collections import Counter
from typing import Dict, Any, List, Tuple, Optional



def _mask_password(p: str) -> str:
    if not p:
        return ""
    if len(p) <= 2:
        return "•" * len(p)
    return "•" * (len(p) - 2) + p[-2:]


def _format_input(trap_type: str, input_data: str) -> str:
    """
    מציג את ה-input בטבלה בצורה קריאה לפי סוג הטראפ.
    """
    text = str(input_data).strip()
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
        t = trap_type.lower()

        # פישינג / FTP / IoT
        if "username" in parsed or "password" in parsed:
            uname_s = html.escape(str(parsed.get("username", "")))
            pwd_s = _mask_password(str(parsed.get("password", "")))
            dns_s = html.escape(str(parsed.get("dns", ""))) if "dns" in parsed else None
            target = html.escape(str(parsed.get("target", ""))) if "target" in parsed else None

            out = f"<b>User:</b> {uname_s} <br><b>Pass:</b> {pwd_s}"
            if dns_s:
                out += f"<br><b>DNS:</b> {dns_s}"
            if target:
                out += f"<br><b>Target:</b> {target}"
            return out

        # SSH
        if "command" in parsed:
            return f"<b>Command:</b> {html.escape(str(parsed['command']))}"

        # HTTP
       
        if "method" in parsed and "path" in parsed:
            method = html.escape(str(parsed.get("method", "")))
            path = html.escape(str(parsed.get("path", "")))
            payload = html.escape(str(parsed.get("payload", ""))) if "payload" in parsed else ""
            out = f"<b>Method:</b> {method} <br><b>Path:</b> {path}"
            if payload:
                out += f"<br><b>Payload:</b> {payload}"
            return out

        

        # Open Ports
        if "port" in parsed:
            return f"<b>Port:</b> {html.escape(str(parsed['port']))}"

        # Ransomware
        if "file" in parsed and t == "ransomware":
            fname = html.escape(str(parsed["file"]))
            return f"<b>File:</b> {fname} <br><b>Status:</b> Encrypted"

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
        "iot_router": "📡",
    }
    return mapping.get(trap_type.lower(), "❓")


def _looks_like_csv(line: str) -> bool:
    if line.count(", ") < 3:
        return False
    if len(line) >= 19 and line[4] == "-" and line[7] == "-" and line[13] == ":" and line[16] == ":":
        return True
    return False


def generate_report():
    # נקרא לדאטה מובנה (כולל rows + stats)
    data = generate_report_data()  

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
    for trap, count in data.get("stats", {}).items():
        html_lines.append(f"<li>{_trap_icon(trap)} {trap}: <b>{count}</b></li>")
    html_lines.append("</ul></div>")

    # טבלה
    html_lines.append("<table class='report-table'>")
    html_lines.append("<tr><th>Timestamp</th><th>Trap</th><th>IP</th><th>Input</th></tr>")

    for row in data.get("rows", []):
        html_lines.append(
            f"<tr><td>{html.escape(str(row['timestamp']))}</td>"
            f"<td>{row['icon']} {html.escape(str(row['trap']))}</td>"
            f"<td>{html.escape(str(row['ip']))}</td>"
            f"<td>{row['input_pretty']}</td></tr>"
        )

    html_lines.extend(["</table>", "</body>", "</html>"])

    base_dir = Path(__file__).resolve().parents[1]
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    out_path = reports_dir / "summary.html"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    print(f"✅ Report generated at {out_path}")
    return out_path





def generate_report_data(filter_trap: Optional[str] = None) -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parents[1]
    log_path = base_dir / "logs" / "honeypot.log"

    if not log_path.exists():
        return {"rows": [], "stats": {}, "error": "log_not_found"}

    with log_path.open("r", encoding="utf-8") as f:
        log_lines = f.readlines()

    rows: List[Tuple[str, str, str, Any]] = []
    trap_counter: Counter = Counter()
    seen_inputs: dict = {}

    def add_row(ts, trap, ip, input_data):
        # סינון לפי trap_type אם התבקש
        if filter_trap and trap.lower() != filter_trap.lower():
            return

        trap_counter[trap] += 1

        key = (trap, ip, input_data)
        if key in seen_inputs:
            idx = seen_inputs[key]
            ts0, trap0, ip0, inp0 = rows[idx]
            if isinstance(inp0, str) and "(x" in inp0:
                base, num = inp0.rsplit("(x", 1)
                try:
                    num = int(num.strip(")")) + 1
                except Exception:
                    num = 2
                rows[idx] = (ts0, trap0, ip0, f"{base.strip()} (x{num})")
            else:
                rows[idx] = (ts0, trap0, ip0, f"{inp0} (x2)")
        else:
            seen_inputs[key] = len(rows)
            rows.append((ts, trap, ip, input_data))

    for raw in log_lines:
        line = raw.strip()
        if not line:
            continue

        try:
            if line.startswith("[") and "]" in line and " from " in line and ": " in line:
                timestamp = line[1:20]
                rest = line[line.index("]") + 2:].strip()
                trap_type, after_type = rest.split(" from ", 1)
                ip, input_data = after_type.split(": ", 1)
                add_row(timestamp, trap_type, ip, input_data)

            elif _looks_like_csv(line):
                parts = [p.strip() for p in line.split(", ", 3)]
                if len(parts) < 4:
                    continue
                timestamp, trap_type, ip, input_data = parts[0], parts[1], parts[2], parts[3]
                add_row(timestamp, trap_type, ip, input_data)

            else:
                continue

        except Exception:
            continue

    # הפורמט שיוחזר כ-JSON
    return {
        "stats": dict(trap_counter),
        "rows": [
            {
                "timestamp": ts,
                "trap": trap,
                "ip": ip,
                "input_raw": input_data,
                "input_pretty": _format_input(trap, input_data if not (isinstance(input_data, dict) and "raw_input" in input_data) else (input_data.get("input") or input_data["raw_input"])),
                "icon": _trap_icon(trap),
            }
            for (ts, trap, ip, input_data) in rows
        ],
    }
