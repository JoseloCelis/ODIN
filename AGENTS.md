# AGENTS.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

## Qué es este repositorio

- **ODIN** (*Otsu + Directional + Intensity + Non-Maximum Suppression*): aplicación de escritorio
  (GTK4 + libadwaita vía PyGObject) que detecta bordes a nivel subpíxel y mide características
  geométricas: anchos de líneas, centros y radios de círculos en imágenes BMP/TIFF/JPEG.
  Python 3.12, numpy / scipy / opencv / matplotlib.
- Sin empaquetado (`pyproject.toml` / `setup.py`), sin lint/format/typecheck ni CI.
  Sí hay **suite de tests** (pytest) en `tests/`: 44 casos que cubren las etapas 1-5 y el pipeline
  completo, con referencias independientes en `tests/utilidades.py` (convolución con `np.convolve`,
  OpenCV con `BORDER_CONSTANT`, NMS escalar, Otsu por barrido sobre valores reales). Se ejecuta desde
  la raíz con `python3 -m pytest tests -v` (~3-4 s); requiere `python3-pytest` por apt en el host y
  llega por `requirements.txt` en el devcontainer.
  La prueba de humo de que la GUI arranca sigue siendo el `postCreateCommand` del devcontainer:
  `python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); ..."`.

## Cómo ejecutar

- Corre en el host o en el devcontainer. En ambos casos, desde la raíz del repo: `python3 odin/main.py`
  (o equivalentemente `python3 -m odin.main`). **No existe `main.py` en la raíz.**
- **Host (Ubuntu 26.04, ya configurado):** requiere estos paquetes apt (el host **no tiene pip ni venv**;
  apt es la vía oficial y todo va al Python del sistema 3.14):
  ```
  gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi python3-gi-cairo
  python3-opencv python3-numpy python3-scipy python3-matplotlib
  ```
  Sin los typelibs: `ValueError: Namespace Gtk not available`. Sin `python3-gi-cairo`: el callback
  `draw_callback` de `handleImage.py` lanza `TypeError: Couldn't find foreign struct converter for
  'cairo.Context'` (no se pinta el rectángulo de recorte). Sin opencv/numpy/...: `ModuleNotFoundError`.
- **WSL2 / WSLg:** los perfiles de VS Code (en `.vscode/launch.json`) usan Wayland con
  `WAYLAND_DISPLAY=wayland-0` y `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`. El perfil Vulkan fija
  `GSK_RENDERER=vulkan`, lo que evita los avisos EGL/Mesa de la selección automática en el host
  verificado. En ese host, Vulkan reporta `llvmpipe` (dispositivo CPU), por lo que no hay
  aceleración GPU confirmada aunque exista `/dev/dxg`. Forzar `GALLIUM_DRIVER=d3d12` no inicializó
  EGL. El perfil Cairo es el fallback de renderizado CPU.
- **GPU de la interfaz vs. procesamiento:** el renderer Vulkan/OpenGL de GTK solo acelera la interfaz
  si el controlador expone una GPU física; eso no acelera el pipeline de ODIN. El código actual no usa
  APIs OpenCV CUDA/UMat ni OpenCL; numpy, scipy y OpenCV procesan en CPU.
- Para un fallback CPU determinista en WSLg, usar el perfil `🐍 Debug CPU Cairo (Híbrido Automatico)`
  o ejecutar `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir WAYLAND_DISPLAY=wayland-0 GDK_BACKEND=wayland
  GSK_RENDERER=cairo LIBGL_ALWAYS_SOFTWARE=1 python3 odin/main.py`.
- **Devcontainer** (`.devcontainer/devcontainer.json` + `Dockerfile` raíz): entorno limpio/reproducible
  con GTK4, libadwaita, PyGObject y los requisitos de pip preinstalados. El Dockerfile **no copia el
  código fuente** (solo `requirements.txt`): la imagen es un entorno y el código llega con el mount
  del devcontainer en `/workspaces/ODIN`. Su `CMD` es `["python3", "odin/main.py"]`; un `docker run`
  sin mount no arranca.
