import logging
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os

# Define the log file path
LOG_FILE = 'logs/ftp_logs.txt'  # Updated log file path

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

class TrapFTPHandler(FTPHandler):
    def on_login(self, username):
        logging.info(f"Login: {username} from {self.remote_ip}")
        logging.info(f"Connection from {self.remote_ip}:{self.remote_port} - User: {username}")

    def on_disconnect(self):
         logging.info(f"Disconnected {self.remote_ip}:{self.remote_port} - User: {self.username}")

    def on_login_failed(self, username, password):
        logging.warning(f"Failed login: {username} from {self.remote_ip}")

    def ftp_STOR(self, file, callback=None):
        logging.warning(f"Upload attempt from {self.remote_ip}, file: {file}")
        self.respond("550 Uploads are not allowed.")  # Respond with a 550 error
        return '550 Uploads are not allowed.'

    def ftp_LIST(self, path):
        logging.info(f"LIST command from {self.remote_ip}, path: {path}")
        super().ftp_LIST(path)

    def ftp_RETR(self, file, callback=None):
        logging.info(f"RETR command from {self.remote_ip}, file: {file}")
        super().ftp_RETR(file, callback)

    def ftp_MKD(self, dirname):
        logging.info(f"MKD command from {self.remote_ip}, dirname: {dirname}")
        super().ftp_MKD(dirname)

    def ftp_RMD(self, dirname):
        logging.info(f"RMD command from {self.remote_ip}, dirname: {dirname}")
        super().ftp_RMD(dirname)

    def ftp_DELE(self, filename):
        logging.info(f"DELE command from {self.remote_ip}, filename: {filename}")
        super().ftp_DELE(filename)

    def ftp_RNFR(self, filename):
        logging.info(f"RNFR command from {self.remote_ip}, filename: {filename}")
        super().ftp_RNFR(filename)

    def ftp_RNTO(self, filename):
        logging.info(f"RNTO command from {self.remote_ip}, filename: {filename}")
        super().ftp_RNTO(filename)

def run_ftp_server():
    ftp_root = os.path.abspath("ftp_root")
    os.makedirs(ftp_root, exist_ok=True)

    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "12345", ftp_root, perm="elradfmMT")  # Removed "w" permission

    handler = TrapFTPHandler
    handler.authorizer = authorizer
    handler.passive_ports = range(60000, 60010)  # Configure passive ports

    server = FTPServer(("0.0.0.0", 2121), handler)
    print("FTP server running on port 2121...")
    server.serve_forever()
    print("Server loop exited!")

if __name__ == "__main__":
    run_ftp_server()