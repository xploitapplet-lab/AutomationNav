from __future__ import annotations

import logging
import re
import threading
import time
from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Locator, Page, sync_playwright

from app.sites.flaticon import LOGIN_URL, is_identity_provider_url

LOGGER = logging.getLogger(__name__)

EMAIL_SELECTORS = (
    "input[type='email']",
    "input[name='email']",
    "input[name='username']",
    "input[autocomplete='email']",
    "input[autocomplete='username']",
    "input[id*='email' i]",
    "input[id*='correo' i]",
    "input[placeholder*='email' i]",
    "input[placeholder*='e-mail' i]",
    "input[placeholder*='correo' i]",
    "input[aria-label*='email' i]",
    "input[aria-label*='correo' i]",
)

PASSWORD_SELECTORS = (
    "input[type='password']",
    "input[name='password']",
    "input[autocomplete='current-password']",
    "input[id*='password' i]",
    "input[placeholder*='password' i]",
    "input[placeholder*='contraseña' i]",
    "input[aria-label*='password' i]",
    "input[aria-label*='contraseña' i]",
)

COOKIE_SELECTORS = (
    "#onetrust-accept-btn-handler",
    "button#didomi-notice-agree-button",
    "[data-testid='uc-accept-all-button']",
    "button[data-testid='accept-all']",
    "button[id*='accept' i][id*='cookie' i]",
    "button[class*='accept' i][class*='cookie' i]",
    "button[aria-label*='accept' i][aria-label*='cookie' i]",
)

COOKIE_CONTEXT_MARKERS = (
    "cookie",
    "cookies",
    "consent",
    "privacy",
    "privacidad",
)

COOKIE_BUTTON_TEXT = re.compile(
    r"^(aceptar(?: todo| todas| todas las cookies)?|"
    r"accept(?: all)?|allow all|agree|consentir|permitir todas|"
    r"entendido|got it)$",
    re.IGNORECASE,
)

EMAIL_LABEL = re.compile(r"(correo|email|e-mail)", re.IGNORECASE)
PASSWORD_LABEL = re.compile(r"(contraseña|password)", re.IGNORECASE)

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


def is_cookie_consent_text(value: str) -> bool:
    return bool(COOKIE_BUTTON_TEXT.fullmatch(value.strip()))


def _frames(page: Page) -> tuple[Frame, ...]:
    return tuple(page.frames)


def _visible(locator: Locator, timeout: int = 650) -> bool:
    try:
        return locator.is_visible(timeout=timeout)
    except PlaywrightError:
        return False


def _first_visible_in_frames(
    page: Page,
    selectors: tuple[str, ...],
) -> Locator | None:
    for frame in _frames(page):
        for selector in selectors:
            locator = frame.locator(selector).first
            if _visible(locator):
                return locator
    return None


def _first_semantic_field(
    page: Page,
    pattern: re.Pattern[str],
) -> Locator | None:
    for frame in _frames(page):
        for locator in (
            frame.get_by_label(pattern).first,
            frame.get_by_placeholder(pattern).first,
        ):
            if _visible(locator):
                return locator
    return None


def _wait_for_field(
    page: Page,
    selectors: tuple[str, ...],
    semantic_pattern: re.Pattern[str],
    timeout_seconds: float,
) -> Locator | None:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        locator = _first_visible_in_frames(page, selectors)
        if locator is not None:
            return locator

        locator = _first_semantic_field(page, semantic_pattern)
        if locator is not None:
            return locator

        page.wait_for_timeout(250)

    return None


def _first_visible_button(
    page: Page,
    pattern: re.Pattern[str],
) -> Locator | None:
    for frame in _frames(page):
        locator = frame.get_by_role("button", name=pattern).first
        if _visible(locator):
            return locator

    for frame in _frames(page):
        fallback = frame.locator(
            "button[type='submit'], input[type='submit']"
        ).first
        if _visible(fallback):
            return fallback

    return None


def _frame_text(frame: Frame) -> str:
    try:
        return frame.locator("body").inner_text(timeout=1_000).lower()
    except PlaywrightError:
        return ""


def _body_text(page: Page) -> str:
    return "\n".join(
        text
        for text in (_frame_text(frame) for frame in _frames(page))
        if text
    )


