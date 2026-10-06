from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.logging_config import configure_logging
from app.database.db import initialize_database
from app.ui.main_window import MainWindow


def main() -> int:
    configure_logging()
    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName("AutomationNav")
    app.setOrganizationName("AutomationNav")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
