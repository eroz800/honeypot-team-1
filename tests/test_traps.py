# tests/test_traps.py
import time
import pytest
from model.phishing_trap import PhishingTrap
from pathlib import Path
from model.trap_manager import TrapManager
from model.open_ports_trap import OpenPortsTrap


@pytest.fixture
def manager(monkeypatch):
    """
    יוצר TrapManager עם טראפים רשומים מראש.
    מנטרל כתיבה לדיסק בלוגים של HTTP/FTP כדי שהטסטים יהיו נקיים ומהירים.
    """
    m = TrapManager()
    http = m.get_trap("http")
    ftp = m.get_trap("ftp")

    # לנטרל IO של לוגים בטסטים
    if hasattr(http, "_append_log_line"):
        monkeypatch.setattr(http, "_append_log_line", lambda *_: None, raising=False)
    if hasattr(ftp, "_append_log_line"):
        monkeypatch.setattr(ftp, "_append_log_line", lambda *_: None, raising=False)

    return m


def _assert_common(result: dict, trap_type: str, ip: str, input_data: str | None):
    # כל הטראפים שלכם מחזירים דיקט "עטוף" עם המפתחות הבאים
    assert isinstance(result, dict)
    assert result["trap_type"] == trap_type
    assert result["ip"] == ip
    assert result["input"] == input_data
    assert isinstance(result["timestamp"], int)
    # חותמת זמן "סבירה" (לא עתידית ב- > 5 שניות)
    assert result["timestamp"] <= int(time.time()) + 5
    assert "protocol" in result and isinstance(result["protocol"], str)
    assert "data" in result and isinstance(result["data"], dict)


# ---------- בדיקות כלליות על המנהל ----------

def test_list_traps_contains_expected(manager):
    traps = set(manager.list_traps())
    # לפי ה-__init__ שלכם יש שלושה טראפים
    assert {"http", "ftp", "ssh"}.issubset(traps)


def test_get_trap_returns_instances(manager):
    assert manager.get_trap("http") is not None
    assert manager.get_trap("ftp") is not None
    assert manager.get_trap("ssh") is not None
    assert manager.get_trap("not_exists") is None


def test_run_unknown_trap_raises_keyerror(manager):
    with pytest.raises(KeyError):
        manager.run_trap("doesnt_exist", input_data="ping", ip="1.2.3.4")


# ---------- HTTPTrap ----------

def test_http_get_root_ok(manager):
    ip = "127.0.0.10"
    res = manager.run_trap("http", input_data="GET /", ip=ip)
    _assert_common(res, "http", ip, "GET /")
    assert res["protocol"] == "HTTP"
    assert res["data"]["status"] == 200
    assert "Welcome" in res["data"]["body"]
    assert res["data"]["content_type"] == "text/html"


def test_http_post_login(manager):
    ip = "127.0.0.11"
    payload = "POST /login\nuser=admin&pass=123456"
    res = manager.run_trap("http", input_data=payload, ip=ip)
    _assert_common(res, "http", ip, payload)
    assert res["data"]["status"] == 200  # במסלולים מוגדר 200 אם יש התאמה
    assert "Invalid credentials" in res["data"]["body"]


def test_http_unknown_path_404(manager):
    ip = "127.0.0.12"
    res = manager.run_trap("http", input_data="GET /no_such_path", ip=ip)
    _assert_common(res, "http", ip, "GET /no_such_path")
    assert res["data"]["status"] == 404
    assert "<h1>404</h1>" in res["data"]["body"]


# ---------- FTPTrap ----------

def test_ftp_user_requires_pass(manager):
    ip = "10.0.0.5"
    res = manager.run_trap("ftp", input_data="USER anonymous", ip=ip)
    _assert_common(res, "ftp", ip, "USER anonymous")
    assert res["protocol"] == "FTP"
    assert res["data"]["status"] == "ok"
    assert "331" in res["data"]["response"]  # 331 User name okay, need password.


def test_ftp_list_response(manager):
    ip = "10.0.0.6"
    res = manager.run_trap("ftp", input_data="LIST", ip=ip)
    _assert_common(res, "ftp", ip, "LIST")
    body = res["data"]["response"]
    assert "150 Opening ASCII mode data connection" in body
    assert "secret.txt" in body


def test_ftp_unknown_command(manager):
    ip = "10.0.0.7"
    res = manager.run_trap("ftp", input_data="NOPE", ip=ip)
    _assert_common(res, "ftp", ip, "NOPE")
    assert res["data"]["response"] == "502 Command not implemented."


# ---------- SshTrap ----------

def test_ssh_returns_wrapped_dict(manager):
    ip = "192.168.1.30"
    inp = "ls -la /root"
    res = manager.run_trap("ssh", input_data=inp, ip=ip)

    # בדיקות כלליות
    _assert_common(res, "ssh", ip, inp)

    # פרוטוקול מהטראפ
    assert res["protocol"] == "SSH"

    # בודקים שהתוצאה מכילה לוג בפורמט החדש (CSV)
    assert "data" in res
    assert "log" in res["data"]

    log_line = res["data"]["log"]
    assert "ssh" in log_line
    assert ip in log_line
    assert inp in log_line




# ---------- בדיקות עקביות/מעטפת ----------

def test_manager_does_not_double_wrap_when_trap_returns_full_envelope(manager):
    """
    לפי TrapManager.run_trap: אם המלכודת כבר מחזירה דיקט עם המפתחות
    {'trap_type', 'protocol', 'timestamp'} – המנהל מחזיר כמו שזה.
    נבדוק שאין מפתח 'result' נוסף.
    """
    res = manager.run_trap("http", input_data="GET /api/health", ip="8.8.8.8")
    assert "result" not in res
    assert res["trap_type"] == "http"
    assert res["protocol"] == "HTTP"


def test_timestamp_is_recent(manager):
    start = int(time.time())
    res = manager.run_trap("http", input_data="GET /", ip="1.1.1.1")
    ts = res["timestamp"]
    now = int(time.time())
    assert start - 2 <= ts <= now + 2


LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "honeypot.log"

def clear_log():
    if LOG_PATH.exists():
        LOG_PATH.write_text("")

def test_phishing_trap_saves_credentials():
    clear_log()
    trap = PhishingTrap()
    trap.simulate_interaction("giladb", "1234", "127.0.0.1")

    content = LOG_PATH.read_text()
    assert "giladb" in content
    assert "1234" in content
    assert "127.0.0.1" in content

def test_phishing_trap_missing_data():
    clear_log()
    trap = PhishingTrap()
    trap.simulate_interaction("", "", "127.0.0.1")

    content = LOG_PATH.read_text()
    # לא אמור להישמר משתמש ריק
    assert "username': ''" not in content


# ---------- OpenPortsTrap ----------

@pytest.fixture
def trap():
    return OpenPortsTrap()

def test_known_port_recognized(trap):
    # Known port (e.g., 22)
    result = trap.simulate_interaction({"port": 22}, "127.0.0.1")
    assert result["data"]["port"] == 22
    assert result["data"]["service_guess"] != "unknown"
    assert "SSH" in result["data"]["service_guess"] or "FTP" in result["data"]["service_guess"] or "HTTP" in result["data"]["service_guess"]

def test_unknown_port_flagged(trap):
    # Unknown port (e.g., 9999)
    result = trap.simulate_interaction({"port": 9999}, "127.0.0.1")
    assert result["data"]["port"] == 9999
    assert result["data"]["service_guess"] == "unknown"
