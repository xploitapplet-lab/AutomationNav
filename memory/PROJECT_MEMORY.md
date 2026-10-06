# AutomationNav — Memoria del proyecto

## Propósito

Este archivo contiene hechos y reglas duraderas del proyecto. No debe utilizarse como log diario.

## Identidad

Nombre: AutomationNav

Objetivo: aplicación Windows para crear, administrar y ejecutar automatizaciones web sobre sitios autorizados, incluidos portales con login.

## Decisiones base

- Python como lenguaje inicial.
- Playwright como motor de navegador.
- PySide6 para interfaz gráfica.
- SQLite como persistencia inicial.
- PyInstaller para generar ejecutable.
- Separación estricta entre sitio, cuenta, automatización, motor e interfaz.
- Modo visible durante creación y depuración.
- Modo segundo plano para flujos previamente validados.
- Las credenciales no se almacenan en workflows ni código.
- No se evaden CAPTCHA, MFA ni controles de seguridad.
- La grabación genera pasos editables; no se depende de coordenadas de pantalla.
- Los elementos deben guardar selectores primarios y alternativas cuando sea razonable.
- Los bugs deben verificarse contra regresiones.
- Las funciones ya aprobadas no deben eliminarse como efecto secundario de una corrección.

## Gobierno

La coordinación de cambios se define en `AGENTS.md`.

El plan funcional se define en `Plan.md`.

Las decisiones con fecha se registran en `DECISIONS.md`.

El estado de trabajo actual se mantiene en `CURRENT_STATE.md`.
