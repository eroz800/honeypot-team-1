import time
from model.ssh_trap import SshTrap
from model.trap_manager import TrapManager

def test_trap_manager_add_and_run_ssh():
    # יצירת טראפ מסוג SSH
    trap = SshTrap()
    manager = TrapManager()

    # הוספת הטראפ עם שם חדש כדי לא לדרוס קיים
    manager.add_trap("ssh_test", trap)

    # הרצת הטראפ
    res = manager.run_trap("ssh_test", "ls -al", "192.168.0.99")

    # בדיקות התוצאה
    assert res["trap_type"] == "ssh"
    assert res["protocol"] == "SSH"
    assert res["ip"] == "192.168.0.99"
    assert "ls -al" in res["input"]
    assert isinstance(res["timestamp"], int)
    assert res["timestamp"] <= int(time.time()) + 5
    assert "log" in res["data"]
