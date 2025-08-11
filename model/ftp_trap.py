from __future__ import annotations
from datetime import datetime
from pathlib import Path
from .trap import Trap

class FTPTrap(Trap):
    def __init__(self):
        super().__init__()  # בלי פרמטרים כי Trap לא מצפה

    def get_protocol(self) -> str:
        return "FTP"

    def get_type(self) -> str:
        return "ftp"

    def simulate_interaction(self, input_data: str, ip: str):
        # שמירת לוג בפורמט אחיד
        self._append_log_line(self._format_log(input_data, ip))

        # תגובות FTP לדוגמה
        if input_data.upper().startswith("USER"):
            response = "331 User name okay, need password."
        elif input_data.upper().startswith("PASS"):
            response = "530 Not logged in."
        elif input_data.upper().startswith("LIST"):
            response = (
                "150 Opening ASCII mode data connection for file list.\n"
                "-rw-r--r-- 1 user group 0 Jan 1 00:00 secret.txt"
            )
        else:
            response = "502 Command not implemented."

        return {"status": "ok", "response": response}

    # --- עזר לשמירת לוגים ---
    def _format_log(self, command: str, ip: str) -> str:
        ts = datetime.utcnow().isoformat() + "Z"
        command_preview = command.replace("\n", "\\n")[:200]
        return (f'{ts} | protocol=FTP | type=ftp | ip={ip} | '
                f'command="{command_preview}"\n')

    def _append_log_line(self, line: str) -> None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "ftp_honeypot.log").open("a", encoding="utf-8").write(line)
