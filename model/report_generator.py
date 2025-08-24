from __future__ import annotations
from pathlib import Path
import html, json, ast
from collections import Counter
from model.logger import get_log_path

def _mask_password(p: str) -> str:
    if not p:
        return ""
    if len(p) <= 2:
        return "•" * len(p)
    return "•" * (len(p) - 2) + p[-2:]

def _format_input(trap_type: str, input_data: str) -> str:
    """עיבוד יפה של ה-input לפי סוג המלכודת"""
    text = str(input_data).strip()
    parsed = None
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        try:
            parsed = json.loads(text)
        except Exception:
            pass

    if isinstance(parsed, dict):
        t = trap_type.lower()
        # פישינג / FTP / IoT
        if "username" in parsed or "password" in parsed:
            uname_s = html.escape(str(parsed.get("username", "")))
            pwd_s = _mask_password(str(parsed.get("password", "")))
            return f"<b>User:</b> {uname_s} <br><b>Pass:</b> {pwd_s}"

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

        return html.escape(json.dumps(parsed, ensure_ascii=False))

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

def generate_report():
    base_dir = Path(__file__).resolve().parents[1]
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    log_path = Path(get_log_path())
    if not log_path.exists():
        raise FileNotFoundError("לא נמצא קובץ לוג")

    rows = []
    trap_counter = Counter()
    seen_inputs = {}

    with log_path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",", 3)]
            if len(parts) < 4:
                continue
            ts, trap, ip, inp = parts
            trap_counter[trap] += 1

            key = (trap, ip, inp)
            if key in seen_inputs:
                idx = seen_inputs[key]
                ts0, trap0, ip0, inp0 = rows[idx]
                if "(x" in inp0:
                    base, num = inp0.rsplit("(x", 1)
                    num = int(num.strip(")")) + 1
                    rows[idx] = (ts0, trap0, ip0, f"{base.strip()} (x{num})")
                else:
                    rows[idx] = (ts0, trap0, ip0, f"{inp0} (x2)")
            else:
                seen_inputs[key] = len(rows)
                rows.append((ts, trap, ip, inp))

    # HTML
    style = """
    <style>
      body { font-family: system-ui, Arial; margin:20px; background:#0b1220; color:#e6edf3;}
      h1{margin:0 0 10px;}
      .stats{margin:20px 0;padding:10px;background:#111a2e;border:1px solid #1d2a44;border-radius:8px;}
      table{border-collapse:collapse;width:100%;background:#0e1730;}
      th,td{border:1px solid #1d2a44;padding:8px;font-size:14px;}
      th{background:#101a36;}
      tr:hover td{background:#0f1a35;}
    </style>
    <script>setTimeout(()=>location.reload(),10000);</script>
    """

    html_lines = [
        "<html><head><meta charset='utf-8'><title>Honeypot Report</title>",
        style,
        "</head><body>",
        "<h1>📊 Honeypot Activity Summary</h1>",
        "<div class='stats'><h2>Summary Stats</h2><ul>",
    ]

    for trap, count in trap_counter.items():
        html_lines.append(f"<li>{_trap_icon(trap)} {html.escape(trap)}: <b>{count}</b></li>")
    html_lines.append("</ul></div>")

    html_lines.append("<table><tr><th>Timestamp</th><th>Trap</th><th>IP</th><th>Input</th></tr>")
    for ts, trap, ip, inp in rows[::-1]:
        pretty_input = _format_input(trap, inp)
        html_lines.append(
            f"<tr><td>{html.escape(ts)}</td>"
            f"<td>{_trap_icon(trap)} {html.escape(trap)}</td>"
            f"<td>{html.escape(ip)}</td>"
            f"<td>{pretty_input}</td></tr>"
        )
    html_lines.append("</table></body></html>")

    out_path = reports_dir / "summary.html"
    out_path.write_text("\n".join(html_lines), encoding="utf-8")
    print(f"✅ Report generated at {out_path}")
    return out_path

if __name__ == "__main__":
    generate_report()
