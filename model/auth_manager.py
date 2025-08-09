fake_users = {
    "admin": "1234",
    "root": "toor",
    "guest": "guest123"
}
def check_credentials(username: str, password: str) -> bool:
    return fake_users.get(username) == password

