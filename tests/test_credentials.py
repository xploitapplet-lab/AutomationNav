from app.credentials.windows_credential import credential_target


def test_credential_target_is_namespaced() -> None:
    assert credential_target("Flaticon") == "AutomationNav:Flaticon"
