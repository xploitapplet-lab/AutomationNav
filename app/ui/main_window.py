from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
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
from app.sites.flaticon import BASE_URL, SITE_NAME


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._browser_thread: BrowserThread | None = None

        self.setWindowTitle("AutomationNav")
        self.setMinimumSize(760, 430)
        self.resize(900, 520)

        container = QWidget(self)
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("AutomationNav")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        root.addWidget(title)

        subtitle = QLabel(
            "Base inicial para crear y ejecutar automatizaciones web."
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
        self.action_combo.addItem("Abrir sitio")
        self.action_combo.addItem("Login (próxima etapa)")
        self.action_combo.addItem("Grabar automatización (próxima etapa)")

        form.addRow("Sitio:", self.site_combo)
        form.addRow("URL:", self.url_input)
        form.addRow("Acción:", self.action_combo)
        root.addLayout(form)

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
            "Fase 01 · Navegador visible · Las credenciales no se almacenan en Git."
        )
        footer.setStyleSheet("color: #666;")
        root.addWidget(footer)

        self.setCentralWidget(container)

    def _run(self) -> None:
        action = self.action_combo.currentText()

        if action != "Abrir sitio":
            QMessageBox.information(
                self,
                "AutomationNav",
                "Esta acción corresponde a la siguiente etapa del desarrollo.",
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

        if self._browser_thread and self._browser_thread.isRunning():
            QMessageBox.information(
                self,
                "AutomationNav",
                "Ya existe una sesión de navegador activa.",
            )
            return

        self._browser_thread = BrowserThread(url, self)
        self._browser_thread.status_changed.connect(self._set_status)
        self._browser_thread.browser_failed.connect(self._browser_failed)
        self._browser_thread.browser_closed.connect(self._browser_closed)

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._browser_thread.start()

    def _set_status(self, message: str) -> None:
        self.status_label.setText(f"Estado: {message}")

    def _browser_failed(self, message: str) -> None:
        self.status_label.setText("Estado: error al abrir el navegador.")
        QMessageBox.critical(
            self,
            "Error de navegador",
            "AutomationNav no pudo controlar Microsoft Edge.\n\n"
            f"Detalle: {message}",
        )

    def _browser_closed(self) -> None:
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Estado: navegador cerrado.")

    def _stop_browser(self) -> None:
        if self._browser_thread and self._browser_thread.isRunning():
            self._browser_thread.request_stop()
            self.status_label.setText("Estado: solicitando cierre...")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._browser_thread and self._browser_thread.isRunning():
            self._browser_thread.request_stop()
            self._browser_thread.wait(5_000)

        event.accept()
