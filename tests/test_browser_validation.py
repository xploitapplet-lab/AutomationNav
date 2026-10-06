from app.core.browser import is_http_url


def test_accepts_https_url() -> None:
    assert is_http_url("https://www.flaticon.es/")


def test_rejects_invalid_url() -> None:
    assert not is_http_url("flaticon")
