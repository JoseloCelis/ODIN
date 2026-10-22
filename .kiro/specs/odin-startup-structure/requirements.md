# Requirements Document

## Introduction

ODIN es una aplicación de escritorio para procesamiento de imágenes científicas,
orientada a la detección de bordes y medición de características geométricas: anchos de líneas, centros y radios de círculos en imágenes BMP/TIFF/JPEG.
Actualmente la secuencia de arranque no está definida de forma explícita: los módulos de
preprocesamiento, el subsistema GTK4/Adwaita y el sistema de visualización interactiva se
inicializan de manera implícita a través de las importaciones de Python y del constructor
de `MainWindow`.

Este documento captura los requerimientos de **arranque estructurado de ODIN** (`odin-startup-structure`):
qué componentes se inicializan, en qué orden, con qué dependencias entre sí, y cómo se
orquesta el flujo de inicio desde la línea de comandos o el contenedor Docker hasta que la
ventana principal queda disponible para el usuario.

---

## Glossary

- **Application**: Instancia de `ODINAdwaita` (`Adw.Application`), punto de entrada de la
  GUI.
- **Bootstrapper**: Módulo o función responsable de orquestar las fases de arranque previas
  a la creación de la ventana.
- **Display_Validator**: Componente que verifica la disponibilidad de un backend gráfico GDK
  (Wayland o X11) antes de intentar construir la GUI.
- **Module_Loader**: Componente que importa y valida los módulos de preprocesamiento y de
  utilidades.
- **MainWindow**: Ventana principal de la aplicación (`Adw.ApplicationWindow`).
- **Preprocesamiento_Suite**: Conjunto de módulos de procesamiento matemático importados
  desde `odin.Preprocesamiento`. Los archivos físicos son: `DeriGauss.py`, `MagFase.py`,
  `NonMaxSuppressionVectorizado.py`, `MtoOtsu.py`, `DThEdgeTrackHyst.py`, `houghCircles.py`,
  `findCircle.py`, `circuloSimple.py`; importados con los alias: `kernelSeparable`,
  `MagnitudGradiente`, `NonMaxSup`, `Otsu`, `DoubleTh`, `aproxHough`, `circleFilter`, `LSC`
  respectivamente.
- **Handle_Module**: Módulo de utilidades de imagen (`odin.utils.handle`) que encapsula
  carga, conversión y recorte de imágenes.
- **Startup_Log**: Salida de diagnóstico producida durante el arranque que describe el
  estado de cada componente inicializado.
- **Environment_Probe**: Componente que detecta el entorno de ejecución (Linux nativo,
  WSL2, contenedor Docker) y ajusta variables como `DISPLAY` o la ruta de archivos.
- **Sigma**: Parámetro numérico de suavizado Gaussiano; valor predeterminado 3.

---

## Requirements

### Requirement 1: Validación del entorno gráfico

**User Story:** Como operador de ODIN, quiero que la aplicación verifique la disponibilidad de pantalla antes de construir la GUI, para que el error sea informativo en lugar de una excepción no manejada de GTK.

#### Acceptance Criteria

1. WHEN `odin/main.py` es invocado, THE `Display_Validator` SHALL comprobar que `Gdk.Display.get_default()` devuelve un display no nulo antes de continuar con la construcción de `MainWindow`.
2. IF `Gdk.Display.get_default()` devuelve `None`, THEN THE `Display_Validator` SHALL imprimir en `stderr` un mensaje de error que incluya el nombre del componente (`Display_Validator`), la causa (`no se encontró un display GDK disponible`) y una acción recomendada (p.ej. `"Verifique que DISPLAY o WAYLAND_DISPLAY estén configurados"`), e invocar `sys.exit(1)` antes de instanciar cualquier widget GTK.
3. WHEN el display es válido, THE `Display_Validator` SHALL registrar en `stdout` el nombre del backend GDK activo obtenido mediante `Gdk.Display.get_name()`, dentro de una entrada `Startup_Log` de nivel `INFO` en la fase `DISPLAY_VALID`.
4. WHEN `odin/main.py` es invocado, THE `Display_Validator` SHALL completar su verificación antes de que cualquier handler de la señal `activate` de `ODINAdwaita` comience a ejecutarse, de modo que no exista ningún instante en que un handler de `activate` se ejecute sin que la validación haya concluido.

