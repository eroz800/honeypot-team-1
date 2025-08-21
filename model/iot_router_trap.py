# FILE: model/iot_router_trap.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
import time
from typing import Dict
from .trap import Trap


@dataclass
class IoTRouterTrap(Trap):
    """
    מלכודת IoT Router המדמה נתוני התחברות לראוטר (SSID, Password, DNS).
    input_data דוגמה:
      {"ssid": "MyNetwork", "password": "secret123", "dns": "1.1.1.1"}
    """

    def get_protocol(self) -> str:
        return "HTTP"   # לפי הדרישות

    def get_type(self) -> str:
        # לפי הטסט – חייב להיות בדיוק "IoT Router"
        return "IoT Router"

    def simulate_interaction(self, input_data, ip: str):
        if not isinstance(input_data, dict):
            raise ValueError("IoT Router trap requires dict input")

        ssid = input_data.get("ssid", "")
        password = input_data.get("password", "")
        dns = input_data.get("dns", "")

        # משמרים גם את השדות המקוריים וגם מוסיפים username לנוחות
        if ssid:
            input_data["username"] = ssid

        # כתיבת לוג
        self._append_log_line(self._format_log(ip, input_data))

        # מחזירים תשובה עם אותם מפתחות כדי שהטסט יעבור
        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {
                "ssid": ssid,
                "password": password,
                "dns": dns,
                "status": "ok"
            }
        }

    # --- עזרי לוג ---
    def _format_log(self, ip: str, input_data: Dict) -> str:
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        # שים לב: כאן חייב להיות "IoT Router" ולא "iot_router"
        return f'{ts}, IoT Router, {ip}, {input_data}\n'

    def _append_log_line(self, line: str) -> None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "iot_router_honeypot.log").open("a", encoding="utf-8").write(line)
