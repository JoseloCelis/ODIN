# Implementation Plan: odin-startup-structure

## Overview

Este plan convierte el diseño de arranque estructurado de ODIN en tareas de implementación incrementales. El objetivo es reemplazar el proceso de inicialización implícito actual por un flujo explícito con cuatro fases ordenadas: `ENV_PROBE`, `MODULE_LOAD`, `DISPLAY_VALID`, `WINDOW_INIT`, cada una con logging homogéneo y manejo de errores robusto.

La implementación se divide en 8 fases principales que construyen progresivamente la infraestructura de bootstrap, desde el logger base hasta la integración completa en main.py, asegurando que cada componente sea verificable independientemente antes de integrar el siguiente.

## Tasks

- [x] 1. Crear infraestructura base de bootstrap
  - [x] 1.1 Crear archivo bootstrap.py con estructura base
    - Crear `src/bootstrap.py` con imports necesarios (`sys`, `os`, `time`, `dataclasses`, `pathlib`, `typing`)
    - Definir constantes: `FASES`, `NIVELES`, `LOG_FORMAT`, `MAX_MSG_LEN`, `MAX_WARN_LEN`
    - Definir `PREPROCESAMIENTO_SUITE_ORDER` con las 8 tuplas (alias, archivo) en orden
    - Crear dataclasses vacíos: `EnvironmentResult`, `ModuleResult`, `DisplayResult`, `BootstrapResult`
    - _Requisitos: 5.1, 2.1_
  
  - [x] 1.2 Implementar StartupLogger con formato canónico
    - Implementar `StartupLogger.__init__(stream=sys.stdout)`
    - Implementar `StartupLogger.log(fase, nivel, mensaje)` con formato `[ODIN] <fase> | <nivel> | <mensaje>\n`
    - Truncar mensajes a 500 caracteres
    - Asegurar codec UTF-8 y exactamente un `\n` por línea
    - _Requisitos: 5.1, 5.5_
  
  - [x] 1.3 Implementar fallback a stderr en StartupLogger
    - En `StartupLogger.log()`, envolver escritura en try/except OSError
    - Si stdout falla, reintentar en `sys.stderr`
    - Llamar `sys.exit(1)` inmediatamente después del fallback
    - _Requisitos: 5.6_
  
  - [x] 1.4 Implementar log_phase_complete en StartupLogger
    - Implementar `StartupLogger.log_phase_complete(fase, duracion_ms)`
    - Formatear duración con exactamente 1 decimal usando f-string `{duracion_ms:.1f} ms`
    - Emitir entrada INFO con fase y duración
    - _Requisitos: 5.2_
  
  - [x]* 1.5 Escribir tests para StartupLogger
    - **Property 1: Formato canónico de log** — usar Hypothesis con `st.sampled_from(FASES)`, `st.sampled_from(NIVELES)`, `st.text(max_size=500)` (200 ejemplos)
    - **Property 2: Duración con un decimal** — usar Hypothesis con `st.floats(min_value=0.0, max_value=60000.0)` (200 ejemplos)
    - **Property 5: ERROR contiene componente y excepción** — test unitario con excepción simulada
    - Test unitario para fallback a stderr con stdout cerrado
    - _Requisitos: 5.1, 5.2, 5.4, 5.6_

- [x] 2. Checkpoint — Verificar infraestructura de logging
  - Asegurarse de que todos los tests de StartupLogger pasan
  - Verificar que el formato de log cumple exactamente con `[ODIN] <fase> | <nivel> | <mensaje>\n`
  - Preguntar al usuario si hay dudas sobre el formato o comportamiento del logger

