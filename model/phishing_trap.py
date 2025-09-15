import datetime
import os
import json
from model.trap import Trap
from flask import request   

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "honeypot.log")

class PhishingTrap(Trap):
    def __init__(self):
        self.name = "PhishingTrap"

    def get_protocol(self) -> str:
        return "HTTP"

    def get_type(self) -> str:
        return "phishing"

    def simulate_interaction(
        self, username: str, password: str, ip: str = None, timestamp: str = None
    ) -> dict:
        """
        מדמה אינטראקציה של פישינג:
        מקבל שם משתמש, סיסמה ו־IP (אם לא סופק, נשלף מ-request).
        אם שניהם ריקים – לא נרשום ללוג.
        אחרת – נשמור ללוג בפורמט JSON ונחזיר את הדאטה בפורמט אחיד.
        """

        
        if ip is None:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)

       
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        
        data = {
            "trap": self.get_type(),
            "protocol": self.get_protocol(),
            "username": username,
            "password": password,
            "ip": ip,
            "time": timestamp,
        }

        # אם המשתמש והסיסמה ריקים – לא נרשום ללוג
        if not username and not password:
            return data

        # אחרת – נשמור ללוג בפורמט JSON קריא
        log_path = os.path.abspath(LOG_FILE)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

        return data
