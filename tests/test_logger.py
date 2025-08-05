from model.logger import log_interaction

def test_logger():
    log_interaction("Fake SSH Login", "192.168.0.42", "whoami")

if __name__ == "__main__":
    test_logger()
