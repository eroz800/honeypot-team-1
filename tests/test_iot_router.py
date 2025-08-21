import pytest
from model.iot_router_trap import IoTRouterTrap
from controller import api_controller as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client

def test_iot_router_trap_class():
    trap = IoTRouterTrap()
    assert trap.get_type() == "IoT Router"
    assert trap.get_protocol() == "HTTP"

def test_iot_router_post(client):
    # שולחים POST עם נתונים כמו מהטופס
    resp = client.post("/trap/iot_router", data={
        "ssid": "MyNetwork",
        "password": "secret123",
        "dns": "1.1.1.1"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["data"]["ssid"] == "MyNetwork"
    assert data["data"]["dns"] == "1.1.1.1"

def test_iot_router_get(client):
    # GET אמור להחזיר את דף ה-HTML
    resp = client.get("/trap/iot_router")
    assert resp.status_code == 200
    assert b"IoT Router Management" in resp.data
