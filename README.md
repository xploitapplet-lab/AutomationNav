# AutomationNav

AutomationNav es una aplicación Windows para crear, administrar y ejecutar automatizaciones web autorizadas.

## Estado

Fase 01 funcional.

La base actual incluye:
- interfaz PySide6;
- sitio inicial Flaticon;
- apertura de Microsoft Edge mediante Playwright;
- login adaptable para Flaticon/Magnific;
- soporte para correo → continuar → contraseña;
- detección de MFA/CAPTCHA con intervención manual;
- Windows Credential Manager para credenciales locales;
- SQLite local;
- logs locales;
- pruebas automáticas;
- compilación automática de AutomationNav.exe en GitHub Actions.

## Primer flujo

Flaticon utiliza actualmente su proveedor de identidad en `id.magnific.com`.

AutomationNav intenta localizar campos mediante selectores semánticos y alternativas. No depende de coordenadas de pantalla.

Si el sitio solicita MFA, CAPTCHA u otra verificación adicional, AutomationNav lo informa y espera intervención manual. No intenta evadir mecanismos de seguridad.

## Credenciales

Las credenciales no se guardan en GitHub.

Desde la interfaz se puede activar:

`Guardar en Windows Credential Manager después de un login correcto`

También es posible cargar o eliminar la credencial guardada.

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

Cada push válido a `main` ejecuta el workflow de Windows y publica el ejecutable como artefacto de GitHub Actions.

## Seguridad

No subir credenciales, cookies, tokens ni sesiones al repositorio.

Los datos locales se almacenan fuera del directorio de instalación, bajo el perfil del usuario de Windows.
