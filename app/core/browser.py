from __future__ import annotations

import logging
import threading
from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

LOGGER = logging.getLogger(__name__)


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


class BrowserThread(QThread):
    status_changed = Signal(str)
    browser_closed = Signal()
    browser_failed = Signal(str)

    def __init__(self, url: str, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        browser = None
        try:
            self.status_changed.emit("Iniciando Microsoft Edge...")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    channel="msedge",
                    headless=False,
                )
                context = browser.new_context()
                page = context.new_page()

                self.status_changed.emit("Abriendo sitio...")
                page.goto(self.url, wait_until="domcontentloaded", timeout=45_000)
                self.status_changed.emit("Sitio abierto. Navegador en modo visible.")

                while not self._stop_event.wait(0.25):
                    if page.is_closed():
                        break

                self.status_changed.emit("Cerrando navegador...")

        except PlaywrightError as exc:
            LOGGER.exception("Error de Playwright")
            self.browser_failed.emit(str(exc))
        except Exception as exc:
            LOGGER.exception("Error inesperado del navegador")
            self.browser_failed.emit(str(exc))
        finally:
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    LOGGER.exception("No se pudo cerrar el navegador limpiamente")

            self.browser_closed.emit()
