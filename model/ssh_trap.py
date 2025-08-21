from model.trap import Trap
import time

class SshTrap(Trap):
    def get_protocol(self) -> str:
        return "SSH"

    def get_type(self) -> str:
        return "ssh"

    def simulate_interaction(self, input_data, ip: str) -> dict:
        # תומך גם במחרוזת וגם ב־dict
        if isinstance(input_data, str):
            command = input_data
        elif isinstance(input_data, dict):
            command = input_data.get("command", "")
        else:
            command = ""

        # הודעה אחידה – גם להדפסה וגם ללוג
        log_line = f"[SSH] Interaction from {ip}: {command}"
        print(log_line)

        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": command,
            "timestamp": int(time.time()),
            "data": {
                "summary": f"Command executed: {command}",
                "log": log_line
            }
        }