- Se requiere pantalla (X11/Wayland). Ambos perfiles de `launch.json` apuntan explícitamente al socket
  Wayland de WSLg; para Linux nativo hay que adaptar esos valores al socket del host.

## Estructura actual del proyecto

- `odin/main.py` — punto de entrada y GUI (`MainWindow(Adw.ApplicationWindow)`). Contiene también
  `MainWindow._tarea_pesada_computacional`, que orquesta el pipeline completo en un hilo de fondo.
- `odin/utils/` — puente OpenCV ↔ GTK:
  - `handleImage.py` (alias `handle`): carga de imagen, `matriz_a_pixbuf` (matriz → `GdkPixbuf` →
    `Gdk.Texture`), `recortar_imagen` (recorte según el widget) y `VisualizadorInteractivo`.
  - `uiVentanas.py` está vacío.
- `odin/Preprocesamiento/` — un archivo por algoritmo, exportado con alias desde `__init__.py`.
  Orden del pipeline en `main.py`:

  | # | Archivo | Alias público | Rol |
  |---|---------|---------------|-----|
  | ① | `DeriGauss.py` | `kernelSeparable` | Gradiente con kernel derivada-gaussiana separable |
  | ② | `MagFase.py` | `MagnitudGradiente` | Magnitud y dirección del gradiente |
  | ③ | `NonMaxSuppressionVectorizado.py` | `NonMaxSup` | Supresión de no máximos (interpolación subpíxel) |
  | ④ | `MtoOtsu.py` | `Otsu` | Umbrales Otsu y Rosin |
  | ⑤ | `NonMaxSuppressionVectorizado.py` | `NonMaxSup` | Doble umbral |
  | ⑥ | `DThEdgeTrackHyst.py` | `DoubleTh` | Histéresis → bordes finales |
  | ⑦ | `houghCircles.py` | `aproxHough` | Centro aproximado del círculo (Hough) |
  | ⑧ | `findCircle.py` | `circleFilter` | Filtrado de puntos en anillo ±10 px |
  | ⑨ | `circuloSimple.py` | `LSC` | Ajuste del círculo simple (x, y, r) |

- `odin/Preprocesamiento/Convolucion/` — `Conv2D.py` / `ConvC.py` / `ConvR.py`: convolución 1D por
  filas y columnas usada por `kernelSeparable`; su `__init__.py` está comentado (sin exports, pero el
  módulo `Conv2D` sí se usa).
- Sin alias en `__init__.py`: `NMS_Migrado.py` (variante alternativa de NMS, no forma parte del
  pipeline principal).

## Arquitectura objetivo (refactorización pendiente — NO existe aún)

Ruta propuesta; el código actual vive en `odin/` con la estructura descrita arriba. Mientras esta
refactorización no se ejecute, las reglas de la sección "Reglas para agentes" aplican a las partes
objetivo cuando se construyan.

1. **MVC / MVP:** `models/` (matemática pura NumPy, sin imports de `gi`/`Gtk`/`Gdk`/`Adw`/`cairo`),
   `views/` (GTK4 + libadwaita + Cairo), `controllers/` (eventos y despacho asíncrono).
2. **Patrón Estrategia:** familia de algoritmos bajo una interfaz abstracta `DeteccionStrategy`
   (`models/strategies/base_strategy.py`), intercambiable en tiempo de ejecución sin tocar Vistas.
3. **Trabajador asíncrono:** hilos secundarios (`threading.Thread`) + sincronización thread-safe con
   la UI vía `GLib.idle_add(callback)`.
4. Estructura de carpetas objetivo: `config/` (parámetros YAML), `data/` (imágenes de prueba y
   resultados), `src/` (models / views / controllers / utils), `tests/` (`test_otsu.py`, `test_nms.py`).

## Punto de entrada y reglas de importación

