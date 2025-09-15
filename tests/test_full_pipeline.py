import pytest
from model.trap_manager import TrapManager
from model.report_generator import generate_report
from pathlib import Path
import re

HTTP_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "http_honeypot.log"
FTP_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "ftp_honeypot.log"
SSH_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "ssh_honeypot.log"
OPENPORTS_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "open_ports_honeypot.log"
REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "summary.html"

# Helper to clear logs
def clear_logs():
    for log_path in [HTTP_LOG_PATH, FTP_LOG_PATH, SSH_LOG_PATH, OPENPORTS_LOG_PATH]:
        if log_path.exists():
            log_path.write_text("")

def test_end_to_end_pipeline_multiple_traps():
    clear_logs()
    manager = TrapManager()
    interactions = [
        ("http", "GET /", "1.2.3.4", HTTP_LOG_PATH),
        ("http", "POST /login\nuser=admin&pass=123456", "2.2.2.2", HTTP_LOG_PATH),
        ("ftp", "USER anonymous", "3.3.3.3", FTP_LOG_PATH),
        ("ftp", "LIST", "4.4.4.4", FTP_LOG_PATH),
        ("ssh", "ls -la /root", "5.5.5.5", SSH_LOG_PATH),
        ("open_ports", {"port": 22}, "6.6.6.6", OPENPORTS_LOG_PATH),
        ("open_ports", {"port": 9999}, "7.7.7.7", OPENPORTS_LOG_PATH),
    ]
    # Simulate all interactions
    for trap_type, input_data, ip, _ in interactions:
        manager.run_trap(trap_type, input_data=input_data, ip=ip)
    # Verify all log entries
    for trap_type, input_data, ip, log_path in interactions:
        log_content = log_path.read_text()
        assert ip in log_content
        if isinstance(input_data, dict):
            assert str(input_data["port"]) in log_content
        else:
            assert str(input_data).split()[0] in log_content
    # Generate report 
    generate_report()
    # Assert all interactions in report
    report_content = REPORT_PATH.read_text(encoding="utf-8")
    for trap_type, input_data, ip, log_path in interactions:
        assert ip in report_content
        if trap_type == "open_ports" and isinstance(input_data, dict):
            assert str(input_data["port"]) in report_content
            assert "open_ports" in report_content
        else:
            assert str(input_data).split()[0] in report_content
            assert trap_type in report_content
   
    assert "<table" in report_content and "<th>Timestamp</th>" in report_content
