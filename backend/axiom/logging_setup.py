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


def setup_logging(level: str = "DEBUG") -> logging.Logger:
    logger = logging.getLogger("apex")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level))
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level))
    return logger


log = setup_logging()
