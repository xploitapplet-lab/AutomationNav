from app.sites.flaticon import is_identity_provider_url


def test_identifies_current_flaticon_identity_provider() -> None:
    assert is_identity_provider_url(
        "https://id.magnific.com/v2/log-in?client_id=flaticon_es&lang=es"
    )


def test_rejects_flaticon_as_identity_provider() -> None:
    assert not is_identity_provider_url("https://www.flaticon.es/")
