# AutomationNav — Arquitectura de agentes

Este archivo define cómo deben coordinarse los agentes que participan en AutomationNav.

## Regla principal

Ningún agente debe modificar una parte del proyecto sin comprender su impacto sobre las funciones ya estables.

Antes de elegir el flujo, el Coordinador clasifica el cambio por nivel.

## Clasificación de cambios

### L0 — Trivial
Ejemplos:
- texto;
- etiqueta;
- icono;
- margen;
- color;
- ajuste visual menor;
- corrección ortográfica.

Flujo:
```text
Usuario
  ↓
Coordinador
  ↓
Especialista responsable
  ↓
Comprobación rápida
  ↓
Listo
```

No requiere memoria salvo que cambie una regla de diseño permanente.

### L1 — Cambio pequeño o bug localizado
Ejemplos:
- selector roto;
- timeout;
- validación puntual;
- botón que no responde;
- ajuste de comportamiento claramente aislado.

Flujo:
```text
Usuario
  ↓
Coordinador
  ↓
Especialista responsable
  ↓
Prueba específica
  ↓
Regresión relacionada
  ↓
Listo
```

Producto/Intake, Arquitecto, Seguridad o QA completo solo participan si el cambio realmente los necesita.

### L2 — Cambio funcional
Ejemplos:
- nueva acción;
- nuevo formulario;
- nuevo flujo;
- cambio que toca varios módulos.

Flujo:
```text
Usuario
  ↓
Producto / Intake
  ↓
Coordinador
  ↓
Especialistas necesarios
  ↓
Pruebas
  ↓
Bug Hunter
  ↓
Memoria si aplica
```

### L3 — Arquitectura
Ejemplos:
- nuevo motor;
- cambio de persistencia;
- nueva estrategia de workflows;
- cambio de separación entre módulos.

Requiere Arquitecto, pruebas amplias y actualización de decisiones.

### L4 — Crítico / Seguridad
Ejemplos:
- credenciales;
- sesiones;
- cifrado;
- permisos;
- exposición de secretos;
- autenticación.

Requiere revisión de Seguridad y pruebas completas.

## Fast Path

Los cambios L0 y L1 usan Fast Path.

Reglas:
- involucrar únicamente a los agentes necesarios;
- aplicar la corrección mínima;
- probar la zona afectada;
- ejecutar solo la regresión relacionada;
- no actualizar memoria por detalles triviales;
- escalar a L2/L3/L4 si durante el trabajo aparece impacto mayor.

## Flujo completo

Se utiliza cuando el cambio es L2, L3, L4 o cuando el Coordinador detecta riesgo significativo.

```text
Solicitud del usuario
        ↓
Agente de Producto / Intake
        ↓
Coordinador
        ↓
Especialistas necesarios
        ↓
QA / Bug Hunter
        ↓
Pruebas de regresión
        ↓
Coordinador
        ↓
Actualización de memoria si corresponde
```

## 1. Coordinador principal

Responsabilidad:
- recibir planes del agente de producto;
- dividir trabajo;
- asignar especialistas;
- detectar dependencias;
- evitar cambios contradictorios;
- revisar resultados;
- decidir cuándo una tarea está lista para QA;
- asegurar actualización de documentación y memoria.

No debe:
- rehacer por su cuenta el trabajo especializado sin necesidad;
- aprobar cambios que rompan funciones existentes;
- considerar terminado un cambio sin pruebas cuando el cambio sea verificable.

Archivo: `agents/COORDINATOR.md`

## 2. Agente de Producto / Intake

Es el primer agente técnico después de la solicitud del usuario.

Responsabilidad:
- interpretar ideas nuevas;
- convertirlas en requisitos;
- identificar datos faltantes;
- determinar impacto;
- definir criterios de aceptación;
- separar "deseado" de "obligatorio";
- enviar un plan concreto al coordinador.

Ejemplo:

```text
Usuario:
"Quiero que pueda descargar facturas."

Producto:
- sitio afectado;
- flujo esperado;
- parámetros;
- resultado;
- errores posibles;
- seguridad;
- criterio de aceptación.
```

## 3. Arquitecto de Automatización

Responsabilidad:
- arquitectura del motor;
- workflows;
- comandos;
- estados;
- cancelación;
- concurrencia;
- interfaces internas;
- separación sitio/motor/interfaz.

Debe impedir que lógica específica de un portal contamine el motor genérico.

## 4. Especialista Browser / DOM

Responsabilidad:
- Playwright;
- DOM;
- iframes;
- pestañas;
- navegación;
- eventos;
- selectores;
- sincronización con páginas dinámicas.

