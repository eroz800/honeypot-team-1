import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.admin_panel_trap import AdminPanelTrap
import os
print("Test file started")
def test_simulate_interaction_logs_success_and_failure():
    trap = AdminPanelTrap()
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'admin_panel.log')
    # Remove log file before test
    if os.path.exists(log_path):
        os.remove(log_path)

    # Test correct credentials
    input_data = {"username": "admin", "password": "1234"}
    ip = "127.0.0.1"
    result = trap.simulate_interaction(input_data, ip)
    assert result["success"] is True

    # Test incorrect credentials
    input_data_wrong = {"username": "admin", "password": "wrong"}
    result_wrong = trap.simulate_interaction(input_data_wrong, ip)
    assert result_wrong["success"] is False

    # Check log file contents
    with open(log_path, 'r', encoding='utf-8') as f:
        logs = f.read()
    assert "IP: 127.0.0.1" in logs
    assert "User: admin" in logs
    assert "Success: True" in logs
    assert "Success: False" in logs
    assert "AdminPanelTrap" in logs
    
if __name__ == "__main__":
    print("Test file started")
    test_simulate_interaction_logs_success_and_failure()