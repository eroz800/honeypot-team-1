from model.trap import Trap
from model.logger import log_interaction  

import time

class SshTrap(Trap):
    def get_protocol(self) -> str:
        return "SSH"

    def get_type(self) -> str:
        return "ssh"

    def simulate_interaction(self, input_data: str, ip: str) -> dict:
        # Write to per-trap log file in CSV format
        from datetime import datetime, UTC
        from pathlib import Path
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        log_line = f'{ts},ssh,{ip},"{input_data}"\n'
        with (logs_dir / "ssh_honeypot.log").open("a", encoding="utf-8") as f:
            f.write(log_line)
        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {
                "message": "interaction logged",
                "log": log_line
            }
        }
