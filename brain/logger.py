"""Logger structuré JSON avec rotation fichier + stderr/stdout."""
import json
import sys
import time
import os
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
_LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
_LOG_LEVEL = _LOG_LEVELS.get(os.environ.get("WFGY_LOG_LEVEL", "INFO").upper(), 20)

class Logger:
    def __init__(self, name: str):
        self.name = name
        self._file = None

    def _ensure_file(self):
        if self._file is None:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOG_DIR / f"wfgy_{time.strftime('%Y%m%d')}.log"
            self._file = open(log_path, "a", encoding="utf-8")
        return self._file

    def _log(self, level: str, message: str, **extra):
        if _LOG_LEVELS.get(level, 0) < _LOG_LEVEL:
            return
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level,
            "logger": self.name,
            "message": message,
        }
        if extra:
            # Filtrer les secrets des logs
            safe_extra = {k: ("***" if "pass" in k.lower() or "secret" in k.lower() or "token" in k.lower() else v) for k, v in extra.items()}
            record.update(safe_extra)
        line = json.dumps(record, ensure_ascii=False)

        # Écrire dans le fichier de log
        try:
            f = self._ensure_file()
            f.write(line + "\n")
            f.flush()
        except Exception:
            pass

        # Écrire sur stderr (tous les niveaux), stdout réservé aux données
        sys.stderr.write(line + "\n")
        sys.stderr.flush()

    def debug(self, msg, **kw): self._log("DEBUG", msg, **kw)
    def info(self, msg, **kw): self._log("INFO", msg, **kw)
    def warning(self, msg, **kw): self._log("WARNING", msg, **kw)
    def error(self, msg, **kw): self._log("ERROR", msg, **kw)
    def critical(self, msg, **kw): self._log("CRITICAL", msg, **kw)

log = Logger("wfgy")
