# AutomationNav — Estado actual

Última actualización: 2026-10-06

## Estado

Fase 01 funcional, primer flujo real de login implementado e interfaz migrada a Tkinter/ttk.

## Completado

- Repositorio y plan general.
- Arquitectura de agentes, Fast Path y memoria técnica.
- Estructura Python inicial.
- Interfaz ligera con Tkinter/ttk.
- Eliminación completa de PySide6/Qt del runtime.
- Motor de navegador en `threading.Thread` con eventos enviados a la UI mediante `queue.Queue`.
- SQLite local.
- Logs rotativos locales.
- Sitio inicial registrado: Flaticon.
- Apertura de Microsoft Edge mediante Playwright en modo visible.
- Validación de URL.
- Pruebas base.
- Pipeline de Windows con Python 3.13.
- Compilación verificada de AutomationNav.exe con PyInstaller.
- Flujo de login de Flaticon implementado.
- Detección del proveedor de identidad actual de Flaticon: id.magnific.com.
- Soporte para login de una o dos etapas: correo → continuar → contraseña.
- Manejo de OneTrust/cookies y acceso por correo.
- Detección de MFA/CAPTCHA para intervención manual, sin evasión.
- Guardado opcional de credenciales en Windows Credential Manager.
- Carga y eliminación de credenciales desde la interfaz.
- Credenciales excluidas de Git, logs y memoria.
- Artefacto de Windows publicado correctamente por GitHub Actions.

## Build verificado

Workflow: Build AutomationNav Windows  
Run exitoso: #10  
Resultado: success

Commit validado:
695432bfaeeaf30a4fbca046a246c6d6e6b7ecf9

Pasaron:
- instalación de dependencias;
- compileall;
- pytest;
- PyInstaller;
- verificación de AutomationNav.exe;
- carga del artefacto.

## Tamaño

Artefacto anterior con PySide6: aproximadamente 89.9 MB comprimidos.  
Artefacto después de migrar a Tkinter/ttk: aproximadamente 52.7 MB comprimidos.

Reducción aproximada: 41%.

## Artefacto

Nombre: AutomationNav-Windows  
Contenido: AutomationNav.exe

El artefacto de GitHub Actions expira según la política de retención del workflow.

## Dependencias base

- Tkinter/ttk incluido con Python
- Playwright 1.63.0
- PyInstaller 6.22.3

## Seguridad

Las credenciales de prueba de Flaticon no se almacenan en GitHub, logs ni memoria.

Si el usuario elige guardarlas desde AutomationNav, se almacenan mediante Windows Credential Manager en el equipo local.

## Próximo trabajo

- seguir probando el login real en Windows;
- diagnóstico detallado si Magnific cambia selectores;
- persistencia segura de sesión;
- análisis DOM inicial;
- grabador de automatizaciones;
- editor de pasos;
- optimización adicional del empaquetado de Playwright si resulta conveniente.

## Riesgos tempranos

- cambios del proveedor de identidad;
- DOM dinámico;
- grabador demasiado frágil;
- depender de coordenadas;
- mezclar lógica UI con lógica Playwright;
- persistir sesiones sin protección suficiente.
