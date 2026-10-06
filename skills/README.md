# AutomationNav — Skills reutilizables

Los skills son procedimientos repetibles que los agentes deben seguir.

## Skills iniciales

### analyze-site
Entrada: URL autorizada.
Salida:
- tipo de página;
- formularios;
- elementos relevantes;
- iframes;
- navegación;
- riesgos de automatización.

### define-workflow
Convierte una tarea humana en pasos AutomationNav.

### build-selector
Genera selector principal y alternativas.

### configure-login
Configura login sin almacenar secretos en el workflow.

### record-workflow
Convierte eventos del navegador en pasos editables.

### reproduce-bug
Produce pasos mínimos y evidencia.

### regression-check
Verifica funciones relacionadas antes de aprobar un cambio.

### ui-review
Comprueba estados, validaciones, escalado y navegación.

### security-review
Comprueba secretos, logs, sesiones y permisos.

### update-memory
Actualiza únicamente información duradera o el estado vigente.

## Regla

Los skills describen **cómo realizar una tarea**.
Los agentes describen **quién es responsable**.
La memoria describe **qué se decidió o cuál es el estado actual**.
