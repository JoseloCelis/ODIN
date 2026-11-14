# AGENTS.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Bienvenido al repositorio del software **ODIN** (*Otsu + Directional + Intensity + Non-Maximum Suppression*).
Este documento define las directrices arquitectónicas, la estructura modular actual (`src/odin/`) y los
protocolos de desarrollo.

---

## 1. Visión General del Proyecto y Estado del Repositorio

**ODIN** es una aplicación de escritorio de alto rendimiento desarrollada en Python 3.12+
(**GTK 4** + **Libadwaita** mediante **PyGObject**) orientada al procesamiento digital de imágenes,
detección de bordes a nivel subpíxel y medición de características geométricas (anchos de línea,
centros y radios de círculos) en imágenes BMP, TIFF y JPEG.

### Estado del Código y Testing

* **Punto de Entrada Real:** Se ejecuta desde la raíz del repositorio mediante
  `python3 main.py` (o `python3 -m odin`). El arranque se delega a `src/odin/bootstrap.py`
  y la ventana principal vive en `src/odin/views/main_window.py`.
* **Suite de Pruebas Unitarias:** 183 casos en `tests/` ejecutados con `pytest`:

  ```bash
  python3 -m pytest tests -v
  ```

* **Prueba de Humo de la UI:**

  ```bash
  python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print(f'GTK {Gtk.MAJOR_VERSION} OK, Adw OK')"
  ```

---

## 2. Configuración y Ejecución Multientorno (Entorno Híbrido)

El proyecto opera de forma transparente entre tres estaciones de trabajo
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

## 3. Estructura del Código (`src/odin/`)

El código fuente reside íntegramente en `src/odin/` con arquitectura MVC/MVP por dominios.

### Layout Actual

```text
src/
├── main.py                     # Punto de entrada (delega a odin.views.main_window.main)
└── odin/
    ├── __init__.py
    ├── __main__.py             # Permite `python3 -m odin`
    ├── bootstrap.py            # Inicialización: logging, paths, entorno, imports pesados
    ├── utils/
    │   ├── __init__.py
    │   └── handleImage.py      # Puente OpenCV ↔ GdkPixbuf / Gdk.Texture (alias `handle`)
    ├── views/
    │   ├── __init__.py
    │   ├── main_window.py      # Ventana principal (Adw.ApplicationWindow)
    │   ├── interactive_viewer.py   # VisualizadorInteractivo (recorte Cairo)
    │   └── compartido/         # Vistas genéricas reutilizables entre dominios
    ├── controllers/
    │   ├── __init__.py
    │   ├── main_controller.py  # Orquestador principal (carga, pipeline, hilos)
    │   └── worker_thread.py    # Threading + GLib.idle_add para UI
    ├── Preprocesamiento/       # Dominio: etapas ①-②
    │   ├── __init__.py         # Aliases públicos: kernelSeparable, MagnitudGradiente
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── convolucion.py  # Conv2D/ConvC/ConvR (convolución 1D separable)
    │   │   ├── deri_gauss.py   # Etapa ①: kernel derivada-gaussiana separable
    │   │   └── mag_fase.py     # Etapa ②: magnitud y dirección del gradiente
    │   ├── views/
    │   └── controllers/
    ├── Procesamiento/          # Dominio: etapas ③-⑦
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── non_max_sup.py        # Etapa ③ y ⑤: NMS vectorizado + doble umbral
    │   │   ├── otsu_rosin.py         # Etapa ④: umbrales Otsu y Rosin
    │   │   ├── edge_track_hyst.py    # Etapa ⑥: histéresis (DoubleTh)
    │   │   ├── hough_circles.py      # Etapa ⑦: centro aproximado (aproxHough)
    │   │   └── strategies/           # Patrón Estrategia (pendiente)
    │   │       └── base_strategy.py  # DeteccionStrategy (abstracto)
    │   ├── views/
    │   └── controllers/
    └── Ajustes/                # Dominio: etapas ⑧-⑨
        ├── __init__.py
        ├── models/
        │   ├── __init__.py
        │   ├── find_circle.py        # Etapa ⑧: filtrado anillo ±10 px (circleFilter)
        │   └── circulo_simple.py     # Etapa ⑨: ajuste círculo simple (LSC)
        ├── views/
        └── controllers/
```

### Pipeline de Procesamiento Subpíxel (9 Etapas)

| # | Módulo (`models/`) | Alias Público | Rol |
|---|-------------------|---------------|-----|
| ① | `Preprocesamiento/models/deri_gauss.py` | `kernelSeparable` | Gradiente con kernel derivada-gaussiana separable |
| ② | `Preprocesamiento/models/mag_fase.py` | `MagnitudGradiente` | Magnitud y dirección del gradiente |
| ③ | `Procesamiento/models/non_max_sup.py` | `NonMaxSup` | Supresión de no máximos (interpolación subpíxel) |
| ④ | `Procesamiento/models/otsu_rosin.py` | `Otsu` | Umbrales Otsu y Rosin |
| ⑤ | `Procesamiento/models/non_max_sup.py` | `NonMaxSup` | Doble umbral |
| ⑥ | `Procesamiento/models/edge_track_hyst.py` | `DoubleTh` | Histéresis → bordes finales |
| ⑦ | `Procesamiento/models/hough_circles.py` | `aproxHough` | Centro aproximado del círculo (Hough) |
| ⑧ | `Ajustes/models/find_circle.py` | `circleFilter` | Filtrado de puntos en anillo ±10 px |
| ⑨ | `Ajustes/models/circulo_simple.py` | `LSC` | Ajuste del círculo simple (x, y, r) |

