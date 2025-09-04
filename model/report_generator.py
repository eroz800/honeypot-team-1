from io import StringIO, BytesIO
from typing import List, Dict
import csv

# פונקציה שמחזירה אירועים לדוחות (כרגע דוגמה — צריך להחליף בקריאה אמיתית ל־DB/לוגים)
def _fetch_events() -> List[Dict]:
    return [
        {
            "time": "2025-09-01T10:41:55Z",
            "src_ip": "1.2.3.4",
            "trap_type": "ssh",
            "action": "login_attempt",
            "username": "root",
            "details": "failed password",
        },
    ]


# נירמול סוגי טראפים לשמות אחידים
TRAP_ALIASES = {
    "admin": "admin_panel",
    "panel": "admin_panel",
    "ports": "open_ports",
    "portscan": "open_ports",
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