---

### Requirement 2: Carga y validación de módulos de preprocesamiento

**User Story:** Como desarrollador de ODIN, quiero que la importación de los módulos de preprocesamiento ocurra de forma ordenada y verificable, para detectar dependencias faltantes al arrancar y no durante el primer clic del usuario.

#### Acceptance Criteria

1. WHEN `odin/__init__.py` es importado, THE `Module_Loader` SHALL importar los módulos de `Preprocesamiento_Suite` en el orden secuencial de alias: `kernelSeparable` (desde `DeriGauss.py`), `MagnitudGradiente` (desde `MagFase.py`), `NonMaxSup` (desde `NonMaxSuppressionVectorizado.py`), `Otsu` (desde `MtoOtsu.py`), `DoubleTh` (desde `DThEdgeTrackHyst.py`), `aproxHough` (desde `houghCircles.py`), `circleFilter` (desde `findCircle.py`), `LSC` (desde `circuloSimple.py`); y registrar en `Startup_Log` (fase `MODULE_LOAD`, nivel `INFO`) una entrada por cada módulo importado exitosamente, en el mismo orden de importación.
2. WHEN `odin/__init__.py` es importado, THE `Module_Loader` SHALL importar `Handle_Module` desde `odin.utils` y registrar una entrada `"Handle_Module: OK"` en `Startup_Log` (fase `MODULE_LOAD`, nivel `INFO`).
3. IF algún módulo de `Preprocesamiento_Suite` lanza `ImportError` durante la importación, THEN THE `Module_Loader` SHALL capturar la excepción, registrar el nombre del módulo fallido en `Startup_Log` (fase `MODULE_LOAD`, nivel `ERROR`), y relanzar un `RuntimeError` cuyo mensaje contenga el nombre exacto del módulo fallido como subcadena.
4. IF `Handle_Module` lanza `ImportError`, THEN THE `Module_Loader` SHALL capturar la excepción, registrar el fallo en `Startup_Log` (fase `MODULE_LOAD`, nivel `ERROR`), y relanzar un `RuntimeError` cuyo mensaje contenga la cadena `"Handle_Module"` y una descripción que indique que el subsistema de imagen no está disponible.
5. WHEN todos los módulos se importan correctamente, THE `Module_Loader` SHALL registrar en `Startup_Log` (fase `MODULE_LOAD`, nivel `INFO`) las cadenas `"Preprocesamiento_Suite: OK"` y `"Handle_Module: OK"` al finalizar la importación de cada grupo.

---

### Requirement 3: Detección del entorno de ejecución

**User Story:** Como operador de ODIN, quiero que la aplicación detecte automáticamente si se ejecuta en Linux nativo, WSL2 o un contenedor Docker, para que configure correctamente las rutas de acceso a archivos y el backend gráfico sin intervención manual.

#### Acceptance Criteria

1. WHEN el `Bootstrapper` se ejecuta, THE `Environment_Probe` SHALL examinar `os.uname().release` para determinar si contiene la cadena `"microsoft"` (sin distinción de mayúsculas) y clasificar el entorno como `WSL2`; si `os.uname()` no está disponible o lanza una excepción, THE `Environment_Probe` SHALL clasificar el entorno como `NATIVE_LINUX`.
2. WHEN el `Bootstrapper` se ejecuta dentro de un contenedor Docker, THE `Environment_Probe` SHALL detectar la presencia del archivo `/.dockerenv` y clasificar el entorno como `DOCKER`, con prioridad sobre la clasificación `WSL2` si ambas condiciones se cumplen simultáneamente.
3. WHEN el entorno clasificado es `WSL2`, THE `Environment_Probe` SHALL establecer la ruta base de archivos mediante la siguiente cascada de prioridades, deteniéndose en la primera ruta existente y accesible:
   1. `/home/<usuario>/proyectos/ODIN` (directorio de trabajo preferido del proyecto)
   2. `/home/<usuario>` (directorio home del usuario)
   3. `Path.home()` (fallback garantizado)
   
   donde `<usuario>` es el nombre del usuario activo del sistema operativo obtenido mediante `os.getlogin()` o `Path.home().name`.
