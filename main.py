from __future__ import annotations

import ctypes
import logging
import traceback
from datetime import datetime

from app.core.logging_config import configure_logging
from app.core.paths import log_dir
from app.database.db import initialize_database
from app.ui.main_window import MainWindow

LOGGER = logging.getLogger(__name__)


def _report_startup_error() -> None:
    detail = traceback.format_exc()

    try:
        path = log_dir() / "startup_error.log"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n[{datetime.now().isoformat(timespec='seconds')}] "
                "Error al iniciar AutomationNav\n"
            )
            handle.write(detail)
            handle.write("\n")
    except Exception:
        pass

    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "AutomationNav no pudo iniciar.\n\n"
            "Se guardó el detalle en:\n"
            "%LOCALAPPDATA%\\AutomationNav\\logs\\startup_error.log",
            "AutomationNav - Error de inicio",
            0x10,
        )
    except Exception:
        pass


def main() -> int:
    try:
        configure_logging()
        initialize_database()
        window = MainWindow()
        window.run()
        return 0
    except Exception:
        LOGGER.exception("Error fatal durante el inicio de AutomationNav")
        _report_startup_error()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
