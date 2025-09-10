# FILE: tests/test_ransomware_trap.py
from pathlib import Path
from model.ransomware_trap import RansomwareTrap, BAIT_DIR, LOG_FILE

def test_ransomware_encrypts_and_writes_log():
    """
    בודק:
    1) שינוי שמות קבצים ל-.locked בתיקיית bait_files/
    2) יצירת README.txt
    3) רישום ללוג ב-logs/ransomware_honeypot.log
    (הטסט מגבה את bait_files אם היא קיימת ומשחזר בסוף)
    """
    base_dir = Path(__file__).resolve().parents[1]
    bait_dir = BAIT_DIR
    log_file = LOG_FILE
    logs_dir = log_file.parent

    # גיבוי bait_files אם קיימת
    backup_dir = None
    if bait_dir.exists():
        backup_dir = bait_dir.with_name("bait_files__backup_for_test")
        if backup_dir.exists():
            for p in backup_dir.rglob("*"):
                if p.is_file():
                    p.unlink()
            backup_dir.rmdir()
        bait_dir.rename(backup_dir)

    # יצירת bait_files נקייה
    bait_dir.mkdir(parents=True, exist_ok=True)
    (bait_dir / "a.pdf").write_text("BAIT A\n", encoding="utf-8")
    (bait_dir / "b.docx").write_text("BAIT B\n", encoding="utf-8")

    # הכנה ללוג
    logs_dir.mkdir(parents=True, exist_ok=True)
    if log_file.exists():
        log_text_before = log_file.read_text(encoding="utf-8")
    else:
        log_text_before = ""

    try:
        trap = RansomwareTrap()
        out = trap.run("TEST-RANSOM", "10.0.0.9")

        # --- בדיקות פלט ---
        assert out["trap_type"] == "ransomware"
        assert out["protocol"] == "FILE"
        assert "data" in out
        data = out["data"]
        assert data["changed_count"] >= 2
        assert any(name.endswith(".locked") for name in data["changed_files"])
        assert "README.txt" in str(data["note"])

        # --- בדיקת קבצים בפועל ---
        locked_files = {p.name for p in bait_dir.glob("*.locked")}
        assert "a.pdf.locked" in locked_files
        assert "b.docx.locked" in locked_files
        assert (bait_dir / "README.txt").exists()

        # --- בדיקת README ---
        readme_content = (bait_dir / "README.txt").read_text(encoding="utf-8").lower()
        keywords = ["ransom", "recover", "bitcoin", "כופר", "שחזור"]
        assert any(k in readme_content for k in keywords)

        # --- בדיקת לוג ---
        assert log_file.exists()
        log_text_after = log_file.read_text(encoding="utf-8")
        assert len(log_text_after) > len(log_text_before)
        assert "lock:" in log_text_after
    assert "summary:" in log_text_after

    finally:
        # ניקוי
        if bait_dir.exists():
            for p in bait_dir.iterdir():
                try:
                    p.unlink()
                except IsADirectoryError:
                    pass
            try:
                bait_dir.rmdir()
            except OSError:
                pass

        # שחזור גיבוי אם היה
        if backup_dir and backup_dir.exists():
            backup_dir.rename(bait_dir)
        else:
            bait_dir.mkdir(parents=True, exist_ok=True)
