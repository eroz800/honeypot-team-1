from model.trap import Trap
from model.logger import log_event  # ← זה היה חסר
import time

class SshTrap(Trap):
    def get_protocol(self) -> str:
        return "SSH"

    def get_type(self) -> str:
        return "ssh"

    def simulate_interaction(self, input_data: str, ip: str) -> dict:
        log_line = f"[SSH] Interaction from {ip}: {input_data}"
        log_event("honeypot.log", log_line)  # ← הוספנו את זה
        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {
                "log": log_line
            }
        }
