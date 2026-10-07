from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Callable
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Locator, Page, sync_playwright

from app.sites.flaticon import LOGIN_URL, is_identity_provider_url

LOGGER = logging.getLogger(__name__)
BrowserEventCallback = Callable[[str, str], None]

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

COOKIE_ACCEPT_SELECTORS = (
    "#onetrust-accept-btn-handler",
    "button#didomi-notice-agree-button",
    "[data-testid='uc-accept-all-button']",
    "button[data-testid='accept-all']",
    "button[id*='accept' i][id*='cookie' i]",
    "button[class*='accept' i][class*='cookie' i]",
    "button[aria-label*='accept' i][aria-label*='cookie' i]",
)

COOKIE_CLOSE_SELECTORS = (
    "#close-pc-btn-handler",
    "#onetrust-pc-sdk button.ot-close-icon",
    "#onetrust-close-btn-container button",
    "button[aria-label='Cerrar']",
    "button[aria-label='Close']",
    "button[aria-label*='cerrar' i]",
    "button[aria-label*='close' i]",
)

COOKIE_OVERLAY_SELECTORS = (
    "#onetrust-pc-sdk",
    "#onetrust-banner-sdk",
    ".onetrust-pc-dark-filter",
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

EMAIL_METHOD_BUTTON = re.compile(
    r"(continuar|seguir|acceder|iniciar|usar|continue|use|sign in|log in)"
    r".*(correo|correo electrónico|email|e-mail)|"
    r"(correo|correo electrónico|email|e-mail)"
    r".*(continuar|seguir|acceder|iniciar|usar|continue|use|sign in|log in)",
    re.IGNORECASE,
)

EMAIL_LABEL = re.compile(r"(correo|email|e-mail)", re.IGNORECASE)
PASSWORD_LABEL = re.compile(r"(contraseña|password)", re.IGNORECASE)
NEXT_BUTTON = re.compile(r"^(continuar|siguiente|continue|next)$", re.IGNORECASE)
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


def is_email_method_text(value: str) -> bool:
    return bool(EMAIL_METHOD_BUTTON.search(value.strip()))


def _frames(page: Page) -> tuple[Frame, ...]:
    return tuple(page.frames)


def _visible(locator: Locator, timeout: int = 650) -> bool:
    try:
        return locator.is_visible(timeout=timeout)
    except PlaywrightError:
        return False


def _first_visible_in_frames(page: Page, selectors: tuple[str, ...]) -> Locator | None:
    for frame in _frames(page):
        for selector in selectors:
            locator = frame.locator(selector).first
            if _visible(locator):
                return locator
    return None


def _first_semantic_field(page: Page, pattern: re.Pattern[str]) -> Locator | None:
    for frame in _frames(page):
        for locator in (
            frame.get_by_label(pattern).first,
            frame.get_by_placeholder(pattern).first,
        ):
            if _visible(locator):
                return locator
    return None


def _single_text_input_candidate(page: Page) -> Locator | None:
    candidates: list[Locator] = []

    for frame in _frames(page):
        inputs = frame.locator(
            "input:not([type]), input[type='text'], input[type='email']"
        )
        try:
            count = min(inputs.count(), 30)
        except PlaywrightError:
            continue

        for index in range(count):
            locator = inputs.nth(index)
            if not _visible(locator):
                continue

            try:
                metadata = " ".join(
                    (
                        (locator.get_attribute("id") or "").lower(),
                        (locator.get_attribute("name") or "").lower(),
                        (locator.get_attribute("aria-label") or "").lower(),
                        (locator.get_attribute("placeholder") or "").lower(),
                    )
                )
            except PlaywrightError:
                continue

            if "vendor-search-handler" in metadata:
                continue
            if any(word in metadata for word in ("cookie", "búsqueda", "search")):
                continue
            candidates.append(locator)

    if len(candidates) == 1:
        LOGGER.info("Se usará el único campo de texto visible como candidato de correo.")
        return candidates[0]

    return None


def _wait_for_field(
    page: Page,
    selectors: tuple[str, ...],
    semantic_pattern: re.Pattern[str],
    timeout_seconds: float,
    allow_single_text_fallback: bool = False,
) -> Locator | None:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        locator = _first_visible_in_frames(page, selectors)
        if locator is not None:
            return locator

        locator = _first_semantic_field(page, semantic_pattern)
        if locator is not None:
            return locator

        if allow_single_text_fallback:
            locator = _single_text_input_candidate(page)
            if locator is not None:
                return locator

        page.wait_for_timeout(250)

    return None


def _first_visible_button(
    page: Page,
    pattern: re.Pattern[str],
    include_links: bool = False,
) -> Locator | None:
    roles = ("button", "link") if include_links else ("button",)

    for frame in _frames(page):
        for role in roles:
            locator = frame.get_by_role(role, name=pattern).first
            if _visible(locator):
                return locator

    if not include_links:
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


def _click_known_cookie_accept(page: Page) -> bool:
    for frame in _frames(page):
        for selector in COOKIE_ACCEPT_SELECTORS:
            locator = frame.locator(selector).first
            if not _visible(locator):
                continue
            try:
                locator.click(timeout=1_500)
                LOGGER.info("Aviso de cookies aceptado con selector conocido.")
                return True
            except PlaywrightError:
                continue
    return False


def _click_cookie_accept_by_text(page: Page) -> bool:
    for frame in _frames(page):
        context = _frame_text(frame)
        if not any(marker in context for marker in COOKIE_CONTEXT_MARKERS):
            continue

        buttons = frame.get_by_role("button")
        try:
            count = min(buttons.count(), 30)
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
                LOGGER.info("Aviso de cookies aceptado por texto: %s", text)
                return True
            except PlaywrightError:
                continue
    return False


def _close_cookie_preferences(page: Page) -> bool:
    closed = False
    for _ in range(3):
        found_visible = False
        for frame in _frames(page):
            for selector in COOKIE_CLOSE_SELECTORS:
                locator = frame.locator(selector).first
                if not _visible(locator):
                    continue
                found_visible = True
                try:
                    locator.click(timeout=1_500)
                    LOGGER.info("Centro de preferencias de cookies cerrado con %s.", selector)
                    closed = True
                    page.wait_for_timeout(300)
                except PlaywrightError:
                    continue
        if not found_visible:
            break
    return closed


def _cookie_overlay_visible(page: Page) -> bool:
    return _first_visible_in_frames(page, COOKIE_OVERLAY_SELECTORS) is not None


def _dismiss_cookie_consent(page: Page) -> bool:
    accepted = False
    for _ in range(3):
        if _click_known_cookie_accept(page) or _click_cookie_accept_by_text(page):
            accepted = True
            page.wait_for_timeout(500)
        _close_cookie_preferences(page)
        if not _cookie_overlay_visible(page):
            break
        page.wait_for_timeout(350)
    return accepted


def _refresh_login_after_consent(page: Page) -> None:
    LOGGER.info("Recargando login después del consentimiento: %s", page.url)
    try:
        page.reload(wait_until="domcontentloaded", timeout=45_000)
    except PlaywrightError:
        LOGGER.warning("Reload falló; se volverá a navegar a LOGIN_URL.")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(1_000)
    _close_cookie_preferences(page)


def _open_email_login_method(page: Page) -> bool:
    locator = _first_visible_button(page, EMAIL_METHOD_BUTTON, include_links=True)
    if locator is None:
        return False

    try:
        label = locator.inner_text(timeout=500).strip()
    except PlaywrightError:
        label = ""

    try:
        locator.click(timeout=2_000)
    except PlaywrightError:
        return False

    LOGGER.info("Método de acceso por correo abierto%s.", f": {label}" if label else "")
    page.wait_for_timeout(700)
    return True


def _log_login_diagnostics(page: Page, stage: str) -> None:
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
        LOGGER.error("Frame %d | url=%s", frame_index, frame.url)

        inputs = frame.locator("input")
        try:
            input_count = min(inputs.count(), 30)
        except PlaywrightError:
            input_count = 0

        for input_index in range(input_count):
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

        buttons = frame.get_by_role("button")
        try:
            button_count = min(buttons.count(), 30)
        except PlaywrightError:
            button_count = 0

        for button_index in range(button_count):
            button = buttons.nth(button_index)
            if not _visible(button, timeout=250):
                continue
            try:
                text = button.inner_text(timeout=300).strip()
            except PlaywrightError:
                text = "<sin texto>"
            LOGGER.error(
                "Button frame=%d index=%d text=%r",
                frame_index,
                button_index,
                text[:150],
            )


class BrowserWorker(threading.Thread):
    def __init__(
        self,
        url: str,
        action: str = "open",
        username: str = "",
        password: str = "",
        event_callback: BrowserEventCallback | None = None,
    ) -> None:
        super().__init__(daemon=True)
        self.url = url
        self.action = action
        self.username = username
        self.password = password
        self._event_callback = event_callback
        self._stop_event = threading.Event()

    def _emit(self, event_type: str, message: str = "") -> None:
        if self._event_callback is not None:
            self._event_callback(event_type, message)

    def request_stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        try:
            self._emit("status", "Iniciando Microsoft Edge...")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge", headless=False)
                try:
                    context = browser.new_context()
                    page = context.new_page()

                    if self.action == "flaticon_login":
                        self._run_flaticon_login(page)
                    else:
                        self._open_page(page, self.url)

                    while not self._stop_event.wait(0.25):
                        if page.is_closed():
                            break

                    if not page.is_closed():
                        self._emit("status", "Cerrando navegador...")
                finally:
                    try:
                        browser.close()
                    except PlaywrightError as exc:
                        LOGGER.info("Navegador ya cerrado: %s", exc)

        except PlaywrightError as exc:
            if "Target page, context or browser has been closed" in str(exc):
                LOGGER.info("El usuario cerró el navegador durante la automatización.")
            else:
                LOGGER.exception("Error de Playwright")
                self._emit("failed", str(exc))
        except Exception as exc:
            LOGGER.exception("Error inesperado del navegador")
            self._emit("failed", str(exc))
        finally:
            self.password = ""
            self._emit("closed", "")

    def _open_page(self, page: Page, url: str) -> None:
        self._emit("status", "Abriendo sitio...")
        page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        self._emit("status", "Sitio abierto. Navegador en modo visible.")

    def _run_flaticon_login(self, page: Page) -> None:
        if not self.username.strip() or not self.password:
            raise RuntimeError("Faltan correo o contraseña para iniciar sesión.")

        self._emit("status", "Abriendo acceso de Flaticon...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(800)

        self._emit("status", "Comprobando aviso de cookies...")
        dismissed = _dismiss_cookie_consent(page)

        if dismissed:
            self._emit("status", "Cookies aceptadas. Recargando formulario de acceso...")
            _refresh_login_after_consent(page)
            _dismiss_cookie_consent(page)

        self._emit("status", "Buscando acceso por correo...")
        email = _wait_for_field(
            page,
            EMAIL_SELECTORS,
            EMAIL_LABEL,
            timeout_seconds=4,
            allow_single_text_fallback=True,
        )

        if email is None and _open_email_login_method(page):
            _dismiss_cookie_consent(page)
            email = _wait_for_field(
                page,
                EMAIL_SELECTORS,
                EMAIL_LABEL,
                timeout_seconds=12,
                allow_single_text_fallback=True,
            )

        if email is None:
            self._emit("status", "Reintentando carga del formulario...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(1_000)
            _dismiss_cookie_consent(page)
            _close_cookie_preferences(page)

            email = _wait_for_field(
                page,
                EMAIL_SELECTORS,
                EMAIL_LABEL,
                timeout_seconds=4,
                allow_single_text_fallback=True,
            )
            if email is None and _open_email_login_method(page):
                email = _wait_for_field(
                    page,
                    EMAIL_SELECTORS,
                    EMAIL_LABEL,
                    timeout_seconds=10,
                    allow_single_text_fallback=True,
                )

        if email is None:
            _log_login_diagnostics(page, "email_no_encontrado")
            raise RuntimeError(
                "No se encontró el acceso por correo después de cerrar cookies, "
                "recargar Magnific y revisar sus métodos de inicio de sesión. "
                "El diagnóstico detallado quedó guardado en el log."
            )

        self._emit("status", "Introduciendo correo...")
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
                self._emit("status", "Continuando al campo de contraseña...")
                next_button.click()
                page.wait_for_timeout(500)
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
                "El diagnóstico detallado quedó guardado en el log."
            )

        self._emit("status", "Introduciendo contraseña...")
        password.fill(self.password)

        _dismiss_cookie_consent(page)
        submit = _first_visible_button(page, SUBMIT_BUTTON)
        if submit is None:
            _log_login_diagnostics(page, "submit_no_encontrado")
            raise RuntimeError(
                "No se encontró el botón para iniciar sesión. "
                "El diagnóstico detallado quedó guardado en el log."
            )

        self._emit("status", "Enviando inicio de sesión...")
        submit.click()

        deadline = time.monotonic() + 60
        manual_notified = False

        while time.monotonic() < deadline and not self._stop_event.is_set():
            current_url = page.url

            if not is_identity_provider_url(current_url):
                self._emit("status", "Inicio de sesión confirmado.")
                self._emit("login_succeeded", current_url)
                return

            body = _body_text(page)
            if any(marker in body for marker in INVALID_LOGIN_MARKERS):
                raise RuntimeError(
                    "El sitio rechazó las credenciales o mostró un error de acceso."
                )

            if any(marker in body for marker in MANUAL_ACTION_MARKERS) and not manual_notified:
                manual_notified = True
                self._emit(
                    "manual_action_required",
                    "Flaticon requiere una verificación manual. "
                    "Completa el paso en Edge; AutomationNav continuará observando.",
                )

            page.wait_for_timeout(500)

        if self._stop_event.is_set():
            return

        _log_login_diagnostics(page, "confirmacion_timeout")
        raise RuntimeError(
            "No se pudo confirmar el inicio de sesión dentro del tiempo esperado."
        )
