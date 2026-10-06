from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.core.paths import log_dir


def configure_logging() -> None:
    log_file = log_dir() / "automationnav.log"

    handler = RotatingFileHandler(
        log_file,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not any(isinstance(item, RotatingFileHandler) for item in root.handlers):
        root.addHandler(handler)
