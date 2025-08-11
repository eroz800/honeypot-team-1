# model/logger.py
from datetime import datetime
import os

LOG_FILE = "logs/honeypot.log"

def log_interaction(trap_type: str, ip: str, input_data: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {trap_type} from {ip}: {input_data}\n"

    os.makedirs("logs", exist_ok=True)  

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)
