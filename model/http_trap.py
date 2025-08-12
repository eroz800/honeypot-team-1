# model/http_trap.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import time
from typing import Dict
from .trap import Trap


@dataclass
class HTTPTrap(Trap):
    """
    מלכודת HTTP בסיסית המדמה GET/POST.
    input_data דוגמה:
      "GET /"
      "GET /api/health"
      "POST /login\nuser=admin&pass=123456"
    """

    _routes: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "/": {"GET": "<h1>Welcome</h1><p>Internal Admin Portal</p>"},
        "/login": {
            "GET": "<form method='POST'><input name='user'><input type='password' name='pass'><button>Sign in</button></form>",
            "POST": "Invalid credentials"
        },
        "/api/health": {"GET": '{"status":"ok","version":"1.0.0"}'}
    })

    # --- ממשק ה-ABC שלך ---
    def get_protocol(self) -> str:
        return "HTTP"

    def get_type(self) -> str:
        # חשוב! זה צריך להתאים למפתח שבו אתה רושם ב-TrapManager ("http")
        return "http"

    def simulate_interaction(self, input_data: str, ip: str) -> None:
        method, path, body = self._parse_request(input_data)

        # בחירת תשובה
        matched = path in self._routes and method in self._routes[path]
        status = 200 if matched else 404
        response_body = self._routes.get(path, {}).get(method, "<h1>404</h1>")

        # לוג לקובץ
        self._append_log_line(self._format_log(method, path, status, ip, body))

        # אופציונלי לשימוש פנימי/בדיקות
        self._last_response = {"status": status, "body": response_body}
        return {
    "trap_type": self.get_type(),
    "protocol": self.get_protocol(),
    "ip": ip,
    "input": input_data,
    "timestamp": int(time.time()),
    "data": {
        "status": status,
        "body": response_body,
        "content_type": "application/json" if path.startswith("/api/") else "text/html"
    }
}


    # --- עזר ---
    def _parse_request(self, raw: str) -> tuple[str, str, str]:
        raw = (raw or "").strip()
        if not raw:
            return "GET", "/", ""
        parts = raw.split("\n", 1)
        start_line = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        tokens = start_line.split()
        method = tokens[0].upper() if tokens else "GET"
        path = tokens[1] if len(tokens) > 1 else "/"
        if not path.startswith("/"):
            path = "/" + path
        if method not in ("GET", "POST"):
            method = "GET"
        return method, path, body

    def _format_log(self, method: str, path: str, status: int, ip: str, body: str) -> str:
        ts = datetime.utcnow().isoformat() + "Z"
        body_preview = body.replace("\n", "\\n")[:200]
        return (f'{ts} | protocol=HTTP | type=http | ip={ip} | '
                f'method={method} | path={path} | status={status} | body="{body_preview}"\n')

    def _append_log_line(self, line: str) -> None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "http_honeypot.log").open("a", encoding="utf-8").write(line)
