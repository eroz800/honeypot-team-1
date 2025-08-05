from model.auth_manager import check_credentials

def test_auth():
    print(check_credentials("admin", "1234"))       # ✅ True
    print(check_credentials("admin", "wrong"))      # ❌ False
    print(check_credentials("guest", "guest123"))   # ✅ True
    print(check_credentials("hacker", "toor"))      # ❌ False

if __name__ == "__main__":
    test_auth()