- [x] 3. Implementar detección de entorno
  - [x] 3.1 Implementar algoritmo de clasificación de entorno
    - Implementar `EnvironmentProbe.__init__(logger)` guardando referencia al logger
    - Implementar método privado `_classify(release: str, dockerenv_path: Path) -> str`
    - Prioridad: verificar existencia de `dockerenv_path` → `DOCKER`
    - Si no, verificar `"microsoft" in release.lower()` → `WSL2`
    - En cualquier otro caso (incluido `AttributeError`) → `NATIVE_LINUX`
    - _Requisitos: 3.1, 3.2_
  
  - [x] 3.2 Implementar resolución de ruta base con cascada de prioridades
    - Implementar método estático `_resolve_base_path(env_type: str, username: str) -> Path`
    - Para los tres entornos (`WSL2`, `NATIVE_LINUX`, `DOCKER`), probar en orden hasta encontrar la primera ruta existente y accesible:
      1. **Prioridad 1**: `/home/{username}/proyectos/ODIN` — directorio de trabajo preferido del proyecto
      2. **Prioridad 2**: `/home/{username}` — directorio home del usuario
      3. **Prioridad 3**: `Path.home()` — fallback garantizado (siempre existe)
    - Para cada candidato, verificar con `Path.exists() and Path.is_dir()` antes de continuar
    - Devolver la primera ruta válida encontrada
    - Nota: Todas las rutas usan el sistema de archivos nativo Linux (`/home/`) en lugar del montaje de Windows (`/mnt/c/`) por razones de rendimiento en WSL2
    - _Requisitos: 3.3, 3.4_
  
  - [x] 3.3 Implementar EnvironmentProbe.detect() completo
    - Implementar `detect() -> EnvironmentResult`
    - Obtener username con `os.getlogin()` o `Path.home().name` como respaldo
    - Medir tiempo con `time.monotonic()` antes y después de clasificación
    - Llamar `_classify(os.uname().release, Path("/.dockerenv"))`
    - Llamar `_resolve_base_path(env_type, username)`
    - Registrar `ENV_PROBE INFO` con env_type y base_path
    - Si duración > 200ms, registrar `ENV_PROBE WARNING` antes del INFO
    - Devolver `EnvironmentResult(env_type, base_path, detection_ms)`
    - _Requisitos: 3.5, 3.6_
  
  - [x]* 3.4 Escribir tests para EnvironmentProbe
    - **Property 6: WSL2 robusto a capitalización** — Hypothesis con variantes de "microsoft" (200 ejemplos)
    - **Property 7: DOCKER tiene prioridad** — Hypothesis con cualquier release + dockerenv existente (200 ejemplos)
    - **Property 8: base_path siempre existe** — Hypothesis con env_type y username generados (100 ejemplos)
    - **Property 9: Log contiene entorno y ruta** — test unitario verificando substring en log
    - Test unitario para WARNING cuando detección > 200ms (usar `time.sleep` o mock)
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint — Verificar detección de entorno
  - Asegurarse de que todos los tests de EnvironmentProbe pasan
  - Verificar que la detección funciona en los tres entornos (WSL2, DOCKER, NATIVE_LINUX)
  - Preguntar al usuario si hay dudas sobre la lógica de detección

