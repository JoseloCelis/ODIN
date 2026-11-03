# AGENTS.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Bienvenido al repositorio del software **ODIN** (*Otsu + Directional + Intensity + Non-Maximum Suppression*).
Este documento define las directrices arquitectónicas, la estructura modular actual (legacy) y la
proyectada (objetivo `src/odin/`), la configuración multientorno y los protocolos de desarrollo.

---

## 1. Visión General del Proyecto y Estado del Repositorio

**ODIN** es una aplicación de escritorio de alto rendimiento desarrollada en Python 3.12+
(**GTK 4** + **Libadwaita** mediante **PyGObject**) orientada al procesamiento digital de imágenes,
detección de bordes a nivel subpíxel y medición de características geométricas (anchos de línea,
centros y radios de círculos) en imágenes BMP, TIFF y JPEG.

### Estado del Código y Testing

* **Punto de Entrada Real:** Se ejecuta desde la raíz del repositorio mediante
  `python3 odin/main.py` o `python3 -m odin.main`. (No existe un archivo `main.py` en la raíz).
* **Suite de Pruebas Unitarias:** Incluye 44 casos de prueba en `tests/` ejecutados con `pytest`
  que cubren las etapas 1 a 5 y el pipeline completo, utilizando referencias independientes de
  convolución, NMS y Otsu:

  ```bash
  python3 -m pytest tests -v
  ```

* **Prueba de Humo de la UI:** Verificación rápida del arranque del entorno GTK 4 y Libadwaita:

  ```bash
  python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print(f'GTK {Gtk.MAJOR_VERSION} OK, Adw OK')"
  ```

---

## 2. Configuración y Ejecución Multientorno (Entorno Híbrido)

El proyecto está preparado para operar de forma transparente entre tres estaciones de trabajo
compartiendo la misma infraestructura (`.devcontainer/devcontainer.json`,
`.vscode/launch.json` y `.vscode/settings.json`).

### Estaciones de Trabajo Soportadas

1. **PC Personal (Casa) — Linux Nativo (Linux Mint / Ubuntu):**
   * Conexión gráfica directa mediante el socket nativo del host (`/tmp/.X11-unix`).
   * Dependencias vía `apt` (el host no cuenta con `pip` ni `venv`):
     `gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi python3-gi-cairo python3-opencv python3-numpy
     python3-scipy python3-matplotlib`

2. **PC Laboral #1 — Windows + WSL2 / WSLg con GPU NVIDIA:**
   * Aceleración gráfica mediante passthrough de librerías (`/usr/lib/wsl/lib`, `/mnt/wslg`).
   * Perfil VS Code: **`🐍 Debug GPU (Híbrido Automatico)`**.

3. **PC Laboral #2 — Windows + WSL2 / WSLg con GPU AMD Radeon:**
   * Perfil principal: **`🐍 Debug GPU (Híbrido Automatico)`** con aceleración Vulkan.
   * Perfil fallback: **`🐍 Debug CPU Cairo (Híbrido Automatico)`** con
     `LIBGL_ALWAYS_SOFTWARE=1` y `GSK_RENDERER=cairo`.

### Variables de Entorno Clave

* `PYTHONPATH="${workspaceFolder}"`
* `GTK_A11Y=none`
* `GSK_RENDERER=vulkan` o `cairo` (según perfil)
* `GDK_BACKEND=wayland,x11`
* `DISPLAY="${env:DISPLAY}"`
* `WAYLAND_DISPLAY="${env:WAYLAND_DISPLAY}"`
* `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`

### Configuración del Devcontainer

`.devcontainer/devcontainer.json` monta simultáneamente los sockets gráficos para Linux Nativo
(`/tmp/.X11-unix`) y WSLg (`/usr/lib/wsl`, `/mnt/wslg`), garantizando que la aplicación inicie
sin modificaciones adicionales en cualquiera de los tres entornos.

---

## 3. Estructura Actual del Código (Legacy) vs. Arquitectura Objetivo

El sistema vive actualmente en la estructura funcional `odin/`, proyectada para refactorizarse
progresivamente hacia una arquitectura MVC/MVP y Estrategia bajo el paquete **`src/odin/`**.

### A. Estructura Actual del Código (`odin/`)

* `odin/main.py`: Punto de entrada y ventana principal (`MainWindow(Adw.ApplicationWindow)`).
  Contiene `MainWindow._tarea_pesada_computacional`, que orquesta el pipeline en un hilo
  secundario.
* `odin/utils/handleImage.py` (alias `handle`): Carga de imágenes, conversión a pixbuf/texturas
  (`matriz_a_pixbuf`), recortes y renderizado en Cairo (`VisualizadorInteractivo`).
* `odin/utils/uiVentanas.py`: Vacío.
* `odin/Preprocesamiento/`: Módulos de algoritmos matemáticos individuales expuestos mediante
  aliases en `__init__.py`.
* `odin/Preprocesamiento/Convolucion/`: Subpaquete de convoluciones separables 1D
  (`Conv2D.py`, `ConvC.py`, `ConvR.py`; su `__init__.py` está comentado).

### Pipeline Actual de Procesamiento Subpíxel (9 Etapas)

