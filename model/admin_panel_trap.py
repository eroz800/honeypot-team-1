from .trap import Trap
import json

class AdminPanelTrap(Trap):
    def get_protocol(self) -> str:
        return "http"

    def get_type(self) -> str:
        return "admin_panel"

    def simulate_interaction(self, input_data: dict, ip: str) -> dict:
        from datetime import datetime
        from .auth_manager import check_credentials
        import os

        username = input_data.get("username", "")
        password = input_data.get("password", "")
        success = check_credentials(username, password)
        timestamp = datetime.now().isoformat()

        # Log as JSON for compatibility with report_generator
        log_entry = {
            "trap_type": "admin_panel",
            "time": timestamp,
            "ip": ip,
            "username": username,
            "success": success
        }
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'admin_panel.log')
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + "\n")
            print(f"Log entry written to {log_path}: {log_entry}")
        except Exception as e:
            print(f"Failed to write log entry: {e}")

        result = {
            "ip": ip,
            "time": timestamp,
            "username": username,
            "success": success,
            "message": "Login attempt {}".format("succeeded" if success else "failed")
        }
        return result