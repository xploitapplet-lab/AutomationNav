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

## Política de memoria

La memoria debe ser selectiva.

### Guardar
- decisiones duraderas;
- arquitectura;
- seguridad;
- convenciones;
- comportamientos aprobados que deben preservarse;
- bugs importantes con valor futuro;
- estado relevante del proyecto.

### No guardar
- cambios triviales;
- correcciones de texto;
- pequeños ajustes visuales;
- pruebas temporales;
- detalles de depuración ya resueltos;
- cada commit.

Git mantiene el historial detallado. La memoria existe para acelerar decisiones futuras, no para duplicar el historial.

## Política de ejecución rápida

- L0 y L1 usan Fast Path.
- Se involucran solo los agentes necesarios.
- Se exige prueba específica y regresión relacionada.
- Se escala a L2/L3/L4 cuando aparece impacto mayor.

## Gobierno

La coordinación de cambios se define en `AGENTS.md`.

El plan funcional se define en `Plan.md`.

Las decisiones con fecha se registran en `DECISIONS.md`.

El estado de trabajo actual se mantiene en `CURRENT_STATE.md`.
