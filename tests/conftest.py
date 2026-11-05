"""Configuración global de pytest para ODIN.

Añade src/ al path para que los tests puedan importar desde src.odin.*.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
