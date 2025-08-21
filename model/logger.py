
from datetime import datetime
import os, json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_FILE = BASE_DIR / "logs" / "honeypot.log"

def log_interaction(trap_type: str, ip: str, input_data) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(BASE_DIR / "logs", exist_ok=True)

    # נוודא שה־input תמיד נרשם כמחרוזת JSON
    if not isinstance(input_data, str):
        try:
            input_str = json.dumps(input_data, ensure_ascii=False)
        except Exception:
            input_str = str(input_data)
    else:
        input_str = input_data

    # כתיבה בפורמט CSV אחיד
    log_line = f"{timestamp}, {trap_type}, {ip}, {input_str}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    # גם להדפיס למסוף בזמן אמת
    print(log_line.strip())

