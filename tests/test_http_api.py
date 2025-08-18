import requests

r = requests.post("http://127.0.0.1:5000/simulate", json={
    "trap_type": "http",
    "input": {
        "method": "GET",
        "path": "/test",
        "payload": ""
    }
})
print(r.text)