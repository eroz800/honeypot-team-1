

from model.trap import Trap

class TrapManager:
    def __init__(self):
        self.traps: list[Trap] = []

    def add_trap(self, trap: Trap) -> None:
        self.traps.append(trap)

    def run_trap(self, trap_type: str, input_data: str, ip: str) -> None:
        for trap in self.traps:
            if trap.get_type() == trap_type:
                trap.simulate_interaction(input_data, ip)
                return
        print(f"No trap found for type: {trap_type}")