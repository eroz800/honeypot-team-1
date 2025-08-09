
from model.trap import Trap

class SshTrap(Trap):
    def get_protocol(self) -> str:
        return "SSH"

    def get_type(self) -> str:
        return "Fake SSH Login"

    def simulate_interaction(self, input_data: str, ip: str) -> str:
       log_line = f"[SSH] Interaction from {ip}: {input_data}"
       print(log_line)
       return log_line

