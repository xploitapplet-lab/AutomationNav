from __future__ import annotations

import logging
import re
import threading
import time
from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, sync_playwright

from app.sites.flaticon import LOGIN_URL, is_identity_provider_url

LOGGER = logging.getLogger(__name__)

EMAIL_SELECTORS = (
    "input[type='email']",
    "input[name='email']",
    "input[autocomplete='email']",
    "input[autocomplete='username']",
    "input[id*='email' i]",
)

PASSWORD_SELECTORS = (
    "input[type='password']",
    "input[name='password']",
    "input[autocomplete='current-password']",
    "input[id*='password' i]",
)

NEXT_BUTTON = re.compile(
    r"^(continuar|siguiente|continue|next)$",
    re.IGNORECASE,
)

SUBMIT_BUTTON = re.compile(
    r"(inicia sesión|iniciar sesión|acceder|entrar|log in|sign in)",
    re.IGNORECASE,
)

INVALID_LOGIN_MARKERS = (
    "contraseña incorrecta",
    "correo o contraseña",
    "credenciales incorrectas",
    "incorrect password",
    "invalid password",
    "invalid credentials",
)

MANUAL_ACTION_MARKERS = (
    "captcha",
    "verifica que eres humano",
    "verificación en dos pasos",
    "código de verificación",
    "authentication code",
    "verification code",
    "two-factor",
    "two factor",
)


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _first_visible(page: Page, selectors: tuple[str, ...]) -> Locator | None:
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=750):
                return locator
        except PlaywrightError:
            continue
    return None


def _wait_for_visible(
    page: Page,
    selectors: tuple[str, ...],
    timeout_seconds: float,
) -> Locator | None:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        locator = _first_visible(page, selectors)
        if locator is not None:
            return locator
        page.wait_for_timeout(250)

    return None


def _first_visible_button(page: Page, pattern: re.Pattern[str]) -> Locator | None:
    locator = page.get_by_role("button", name=pattern).first
    try:
        if locator.is_visible(timeout=750):
            return locator
    except PlaywrightError:
        pass

    fallback = page.locator("button[type='submit'], input[type='submit']").first
    try:
        if fallback.is_visible(timeout=750):
            return fallback
    except PlaywrightError:
        pass

    return None


def _body_text(page: Page) -> str:
    try:
        return page.locator("body").inner_text(timeout=1_500).lower()
    except PlaywrightError:
        return ""


class BrowserThread(QThread):
    status_changed = Signal(str)
    browser_closed = Signal()
    browser_failed = Signal(str)
    login_succeeded = Signal(str)
    manual_action_required = Signal(str)

    def __init__(
        self,
        url: str,
        action: str = "open",
        username: str = "",
        password: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.url = url
        self.action = action
        self.username = username
        self.password = password
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

                if self.action == "flaticon_login":
                    self._run_flaticon_login(page)
                else:
                    self._open_page(page, self.url)

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
            self.password = ""

            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    LOGGER.exception("No se pudo cerrar el navegador limpiamente")

            self.browser_closed.emit()

    def _open_page(self, page: Page, url: str) -> None:
        self.status_changed.emit("Abriendo sitio...")
        page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        self.status_changed.emit("Sitio abierto. Navegador en modo visible.")

    def _run_flaticon_login(self, page: Page) -> None:
        if not self.username.strip() or not self.password:
            raise RuntimeError("Faltan correo o contraseña para iniciar sesión.")

        self.status_changed.emit("Abriendo acceso de Flaticon...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45_000)

        email = _wait_for_visible(page, EMAIL_SELECTORS, timeout_seconds=12)
        if email is None:
            raise RuntimeError(
                "No se encontró el campo de correo. "
                "El proveedor de identidad pudo haber cambiado."
            )

        self.status_changed.emit("Introduciendo correo...")
        email.fill(self.username)

        password = _first_visible(page, PASSWORD_SELECTORS)
        if password is None:
            next_button = _first_visible_button(page, NEXT_BUTTON)
            if next_button is not None:
                self.status_changed.emit("Continuando al campo de contraseña...")
                next_button.click()
                password = _wait_for_visible(
                    page,
                    PASSWORD_SELECTORS,
                    timeout_seconds=12,
                )

        if password is None:
            raise RuntimeError(
                "No se encontró el campo de contraseña. "
                "Se guardará el diagnóstico en el log."
            )

        self.status_changed.emit("Introduciendo contraseña...")
        password.fill(self.password)

        submit = _first_visible_button(page, SUBMIT_BUTTON)
        if submit is None:
            raise RuntimeError("No se encontró el botón para iniciar sesión.")

        self.status_changed.emit("Enviando inicio de sesión...")
        submit.click()

        deadline = time.monotonic() + 60
        manual_notified = False

        while time.monotonic() < deadline and not self._stop_event.is_set():
            current_url = page.url

            if not is_identity_provider_url(current_url):
                self.status_changed.emit("Inicio de sesión confirmado.")
                self.login_succeeded.emit(current_url)
                return

            body = _body_text(page)

            if any(marker in body for marker in INVALID_LOGIN_MARKERS):
                raise RuntimeError(
                    "El sitio rechazó las credenciales o mostró un error de acceso."
                )

            if any(marker in body for marker in MANUAL_ACTION_MARKERS):
                if not manual_notified:
                    manual_notified = True
                    self.manual_action_required.emit(
                        "Flaticon requiere una verificación manual. "
                        "Completa el paso en Edge; AutomationNav continuará observando."
                    )

            page.wait_for_timeout(500)

        if self._stop_event.is_set():
            return

        raise RuntimeError(
            "No se pudo confirmar el inicio de sesión dentro del tiempo esperado."
        )
