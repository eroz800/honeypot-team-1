from pathlib import Path

def generate_report():
    # מחשב את נתיב התיקייה הראשית של הפרויקט
    base_dir = Path(__file__).resolve().parents[1]
    log_path = base_dir / "logs" / "honeypot.log"

    # בדיקה אם קובץ הלוג קיים
    if not log_path.exists():
        print("לא נמצא קובץ לוג. אין מה לסכם.")
        raise FileNotFoundError

    # קריאת הלוג
    with log_path.open("r", encoding="utf-8") as f:
        log_lines = f.readlines()

    # יצירת שורות HTML
    html_lines = [
    "<html>",
    "<head><title>Honeypot Report</title><link rel='stylesheet' href='/style.css'></head>",
    "<body>",
    "<h1>Honeypot Activity Summary</h1>",
    "<table class='report-table'>",
    "<tr><th>Timestamp</th><th>Trap Type</th><th>IP</th><th>Input</th></tr>"
]


    for line in log_lines:
        try:
            timestamp = line[1:20]
            rest = line[22:].strip()
            trap_type, after_type = rest.split(" from ", 1)
            ip, input_data = after_type.split(": ", 1)
            html_lines.append(
                f"<tr><td>{timestamp}</td><td>{trap_type}</td><td>{ip}</td><td>{input_data}</td></tr>"
            )
        except ValueError:
            continue  # דילוג על שורות לא תקינות

    html_lines.extend(["</table>", "</body>", "</html>"])

    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    out_path = reports_dir / "summary.html"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    print(f"The report was generated successfully in {out_path}")
    return out_path  # מחזיר נתיב מלא לקובץ

