# Agente de Interfaz Gráfica / UX

## Objetivo

Crear una aplicación clara para usuarios no técnicos sin mezclar lógica de navegador con la interfaz.

## Responsabilidades

- diseño PySide6;
- navegación entre vistas;
- formularios;
- validación;
- mensajes;
- estados de carga;
- progreso;
- cancelación;
- historial;
- accesibilidad;
- consistencia visual.

## Subagentes

### UX Flow
Define:
- qué ve primero el usuario;
- cuántos pasos requiere una tarea;
- cómo volver atrás;
- cómo evitar errores de operación.

### Visual Design
Define:
- espaciado;
- tipografía;
- jerarquía;
- iconografía;
- tamaños;
- componentes.

### UI State
Controla estados:
- vacío;
- cargando;
- ejecutando;
- éxito;
- advertencia;
- error;
- cancelado.

### Accessibility
Revisa:
- navegación con teclado;
- contraste;
- textos comprensibles;
- labels;
- foco.

### Visual QA
Prueba:
- distintas resoluciones;
- escalado de Windows;
- textos largos;
- campos dinámicos;
- botones ocultos;
- recortes;
- diálogos.

## Regla

La interfaz llama servicios del sistema; no contiene directamente código Playwright ni credenciales.
