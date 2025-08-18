import requests

r = requests.post("http://127.0.0.1:5000/simulate", json={
    "trap_type": "ftp",
    "input": {"username": "test", "password": "test123"}
})
print(r.text)