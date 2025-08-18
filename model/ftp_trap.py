from __future__ import annotations
from datetime import datetime, UTC
from pathlib import Path
import time
from .trap import Trap

class FTPTrap(Trap):
    def __init__(self):
        super().__init__()  # בלי פרמטרים כי Trap לא מצפה

    def get_protocol(self) -> str:
        return "FTP"

    def get_type(self) -> str:
        return "ftp"

    def simulate_interaction(self, input_data, ip: str):
        # Handle dict or string input_data
        if isinstance(input_data, dict):
            username = input_data.get("username", "")
            password = input_data.get("password", "")
            command = f"USER {username}\nPASS {password}"
        else:
            command = str(input_data)

        # Logging
        self._append_log_line(self._format_log(command, ip))

        # Example FTP responses
        if command.upper().startswith("USER"):
            response = "331 User name okay, need password."
        elif command.upper().startswith("PASS"):
            response = "530 Not logged in."
        elif command.upper().startswith("LIST"):
            response = (
                "150 Opening ASCII mode data connection for file list.\n"
                "-rw-r--r-- 1 user group 0 Jan 1 00:00 secret.txt"
            )
        else:
            response = "502 Command not implemented."

        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {
                "status": "ok",
                "response": response
            }
        }

    # --- עזר לשמירת לוגים ---
    def _format_log(self, command: str, ip: str) -> str:
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        command_preview = command.replace("\n", "\\n")[:200]
        return (f'{ts} | protocol=FTP | type=ftp | ip={ip} | '
                f'command="{command_preview}"\n')

    def _append_log_line(self, line: str) -> None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "ftp_honeypot.log").open("a", encoding="utf-8").write(line)
