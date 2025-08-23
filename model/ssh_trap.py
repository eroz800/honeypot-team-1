from model.trap import Trap
from model.logger import log_interaction  # ← שימוש בשם הפונקציה שלך

import time

class SshTrap(Trap):
    def get_protocol(self) -> str:
        return "SSH"

    def get_type(self) -> str:
        return "ssh"

    def simulate_interaction(self, input_data: str, ip: str) -> dict:
        log_interaction(self.get_type(), ip, input_data)  # ← כתיבה ללוג
        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {
                "message": "interaction logged"
            }
        }
