"""Capa de modelos del dominio Ajustes.

Lógica matemática pura en NumPy/SciPy. Sin imports de gi, Gtk, Gdk, Adw ni cairo.
"""

from .find_circle import (
    find_circle,
    segmento_mas_largo,
    cobertura_angular,
    validar_anillo,
    tolerancia_anillo,
    TOLERANCIA_MAX_PX,
    FRACCION_TOLERANCIA_RADIO,
    UMBRAL_COBERTURA,
    HUECO_MAX_DEG,
    MINIMO_PUNTOS,
)
from .circulo_simple import (
    Circulo_simple,
    UMBRAL_CONDICION_NORMALIZADA,
)

__all__ = [
    "find_circle",
    "segmento_mas_largo",
    "cobertura_angular",
    "validar_anillo",
    "tolerancia_anillo",
    "TOLERANCIA_MAX_PX",
    "FRACCION_TOLERANCIA_RADIO",
    "UMBRAL_COBERTURA",
    "HUECO_MAX_DEG",
    "MINIMO_PUNTOS",
    "Circulo_simple",
    "UMBRAL_CONDICION_NORMALIZADA",
]
