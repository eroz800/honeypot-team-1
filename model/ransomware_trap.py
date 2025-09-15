
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
import time
from typing import List, Dict
from .trap import Trap


BASE_DIR = Path(__file__).resolve().parents[1]
BAIT_DIR = BASE_DIR / "bait_files"
LOG_FILE = BASE_DIR / "logs" / "ransomware_honeypot.log"

@dataclass
class RansomwareTrap(Trap):
    """
    סימולציית 'כופרה' בטוחה:
    - עוברת על תיקיית bait_files/
    - משנה שם קבצים לסיומת .locked (שינוי שם בלבד)
    - יוצרת README.txt עם 'דרישת כופר'
    - רושמת כל שינוי לקובץ לוג ייעודי
    """
    name: str = "ransomware"   

    
    def get_protocol(self) -> str:
        return "FILE"

    def get_type(self) -> str:
        return "ransomware"

    # API עיקרי להפעלה 
    def simulate_interaction(self, input_data: str, ip: str) -> Dict:
        bait_dir = BAIT_DIR
        bait_dir.mkdir(parents=True, exist_ok=True)

        
        self._ensure_sample_bait_files(bait_dir)

        
        changed: List[str] = []
        for p in bait_dir.iterdir():
            if p.is_file() and not p.name.endswith(".locked") and p.name != "README.txt":
                locked = p.with_suffix(p.suffix + ".locked")
                p.rename(locked)
                changed.append(locked.name)
                self._append_log_line(self._format_log(ip, f"lock:{p.name} -> {locked.name}"))

        
        note_path = bait_dir / "README.txt"
        self._write_ransom_note(note_path)

        # לוג מסכם
        self._append_log_line(
            self._format_log(ip, f"summary: changed={len(changed)} note={note_path.name}")
        )

        return {
            "trap_type": self.get_type(),
            "protocol": self.get_protocol(),
            "ip": ip,
            "input": input_data,
            "timestamp": int(time.time()),
            "data": {
                "changed_count": len(changed),
                "changed_files": changed,
                "note": str(note_path.relative_to(BASE_DIR))
            }
        }

    # כדי לעבוד חלק עם TrapManager
    def run(self, input_data: str, ip: str):
        return self.simulate_interaction(input_data, ip)

    # יצירת פיתיונות בסיסיים אם חסרים
    def _ensure_sample_bait_files(self, bait_dir: Path) -> None:
        samples = [
            bait_dir / "invoice_2025.pdf",
            bait_dir / "resume.docx",
        ]
        for f in samples:
            if not (f.exists() or f.with_suffix(f.suffix + ".locked").exists()):
                f.write_text("BAIT FILE\n", encoding="utf-8")

    
    def _write_ransom_note(self, note_path: Path) -> None:
        if not note_path.exists():
            note = (
                "Your files have been locked.\n"
                "To recover them, send 1 BTC to 1FAKEADDRESS...\n"
                "This is a HONEYPOT SIMULATION — no real encryption was performed.\n"
            )
            note_path.write_text(note, encoding="utf-8")

    # עזרי לוג 
    def _format_log(self, ip: str, message: str) -> str:
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        message = (message or "").replace("\n", "\\n")[:500]
        return f'{ts} | protocol=FILE | type=ransomware | ip={ip} | action="{message}"\n'

    def _append_log_line(self, line: str) -> None:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.open("a", encoding="utf-8").write(line)


if __name__ == "__main__":
    t = RansomwareTrap()
    print(t.run("SIMULATE", "127.0.0.1"))