- La GUI lanza bajo el guard `if __name__ == "__main__":`, así que `import odin.main` **no** abre
  ventanas. Dos formas válidas de ejecutarlo (desde la raíz del repo):
  - `python3 odin/main.py` — como script; `sys.path[0]` es `odin/`.
  - `python3 -m odin.main` — como módulo del paquete.
- Los imports de `main.py` se ramifican según `__package__`: relativos (`from .utils import handle`)
  cuando se ejecuta como módulo, planos (`from utils import handle`) cuando es script. Si agregas
  imports nuevos a `main.py`, respeta esa doble rama o solo funcionará en un modo.
- `import odin` (API de librería) también funciona desde la raíz del repo.
- Los nombres públicos son **alias**, definidos en los `__init__.py` de los paquetes:
  `odin/Preprocesamiento/__init__.py` mapea archivo → algoritmo
  (`MtoOtsu as Otsu`, `houghCircles as aproxHough`, `DeriGauss as kernelSeparable`, ...),
  `odin/utils/__init__.py` mapea `handleImage as handle`.
  Para agregar un algoritmo: crear el módulo, exportarlo + alias en `Preprocesamiento/__init__.py`,
  y luego importarlo en `main.py` a través del alias. No importar archivos de algoritmos directamente.
- Los `__init__.py` y algunos módulos imprimen mensajes de debug al importarse
  (`Preprocesaminento was loaded`, `DeriGauss.py = ...`): son intencionales, no los "limpies".

## Patrones de ejecución

- La matemática pesada corre en un `threading.Thread` de fondo
  (`MainWindow._tarea_pesada_computacional`). Cualquier cosa que toque widgets desde ese hilo debe
  serializarse con `GLib.idle_add` (diálogos, reactivar botones).
- `main.py` llama `Otsu.umbralRosinYOtsu(..., histo=True)`, así que ventanas de matplotlib aparecen
  durante el procesamiento (`plt.show(block=False)` en `MtoOtsu.py`). La forzación del backend Agg en
  `DeriGauss.py` está comentada.
- Las funciones de `odin/utils/handleImage.py` toman la ventana como primer argumento (`self`) y
  leen/escriben estado GTK en ella (`recortar_imagen` asigna `self.xRecorte` / `self.yRecorte` como
  efecto secundario y necesita la geometría del widget `self.image_container`). No son helpers
  independientes.
- Flujo de datos: matriz OpenCV → `handle.matriz_a_pixbuf` (normaliza `uint8` no-`uint8`, convierte
  gray/BGR a RGB) → `GdkPixbuf.Pixbuf` → `Gdk.Texture` para las vistas de resultados.
- Renderizado del recorte: `VisualizadorInteractivo` usa `Gtk.DrawingArea.set_draw_func` con un
  callback Cairo para pintar el rectángulo de recorte.

## Reglas para agentes de IA y desarrolladores

### Modelo (lógica matemática, hoy `odin/Preprocesamiento/`, mañana `src/models/`)
1. **Aislamiento total de UI:** nunca importar `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo` en la capa de
   modelos. (Hoy los algoritmos usan `GLib.idle_add` para dibujar histogramas — deuda conocida que
   la refactorización debe eliminar.)
2. **Arreglos puros:** las funciones matemáticas reciben y retornan `numpy.ndarray` o tipos numéricos.
3. **Vectorización:** evitar bucles `for` anidados sobre píxeles; usar broadcasting, slicing,
   máscaras booleanas y funciones vectorizadas de NumPy/SciPy.
4. **Histéresis no recursiva:** usar `scipy.ndimage` / `cv2.connectedComponents`; no reintroducir
   recursión que cause Stack Overflow.

### Vista (`src/views/`)
1. Solo posicionamiento de widgets, estilos y renderizado. Sin algoritmos ni convoluciones.
2. Estabilidad de renderizado: `set_hexpand(True)` / `set_expand(True)` en el widget central para
   evitar que colapse a 0 píxeles.

### Controlador (`src/controllers/`)
1. **Nunca** invocar métodos de GTK desde un hilo secundario.
2. Procesamiento pesado en `threading.Thread`; resultados de vuelta a la Vista con
   `GLib.idle_add(callback)`.

