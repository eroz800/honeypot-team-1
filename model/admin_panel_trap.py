from .trap import Trap

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

		log_entry = f"[AdminPanelTrap] {timestamp} | IP: {ip} | User: {username} | Success: {success}\n"
		log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
		os.makedirs(log_dir, exist_ok=True)
		log_path = os.path.join(log_dir, 'admin_panel.log')
		try:
			with open(log_path, 'a', encoding='utf-8') as f:
				f.write(log_entry)
			print(f"Log entry written to {log_path}: {log_entry.strip()}")
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
