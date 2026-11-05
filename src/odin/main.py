#!/usr/bin/env python3
"""Punto de entrada directo de ODIN (dentro de src/odin/).

Ejecución para desarrollo diario:
    python3 src/odin/main.py
    python3 -m src.odin.main
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from odin.bootstrap import run_bootstrap, DisplayValidator, StartupLogger
from odin.views.main_window import main


if __name__ == "__main__":
    sys.exit(main(sys.argv))
