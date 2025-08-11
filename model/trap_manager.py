

# model/trap_manager.py
from typing import Dict
from .http_trap import HTTPTrap
from .ftp_trap import FTPTrap


class TrapManager:
    def __init__(self):
        self._traps: Dict[str, object] = {}

        # רישום מלכודות קיימות...
        # self._traps["ssh"] = SSHTrap()
        # self._traps["ftp"] = FTPTrap()

        # HTTP:
        self._traps["http"] = HTTPTrap()
        # FTP:
        self._traps["ftp"] = FTPTrap()

    def get_trap(self, name: str):
        return self._traps.get(name)

    def list_traps(self):
        return list(self._traps.keys())

    # נוח להפעלה לפי type (שם)
    def run_trap(self, trap_type: str, input_data: str, ip: str) -> None:
        trap = self._traps.get(trap_type)
        if trap is None:
            print(f"No trap found for type: {trap_type}")
            return
        trap.simulate_interaction(input_data, ip)