---

## 4. Patrones de Diseño y Reglas de Importación

### 1. Modelo-Vista-Controlador (MVC / MVP)

* **Modelo (`src/odin/<dominio>/models/`):** Matemática pura en NumPy/SciPy, 100% independiente de `gi`, `Gtk`, `Gdk`, `Adw` o `cairo`. Un `<dominio>` por área de negocio (`Preprocesamiento`, `Procesamiento`, `Ajustes`).
* **Vista (`src/odin/<dominio>/views/`):** Interfaz gráfica adaptativa en GTK 4 / Libadwaita y dibujado vectorial en Cairo. Las vistas genéricas compartidas (p. ej. `VisualizadorInteractivo` en `src/odin/views/compartido/`) evitan duplicación por dominio.
* **Controlador (`src/odin/<dominio>/controllers/`):** Orquestación de eventos de la UI y ejecución asíncrona de tareas pesadas en hilos secundarios.

### 2. Patrón Estrategia (Strategy Pattern)

Familia de algoritmos encapsulada bajo la interfaz abstracta
`DeteccionStrategy` (`src/odin/Procesamiento/models/strategies/base_strategy.py`).
Permite alternar la estrategia de procesamiento en tiempo de ejecución sin modificar
Vistas ni Controladores.

### 3. Reglas de Importación y Aliases

* Ejecución soportada: `python3 main.py` (script) y `python3 -m odin` (módulo).
* Los módulos de algoritmos se consumen a través de los aliases expuestos en los
  `__init__.py` de cada dominio (ej. `from odin.Preprocesamiento import kernelSeparable`,
  `from odin.utils import handle`).
* **No importar archivos de algoritmos directamente**; usar siempre el alias público.

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

## 6. Skills — Carga y Registro (Gentle AI)

El proyecto usa **Gentle AI Skills** como unidades de conocimiento reutilizables para tareas
recurrentes (ramas/PR, commits, revisión, diseño, issues, etc.).

### Ubicación y Estructura

* Directorio raíz de skills: `.skills/` (en la raíz del repo).
* Cada skill es una carpeta con su `SKILL.md` (frontmatter + instrucciones).
* Ejemplos instalados: `skill-creator/`, `pytest/`, `github-pr/`, `angular/`, `django-drf/`, etc.

### Protocolo de Carga (Skill Registry Protocol)

1. **El padre resuelve rutas una vez por sesión** bajo `## Skills to load before work`.
2. Los subagentes leen esos `SKILL.md` primero (`paths-injected`) o reportan rutas no disponibles.
3. Fallbacks documentados en `orchestrator-skills.md`.

### Discovery Intent-Driven

Para peticiones con forma de skill, `<available_skills>` es solo ayuda de descubrimiento,
nunca anula una petición concreta. Ver `orchestrator-skills.md` para orden y hints.

### Creación y Mejora de Skills

* **Crear:** trigger `/skill-creation` → `gentle-ai-skill-creator` (frontmatter válido obligatorio).
* **Mejorar/Auditar:** trigger `improve skills` / `audit skills` → `gentle-ai-skill-improver`.
* **Actualizar registro:** trigger `update skills` / `actualizar skills` → `gentle-ai-skill-registry`.

### Skills Propias del Proyecto (por añadir)

Cuando el proyecto requiera skills específicas (p. ej. `odin-pipeline`, `odin-testing`,
`odin-gtk-debug`), se crearán bajo `.skills/odin-*` siguiendo el mismo protocolo.

---

## 7. Convenciones, Memoria y Estado del Proyecto

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

## 8. Referencias Rápidas (Archivos Clave)

| Propósito | Archivo |
|-----------|---------|
| Arranque y bootstrap | `src/odin/bootstrap.py` |
| Ventana principal | `src/odin/views/main_window.py` |
| Controlador principal | `src/odin/controllers/main_controller.py` |
| Worker thread (async) | `src/odin/controllers/worker_thread.py` |
| Aliases Preprocesamiento | `src/odin/Preprocesamiento/__init__.py` |
| Aliases Procesamiento | `src/odin/Procesamiento/__init__.py` |
| Aliases Ajustes | `src/odin/Ajustes/__init__.py` |
| Utils imagen (handle) | `src/odin/utils/handleImage.py` |
| Estrategia base | `src/odin/Procesamiento/models/strategies/base_strategy.py` |
| Tests | `tests/` (pytest) |
| Memoria proyecto | `MEMORY.md` |
| Specs Kiro | `.kiro/specs/` |

---