- [x] 5. Implementar cargador de módulos
  - [x] 5.1 Implementar detección de modo SCRIPT vs PACKAGE
    - Implementar `ModuleLoader.__init__(logger, package_context)`
    - Guardar `package_context` (valor de `__package__` desde main.py)
    - Implementar método `_detect_mode() -> Literal["SCRIPT", "PACKAGE"]`
    - Devolver `"PACKAGE"` si `package_context` no es `None` ni `""`
    - Devolver `"SCRIPT"` en caso contrario
    - _Requisitos: 6.1, 6.2, 6.4_
  
  - [x] 5.2 Implementar importación de Preprocesamiento_Suite
    - Implementar `load() -> ModuleResult`
    - Detectar modo con `_detect_mode()`
    - Iterar sobre `PREPROCESAMIENTO_SUITE_ORDER`
    - Para cada `(alias, archivo)`:
      - Si modo PACKAGE: `importlib.import_module(f".Preprocesamiento.{archivo}", package="odin")`
      - Si modo SCRIPT: `importlib.import_module(f"Preprocesamiento.{archivo}")`
      - Asignar módulo importado a `preprocesamiento[alias]`
      - Registrar `MODULE_LOAD INFO` con `"{alias}: OK"`
      - Si `ImportError`: capturar, registrar `MODULE_LOAD ERROR` con nombre del archivo, relanzar `RuntimeError` con mensaje que contenga el alias
    - _Requisitos: 2.1, 2.3, 2.5_
  
  - [x] 5.3 Implementar importación de Handle_Module
    - Dentro de `load()`, después de Preprocesamiento_Suite:
      - Si modo PACKAGE: `importlib.import_module(".utils.handle", package="odin")`
      - Si modo SCRIPT: `importlib.import_module("utils.handle")`
      - Asignar a `handle`
      - Registrar `MODULE_LOAD INFO` con `"Handle_Module: OK"`
      - Si `ImportError`: capturar, registrar `MODULE_LOAD ERROR`, relanzar `RuntimeError` con substring `"Handle_Module"`
    - Devolver `ModuleResult(preprocesamiento, handle, mode)`
    - _Requisitos: 2.2, 2.4, 2.5_
  
  - [x] 5.4 Implementar logging de estrategia en ModuleLoader
    - Al inicio de `load()`, registrar `MODULE_LOAD INFO` con modo detectado
    - Al final de `load()`, registrar `MODULE_LOAD INFO` con todos los alias resueltos
    - _Requisitos: 6.5_
  
  - [x]* 5.5 Escribir tests para ModuleLoader
    - **Property 3: RuntimeError contiene nombre del módulo** — Hypothesis con `st.sampled_from([alias for alias, _ in PREPROCESAMIENTO_SUITE_ORDER])` (50 ejemplos), mock de `importlib.import_module` para lanzar `ImportError`
    - **Property 10: Error contiene módulo y modo** — test unitario con mock
    - **Property 11: Log contiene modo y módulos resueltos** — test unitario verificando substrings
    - Test unitario para modo SCRIPT (package_context=None)
    - Test unitario para modo PACKAGE (package_context="odin")
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.5_

- [x] 6. Checkpoint — Verificar cargador de módulos
  - Asegurarse de que todos los tests de ModuleLoader pasan
  - Verificar que el orden de importación respeta PREPROCESAMIENTO_SUITE_ORDER
  - Preguntar al usuario si hay dudas sobre el manejo de ImportError

- [x] 7. Implementar validador de display
  - [x] 7.1 Implementar DisplayValidator.validate()
    - Implementar `DisplayValidator.__init__(logger)`
    - Implementar `validate() -> DisplayResult`
    - Importar `gi` y llamar `gi.require_version('Gtk', '4.0')` y `gi.require_version('Gdk', '3.0')` si es necesario (verificar versión exacta en el código actual)
    - Importar `Gdk` desde `gi.repository`
    - Llamar `display = Gdk.Display.get_default()`
    - Si `display is None`:
      - Escribir en `sys.stderr`: `[ODIN] DISPLAY_VALID | ERROR | Display_Validator: no se encontró un display GDK disponible.\nAcción recomendada: Verifique que DISPLAY o WAYLAND_DISPLAY estén configurados.\n`
      - Llamar `sys.exit(1)`
    - Si display válido:
      - Obtener `backend_name = type(display).__name__`
      - Registrar `DISPLAY_VALID INFO` con backend_name
      - Devolver `DisplayResult(display, backend_name)`
    - _Requisitos: 1.1, 1.2, 1.3_
  
  - [x]* 7.2 Escribir tests para DisplayValidator
    - Test unitario con mock de `Gdk.Display.get_default()` devolviendo `None` → verificar stderr y `sys.exit(1)`
    - Test unitario con mock devolviendo objeto display → verificar log INFO y DisplayResult
    - _Requisitos: 1.1, 1.2, 1.3_

- [x] 8. Implementar orquestador bootstrap
  - [x] 8.1 Implementar run_bootstrap()
    - Implementar función `run_bootstrap(package_context: str | None = None) -> BootstrapResult`
    - Crear `logger = StartupLogger()`
    - Crear `env_probe = EnvironmentProbe(logger)` y llamar `env = env_probe.detect()`
    - Crear `module_loader = ModuleLoader(logger, package_context)` y llamar `modules = module_loader.load()`
    - Envolver todo en try/except general:
      - Capturar cualquier excepción
      - Registrar `WINDOW_INIT ERROR` con tipo y mensaje de excepción
      - Llamar `sys.exit(1)`
    - Devolver `BootstrapResult(env, modules, logger)`
    - _Requisitos: 4.1, 4.2_
  
  - [x]* 8.2 Escribir test de integración para run_bootstrap
    - **Property 4: Aborto con log ERROR ante fallo** — test con mock de cada componente fallando, verificar que no se instancia MainWindow, se emite ERROR, y se llama sys.exit(1)
    - Test exitoso end-to-end verificando que BootstrapResult contiene los tres componentes
    - _Requisitos: 4.1, 4.2_

