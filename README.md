# ODIN

**ODIN** (*Otsu + Directional + Intensity + Non-Maximum Suppression*) es una aplicación de escritorio de alto rendimiento para el **procesamiento digital de imágenes**: detección de bordes a nivel **subpíxel** y medición de características geométricas (anchos de línea, centros y radios de círculo) en imágenes **BMP, TIFF y JPEG**.

Construida en **Python 3.12+** con **GTK 4 + Libadwaita** (PyGObject) y acelerada con OpenCV/NumPy/SciPy.

## Características

- Detección de bordes subpíxel mediante pipeline de 9 etapas (gradiente separable → NMS → umbrales Otsu/Rosin → histéresis → Hough → ajuste de círculo por mínimos cuadrados).
- Interfaz gráfica nativa GNOME con visualizador interactivo (recorte Cairo).
- Mediciones geométricas: anchos de línea, centros y radios de círculos.
- Suite de pruebas: unitarias por dominio, integración y propiedades (Hypothesis).

## Pipeline de procesamiento

| # | Etapa | Alias público | Rol |
|---|-------|---------------|-----|
| ① | `Preprocesamiento/models/deri_gauss.py` | `kernelSeparable` | Gradiente con kernel derivada-gaussiana separable |
| ② | `Preprocesamiento/models/mag_fase.py` | `MagnitudGradiente` | Magnitud y dirección del gradiente |
| ③ | `Procesamiento/models/non_max_sup.py` | `NonMaxSup` | Supresión de no máximos (interpolación subpíxel) |
| ④ | `Procesamiento/models/otsu_rosin.py` | `Otsu` | Umbrales Otsu y Rosin |
| ⑤ | `Procesamiento/models/non_max_sup.py` | `NonMaxSup` | Doble umbral |
| ⑥ | `Procesamiento/models/edge_track_hyst.py` | `DoubleTh` | Histéresis → bordes finales |
| ⑦ | `Procesamiento/models/hough_circles.py` | `aproxHough` | Centro aproximado del círculo (Hough) |
| ⑧ | `Ajustes/models/find_circle.py` | `circleFilter` | Filtrado de puntos en anillo ±10 px |
| ⑨ | `Ajustes/models/circulo_simple.py` | `LSC` | Ajuste del círculo simple `(x, y, r)` |

Los algoritmos se consumen **exclusivamente** a través de los aliases públicos de cada dominio (`from odin.Preprocesamiento import kernelSeparable`); nunca importando los módulos directamente.

## Requisitos

- Python 3.12+
- GTK 4 + Libadwaita vía PyGObject
- OpenCV, NumPy, SciPy

En Ubuntu / Linux Mint (paquetes del sistema):

```bash
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi python3-gi-cairo \
  python3-opencv python3-numpy python3-scipy python3-matplotlib
```

## Ejecución

Desde la raíz del repositorio:

```bash
python3 main.py
# o
python3 -m odin
```

## Pruebas

```bash
python3 -m pytest tests -v
```

En entorno sin servidor gráfico (CI / WSL):

```bash
xvfb-run -a ODIN_TEST_LENTO=1 python3 -m pytest tests -q
```

Smoke test de la UI:

```bash
python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print(f'GTK {Gtk.MAJOR_VERSION} OK, Adw OK')"
```

## Estructura

Arquitectura MVC por dominios de negocio bajo `src/odin/`:

```text
src/odin/
├── bootstrap.py          # Logging, paths, entorno, imports pesados
├── utils/handleImage.py  # Puente OpenCV ↔ GdkPixbuf/Gdk.Texture (alias `handle`)
├── views/                # Ventana principal + visualizador interactivo (Cairo)
├── controllers/          # Orquestación de UI + hilos (GLib.idle_add)
├── Preprocesamiento/     # Etapas ①-②
├── Procesamiento/        # Etapas ③-⑦
└── Ajustes/              # Etapas ⑧-⑨
```

- **Modelo**: matemática pura NumPy/SciPy, sin dependencias de UI, vectorizada.
- **Vista**: GTK 4 / Libadwaita imperativo (sin `.blp` ni GtkBuilder).
- **Controladores**: pesado en `threading.Thread`, resultados a la vista con `GLib.idle_add`.

## Releases

Versiones y notas: [Releases](https://github.com/JoseloCelis/ODIN/releases)

Cada release incluye el archivo `odin-<versión>.zip` con el árbol del tag.

<!-- Captura de pantalla: pendiente -->
