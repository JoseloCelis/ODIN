#!/usr/bin/env python3
"""Punto de entrada directo de ODIN.

Ejecución para desarrollo diario:
    python3 main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from odin.views.main_window import main


if __name__ == "__main__":
    sys.exit(main(sys.argv))
