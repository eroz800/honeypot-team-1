from io import StringIO, BytesIO
from typing import List, Dict
import csv
import os
import json
import glob
from pathlib import Path

def _fetch_events():
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    events = []
    log_files = glob.glob(str(logs_dir / "*.log")) + glob.glob(str(logs_dir / "*.txt"))
    for file in log_files:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # JSON
                try:
                    obj = json.loads(line)
                    event = {
                        "time": obj.get("time") or obj.get("timestamp"),
                        "trap_type": obj.get("trap") or obj.get("trap_type"),
                        "src_ip": obj.get("ip") or obj.get("src_ip"),
                        "input": obj.get("input") or obj.get("details") or obj.get("action") or "",
                    }
                    events.append(event)
                    continue
                except Exception:
                    pass
                # CSV
                try:
                    if line.count(",") >= 3:
                        reader = csv.reader([line])
                        row = next(reader)
                        event = {
                            "time": row[0],
                            "trap_type": row[1],
                            "src_ip": row[2],
                            "input": row[3] if len(row) > 3 else "",
                        }
                        events.append(event)
                        continue
                except Exception:
                    pass
    events.sort(key=lambda e: e.get("time") or "", reverse=True)
    return events

# נירמול סוגי טראפים לשמות אחידים
TRAP_ALIASES = {
    # Admin Panel
    "admin": "admin_panel",
    "panel": "admin_panel",
    "adminpanel": "admin_panel",
    "admin_panel": "admin_panel",

    # HTTP
    "http": "http",
    "httptrap": "http",

    # FTP
    "ftp": "ftp",
    "ftptrap": "ftp",

    # SSH
    "ssh": "ssh",
    "sshtrap": "ssh",

    # Ransomware
    "ransom": "ransomware",
    "ransomware": "ransomware",
    "crypto": "ransomware",

    # Open Ports
    "ports": "open_ports",
    "portscan": "open_ports",
    "open_ports": "open_ports",

    # IoT Router
    "iot": "iot_router",
    "iot router": "iot_router",
    "iot_router": "iot_router",

    # Phishing
    "phish": "phishing",
    "phishing": "phishing",
}



def get_events_for_report() -> List[Dict]:
    rows = _fetch_events()
    out = []
    for r in rows:
        rr = {**r}
        tt = (rr.get("trap_type") or "").lower()
        rr["trap_type"] = TRAP_ALIASES.get(tt, tt)
        rr.setdefault("username", "")
        rr.setdefault("details", "")
        out.append(rr)
    return out


def export_csv() -> str:
    rows = get_events_for_report()
    fieldnames = ["time", "src_ip", "trap_type", "action", "username", "details"]
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue()


def export_pdf() -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm

    rows = get_events_for_report()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # כותרת
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 2 * cm, "Honeypot — Summary Report")

    y = height - 3 * cm
    headers = ["Time", "IP", "Trap", "Action", "User", "Details"]
    xs = [1.5 * cm, 6 * cm, 9 * cm, 12 * cm, 15 * cm, 17 * cm]

    # הדפסת כותרות הטבלה
    c.setFont("Helvetica-Bold", 10)
    for h, x in zip(headers, xs):
        c.drawString(x, y, h)

    # הדפסת שורות
    c.setFont("Helvetica", 9)
    y -= 0.6 * cm
    for r in rows:
        values = [
            r.get("time", ""),
            r.get("src_ip", ""),
            r.get("trap_type", ""),
            r.get("action", ""),
            r.get("username", ""),
            (r.get("details", "") or "")[:60],
        ]
        for v, x in zip(values, xs):
            c.drawString(x, y, str(v))
        y -= 0.55 * cm

        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 9)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
