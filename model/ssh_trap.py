# model/ssh_trap.py
from model.trap import Trap
import time

class SshTrap(Trap):
    def get_protocol(self) -> str:
        return "SSH"

    def get_type(self) -> str:
        return "ssh"

    def simulate_interaction(self, input_data: dict, ip: str) -> dict:
        command = input_data.get("command", "")
        log_line = f"[SSH] {ip} ran command: {command}"

        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            # כאן מחזירים מחרוזת, לא dict
            "input": f"Command: {command}",
            "timestamp": int(time.time()),
            "data": {
                "summary": f"Command executed: {command}",
                "log": log_line
            }
        }