- [x] 9. Checkpoint — Verificar bootstrap completo
  - Asegurarse de que run_bootstrap() se ejecuta sin errores
  - Verificar que todas las fases se registran en el orden correcto
  - Preguntar al usuario si hay dudas sobre la orquestación

- [x] 10. Refactorizar src/odin/__init__.py
  - [x] 10.1 Actualizar imports de preprocesamiento
    - Reemplazar imports directos por imports desde archivos físicos con alias
    - Cambiar `from .Preprocesamiento import LSC, DoubleTh, ...` por:
      ```python
      from .Preprocesamiento import (
          DeriGauss as kernelSeparable,
          MagFase as MagnitudGradiente,
          NonMaxSuppressionVectorizado as NonMaxSup,
          MtoOtsu as Otsu,
          DThEdgeTrackHyst as DoubleTh,
          houghCircles as aproxHough,
          findCircle as circleFilter,
          circuloSimple as LSC,
      )
      ```
    - _Requisitos: 2.1_
  
  - [x] 10.2 Exportar módulo bootstrap
    - Agregar `from . import bootstrap` al inicio (después de imports de preprocesamiento)
    - Agregar `from .bootstrap import BootstrapResult`
    - Actualizar `__all__` para incluir `"bootstrap"` y `"BootstrapResult"`
    - Eliminar el `print()` de inicialización del módulo
    - _Requisitos: 4.1_

- [x] 11. Refactorizar src/main.py — parte 1 (imports y estructuras)
  - [x] 11.1 Agregar imports de bootstrap
    - Agregar bloque de importación dual después de los imports de gi:
      ```python
      if __package__:
          from .bootstrap import run_bootstrap, DisplayValidator
      else:
          from bootstrap import run_bootstrap, DisplayValidator
      ```
    - Agregar `import time` para medir duración de WINDOW_INIT
    - _Requisitos: 4.1, 6.1, 6.2_
  
  - [x] 11.2 Eliminar detección de display del ámbito de módulo
    - Eliminar las líneas:
      ```python
      display = Gdk.Display.get_default()
      if display:
          backend_name = type(display).__name__
          print(f"El backend activo de GDK es: {backend_name}")
      else:
          print(" No se pudo inicializar ninguna pantalla gráfica")
      ```
    - La validación de display ahora ocurre en `on_activate`
    - _Requisitos: 1.1, 1.4_

- [x] 12. Refactorizar src/main.py — parte 2 (MainWindow)
  - [x] 12.1 Actualizar constructor de MainWindow
    - Cambiar signatura a: `__init__(self, *args, bootstrap_result, logger, **kwargs)`
    - Guardar `self._bootstrap_result = bootstrap_result`
    - Guardar `self._logger = logger`
    - Agregar al inicio del constructor: `t0 = time.monotonic()`
    - _Requisitos: 4.1_
  
  - [x] 12.2 Implementar orden estricto de construcción de widgets
    - Documentar con comentarios el orden: ToolbarView → HeaderBar → NavigationSplitView → sidebar → VisualizadorInteractivo → ViewStack
    - No reorganizar código, solo asegurar que el orden actual se mantiene
    - _Requisitos: 4.3_
  
  - [x] 12.3 Implementar fallback para VisualizadorInteractivo
    - Envolver construcción de `self.image_container = handle.VisualizadorInteractivo()` en try/except
    - Capturar cualquier excepción (no solo `NameError`)
    - En except:
      - Crear `Gtk.Picture` de respaldo con las mismas propiedades
      - Registrar `WINDOW_INIT WARNING` con mensaje: `f"VisualizadorInteractivo falló, usando Gtk.Picture como respaldo: {type(e).__name__}: {e}"`
    - _Requisitos: 4.5_
  
  - [x] 12.4 Implementar logging de fase WINDOW_INIT
    - Al final del constructor, antes de return, agregar:
      ```python
      duracion_ms = (time.monotonic() - t0) * 1000
      self._logger.log_phase_complete("WINDOW_INIT", duracion_ms)
      ```
    - _Requisitos: 4.6, 5.2_
  
  - [x] 12.5 Refactorizar show_openDialog para usar base_path
    - Eliminar todo el bloque de detección de WSL2/Docker (líneas que verifican `os.uname().release`)
    - Reemplazar por: `home_dir = str(self._bootstrap_result.env.base_path)`
    - Eliminar el fallback a `Path.home()` (ya manejado por EnvironmentProbe)
    - Simplificar verificación de existencia: `if not os.path.exists(home_dir): home_dir = str(Path.home())`
    - _Requisitos: 3.3, 3.4_

