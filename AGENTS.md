# AGENTS.md

## Qué es este repositorio

- ODIN: una app de escritorio (GTK4 + libadwaita vía PyGObject) que detecta bordes y mide
  características geométricas en imágenes: anchos de líneas, centros y radios de círculos.
  Python 3.12, numpy / scipy / opencv / matplotlib.
- Sin empaquetado (`pyproject.toml` / `setup.py`), **sin tests, sin lint/format/typecheck, sin CI**.
  La única verificación disponible es que la app arranque y el pipeline corra sobre una imagen.
  El `postCreateCommand` del devcontainer es la prueba de humo de facto:
  `python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); ..."`.

## Estructura del proyecto

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
  | ③ | `NonMaxSuppressionVectorizado.py` | `NonMaxSup` | Supresión de no máximos (interpolación) |
  | ④ | `MtoOtsu.py` | `Otsu` | Umbrales Otsu y Rosin |
  | ⑤ | `NonMaxSuppressionVectorizado.py` | `NonMaxSup` | Doble umbral |
  | ⑥ | `DThEdgeTrackHyst.py` | `DoubleTh` | Histéresis → bordes finales |
  | ⑦ | `houghCircles.py` | `aproxHough` | Centro aproximado del círculo (Hough) |
  | ⑧ | `findCircle.py` | `circleFilter` | Filtrado de puntos en anillo ±10 px |
  | ⑨ | `circuloSimple.py` | `LSC` | Ajuste del círculo simple (x, y, r) |

- `odin/Preprocesamiento/Convolucion/` — `Conv2D.py` / `ConvC.py` / `ConvR.py`: convolución 1D por
  filas y columnas usada por `kernelSeparable`; su `__init__.py` está comentado (sin exports).
- Sin alias en `__init__.py`: `NMS_Migrado.py` (variante alternativa de NMS, no forma parte del
  pipeline principal).

## Cómo ejecutar

- Corre en el host o en el devcontainer. En ambos casos, desde la raíz del repo: `python3 odin/main.py`
  (o equivalentemente `python3 -m odin.main`).
- **Host (Ubuntu 26.04, ya configurado):** requiere estos paquetes apt (el host **no tiene pip ni venv**;
  apt es la vía oficial y todo va al Python del sistema 3.14):
  ```
  gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi python3-gi-cairo
  python3-opencv python3-numpy python3-scipy python3-matplotlib
  ```
  Sin los typelibs: `ValueError: Namespace Gtk not available`. Sin `python3-gi-cairo`: el callback
  `draw_callback` de `handleImage.py` lanza `TypeError: Couldn't find foreign struct converter for
  'cairo.Context'` (no se pinta el rectángulo de recorte). Sin opencv/numpy/...: `ModuleNotFoundError`.
- **WSL2 / WSLg:** los perfiles de VS Code usan Wayland con `WAYLAND_DISPLAY=wayland-0` y
  `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`. El perfil Vulkan fija `GSK_RENDERER=vulkan`, lo que evita
  los avisos EGL/Mesa de la selección automática en el host verificado. En ese host, Vulkan reporta
  `llvmpipe` (dispositivo CPU), por lo que no hay aceleración GPU confirmada aunque exista `/dev/dxg`.
  Forzar `GALLIUM_DRIVER=d3d12` no inicializó EGL. El perfil Cairo es el fallback de renderizado CPU.
- **GPU de la interfaz vs. procesamiento:** el renderer Vulkan/OpenGL de GTK solo acelera la interfaz
  si el controlador expone una GPU física; eso no acelera el pipeline de ODIN. El código actual no usa
  APIs OpenCV CUDA/UMat ni OpenCL; numpy, scipy y OpenCV procesan en CPU.
- Para un fallback CPU determinista en WSLg, usar el perfil `🐍 Debug CPU Cairo (Híbrido Automatico)`
  o ejecutar `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir WAYLAND_DISPLAY=wayland-0 GDK_BACKEND=wayland
  GSK_RENDERER=cairo LIBGL_ALWAYS_SOFTWARE=1 python3 odin/main.py`.