### Extensión mediante Estrategia
1. Heredar de `DeteccionStrategy`, implementar `detectar(self, imagen_np: np.ndarray, **kwargs) -> np.ndarray`.
2. Registrar la estrategia en el controlador sin modificar las vistas.

### Flujo de trabajo
- Antes de una tarea no trivial, proponer un plan y esperar el OK del usuario.
- Una tarea a la vez; al terminar, reportar qué cambió para que el usuario revise.
- Si no estás seguro al 90%, preguntar. No inventar.
- Preguntar antes de: dependencias nuevas, archivos nuevos, cambios en el formato de datos, o
  modificar el código existente de ODIN y explicar los cambios.
- 🚫 **Nunca** modificar el código ya creado de ODIN sin autorización explícita.

## Memoria del proyecto

- `MEMORY.md` (en la raíz del repo) es el ledger del proyecto entre sesiones: estado actual,
  decisiones con su porqué, aprendizajes y próximos pasos. Máximo ~50 líneas; al crecer, resumir o
  eliminar lo que ya no aporte.
- Engram es la memoria interna del agente de OpenCode (automática, buscable, sobrevive sesiones).
- **Si Engram y `MEMORY.md` se contradicen, NO decidir por cuenta propia: preguntar al usuario
  cuál manda.**
- Reglas permanentes → esta sección de `AGENTS.md`. Estado y decisiones vigentes → `MEMORY.md`.
- Nunca guardar datos sensibles (claves, tokens, datos personales).

## Convenciones

- Identificadores, comentarios, cadenas de UI y mensajes de commit están **en español**. Mantener el
  código nuevo en español para ser coherente.
- Código simple, nombres descriptivos y comentarios solo donde aporten. Diseño limpio.
- Commits convencionales: `<tipo>[<scope>]: <descripción>` (`feat`, `fix`, `refactor`, `docs`, ...).
- `requirements.txt` se mantiene en **UTF-8** (decisión vigente; la codificación UTF-16LE con BOM
  fue un error histórico ya corregido).
- El diálogo de abrir archivo hardcodea rutas del host: `/home` en Linux, y una ruta `/mnt/c/Users/...`
  en WSL2 (detectado porque `os.uname().release` contiene `"microsoft"`).
- Remoto es Azure DevOps (`git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`); las ramas de largo
  plazo son `master` (HEAD de origin), `main`, `rama`, `rama-Hybrida`.

## Gotchas de entorno / archivos

- **Host sin pip ni venv:** todo se instala con apt al Python del sistema (ver "Cómo ejecutar").
  No intentar `pip install` en el host.
- **WSLg + Wayland rompe los popovers de GTK4**
  ([microsoft/wslg#1299](https://github.com/microsoft/wslg/issues/1299)): el listado del `Adw.ComboRow`
  de "Selección / Recorte" puede quedar detrás de la ventana principal (solo en Wayland, no en X11).
  Workaround: `GDK_BACKEND=x11 python3 odin/main.py` (WSLg trae XWayland). Los perfiles actuales usan
  Wayland para evitar el error de memoria compartida X11 observado en este entorno; si se necesita
  probar X11, combinarlo con Cairo y verificar que la ventana no quede transparente.
- PyGObject se instala en el Dockerfile (`pip3 install pygobject pygobject-stubs`), no en
  `requirements.txt`. Las dependencias están sin fijar (unpinned).
- El filtro de imágenes acepta solo bmp / tiff / jpeg. No hay imágenes de ejemplo ni fixtures en el
  repo — traer las propias para ejercitar el pipeline.
- `odin/utils/uiVentanas.py` está vacío; `odin/Preprocesamiento/Convolucion/__init__.py` está
  completamente comentado (ese subpaquete está inactivo como paquete, aunque `Conv2D.py` se usa).
- Hay un dump de core (`core.2463`, probablemente del crash de GTK) en la raíz: no commitear;
  agregar a `.gitignore` o eliminar.
