from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from ctypes import wintypes

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168


@dataclass(frozen=True, slots=True)
class StoredCredential:
    username: str
    password: str


def credential_target(site_name: str) -> str:
    normalized = site_name.strip() or "Unknown"
    return f"AutomationNav:{normalized}"


class CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


PCREDENTIALW = ctypes.POINTER(CREDENTIALW)


class WindowsCredentialStore:
    """Stores credentials in Windows Credential Manager for the current user."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("Windows Credential Manager solo está disponible en Windows.")

        self._advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)

        self._cred_write = self._advapi32.CredWriteW
        self._cred_write.argtypes = [PCREDENTIALW, wintypes.DWORD]
        self._cred_write.restype = wintypes.BOOL

        self._cred_read = self._advapi32.CredReadW
        self._cred_read.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(PCREDENTIALW),
        ]
        self._cred_read.restype = wintypes.BOOL

        self._cred_delete = self._advapi32.CredDeleteW
        self._cred_delete.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self._cred_delete.restype = wintypes.BOOL

        self._cred_free = self._advapi32.CredFree
        self._cred_free.argtypes = [ctypes.c_void_p]
        self._cred_free.restype = None

    def write(self, target: str, username: str, password: str) -> None:
        if not target.strip():
            raise ValueError("El target de credencial no puede estar vacío.")
        if not username.strip():
            raise ValueError("El usuario no puede estar vacío.")

        password_bytes = password.encode("utf-16-le")
        blob = (wintypes.BYTE * len(password_bytes)).from_buffer_copy(password_bytes)

        credential = CREDENTIALW()
        credential.Flags = 0
        credential.Type = CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.Comment = "Credencial administrada por AutomationNav"
        credential.CredentialBlobSize = len(password_bytes)
        credential.CredentialBlob = ctypes.cast(
            blob,
            ctypes.POINTER(wintypes.BYTE),
        )
        credential.Persist = CRED_PERSIST_LOCAL_MACHINE
        credential.AttributeCount = 0
        credential.Attributes = None
        credential.TargetAlias = None
        credential.UserName = username

        if not self._cred_write(ctypes.byref(credential), 0):
            error = ctypes.get_last_error()
            raise OSError(error, ctypes.FormatError(error))

    def read(self, target: str) -> StoredCredential | None:
        pointer = PCREDENTIALW()

        if not self._cred_read(
            target,
            CRED_TYPE_GENERIC,
            0,
            ctypes.byref(pointer),
        ):
            error = ctypes.get_last_error()
            if error == ERROR_NOT_FOUND:
                return None
            raise OSError(error, ctypes.FormatError(error))

        try:
            credential = pointer.contents
            username = credential.UserName or ""

            if credential.CredentialBlobSize:
                raw = ctypes.string_at(
                    credential.CredentialBlob,
                    credential.CredentialBlobSize,
                )
                password = raw.decode("utf-16-le")
            else:
                password = ""

            return StoredCredential(username=username, password=password)
        finally:
            self._cred_free(pointer)

    def delete(self, target: str) -> bool:
        if self._cred_delete(target, CRED_TYPE_GENERIC, 0):
            return True

        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return False

        raise OSError(error, ctypes.FormatError(error))
