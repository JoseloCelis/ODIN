"""Estrategias de detección de bordes intercambiables.

Expone el contrato público del paquete: las subclases concretas se registran en
el controlador y las vistas no cambian (AGENTS.md §4).
"""

from .base_strategy import DeteccionStrategy

__all__ = ["DeteccionStrategy"]