4. WHEN el entorno clasificado es `NATIVE_LINUX` o `DOCKER`, THE `Environment_Probe` SHALL establecer la ruta base de archivos mediante la siguiente cascada de prioridades, deteniéndose en la primera ruta existente y accesible:
   1. `/home/<usuario>/proyectos/ODIN` (directorio de trabajo preferido del proyecto)
   2. `/home/<usuario>` (directorio home del usuario)
   3. `Path.home()` (fallback garantizado)
   
   donde `<usuario>` es el nombre del usuario activo del sistema operativo obtenido mediante `os.getlogin()` o `Path.home().name`.
5. WHEN la detección de entorno finaliza, THE `Environment_Probe` SHALL registrar en `Startup_Log` (fase `ENV_PROBE`, nivel `INFO`) el valor de la clasificación de entorno detectada (`WSL2`, `NATIVE_LINUX` o `DOCKER`) y la ruta base de archivos seleccionada como cadena absoluta, antes de que `MainWindow` sea construida.
6. THE `Environment_Probe` SHALL completar todas las operaciones de detección de entorno y selección de ruta base en menos de 200 ms medidos desde el inicio de la ejecución del `Bootstrapper`; IF el tiempo de detección supera 200 ms, THEN THE `Environment_Probe` SHALL registrar una advertencia en `Startup_Log` (fase `ENV_PROBE`, nivel `WARNING`) e igualmente completar la detección antes de construir `MainWindow`.

---

### Requirement 4: Inicialización de la ventana principal

**User Story:** Como usuario de ODIN, quiero que la ventana principal se cargue con todos sus componentes listos (barra superior, sidebar, visualizador, panel de resultados) en un orden predecible, para que la interfaz no aparezca en un estado parcial o incoherente.

#### Acceptance Criteria

1. WHEN `ODINAdwaita` emite la señal `activate`, THE `Application` SHALL instanciar `MainWindow` únicamente después de que `Display_Validator`, `Module_Loader` y `Environment_Probe` hayan completado su ejecución sin errores, y cada uno de esos tres componentes no deberá superar 2 segundos de tiempo de ejecución.
2. IF `Display_Validator`, `Module_Loader` o `Environment_Probe` terminan con error o superan su tiempo límite de 2 segundos, THEN THE `Application` SHALL abortar la construcción de `MainWindow`, registrar el componente fallido en `Startup_Log` (fase `WINDOW_INIT`, nivel `ERROR`), y terminar el proceso con `sys.exit(1)` antes de instanciar cualquier widget GTK.
3. WHEN `MainWindow.__init__` es llamado, THE `MainWindow` SHALL construir los componentes en el siguiente orden estricto: `ToolbarView` → `HeaderBar` → `NavigationSplitView` → sidebar de controles → panel de visualización (`VisualizadorInteractivo`) → panel de resultados (`ViewStack`); si un componente lanza una excepción no recuperable, la construcción SHALL detenerse antes de instanciar los componentes subsiguientes.
4. WHEN todos los componentes de `MainWindow` han sido instanciados sin errores irrecuperables, THE `MainWindow` SHALL invocar `self.win.present()` para hacerse visible al usuario; `present()` no SHALL invocarse si algún componente no pudo instanciarse.
5. IF `VisualizadorInteractivo` no puede ser instanciado, THEN THE `MainWindow` SHALL sustituirlo por un `Gtk.Picture` de respaldo, registrar la causa del fallo y el nombre del componente de respaldo en `Startup_Log` (fase `WINDOW_INIT`, nivel `WARNING`), y continuar con la construcción de los componentes restantes.
6. THE `MainWindow` SHALL completar su construcción medida desde la llamada a `__init__` hasta la invocación de `self.win.present()` en menos de 3 segundos en hardware de referencia (CPU de cuatro núcleos a 2.0 GHz o superior, 4 GB de RAM, sin GPU dedicada, ejecutándose en Linux nativo x86_64 o WSL2 con Ubuntu 24.04 o superior).

