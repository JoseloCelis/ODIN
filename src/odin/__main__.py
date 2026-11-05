"""Punto de entrada del paquete odin.

Permite lanzar la GUI directamente desde terminal con:
    python3 -m src.odin
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from odin.views.main_window import main

if __name__ == "__main__":
    main()
