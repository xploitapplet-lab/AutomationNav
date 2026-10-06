# AutomationNav

AutomationNav es una aplicación Windows para crear, administrar y ejecutar automatizaciones web autorizadas.

## Estado

Fase 01 en desarrollo.

La primera base incluye:
- interfaz PySide6;
- sitio inicial Flaticon;
- apertura de Microsoft Edge mediante Playwright;
- SQLite local;
- logs locales;
- compilación automática de AutomationNav.exe en GitHub Actions.

## Desarrollo local

Requiere Python 3.13 y Microsoft Edge.

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
~~~

## Compilación Windows

~~~powershell
pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --onefile --windowed --name AutomationNav --collect-all playwright main.py
~~~

Resultado:

~~~text
dist\AutomationNav.exe
~~~

Cada push a main ejecuta el workflow de Windows y publica el ejecutable como artefacto de GitHub Actions.

## Seguridad

No subir credenciales, cookies, tokens ni sesiones al repositorio.

Los datos locales se almacenarán fuera del directorio de instalación, bajo el perfil del usuario de Windows.