- **Devcontainer** (`.devcontainer/devcontainer.json` + `Dockerfile` raíz): entorno limpio/reproducible
  con GTK4, libadwaita, PyGObject y los requisitos de pip preinstalados. También hay dos configs de debug
  de VS Code en `.vscode/launch.json`:
  - `🐍 Debug Vulkan (Híbrido Automatico)` — Wayland; fuerza `GSK_RENDERER=vulkan`, pero no garantiza
    acceso a GPU física.
  - `🐍 Debug CPU Cairo (Híbrido Automatico)` — Wayland; fuerza `GSK_RENDERER=cairo` y
    `LIBGL_ALWAYS_SOFTWARE=1`.
- Se requiere pantalla (X11/Wayland). Ambos perfiles de `launch.json` apuntan explícitamente al socket
  Wayland de WSLg (`WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`); para Linux
  nativo hay que adaptar esos valores al socket del host.
- El Dockerfile **no copia el código fuente** (solo `requirements.txt`): la imagen es un entorno y el
  código llega con el mount del devcontainer en `/workspaces/ODIN`. Su `CMD` es
  `["python3", "odin/main.py"]` (entrypoint real, no un `main.py` raíz inexistente): solo lanza la app
  con el repo montado; un `docker run` sin mount no arranca.

## Punto de entrada y reglas de importación

- `odin/main.py` es el punto de entrada. La GUI lanza bajo el guard `if __name__ == "__main__":`,
  así que `import odin.main` **no** abre ventanas. Dos formas válidas de ejecutarlo (desde la raíz del repo):
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
  serializarse con `GLib.idle_add` (diálogos, reactivar botones) — ver el final de ese método.
- `main.py` llama `Otsu.umbralRosinYOtsu(..., histo=True)`, así que ventanas de matplotlib aparecen
  durante el procesamiento (`plt.show(block=False)` en `MtoOtsu.py`). La forzación del backend Agg en
  `DeriGauss.py` está comentada.
- Las funciones de `odin/utils/handleImage.py` toman la ventana como primer argumento (`self`) y
  leen/escriben estado GTK en ella (`recortar_imagen` asigna `self.xRecorte` / `self.yRecorte` como
  efecto secundario y necesita la geometría del widget `self.image_container`). No son helpers independientes.
- Flujo de datos: matriz OpenCV → `handle.matriz_a_pixbuf` (normaliza `uint8` no-`uint8`, convierte
  gray/BGR a RGB) → `GdkPixbuf.Pixbuf` → `Gdk.Texture` para las vistas de resultados.

## Gotchas de entorno / archivos

- `requirements.txt` está en **UTF-16LE con BOM y CRLF**. pip lo lee bien, pero grep, editores y
  git lo ven como binario. Preservar la codificación (o convertirla deliberadamente), no "arreglarlo" de paso.
- PyGObject se instala en el Dockerfile (`pip3 install pygobject pygobject-stubs`), no en
  `requirements.txt`. Las dependencias están sin fijar (unpinned).
- El diálogo de abrir archivo hardcodea rutas del host: `/home` en Linux, y
  `/mnt/c/Users/jolopez/OneDrive - Consejo Nacional...` en WSL2 (detectado porque
  `os.uname().release` contiene `"microsoft"`).
- El filtro de imágenes acepta solo bmp / tiff / jpeg. No hay imágenes de ejemplo ni fixtures en el repo —
  traer las propias para ejercitar el pipeline.
- **WSLg + Wayland rompe los popovers de GTK4**
  ([microsoft/wslg#1299](https://github.com/microsoft/wslg/issues/1299)): el listado del `Adw.ComboRow`
  de "Selección / Recorte" puede quedar detrás de la ventana principal (solo en Wayland, no en X11).
  Workaround conocido: ejecutar con `GDK_BACKEND=x11 python3 odin/main.py` (WSLg trae XWayland).
  Los perfiles actuales usan Wayland para evitar el error de memoria compartida X11 observado en este
  entorno; si se necesita probar X11, combinarlo con Cairo y verificar que la ventana no quede transparente.
- `odin/utils/uiVentanas.py` está vacío; `odin/Preprocesamiento/Convolucion/__init__.py` está
  completamente comentado (ese subpaquete está inactivo).

## Convenciones

- Identificadores, comentarios, cadenas de UI y mensajes de commit están **en español**
  (`tarea_pesada_computacional`, "Procesando", ...). Mantener el código nuevo en español para ser coherente.
- El remoto es Azure DevOps (`git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`); las ramas de largo
  plazo son `master` (HEAD de origin), `main`, `rama`, `rama-Hybrida`.
