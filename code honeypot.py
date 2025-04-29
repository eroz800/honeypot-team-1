
import sys
import threading
import paramiko

HOST_KEY = paramiko.RSAKey.generate(2048)

LOG_FILE = "honeypot.log"

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        with open(LOG_FILE, "a") as f:
            f.write(f"[LOGIN ATTEMPT] Username: {username} | Password: {password}\n")
        print(f"[LOGIN ATTEMPT] Username: {username} | Password: {password}")
        return paramiko.AUTH_SUCCESSFUL  # Always allow

def start_server(host="0.0.0.0", port=2222):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(100)
        print(f"[+] SSH Honeypot listening on {host}:{port}")
    except Exception as e:
        print(f"[!] Bind failed: {e}")
        sys.exit(1)

    while True:
        client, addr = sock.accept()
        print(f"[+] Connection from {addr[0]}:{addr[1]}")
        try:
            transport = paramiko.Transport(client)
            transport.add_server_key(HOST_KEY)
            server = SSHServer()
            transport.start_server(server=server)

            chan = transport.accept(20)
            if chan is None:
                continue

            chan.send("This is a fake SSH server. Go away.\n")
            chan.close()

        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    start_server()
