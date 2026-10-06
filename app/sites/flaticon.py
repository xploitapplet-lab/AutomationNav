from __future__ import annotations

from urllib.parse import urlparse

SITE_NAME = "Flaticon"
BASE_URL = "https://www.flaticon.es/"
LOGIN_URL = "https://id.magnific.com/v2/log-in?client_id=flaticon_es&lang=es"
CREDENTIAL_TARGET = "AutomationNav:Flaticon"


def is_identity_provider_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False

    return hostname == "id.magnific.com"