---

### Requirement 5: Registro de diagnóstico de arranque (Startup Log)

**User Story:** Como desarrollador de ODIN, quiero que la secuencia de arranque produzca un registro diagnóstico legible en la salida estándar, para poder depurar problemas de inicialización sin necesidad de un depurador interactivo.

#### Acceptance Criteria

1. THE `Startup_Log` SHALL emitir cada entrada con el formato: `[ODIN] <fase> | <nivel> | <mensaje>`, donde `<fase>` es uno de `ENV_PROBE`, `MODULE_LOAD`, `DISPLAY_VALID`, `WINDOW_INIT`; `<nivel>` es uno de `INFO`, `WARNING`, `ERROR`; y `<mensaje>` tiene una longitud máxima de 500 caracteres.
2. WHEN una fase de arranque se completa sin errores, THE `Startup_Log` SHALL emitir una entrada de nivel `INFO` que incluya el nombre de la fase y su duración en milisegundos con precisión de un decimal (por ejemplo, `123.4 ms`).
3. IF una fase de arranque produce una condición de advertencia recuperable, THEN THE `Startup_Log` SHALL emitir una entrada de nivel `WARNING` con una descripción de la condición (máximo 200 caracteres) y el nombre de la acción de respaldo adoptada.
4. IF una fase de arranque produce un error irrecuperable, THEN THE `Startup_Log` SHALL emitir una entrada de nivel `ERROR` con el nombre del componente, el tipo de excepción y el mensaje de la excepción (máximo 500 caracteres) antes de que el proceso termine con código de salida distinto de cero.
5. THE `Startup_Log` SHALL escribir todas las entradas en `stdout` usando el codec `UTF-8`, terminando cada línea con un único carácter de nueva línea (`\n`), para ser capturadas por el subsistema de logging del contenedor Docker sin configuración adicional.
6. IF el `Startup_Log` no puede escribir en `stdout` (por ejemplo, descriptor cerrado), THEN THE `Startup_Log` SHALL intentar emitir la entrada de fallo en `stderr` e inmediatamente terminar el proceso con código de salida distinto de cero.

---

### Requirement 6: Compatibilidad con el modo de ejecución dual

**User Story:** Como desarrollador de ODIN, quiero que la aplicación funcione correctamente tanto al ejecutarse como paquete (`python3 -m odin.main`) como al ejecutarse como script directo (`python3 odin/main.py`), para no romper el flujo de trabajo de desarrollo local ni el entrypoint del Dockerfile.

#### Acceptance Criteria

1. WHEN `odin/main.py` es ejecutado como script (`__package__` es `None` o cadena vacía), THE `Bootstrapper` SHALL resolver las importaciones de `Preprocesamiento_Suite` y `Handle_Module` usando rutas absolutas desde `sys.path[0]`, de modo que ambos módulos queden disponibles en el espacio de nombres sin lanzar `ImportError`.
2. WHEN `odin/main.py` es ejecutado como paquete (`__package__ == 'odin'`), THE `Bootstrapper` SHALL resolver las importaciones de `Preprocesamiento_Suite` y `Handle_Module` usando rutas relativas (`.Preprocesamiento` y `.utils`), de modo que ambos módulos queden disponibles en el espacio de nombres sin lanzar `ImportError`.
3. IF el `Bootstrapper` no puede resolver las importaciones de `Preprocesamiento_Suite` o `Handle_Module` en el modo detectado, THEN THE `Bootstrapper` SHALL terminar la ejecución con un mensaje de error que indique el módulo que no pudo cargarse y el modo de ejecución activo (`SCRIPT` o `PACKAGE`).
4. THE `Bootstrapper` SHALL determinar la estrategia de importación exclusivamente a partir del valor de `__package__` en tiempo de ejecución, sin requerir modificación de variables de entorno por parte del usuario o del operador.
5. WHEN el `Bootstrapper` selecciona la estrategia de importación, THE `Startup_Log` SHALL registrar una entrada en la fase `MODULE_LOAD` (nivel `INFO`) que incluya el modo de ejecución detectado (`SCRIPT` o `PACKAGE`) y los nombres de los módulos resueltos.
