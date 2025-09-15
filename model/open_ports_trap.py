
from __future__ import annotations
from datetime import datetime, UTC
from pathlib import Path
import time
import json
import ast
from typing import Any, Dict, Tuple
from .trap import Trap


BANNERS: Dict[int, str] = {
    21:   "220 FTP Service Ready",
    22:   "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3",
    80:   "HTTP/1.1 200 OK",
    443:  "HTTP/1.1 200 OK (TLS handshake simulated)",
    3306: "5.7.36-MySQL Community Server (GPL)",
}

class OpenPortsTrap(Trap):
    """
    מלכודת פורטים פתוחים (TCP):
    - קולטת פורט ממגוון פורמטים (int/str/JSON/dict)
    - מחזירה באנר קבוע (כפי שהטסטים מצפים) + ניחוש שירות לפי הפורט
    - מזהה nmap לפי הטקסט הגולמי
    - רושמת אינטראקציה ללוג
    """
    name = "open_ports"

    # מזהה פרוטוקול/סוג 
    def get_protocol(self) -> str:
        return "TCP"

    def get_type(self) -> str:
        return "open_ports"

    # נקודת הכניסה העיקרית 
    def simulate_interaction(self, input_data: Any, ip: str) -> Dict[str, Any]:
        # חילוץ הפורט וטקסט גולמי לזיהוי nmap
        port, raw_str = self._extract_port_and_raw(input_data)

        # הבאנר שהטסטים מצפים לו 
        banner = "Fake Open Port Service Banner"

       
        service_guess = BANNERS.get(port, "unknown")

        # זיהוי nmap
        nmap_detected = self._looks_like_nmap(raw_str)

        # לוג נפרד אם זוהה nmap
        if nmap_detected:
            self._append_log_line(
                self._format_log(ip=ip, input_data=f"port={port} (nmap detected)", banner="detected nmap scan")
            )

        
        pretty_input = f"Port: {port}" if port else (str(input_data).strip())
        self._append_log_line(self._format_log(ip=ip, input_data=pretty_input, banner=banner))

        # תשובה ל-UI/בדיקות
        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": pretty_input,
            "raw_input": input_data,   
            "timestamp": int(time.time()),
            "data": {
                "port": port,
                "banner": banner,               
                "service_guess": service_guess, 
                "nmap_detected": nmap_detected,
            }
        }

   
    def run(self, input_data: Any, ip: str):
        return self.simulate_interaction(input_data, ip)

    
    def _extract_port_and_raw(self, input_data: Any) -> Tuple[int, str]:
        """
        תומך ב:
          - מספר: 22
          - מחרוזת: "22" / "scan 22" / "nmap -sV 22" / '{"port": 80}'
          - dict/JSON: {"port": 22} או {"port": "22"}
        מחזיר: (port:int, raw_str:str)
        """
        # dict
        if isinstance(input_data, dict):
            p = input_data.get("port")
            try:
                return int(p), str(input_data)
            except Exception:
                return 0, str(input_data)

        # מספר
        if isinstance(input_data, int):
            return input_data, str(input_data)

        # מחרוזת
        if isinstance(input_data, str):
            raw = input_data

            # JSON
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and "port" in obj:
                    return int(obj["port"]), raw
            except Exception:
                pass

            # literal_eval
            try:
                obj = ast.literal_eval(raw)
                if isinstance(obj, dict) and "port" in obj:
                    return int(obj["port"]), raw
            except Exception:
                pass

           
            tokens = [t for t in raw.replace("/", " ").split() if t.isdigit()]
            if tokens:
                try:
                    return int(tokens[0]), raw
                except Exception:
                    pass

           
            try:
                return int(raw.strip()), raw
            except Exception:
                return 0, raw

        
        return 0, str(input_data)

    
    def _looks_like_nmap(self, raw: str) -> bool:
        raw = (raw or "").lower()
        indicators = ["nmap", "-sv", "--version", "-ss", "-p "]
        return any(k in raw for k in indicators)

    
    def _format_log(self, ip: str, input_data: str, banner: str) -> str:
        from datetime import datetime, UTC
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        # Write as CSV: timestamp, trap_type, ip, input_data
        return f'{ts},open_ports,{ip},"{input_data}"\n'

    def _append_log_line(self, line: str) -> None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "open_ports_honeypot.log").open("a", encoding="utf-8").write(line)


if __name__ == "__main__":
    t = OpenPortsTrap()
    print(t.run({"port": 22}, "127.0.0.1"))
    print(t.run('{"port": 80}', "127.0.0.1"))
    print(t.run("nmap -sV 443", "127.0.0.1"))
    print(t.run("9999", "127.0.0.1"))