def _dismiss_cookie_consent(page: Page) -> bool:
    """Dismiss a visible cookie banner in the page or any iframe."""

    for _ in range(3):
        for frame in _frames(page):
            for selector in COOKIE_SELECTORS:
                locator = frame.locator(selector).first
                if not _visible(locator):
                    continue

                try:
                    locator.click(timeout=1_500)
                    page.wait_for_timeout(500)
                    LOGGER.info("Aviso de cookies cerrado con selector conocido.")
                    return True
                except PlaywrightError:
                    continue

        for frame in _frames(page):
            context = _frame_text(frame)
            if not any(marker in context for marker in COOKIE_CONTEXT_MARKERS):
                continue

            buttons = frame.get_by_role("button")
            try:
                count = min(buttons.count(), 20)
            except PlaywrightError:
                continue

            for index in range(count):
                button = buttons.nth(index)
                if not _visible(button):
                    continue

                try:
                    text = button.inner_text(timeout=500).strip()
                except PlaywrightError:
                    continue

                if not is_cookie_consent_text(text):
                    continue

                try:
                    button.click(timeout=1_500)
                    page.wait_for_timeout(500)
                    LOGGER.info(
                        "Aviso de cookies cerrado por texto de botón: %s",
                        text,
                    )
                    return True
                except PlaywrightError:
                    continue

        page.wait_for_timeout(350)

    return False


def _log_login_diagnostics(page: Page, stage: str) -> None:
    """Log structure useful for debugging without logging field values."""

    try:
        title = page.title()
    except PlaywrightError:
        title = "<no disponible>"

    LOGGER.error(
        "Diagnóstico login | etapa=%s | url=%s | titulo=%s | frames=%d",
        stage,
        page.url,
        title,
        len(page.frames),
    )

    for frame_index, frame in enumerate(_frames(page)):
        LOGGER.error(
            "Frame %d | url=%s",
            frame_index,
            frame.url,
        )

        inputs = frame.locator("input")
        try:
            count = min(inputs.count(), 20)
        except PlaywrightError:
            continue

        for input_index in range(count):
            item = inputs.nth(input_index)
            attributes: dict[str, str | None] = {}

            for attribute in (
                "type",
                "name",
                "id",
                "placeholder",
                "autocomplete",
                "aria-label",
            ):
                try:
                    attributes[attribute] = item.get_attribute(attribute)
                except PlaywrightError:
                    attributes[attribute] = None

            LOGGER.error(
                "Input frame=%d index=%d attrs=%s",
                frame_index,
                input_index,
                attributes,
            )


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
        page.wait_for_timeout(700)

        self.status_changed.emit("Comprobando aviso de cookies...")
        dismissed = _dismiss_cookie_consent(page)
        if dismissed:
            self.status_changed.emit("Cookies aceptadas. Buscando formulario...")
            page.wait_for_timeout(700)

        email = _wait_for_field(
            page,
            EMAIL_SELECTORS,
            EMAIL_LABEL,
            timeout_seconds=15,
        )
        if email is None:
            # Some consent managers render late. Give them one more pass.
            if _dismiss_cookie_consent(page):
                page.wait_for_timeout(700)
                email = _wait_for_field(
                    page,
                    EMAIL_SELECTORS,
                    EMAIL_LABEL,
                    timeout_seconds=8,
                )

        if email is None:
            _log_login_diagnostics(page, "email_no_encontrado")
            raise RuntimeError(
                "No se encontró el campo de correo después de revisar cookies, "
                "página principal e iframes. Revisa el log de AutomationNav para "
                "ver la estructura detectada."
            )

        self.status_changed.emit("Introduciendo correo...")
        email.fill(self.username)

        password = _wait_for_field(
            page,
            PASSWORD_SELECTORS,
            PASSWORD_LABEL,
            timeout_seconds=2,
        )

        if password is None:
            next_button = _first_visible_button(page, NEXT_BUTTON)
            if next_button is not None:
                self.status_changed.emit("Continuando al campo de contraseña...")
                next_button.click()
                page.wait_for_timeout(400)
                _dismiss_cookie_consent(page)
                password = _wait_for_field(
                    page,
                    PASSWORD_SELECTORS,
                    PASSWORD_LABEL,
                    timeout_seconds=15,
                )

        if password is None:
            _log_login_diagnostics(page, "password_no_encontrado")
            raise RuntimeError(
                "No se encontró el campo de contraseña. "
                "Revisa el log de AutomationNav para ver la estructura detectada."
            )

        self.status_changed.emit("Introduciendo contraseña...")
        password.fill(self.password)

        _dismiss_cookie_consent(page)
        submit = _first_visible_button(page, SUBMIT_BUTTON)
        if submit is None:
            _log_login_diagnostics(page, "submit_no_encontrado")
            raise RuntimeError(
                "No se encontró el botón para iniciar sesión. "
                "Revisa el log de AutomationNav."
            )

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

        _log_login_diagnostics(page, "confirmacion_timeout")
        raise RuntimeError(
            "No se pudo confirmar el inicio de sesión dentro del tiempo esperado."
        )
