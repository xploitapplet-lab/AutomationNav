# AutomationNav — Estado actual

Última actualización: 2026-10-06

## Estado

Fase 01 funcional y primer flujo real de login implementado.

## Completado

- Repositorio y plan general.
- Arquitectura de agentes, Fast Path y memoria técnica.
- Estructura Python inicial.
- Interfaz PySide6 inicial.
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
- Detección de MFA/CAPTCHA para intervención manual, sin evasión.
- Guardado opcional de credenciales en Windows Credential Manager.
- Carga y eliminación de credenciales desde la interfaz.
- Credenciales excluidas de Git, logs y memoria.
- Artefacto de Windows publicado correctamente por GitHub Actions.

## Build verificado

Workflow: Build AutomationNav Windows  
Run exitoso: #4  
Resultado: success

Commit validado:
8a8cbb3a5a225cb657bd6703c5dfdfab0ce49e40

Pasaron:
- instalación de dependencias;
- compileall;
- pytest;
- PyInstaller;
- verificación de AutomationNav.exe;
- carga del artefacto.

## Artefacto

Nombre: AutomationNav-Windows  
Contenido: AutomationNav.exe

El artefacto de GitHub Actions expira según la política de retención del workflow.

## Dependencias base

- PySide6 6.11.2
- Playwright 1.63.0
- PyInstaller 6.22.3

## Seguridad

Las credenciales de prueba de Flaticon no se almacenan en GitHub, logs ni memoria.

Si el usuario elige guardarlas desde AutomationNav, se almacenan mediante Windows Credential Manager en el equipo local.

## Próximo trabajo

- prueba real del login en Windows;
- diagnóstico detallado si Magnific cambia selectores;
- persistencia segura de sesión;
- análisis DOM inicial;
- grabador de automatizaciones;
- editor de pasos.

## Riesgos tempranos

- cambios del proveedor de identidad;
- DOM dinámico;
- grabador demasiado frágil;
- depender de coordenadas;
- mezclar lógica UI con lógica Playwright;
- persistir sesiones sin protección suficiente.
