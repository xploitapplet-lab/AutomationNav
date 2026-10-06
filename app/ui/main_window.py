from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.browser import BrowserThread, is_http_url
from app.credentials import WindowsCredentialStore
from app.sites.flaticon import (
    BASE_URL,
    CREDENTIAL_TARGET,
    SITE_NAME,
)

LOGGER = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._browser_thread: BrowserThread | None = None
        self._credential_store: WindowsCredentialStore | None = None

        self.setWindowTitle("AutomationNav")
        self.setMinimumSize(760, 500)
        self.resize(900, 590)

        container = QWidget(self)
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("AutomationNav")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        root.addWidget(title)

        subtitle = QLabel(
            "Crea y ejecuta automatizaciones web desde una interfaz de Windows."
        )
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.site_combo = QComboBox()
        self.site_combo.addItem(SITE_NAME)

        self.url_input = QLineEdit(BASE_URL)
        self.url_input.setClearButtonEnabled(True)

        self.action_combo = QComboBox()
        self.action_combo.addItem("Abrir sitio", "open")
        self.action_combo.addItem("Iniciar sesión", "flaticon_login")
        self.action_combo.addItem(
            "Grabar automatización (próxima etapa)",
            "recorder",
        )

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@ejemplo.com")
        self.email_input.setClearButtonEnabled(True)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Contraseña")

        self.save_credentials = QCheckBox(
            "Guardar en Windows Credential Manager después de un login correcto"
        )

        form.addRow("Sitio:", self.site_combo)
        form.addRow("URL:", self.url_input)
        form.addRow("Acción:", self.action_combo)
        form.addRow("Correo:", self.email_input)
        form.addRow("Contraseña:", self.password_input)
        form.addRow("", self.save_credentials)
        root.addLayout(form)

        credential_buttons = QHBoxLayout()
        self.load_credential_button = QPushButton("Cargar credencial")
        self.delete_credential_button = QPushButton("Eliminar credencial guardada")
        self.load_credential_button.clicked.connect(self._load_saved_credential)
        self.delete_credential_button.clicked.connect(self._delete_saved_credential)
        credential_buttons.addWidget(self.load_credential_button)
        credential_buttons.addWidget(self.delete_credential_button)
        credential_buttons.addStretch(1)
        root.addLayout(credential_buttons)

        buttons = QHBoxLayout()
        self.run_button = QPushButton("Ejecutar")
        self.stop_button = QPushButton("Detener")
        self.stop_button.setEnabled(False)

        self.run_button.clicked.connect(self._run)
        self.stop_button.clicked.connect(self._stop_browser)

        buttons.addWidget(self.run_button)
        buttons.addWidget(self.stop_button)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self.status_label = QLabel("Estado: listo.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "padding: 12px; border: 1px solid #cfcfcf; border-radius: 6px;"
        )
        root.addWidget(self.status_label)
        root.addStretch(1)

        footer = QLabel(
            "Flaticon usa actualmente el proveedor de identidad de Magnific. "
            "Las credenciales guardadas permanecen en Windows, no en Git."
        )
        footer.setWordWrap(True)
        footer.setStyleSheet("color: #666;")
        root.addWidget(footer)

        self.setCentralWidget(container)
        self._initialize_credential_store()
        self._load_saved_credential(silent=True)

    def _initialize_credential_store(self) -> None:
        try:
            self._credential_store = WindowsCredentialStore()
        except OSError:
            LOGGER.exception("Windows Credential Manager no está disponible")
            self._credential_store = None
            self.save_credentials.setEnabled(False)
            self.load_credential_button.setEnabled(False)
            self.delete_credential_button.setEnabled(False)

    def _run(self) -> None:
        action = self.action_combo.currentData()

        if action == "recorder":
            QMessageBox.information(
                self,
                "AutomationNav",
                "El grabador corresponde a la siguiente etapa.",
            )
            return

        if self._browser_thread and self._browser_thread.isRunning():
            QMessageBox.information(
                self,
                "AutomationNav",
                "Ya existe una sesión de navegador activa.",
            )
            return

        url = self.url_input.text().strip()
        if not is_http_url(url):
            QMessageBox.warning(
                self,
                "URL inválida",
                "Introduce una URL http:// o https:// válida.",
            )
            return

        username = ""
        password = ""

        if action == "flaticon_login":
            username = self.email_input.text().strip()
            password = self.password_input.text()

            if not username or not password:
                QMessageBox.warning(
                    self,
                    "Credenciales",
                    "Introduce correo y contraseña antes de iniciar sesión.",
                )
                return

        self._browser_thread = BrowserThread(
            url=url,
            action=action,
            username=username,
            password=password,
            parent=self,
        )
        self._browser_thread.status_changed.connect(self._set_status)
        self._browser_thread.browser_failed.connect(self._browser_failed)
        self._browser_thread.browser_closed.connect(self._browser_closed)
        self._browser_thread.login_succeeded.connect(self._login_succeeded)
        self._browser_thread.manual_action_required.connect(
            self._manual_action_required
        )

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._browser_thread.start()

    def _set_status(self, message: str) -> None:
        self.status_label.setText(f"Estado: {message}")

    def _browser_failed(self, message: str) -> None:
        self.status_label.setText("Estado: error durante la automatización.")
        QMessageBox.critical(
            self,
            "Error de automatización",
            "AutomationNav encontró un problema.\n\n"
            f"Detalle: {message}",
        )

    def _browser_closed(self) -> None:
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if not self.status_label.text().startswith("Estado: inicio de sesión"):
            self.status_label.setText("Estado: navegador cerrado.")

    def _login_succeeded(self, final_url: str) -> None:
        self.status_label.setText(
            f"Estado: inicio de sesión confirmado. Destino: {final_url}"
        )

        if not self.save_credentials.isChecked():
            return

        if self._credential_store is None:
            QMessageBox.warning(
                self,
                "Credenciales",
                "El login fue correcto, pero Windows Credential Manager "
                "no está disponible.",
            )
            return

        try:
            self._credential_store.write(
                CREDENTIAL_TARGET,
                self.email_input.text().strip(),
                self.password_input.text(),
            )
        except OSError as exc:
            LOGGER.exception("No se pudo guardar la credencial")
            QMessageBox.warning(
                self,
                "Credenciales",
                f"El login fue correcto, pero no se pudo guardar la credencial.\n\n{exc}",
            )
        else:
            self.status_label.setText(
                "Estado: inicio de sesión confirmado y credencial guardada en Windows."
            )

    def _manual_action_required(self, message: str) -> None:
        self.status_label.setText(f"Estado: {message}")
        QMessageBox.information(
            self,
            "Verificación manual",
            message,
        )

    def _load_saved_credential(self, checked: bool = False, silent: bool = False) -> None:
        del checked

        if self._credential_store is None:
            return

        try:
            credential = self._credential_store.read(CREDENTIAL_TARGET)
        except OSError as exc:
            LOGGER.exception("No se pudo cargar la credencial")
            if not silent:
                QMessageBox.warning(
                    self,
                    "Credenciales",
                    f"No se pudo leer Windows Credential Manager.\n\n{exc}",
                )
            return

        if credential is None:
            if not silent:
                QMessageBox.information(
                    self,
                    "Credenciales",
                    "No hay una credencial guardada para Flaticon.",
                )
            return

        self.email_input.setText(credential.username)
        self.password_input.setText(credential.password)
        self.save_credentials.setChecked(True)

        if not silent:
            self.status_label.setText(
                "Estado: credencial cargada desde Windows Credential Manager."
            )

    def _delete_saved_credential(self) -> None:
        if self._credential_store is None:
            return

        try:
            deleted = self._credential_store.delete(CREDENTIAL_TARGET)
        except OSError as exc:
            LOGGER.exception("No se pudo eliminar la credencial")
            QMessageBox.warning(
                self,
                "Credenciales",
                f"No se pudo eliminar la credencial.\n\n{exc}",
            )
            return

        self.password_input.clear()

        if deleted:
            self.status_label.setText(
                "Estado: credencial de Flaticon eliminada de Windows."
            )
        else:
            self.status_label.setText(
                "Estado: no había una credencial guardada para Flaticon."
            )

    def _stop_browser(self) -> None:
        if self._browser_thread and self._browser_thread.isRunning():
            self._browser_thread.request_stop()
            self.status_label.setText("Estado: solicitando cierre...")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._browser_thread and self._browser_thread.isRunning():
            self._browser_thread.request_stop()
            self._browser_thread.wait(5_000)

        event.accept()
