from model.ssh_trap import SshTrap
from model.trap_manager import TrapManager

def test_trap_manager():
    trap = SshTrap()
    manager = TrapManager()

    manager.add_trap(trap)  # מוסיף את מלכודת ה־SSH
    manager.run_trap("Fake SSH Login", "ls -al", "192.168.0.99")  # אמור להדפיס אינטראקציה

if __name__ == "__main__":
    test_trap_manager()
