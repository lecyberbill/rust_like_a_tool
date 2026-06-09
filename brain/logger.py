import json
import sys
import time
import traceback
from pathlib import Path

_LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
_LOG_LEVEL = _LOG_LEVELS.get(Path(sys.argv[0]).stem.upper() if len(sys.argv) > 0 else "INFO", 20)

class Logger:
    def __init__(self, name: str):
        self.name = name

    def _log(self, level: str, message: str, **extra):
        if _LOG_LEVELS.get(level, 0) < _LOG_LEVEL:
            return
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "level": level,
            "logger": self.name,
            "message": message,
            **extra
        }
        if level in ("ERROR", "CRITICAL"):
            sys.stderr.write(json.dumps(record, ensure_ascii=False) + "\n")
            sys.stderr.flush()
        else:
            sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    def debug(self, msg, **kw): self._log("DEBUG", msg, **kw)
    def info(self, msg, **kw): self._log("INFO", msg, **kw)
    def warning(self, msg, **kw): self._log("WARNING", msg, **kw)
    def error(self, msg, **kw): self._log("ERROR", msg, **kw)
    def critical(self, msg, **kw): self._log("CRITICAL", msg, **kw)

log = Logger("wfgy")
