# FILE: model/open_ports_trap.py
from __future__ import annotations
from datetime import datetime, UTC
from pathlib import Path
import time
from .trap import Trap

class OpenPortsTrap(Trap):
    """
    Trap שמדמה שירות פתוח (TCP) ומחזיר Banner, עם רישום לוג.
    """
    name = "open_ports"  # המפתח שבו נרשום ב-TrapManager

    # --- מימושי ה-ABC ---
    def get_protocol(self) -> str:
        return "TCP"

    def get_type(self) -> str:
        return "open_ports"

    def simulate_interaction(self, input_data: str, ip: str):
        banner = "Fake Open Port Service Banner"

        # לוג
        self._append_log_line(self._format_log(ip=ip, input_data=input_data, banner=banner))

        # תשובה ל-UI/בדיקות
        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {"banner": banner}
        }

    # כדי לעבוד חלק עם TrapManager שמפעיל run()
    def run(self, input_data: str, ip: str):
        return self.simulate_interaction(input_data, ip)

    # --- עזרי לוג ---
    def _format_log(self, ip: str, input_data: str, banner: str) -> str:
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        input_data = (input_data or "").replace("\n", "\\n")[:200]
        return (f'{ts} | protocol=TCP | type=open_ports | ip={ip} | '
                f'input="{input_data}" | banner="{banner}"\n')

    def _append_log_line(self, line: str) -> None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "open_ports_honeypot.log").open("a", encoding="utf-8").write(line)


if __name__ == "__main__":
    # בדיקה ידנית מהירה: py -m model.open_ports_trap
    t = OpenPortsTrap()
    print(t.run("PING", "127.0.0.1"))