- [x] 13. Refactorizar src/main.py — parte 3 (ODINAdwaita)
  - [x] 13.1 Actualizar constructor de ODINAdwaita
    - Cambiar signatura a: `__init__(self, bootstrap_result, logger, **kwargs)`
    - Guardar `self._bootstrap_result = bootstrap_result`
    - Guardar `self._logger = logger`
    - _Requisitos: 4.1_
  
  - [x] 13.2 Mover validación de display a on_activate
    - En `on_activate`, antes de instanciar MainWindow, agregar:
      ```python
      validator = DisplayValidator(self._logger)
      validator.validate()  # sys.exit(1) si falla
      ```
    - _Requisitos: 1.1, 1.4_
  
  - [x] 13.3 Actualizar llamada a MainWindow
    - Cambiar `self.win = MainWindow(application=app)` por:
      ```python
      self.win = MainWindow(
          application=app,
          bootstrap_result=self._bootstrap_result,
          logger=self._logger,
      )
      ```
    - _Requisitos: 4.1, 4.4_
  
  - [x] 13.4 Integrar run_bootstrap en __main__
    - Reemplazar `if __name__ == "__main__":` por:
      ```python
      if __name__ == "__main__":
          result = run_bootstrap(__package__)
          app = ODINAdwaita(
              bootstrap_result=result,
              logger=result.logger,
              application_id="com.detectorDistancias.Odin",
          )
          sys.exit(app.run(sys.argv))
      ```
    - _Requisitos: 4.1, 4.2_

- [x] 14. Checkpoint — Verificar integración completa
  - Ejecutar `python3 -m src.odin.main` (modo PACKAGE) y verificar que arranca sin errores
  - Ejecutar `python3 src/main.py` (modo SCRIPT) y verificar que arranca sin errores
  - Verificar que el log de arranque contiene las 4 fases en orden
  - Preguntar al usuario si hay dudas sobre la integración

- [x] 15. Escribir tests de integración end-to-end
  - Nota: 15.1-15.3 (opcionales, `*`) omitidas; 15.4 implementado y verde. El fallo sin display se verificó manualmente: exit 1 + `DISPLAY_VALID | ERROR`.
  - [ ]* 15.1 Test de arranque exitoso en modo PACKAGE
    - Ejecutar `python3 -m src.odin.main --version` (agregar flag --version si no existe, o usar otro método de verificación)
    - Capturar stdout y verificar presencia de las 4 fases en orden
    - Verificar que el proceso termina con código 0
    - _Requisitos: 4.1, 6.2_
  
  - [ ]* 15.2 Test de arranque exitoso en modo SCRIPT
    - Ejecutar `python3 src/main.py --version`
    - Capturar stdout y verificar presencia de las 4 fases en orden
    - Verificar que el proceso termina con código 0
    - _Requisitos: 4.1, 6.1_
  
  - [ ]* 15.3 Test de fallo sin display
    - Ejecutar proceso en entorno sin DISPLAY ni WAYLAND_DISPLAY
    - Capturar stderr y verificar mensaje de error estructurado
    - Verificar que el proceso termina con código 1
    - _Requisitos: 1.2_
  
  - [x]* 15.4 Test de orden de módulos en log
    - Ejecutar arranque completo
    - Parsear stdout
    - Verificar que los 8 módulos de Preprocesamiento_Suite aparecen en el orden exacto de PREPROCESAMIENTO_SUITE_ORDER
    - _Requisitos: 2.1, 2.5_

