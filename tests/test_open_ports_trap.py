# FILE: tests/test_open_ports_trap.py
from pathlib import Path
from model.open_ports_trap import OpenPortsTrap

def test_open_ports_run_returns_banner_and_logs(tmp_path, monkeypatch):
    # נגדיר נתיב לוג זמני
    log_file = tmp_path / "open_ports_honeypot.log"

    # נעקוף את _append_log_line כך שיכתוב ל-log_file במקום לקבוע
    def fake_append_log_line(self, line: str):
        log_file.write_text(line, encoding="utf-8")
    monkeypatch.setattr(OpenPortsTrap, "_append_log_line", fake_append_log_line)

    # הרצת המלכודת
    trap = OpenPortsTrap()
    out = trap.run("TEST-OPEN", "10.0.0.9")

    # --- בדיקות על הפלט ---
    assert out["trap_type"] == "open_ports"
    assert out["protocol"] == "TCP"
    assert "data" in out
    assert "banner" in out["data"]
    assert out["data"]["banner"].startswith("Fake Open Port Service Banner")

    # --- בדיקות על הלוג ---
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "type=open_ports" in log_text
    assert "ip=10.0.0.9" in log_text
    assert "TEST-OPEN" in log_text
    assert "Fake Open Port Service Banner" in log_text
