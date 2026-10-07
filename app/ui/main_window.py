from __future__ import annotations

import logging
import queue
import tkinter as tk
from tkinter import messagebox, ttk

from app.core.browser import BrowserWorker, is_http_url
from app.credentials import WindowsCredentialStore
from app.sites.flaticon import BASE_URL, CREDENTIAL_TARGET, SITE_NAME

LOGGER = logging.getLogger(__name__)


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("AutomationNav")
        self.root.geometry("860x560")
        self.root.minsize(720, 500)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._browser_worker: BrowserWorker | None = None
        self._credential_store: WindowsCredentialStore | None = None
        self._events: queue.Queue[tuple[str, str]] = queue.Queue()

        self.site_var = tk.StringVar(value=SITE_NAME)
        self.url_var = tk.StringVar(value=BASE_URL)
        self.action_var = tk.StringVar(value="Abrir sitio")
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.save_credentials_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Estado: listo.")

        self._build_ui()
        self._initialize_credential_store()
        self._load_saved_credential(silent=True)
        self.root.after(100, self._process_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")

        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)

        title = ttk.Label(outer, text="AutomationNav", font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        subtitle = ttk.Label(
            outer,
            text="Crea y ejecuta automatizaciones web desde una interfaz ligera de Windows.",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 18))

        ttk.Label(outer, text="Sitio:").grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
        self.site_combo = ttk.Combobox(
            outer,
            textvariable=self.site_var,
            values=(SITE_NAME,),
            state="readonly",
        )
        self.site_combo.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(outer, text="URL:").grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
        self.url_entry = ttk.Entry(outer, textvariable=self.url_var)
        self.url_entry.grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(outer, text="Acción:").grid(row=4, column=0, sticky="e", padx=(0, 10), pady=6)
        self.action_combo = ttk.Combobox(
            outer,
            textvariable=self.action_var,
            values=(
                "Abrir sitio",
                "Iniciar sesión",
                "Grabar automatización (próxima etapa)",
            ),
            state="readonly",
        )
        self.action_combo.grid(row=4, column=1, sticky="ew", pady=6)

        ttk.Label(outer, text="Correo:").grid(row=5, column=0, sticky="e", padx=(0, 10), pady=6)
        self.email_entry = ttk.Entry(outer, textvariable=self.email_var)
        self.email_entry.grid(row=5, column=1, sticky="ew", pady=6)

        ttk.Label(outer, text="Contraseña:").grid(row=6, column=0, sticky="e", padx=(0, 10), pady=6)
        self.password_entry = ttk.Entry(outer, textvariable=self.password_var, show="•")
        self.password_entry.grid(row=6, column=1, sticky="ew", pady=6)

        self.save_credentials_check = ttk.Checkbutton(
            outer,
            text="Guardar en Windows Credential Manager después de un login correcto",
            variable=self.save_credentials_var,
        )
        self.save_credentials_check.grid(row=7, column=1, sticky="w", pady=(4, 12))

        credential_bar = ttk.Frame(outer)
        credential_bar.grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.load_credential_button = ttk.Button(
            credential_bar,
            text="Cargar credencial",
            command=self._load_saved_credential,
        )
        self.load_credential_button.pack(side="left", padx=(0, 8))

        self.delete_credential_button = ttk.Button(
            credential_bar,
            text="Eliminar credencial guardada",
            command=self._delete_saved_credential,
        )
        self.delete_credential_button.pack(side="left")

        actions = ttk.Frame(outer)
        actions.grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 16))

        self.run_button = ttk.Button(actions, text="Ejecutar", command=self._run)
        self.run_button.pack(side="left", padx=(0, 8))

        self.stop_button = ttk.Button(
            actions,
            text="Detener",
            command=self._stop_browser,
            state="disabled",
        )
        self.stop_button.pack(side="left")

        status_frame = ttk.LabelFrame(outer, text="Estado", padding=12)
        status_frame.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        status_frame.columnconfigure(0, weight=1)
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            wraplength=760,
        ).grid(row=0, column=0, sticky="w")

        footer = ttk.Label(
            outer,
            text=(
                "Flaticon usa actualmente el proveedor de identidad de Magnific. "
                "Las credenciales guardadas permanecen en Windows, no en Git."
            ),
            wraplength=780,
        )
        footer.grid(row=11, column=0, columnspan=2, sticky="w")

    def _initialize_credential_store(self) -> None:
        try:
            self._credential_store = WindowsCredentialStore()
        except OSError:
            LOGGER.exception("Windows Credential Manager no está disponible")
            self._credential_store = None
            self.save_credentials_check.configure(state="disabled")
            self.load_credential_button.configure(state="disabled")
            self.delete_credential_button.configure(state="disabled")

    def _action_key(self) -> str:
        return {
            "Abrir sitio": "open",
            "Iniciar sesión": "flaticon_login",
            "Grabar automatización (próxima etapa)": "recorder",
        }.get(self.action_var.get(), "open")

    def _run(self) -> None:
        action = self._action_key()

        if action == "recorder":
            messagebox.showinfo(
                "AutomationNav",
                "El grabador corresponde a la siguiente etapa.",
                parent=self.root,
            )
            return

        if self._browser_worker and self._browser_worker.is_alive():
            messagebox.showinfo(
                "AutomationNav",
                "Ya existe una sesión de navegador activa.",
                parent=self.root,
            )
            return

        url = self.url_var.get().strip()
        if not is_http_url(url):
            messagebox.showwarning(
                "URL inválida",
                "Introduce una URL http:// o https:// válida.",
                parent=self.root,
            )
            return

        username = ""
        password = ""

        if action == "flaticon_login":
            username = self.email_var.get().strip()
            password = self.password_var.get()
            if not username or not password:
                messagebox.showwarning(
                    "Credenciales",
                    "Introduce correo y contraseña antes de iniciar sesión.",
                    parent=self.root,
                )
                return

        self._browser_worker = BrowserWorker(
            url=url,
            action=action,
            username=username,
            password=password,
            event_callback=self._queue_browser_event,
        )
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._browser_worker.start()

    def _queue_browser_event(self, event_type: str, message: str) -> None:
        self._events.put((event_type, message))

    def _process_events(self) -> None:
        try:
            while True:
                event_type, message = self._events.get_nowait()
                if event_type == "status":
                    self.status_var.set(f"Estado: {message}")
                elif event_type == "failed":
                    self.status_var.set("Estado: error durante la automatización.")
                    messagebox.showerror(
                        "Error de automatización",
                        f"AutomationNav encontró un problema.\n\nDetalle: {message}",
                        parent=self.root,
                    )
                elif event_type == "closed":
                    self.run_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    if not self.status_var.get().startswith("Estado: inicio de sesión"):
                        self.status_var.set("Estado: navegador cerrado.")
                elif event_type == "login_succeeded":
                    self._login_succeeded(message)
                elif event_type == "manual_action_required":
                    self.status_var.set(f"Estado: {message}")
                    messagebox.showinfo(
                        "Verificación manual",
                        message,
                        parent=self.root,
                    )
        except queue.Empty:
            pass

        if self.root.winfo_exists():
            self.root.after(100, self._process_events)

    def _login_succeeded(self, final_url: str) -> None:
        self.status_var.set(f"Estado: inicio de sesión confirmado. Destino: {final_url}")

        if not self.save_credentials_var.get() or self._credential_store is None:
            return

        try:
            self._credential_store.write(
                CREDENTIAL_TARGET,
                self.email_var.get().strip(),
                self.password_var.get(),
            )
        except OSError as exc:
            LOGGER.exception("No se pudo guardar la credencial")
            messagebox.showwarning(
                "Credenciales",
                f"El login fue correcto, pero no se pudo guardar la credencial.\n\n{exc}",
                parent=self.root,
            )
        else:
            self.status_var.set(
                "Estado: inicio de sesión confirmado y credencial guardada en Windows."
            )

    def _load_saved_credential(self, silent: bool = False) -> None:
        if self._credential_store is None:
            return

        try:
            credential = self._credential_store.read(CREDENTIAL_TARGET)
        except OSError as exc:
            LOGGER.exception("No se pudo cargar la credencial")
            if not silent:
                messagebox.showwarning(
                    "Credenciales",
                    f"No se pudo leer Windows Credential Manager.\n\n{exc}",
                    parent=self.root,
                )
            return

        if credential is None:
            if not silent:
                messagebox.showinfo(
                    "Credenciales",
                    "No hay una credencial guardada para Flaticon.",
                    parent=self.root,
                )
            return

        self.email_var.set(credential.username)
        self.password_var.set(credential.password)
        self.save_credentials_var.set(True)
        if not silent:
            self.status_var.set(
                "Estado: credencial cargada desde Windows Credential Manager."
            )

    def _delete_saved_credential(self) -> None:
        if self._credential_store is None:
            return

        try:
            deleted = self._credential_store.delete(CREDENTIAL_TARGET)
        except OSError as exc:
            LOGGER.exception("No se pudo eliminar la credencial")
            messagebox.showwarning(
                "Credenciales",
                f"No se pudo eliminar la credencial.\n\n{exc}",
                parent=self.root,
            )
            return

        self.password_var.set("")
        if deleted:
            self.status_var.set("Estado: credencial de Flaticon eliminada de Windows.")
        else:
            self.status_var.set("Estado: no había una credencial guardada para Flaticon.")

    def _stop_browser(self) -> None:
        if self._browser_worker and self._browser_worker.is_alive():
            self._browser_worker.request_stop()
            self.status_var.set("Estado: solicitando cierre...")

    def _on_close(self) -> None:
        if self._browser_worker and self._browser_worker.is_alive():
            self._browser_worker.request_stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