- [x] 16. Checkpoint final — Verificación completa del sistema
  - Ejecutar todos los tests unitarios y de integración
  - Verificar que las 11 propiedades de corrección pasan
  - Verificar que el tiempo de arranque de MainWindow < 3s en hardware de referencia
  - Verificar que el tiempo de detección de entorno < 200ms
  - Preguntar al usuario si hay preguntas finales antes de dar por completada la implementación

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido, pero son altamente recomendadas para garantizar la corrección del sistema
- Cada checkpoint incluye verificación de tests para asegurar que no se introduzcan regresiones
- Los tests de propiedad usan Hypothesis con el número mínimo de ejemplos especificado en el diseño (50-200 según la propiedad)
- La implementación debe mantener compatibilidad con ambos modos de ejecución (SCRIPT y PACKAGE) en todo momento
- El orden de las tareas está diseñado para permitir verificación incremental: cada fase construye sobre la anterior y es testeable independientemente
- Los comentarios en el código deben incluir referencias a los requisitos validados (ej: `# Validates: Requirements 5.1, 5.5`)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4"] },
    { "id": 2, "tasks": ["1.5"] },
    { "id": 3, "tasks": ["3.1", "3.2"] },
    { "id": 4, "tasks": ["3.3"] },
    { "id": 5, "tasks": ["3.4"] },
    { "id": 6, "tasks": ["5.1"] },
    { "id": 7, "tasks": ["5.2", "5.3"] },
    { "id": 8, "tasks": ["5.4"] },
    { "id": 9, "tasks": ["5.5"] },
    { "id": 10, "tasks": ["7.1"] },
    { "id": 11, "tasks": ["7.2"] },
    { "id": 12, "tasks": ["8.1"] },
    { "id": 13, "tasks": ["8.2"] },
    { "id": 14, "tasks": ["10.1", "10.2"] },
    { "id": 15, "tasks": ["11.1", "11.2"] },
    { "id": 16, "tasks": ["12.1", "12.2", "12.3"] },
    { "id": 17, "tasks": ["12.4", "12.5"] },
    { "id": 18, "tasks": ["13.1", "13.2"] },
    { "id": 19, "tasks": ["13.3", "13.4"] },
    { "id": 20, "tasks": ["15.1", "15.2", "15.3", "15.4"] }
  ]
}
```
## Log de verificación (2026-10-30)

- Retomado el trabajo iniciado en otra sesión sin contexto para dejarlo sin restos
  huérfanos antes de commitear. La numeración previa (T21, T5, T9, T14) no
  correspondía a esta lista de tareas; se sustituye por esta entrada.
- Marcar solo lo observado: las casillas de arriba se tacharon con evidencia
  (suite verde y pruebas de mutación), no por existir código.
- Corregido en esta sesión: `resolver_radio` usaba el alias `aproxHough` en bruto
  tras eliminar los imports de nivel de módulo de `main.py`. La suite pasó de
  `1 failed, 146 passed` a verde; `main.py` recibe el módulo por parámetro.
- Los tests de bootstrap no son decorativos: se falsificaron con 4 mutaciones
  (orden de la suite, `MAX_MSG_LEN` 500→600, `sys.exit(1)`→`sys.exit(2)` y la
  fase `WINDOW_INIT` del aborto) y **las 4 rompieron su test**.
- Pendiente 12.2: documentar con comentarios el orden estricto de construcción
  de widgets (ToolbarView → HeaderBar → NavigationSplitView → sidebar →
  VisualizadorInteractivo → ViewStack).
- Pendiente 14: ejecutar la GUI completa en modo PACKAGE y SCRIPT (requiere pantalla).
- Pendiente 15.1/15.2: exigen un flag `--version` que no existe todavía.
  Pendiente 15.3: falta el test que ejecute un subproceso sin DISPLAY.
- Pendiente 16: no se midieron el tiempo de arranque de MainWindow (< 3 s), el de
  detección de entorno (< 200 ms) ni las 11 propiedades de corrección.
