# AutomationNav — Registro de decisiones

## 2026-10-06 — Motor de navegador

**Decisión:** usar Playwright.

**Motivo:** soporte moderno de navegadores, esperas, tabs, descargas, storage state y selectores accesibles.

---

## 2026-10-06 — Interfaz

**Decisión:** usar PySide6.

**Motivo:** aplicación Windows con interfaz más estructurada y escalable que una interfaz mínima de scripts.

---

## 2026-10-06 — Creación de automatizaciones

**Decisión:** combinar reconocimiento DOM + grabación guiada + edición manual.

**No se adopta:** asumir que únicamente introducir una URL permite comprender cualquier portal automáticamente.

---

## 2026-10-06 — Selectores

**Decisión:** utilizar selectores semánticos y estables con alternativas.

**No se adopta:** coordenadas de pantalla como mecanismo principal.

---

## 2026-10-06 — Organización

**Decisión:** trabajar mediante coordinador, agente de producto y especialistas.

**Motivo:** reducir regresiones y evitar que un único agente modifique indiscriminadamente arquitectura, UI, browser y seguridad.

---

## 2026-10-06 — Bugs

**Decisión:** Bug Hunter y Test Engineer son responsabilidades separadas.

**Motivo:** encontrar fallos y diseñar cobertura de pruebas son actividades relacionadas pero distintas.


---

## 2026-10-06 — Fast Path y clasificación de cambios

**Decisión:** clasificar cambios como L0–L4 antes de seleccionar el flujo de agentes.

**Fast Path:** L0 y L1 pasan directamente del Coordinador al especialista responsable, con prueba específica y regresión relacionada.

**Motivo:** resolver cambios pequeños rápidamente sin perder control ni obligarlos a recorrer el flujo completo.

**Memoria:** solo se registran decisiones duraderas, estado relevante, arquitectura, seguridad, convenciones y hallazgos con valor futuro. Los detalles triviales quedan en el historial de Git.


---

## 2026-10-06 — Ejecutable desde la primera fase

**Decisión:** AutomationNav generará un ejecutable Windows desde el comienzo del desarrollo, no únicamente al final del proyecto.

**Implementación:** cada estado válido de la rama `main` debe poder construir `AutomationNav.exe` mediante GitHub Actions.

**Motivo:** probar continuamente el comportamiento real de la aplicación empaquetada y detectar temprano problemas que no aparecen al ejecutar únicamente Python.

**Primer build verificado:** workflow `Build AutomationNav Windows`, run #3, resultado exitoso.