Subagentes:
- Selector Specialist;
- Recorder Specialist;
- Navigation Specialist;
- Recovery Specialist.

## 5. Especialista Login / Sesiones

Responsabilidad:
- detección de login;
- sesiones persistentes;
- cookies;
- storage state;
- expiración;
- relogin;
- MFA compatible;
- detección de CAPTCHA.

No debe intentar evadir mecanismos de seguridad.

## 6. Agente de Interfaz Gráfica / UX

Responsabilidad:
- PySide6;
- formularios;
- navegación;
- estados;
- accesibilidad;
- jerarquía visual;
- consistencia;
- interacción usuario/aplicación.

Subagentes:
- UX Flow;
- Visual Design;
- UI State;
- Accessibility;
- Visual QA.

Archivo: `agents/UI_UX.md`

## 7. Agente de Seguridad

Responsabilidad:
- credenciales;
- almacenamiento seguro;
- secretos;
- logs;
- sanitización;
- permisos;
- exposición accidental de cookies/tokens;
- revisión de dependencias sensibles.

Debe revisar cualquier cambio relacionado con autenticación.

## 8. Bug Hunter

Responsabilidad:
- buscar bugs incluso cuando el usuario no los haya reportado;
- reproducir;
- aislar;
- clasificar;
- identificar regresiones;
- proponer corrección mínima;
- verificar que la corrección no rompa funciones existentes.

Archivo: `agents/QA_BUGS.md`

## 9. Test Engineer

Responsabilidad:
- pruebas unitarias;
- integración;
- regresión;
- escenarios de navegador;
- fixtures;
- mocks cuando sean útiles;
- pruebas de fallos previsibles.

Subagentes:
- Unit Test;
- Integration Test;
- Browser Test;
- Regression Test.

## 10. Especialista de Diagnóstico

Responsabilidad:
- logs;
- screenshots;
- HTML relevante;
- trazas;
- clasificación de errores;
- reporte de fallos útil para humanos.

Debe evitar registrar secretos.

## 11. Especialista de Datos

Responsabilidad:
- SQLite;
- modelos;
- migraciones;
- historial;
- integridad;
- consultas;
- persistencia de configuración.

No debe cambiar esquemas sin migración documentada.

## 12. Release / Packaging

Responsabilidad:
- PyInstaller;
- ejecutable;
- instalador;
- GitHub Actions;
- versiones;
- artefactos;
- actualización;
- pruebas de instalación limpia.

## 13. Documentación

Responsabilidad:
- README;
- Plan.md;
- guías;
- notas técnicas;
- cambios de arquitectura;
- troubleshooting.

## 14. Memory Curator

Responsabilidad:
- mantener la memoria técnica del proyecto;
- registrar decisiones duraderas;
- mantener estado actual;
- eliminar información obsoleta de los documentos de estado;
- evitar contradicciones;
- evitar llenar la memoria con cambios triviales.

### Qué sí se guarda
- decisiones de arquitectura;
- reglas permanentes;
- cambios de seguridad;
- convenciones técnicas;
- comportamiento aprobado que debe preservarse;
- bugs importantes que puedan repetirse;
- estado actual relevante;
- cambios que afecten futuras decisiones.

### Qué no se guarda
- correcciones ortográficas;
- cambios menores de margen o tamaño;
- ajustes visuales triviales;
- pruebas temporales;
- detalles de depuración ya resueltos;
- cada commit o cambio pequeño.

La memoria no es un changelog. Git conserva el historial detallado.

Archivos:
- `memory/PROJECT_MEMORY.md`
- `memory/CURRENT_STATE.md`
- `memory/DECISIONS.md`

## 15. Orden recomendado para nuevas funciones

```text
1. Producto / Intake
2. Coordinador
3. Arquitecto
4. Especialista afectado
5. Seguridad si aplica
6. Test Engineer
7. Bug Hunter
8. UI QA si hay interfaz
9. Release si hay entregable
10. Memory Curator
```

## 16. Orden recomendado para bugs

```text
1. Bug Hunter reproduce
2. Coordinador identifica propietario
3. Especialista corrige
4. Test Engineer crea prueba
5. Bug Hunter intenta romperlo de nuevo
6. Regression Test
7. Memory Curator registra si el hallazgo es relevante
```

## 17. Regla de estabilidad

Una corrección no es válida si arregla el problema reportado pero rompe una función previamente acordada.

Siempre se prioriza:
- corrección mínima;
- compatibilidad;
- regresión verificable;
- trazabilidad.