| # | Archivo | Alias Público | Rol del Algoritmo |
|---|---------|---------------|-------------------|
| ① | `DeriGauss.py` | `kernelSeparable` | Gradiente con kernel derivada-gaussiana separable |
| ② | `MagFase.py` | `MagnitudGradiente` | Magnitud y dirección del gradiente |
| ③ | `NonMaxSuppressionVectorizado.py` | `NonMaxSup` | Supresión de no máximos (interpolación subpíxel) |
| ④ | `MtoOtsu.py` | `Otsu` | Umbrales Otsu y Rosin |
| ⑤ | `NonMaxSuppressionVectorizado.py` | `NonMaxSup` | Doble umbral |
| ⑥ | `DThEdgeTrackHyst.py` | `DoubleTh` | Histéresis → bordes finales |
| ⑦ | `houghCircles.py` | `aproxHough` | Centro aproximado del círculo (Hough) |
| ⑧ | `findCircle.py` | `circleFilter` | Filtrado de puntos en anillo ±10 px |
| ⑨ | `circuloSimple.py` | `LSC` | Ajuste del círculo simple (x, y, r) |

### B. Arquitectura Objetivo (`src/odin/` Layout — Refactorización Pendiente)

```text
ODIN/
├── .devcontainer/                  # Entorno virtualizado híbrido
├── .vscode/                        # Configuración de depuración y workspace
├── config/                         # Parámetros y persistencia (config_default.yaml)
├── data/                           # Imágenes de prueba y resultados exportados
├── src/                            # Directorio raíz del código fuente
│   └── odin/                       # Paquete principal ODIN refactorizado
│       ├── models/                 # Lógica matemática pura en NumPy/SciPy (sin UI)
│       │   └── strategies/         # Patrón Estrategia (base_strategy.py)
│       ├── views/                  # Interfaz gráfica GTK 4 / Libadwaita / Cairo
│       ├── controllers/            # Orquestación de eventos e hilos asíncronos
│       └── utils/                  # Puente OpenCV ↔ GdkPixbuf / Gdk.Texture
├── tests/                          # Suite de pruebas unitarias con pytest
├── main.py                         # Punto de entrada raíz definitivo
└── requirements.txt                # Dependencias en codificación UTF-8
```

---

## 4. Patrones de Diseño y Reglas de Importación

### 1. Modelo-Vista-Controlador (MVC / MVP)

* **Modelo (`src/odin/models/`):** Matemática pura en NumPy/SciPy, 100% independiente de
  `gi`, `Gtk`, `Gdk`, `Adw` o `cairo`.
* **Vista (`src/odin/views/`):** Interfaz gráfica adaptativa en GTK 4 / Libadwaita y
  dibujado vectorial en Cairo.
* **Controlador (`src/odin/controllers/`):** Orquestación de eventos de la UI y ejecución
  asíncrona de tareas pesadas en hilos secundarios.

### 2. Patrón Estrategia (Strategy Pattern)

Familia de algoritmos encapsulada bajo la interfaz abstracta
`DeteccionStrategy` (`src/odin/models/strategies/base_strategy.py`). Permite alternar la
estrategia de procesamiento en tiempo de ejecución sin modificar Vistas ni Controladores.

### 3. Reglas de Importación y Aliases

* Admite ejecución como script (`python3 odin/main.py`) o como módulo (`python3 -m odin.main`).
* Los módulos de algoritmos deben consumirse a través de los aliases expuestos en los archivos
  `__init__.py` (ej. `MtoOtsu as Otsu`, `houghCircles as aproxHough`, `handleImage as handle`).

---

## 5. Reglas Estrictas para Agentes de IA y Desarrolladores

### Capa del Modelo (Lógica Matemática)

1. **Aislamiento Total de UI:** Queda prohibido importar `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`
   dentro de la capa del Modelo.
2. **Arreglos Matriciales Puros:** Las funciones matemáticas reciben y retornan
   `numpy.ndarray` o tipos numéricos nativos.
3. **Vectorización Obligatoria:** Evitar bucles `for` anidados sobre píxeles; usar broadcasting,
   slicing, máscaras booleanas y funciones vectorizadas de NumPy/SciPy.
4. **Histéresis No Recursiva:** Usar `scipy.ndimage` / `cv2.connectedComponents`; no
   reintroducir recursión que cause Stack Overflow.

### Capa de la Vista (UI)

1. Solo posicionamiento de widgets, estilos y renderizado. Sin algoritmos ni convoluciones.
2. **Estabilidad de Renderizado:** `set_hexpand(True)` / `set_expand(True)` en el widget central
   para evitar que colapse a 0 píxeles.

### Controladores e Hilos

1. **Nunca** invocar métodos de GTK desde un hilo secundario.
2. Procesamiento pesado en `threading.Thread`; resultados de vuelta a la Vista con
   `GLib.idle_add(callback)`.

### Extensión mediante Estrategia

1. Heredar de `DeteccionStrategy`, implementar
   `detectar(self, imagen_np: np.ndarray, **kwargs) -> np.ndarray`.
2. Registrar la estrategia en el controlador sin modificar las vistas.

---

## 6. Convenciones, Memoria y Estado del Proyecto

* **Idioma:** Identificadores, comentarios, cadenas de UI y mensajes de commit en **Español**.
* **Codificación:** `requirements.txt` se mantiene obligatoriamente en **UTF-8**.
* **Commits Convencionales:** `<tipo>[<scope>]: <descripción>` (`feat`, `fix`, `refactor`,
  `docs`, `test`, ...). No agregar "Co-Authored-By" ni atribución de IA.
* **Repositorio Remoto:** Azure DevOps (`git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`) con
  ramas de largo plazo `master`, `main`, `rama`, `rama-Hybrida`.
* **Memoria del Proyecto (`MEMORY.md`):** Ledger conciso (~50 líneas) con estado actual,
  decisiones y próximos pasos. En caso de discrepancia entre `MEMORY.md` y Engram, preguntar al
  usuario cuál prevalece.
* **Datos Sensibles:** Nunca guardar claves, tokens ni datos personales.
* **Descarga de Core:** El archivo `core.*` en la raíz (dump de crash de GTK) no debe
  commitearse; agregar a `.gitignore` o eliminar.

---
