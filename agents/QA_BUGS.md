# QA, Bug Hunter y pruebas

## Bug Hunter

Su trabajo no es únicamente confirmar que algo funciona. Debe intentar encontrar cómo falla.

Busca:
- regresiones;
- estados no contemplados;
- timeouts;
- errores de sesión;
- cambios DOM;
- doble clic;
- ejecución repetida;
- cancelación;
- pérdidas de red;
- descargas incompletas;
- formularios vacíos;
- valores extremos;
- errores de escalado visual.

## Ciclo de un bug

```text
Reproducir
↓
Reducir al caso mínimo
↓
Clasificar
↓
Identificar módulo propietario
↓
Corregir
↓
Crear prueba
↓
Repetir escenario
↓
Ejecutar regresión
```

## Test Engineer

### Unit Test
Lógica aislada.

### Integration Test
Comunicación entre módulos.

### Browser Test
Comportamiento Playwright.

### Regression Test
Funciones que ya estaban aprobadas.

### Failure Test
Simula:
- red caída;
- sesión expirada;
- selector ausente;
- descarga fallida;
- timeout;
- ventana cerrada.

## Regla

Un bug corregido debe dejar al menos uno de estos:
- prueba automatizada;
- caso de reproducción documentado;
- fixture;
- escenario de regresión.
