import logging
import sys
import io

# Reconfigure stdout and stderr to support UTF-8 on Windows command prompts, avoiding UnicodeEncodeErrors
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
DATE_FORMAT = "%H:%M:%S"


class TelemetryLogFilter(logging.Filter):
    """Enrichit les logs avec le trace_id si une trace OpenInference est en cours."""
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            try:
                from axiom.core.telemetry import tracer
                tid = tracer.get_current_trace_id()
                record.trace_id = f"[{tid[:10]}] " if tid else ""
            except Exception:
                record.trace_id = ""
        return True


def setup_logging(level: str = "DEBUG") -> logging.Logger:
    logger = logging.getLogger("apex")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level))
        handler.addFilter(TelemetryLogFilter())
        formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(trace_id)s%(message)s", datefmt=DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level))
    return logger


log = setup_logging()
