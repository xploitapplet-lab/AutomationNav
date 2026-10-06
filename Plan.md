# AutomationNav — Plan del proyecto

## 1. Objetivo

AutomationNav será una aplicación de Windows para crear, administrar y ejecutar automatizaciones sobre sitios web que requieren inicio de sesión.

El usuario final no tendrá que programar scripts. La aplicación permitirá registrar un sitio, configurar una cuenta, grabar o definir un flujo y después ejecutarlo desde una interfaz gráfica.

Ejemplos de acciones:
- iniciar sesión;
- navegar a módulos internos;
- consultar registros;
- completar formularios;
- seleccionar filtros y fechas;
- descargar archivos;
- cargar documentos;
- leer tablas o estados;
- generar evidencia de ejecución;
- ejecutar tareas manualmente o mediante programación.

AutomationNav no deberá intentar evadir CAPTCHA, MFA, controles de acceso ni mecanismos de seguridad del sitio. Los flujos deberán respetar las políticas y permisos del portal automatizado.

## 2. Principios de arquitectura

Se mantendrán separadas cinco piezas:

1. **Sitio**: definición del portal, URL, comportamiento y elementos importantes.
2. **Cuenta**: credenciales y sesión asociadas a un sitio.
3. **Automatización**: secuencia reutilizable de acciones.
4. **Motor**: componente genérico que ejecuta los pasos.
5. **Interfaz**: capa utilizada por el usuario para configurar y ejecutar.

Ejemplo:

```text
Sitio: Portal ABC
Cuenta: Compras
Automatizaciones:
  - Descargar facturas
  - Consultar pedidos
  - Descargar reporte
  - Revisar existencias
```

## 3. Tecnología inicial

- Python
- Playwright
- PySide6
- SQLite
- PyInstaller
- pytest
- GitHub Actions

La arquitectura deberá permitir cambiar componentes posteriormente sin rehacer el proyecto completo.

## 4. Modos de uso

### 4.1 Modo usuario
Interfaz simple:
- seleccionar sitio;
- seleccionar cuenta;
- seleccionar automatización;
- completar parámetros;
- ejecutar;
- detener;
- revisar resultado e historial.

### 4.2 Modo grabación
Permite crear un flujo nuevo:
1. registrar URL;
2. abrir navegador visible;
3. iniciar grabación;
4. realizar manualmente el proceso;
5. detectar clics, entradas, selecciones, navegación y descargas;
6. convertirlos en pasos editables;
7. guardar la automatización.

### 4.3 Modo desarrollador
Permite inspeccionar:
- DOM;
- selectores;
- pasos;
- variables;
- eventos;
- capturas;
- logs;
- errores;
- recuperación de selectores.

## 5. Reconocimiento de sitios

Introducir una URL no será suficiente para comprender por completo un sitio. AutomationNav hará un reconocimiento técnico inicial del DOM y después permitirá una grabación guiada.

El reconocimiento intentará identificar:
- inputs;
- passwords;
- buttons;
- links;
- selects;
- checkboxes;
- tablas;
- formularios;
- menús;
- iframes;
- elementos ARIA;
- zonas dinámicas.

Cada elemento relevante podrá guardar varios localizadores:

```text
Selector principal
Selector alternativo 1
Selector alternativo 2
Rol + nombre accesible
Texto
CSS
XPath, solo cuando sea necesario
```

No se utilizarán coordenadas de pantalla como estrategia principal.

## 6. Login y sesiones

El sistema deberá distinguir:
- login requerido;
- sesión activa;
- sesión vencida;
- credenciales incorrectas;
- cuenta bloqueada;
- MFA requerido;
- CAPTCHA detectado.

Cuando el portal lo permita, se reutilizarán cookies y estado de sesión de Playwright.

Las contraseñas nunca se almacenarán dentro del flujo ni del código fuente.

## 7. Credenciales

Prioridad para Windows:
- Windows Credential Manager;
- almacenamiento cifrado si se requiere una alternativa;
- variables de entorno únicamente para desarrollo.

Reglas:
- nunca subir credenciales a Git;
- nunca escribir contraseñas, cookies o tokens sensibles en logs;
- nunca incluir secretos en capturas de diagnóstico si pueden evitarse.

## 8. Motor de automatización

El motor procesará instrucciones genéricas, por ejemplo:

```text
OPEN
LOGIN
CLICK
TYPE
SELECT
CHECK
WAIT
READ
UPLOAD
DOWNLOAD
SCREENSHOT
NAVIGATE
CONDITION
RETRY
```

Los sitios no deberán implementar su propio navegador. Deberán consumir el motor común.

## 9. Variables

Los valores cambiantes deberán ser variables, no datos fijos.

Ejemplo:

```text
{{fecha_inicio}}
{{fecha_final}}
{{cliente}}
{{folio}}
```

La interfaz generará automáticamente los campos requeridos para ejecutar un flujo.

## 10. Editor de automatizaciones

Cada flujo deberá poder:
- mostrar sus pasos;
- editar un paso;
- reordenarlo;
- desactivarlo;
- duplicarlo;
- probar un paso;
- ejecutar desde un punto;
- introducir condiciones;
- configurar esperas;
- definir variables;
- definir tratamiento de errores.

