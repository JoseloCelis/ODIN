"""Configuración común de la suite de ODIN.

Agrega la raíz del repositorio y este directorio al sys.path para que
`odin.*` y las utilidades de referencia se puedan importar tanto con
`python3 -m pytest` como con el script `pytest`.

Fuerza el backend Agg de matplotlib: la etapa 4 dibuja el histograma vía
`GLib.idle_add`, y en un entorno sin pantalla no debe intentarse abrir
ventanas interactivas.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_TESTS = Path(__file__).resolve().parent

for ruta in (str(RAIZ), str(DIR_TESTS)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import matplotlib

matplotlib.use("Agg")
