from app.core.browser import is_cookie_consent_text, is_http_url


def test_accepts_https_url() -> None:
    assert is_http_url("https://www.flaticon.es/")


def test_rejects_invalid_url() -> None:
    assert not is_http_url("flaticon")


def test_cookie_consent_text_in_spanish() -> None:
    assert is_cookie_consent_text("Aceptar todas")


def test_cookie_consent_text_in_english() -> None:
    assert is_cookie_consent_text("Accept all")


def test_non_cookie_action_is_not_consent() -> None:
    assert not is_cookie_consent_text("Iniciar sesión")