## 11. Recuperación de elementos

Si un selector deja de funcionar:

1. probar selector principal;
2. probar selectores alternativos;
3. buscar por rol y nombre;
4. buscar por atributos estables;
5. buscar coincidencia contextual;
6. registrar posible cambio del sitio.

AutomationNav podrá recomendar actualizar el selector principal, pero no deberá modificar silenciosamente un flujo crítico sin dejar registro.

## 12. Diagnóstico

Ante un fallo se registrará, cuando sea seguro:

- fecha y hora;
- sitio;
- cuenta lógica;
- automatización;
- paso;
- URL;
- elemento esperado;
- selector utilizado;
- excepción;
- tiempo esperado;
- captura;
- fragmento HTML relevante;
- intento y reintentos.

El diagnóstico debe ayudar a distinguir:
- fallo de conexión;
- cambio del sitio;
- sesión vencida;
- selector roto;
- error lógico;
- descarga fallida;
- timeout.

## 13. Historial

La aplicación mostrará:
- ejecuciones correctas;
- ejecuciones fallidas;
- duración;
- acción;
- sitio;
- resultado;
- diagnóstico;
- opción de reintento.

## 14. Programación

Fase posterior:
- manual;
- horario específico;
- diaria;
- semanal;
- intervalos permitidos;
- ejecución desatendida cuando el flujo sea compatible.

## 15. Navegador

Dos modos:

### Visible
Para creación, depuración y diagnóstico.

### Segundo plano
Para automatizaciones ya validadas y compatibles.

Durante las primeras fases se priorizará el navegador visible.

## 16. Estructura prevista

```text
AutomationNav/
│
├── app/
│   ├── ui/
│   ├── core/
│   │   ├── engine/
│   │   ├── browser/
│   │   ├── recorder/
│   │   ├── selectors/
│   │   └── recovery/
│   ├── sites/
│   ├── workflows/
│   ├── credentials/
│   ├── sessions/
│   ├── scheduler/
│   ├── diagnostics/
│   └── database/
│
├── agents/
├── memory/
├── config/
├── data/
├── logs/
├── screenshots/
├── downloads/
├── tests/
├── docs/
├── tools/
├── .github/
│   └── workflows/
│
├── AGENTS.md
├── Plan.md
├── .gitignore
├── requirements.txt
├── README.md
└── main.py
```

## 17. Fases

### Fase 01 — Base
- estructura;
- PySide6;
- Playwright;
- SQLite;
- configuración;
- logs;
- ejecutable inicial;
- build automático de Windows desde el inicio.

**Regla de entrega:** desde la Fase 01, todo estado válido de `main` debe poder generar `AutomationNav.exe` mediante GitHub Actions.

### Fase 02 — Navegador
- abrir URL;
- navegación;
- pestañas;
- esperas;
- screenshots;
- cierre limpio;
- control de errores.

### Fase 03 — Gestor de sitios
- alta;
- edición;
- eliminación;
- validación;
- análisis DOM.

### Fase 04 — Login y sesiones
- configuración de campos;
- credenciales;
- sesión persistente;
- detección de sesión vencida.

### Fase 05 — Grabador
- clics;
- texto;
- selects;
- navegación;
- descargas;
- eventos importantes.

### Fase 06 — Editor
- pasos;
- variables;
- condiciones;
- esperas;
- reordenamiento;
- pruebas parciales.

### Fase 07 — Motor genérico
- ejecución completa de workflows;
- control de estado;
- cancelación segura.

### Fase 08 — Recuperación
- selectores alternativos;
- reintentos;
- detección de cambios;
- sugerencias de reparación.

### Fase 09 — Diagnóstico e historial
- capturas;
- HTML;
- logs;
- historial;
- clasificación de errores.

### Fase 10 — Programador
- ejecución programada;
- control de concurrencia;
- ejecución desatendida.

### Fase 11 — Producción
- instalador;
- actualización;
- pruebas;
- documentación;
- endurecimiento de seguridad.

## 18. Reglas de desarrollo

1. No eliminar funcionalidades existentes para corregir otra.
2. Antes de cambiar un flujo estable, crear o actualizar su prueba.
3. Los selectores de un sitio no deberán dispersarse por toda la aplicación.
4. La interfaz no contendrá lógica de automatización.
5. El motor no contendrá credenciales.
6. Los logs no contendrán secretos.
7. Todo bug corregido deberá dejar una prueba o una explicación reproducible.
8. Todo cambio de arquitectura deberá actualizar este plan.
9. Las decisiones duraderas deberán registrarse en `memory/`.
10. Los agentes deberán trabajar bajo las reglas definidas en `AGENTS.md`.

## 19. Criterio de éxito inicial

La primera versión funcional deberá poder:

1. abrir AutomationNav.exe;
2. registrar un sitio;
3. configurar una cuenta de forma segura;
4. abrir el navegador;
5. iniciar sesión;
6. grabar un flujo sencillo;
7. guardar el flujo;
8. ejecutarlo nuevamente;
9. mostrar progreso;
10. registrar resultado y diagnóstico.
