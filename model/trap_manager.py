# model/trap_manager.py
from typing import Dict, Any
import time
from .http_trap import HTTPTrap
from .ftp_trap import FTPTrap
from .ssh_trap import SshTrap
from .admin_panel_trap import AdminPanelTrap
from .phishing_trap import PhishingTrap 

class TrapManager:
    def __init__(self):
        self._traps: Dict[str, object] = {}
        # רישום מלכודות
        self._traps["http"] = HTTPTrap()
        self._traps["ftp"]  = FTPTrap()
        self._traps["ssh"]  = SshTrap()
        self._traps["admin_panel"] = AdminPanelTrap()
        self._traps["phishing"] = PhishingTrap()

    def get_trap(self, name: str):
        return self._traps.get(name)

    def list_traps(self):
        return list(self._traps.keys())

    def add_trap(self, trap_type: str, trap_obj):
        if not hasattr(trap_obj, "simulate_interaction"):
            raise TypeError("trap_obj must implement simulate_interaction")
        self._traps[trap_type] = trap_obj


    

    def run_trap(self, trap_type: str, input_data: Any, ip: str) -> dict:
        trap = self._traps.get(trap_type)
        if trap is None:
            raise KeyError(f"Trap '{trap_type}' not found")

        res = trap.simulate_interaction(input_data, ip)

        # אם המלכודת כבר החזירה מעטפת מלאה – מחזירים כמו שזה
        if isinstance(res, dict) and {"trap_type", "protocol", "timestamp"}.issubset(res.keys()):
            return res

        # עטיפה למעטפת אחידה
        return {
            "protocol":  getattr(trap, "get_protocol", lambda: trap_type.upper())(),
            "trap_type": trap_type,
            "input":     input_data,
            "ip":        ip,
            "timestamp": int(time.time()),
            "result":    res if isinstance(res, dict) else {"value": res},
        }
