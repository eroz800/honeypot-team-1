

# model/report_generator.py

def generate_report():
    try:
        with open("logs/honeypot.log", "r", encoding="utf-8") as f:
            log_lines = f.readlines()
    except FileNotFoundError:
        print("לא נמצא קובץ לוג. אין מה לסכם.")
        return

    html_lines = [
        "<html>",
        "<head><title>Honeypot Report</title></head>",
        "<body>",
        "<h1>Honeypot Activity Summary</h1>",
        "<table border='1'>",
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
            continue  # מדלג על שורות לא תקינות

    html_lines.extend(["</table>", "</body>", "</html>"])

    import os
    os.makedirs("reports", exist_ok=True)

    with open("reports/summary.html", "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    print("  The report was generated successfully in reports/summary.html")
