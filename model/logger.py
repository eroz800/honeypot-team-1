
from __future__ import annotations
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


BASE_DIR = Path(__file__).resolve().parents[1]


LOG_DIR = Path(os.getenv("HONEY_LOG_DIR", str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "honeypot.log"


def _to_json_string(data: Any) -> str:
    """
    הופך כל אובייקט למחרוזת JSON כדי שלא יישברו רווחים/פסיקים בשורת ה-CSV.
    אם לא מצליח -> str(data).
    """
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return str(data)


def log_interaction(trap_type: str, ip: Optional[str], input_data: Any) -> None:
    """
    רושם שורת לוג בפורמט CSV:
    <UTC ISO timestamp>, <trap_type>, <ip>, <input_json>
    """
    
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    safe_ip = ip or "unknown"
    input_str = _to_json_string(input_data)

    log_line = f"{timestamp}, {trap_type}, {safe_ip}, {input_str}\n"

    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    
    print(log_line.strip())


def get_log_path() -> str:
    """פונקציית עזר: מחזירה את הנתיב המלא לקובץ הלוג (שימושי ל-report_generator)."""
    return str(LOG_FILE)
