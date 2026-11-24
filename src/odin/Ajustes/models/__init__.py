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
from .linea_robusta import (
    dist_p_recta,
    euc_space,
    linea_mc,
    linea_robusta,
    linea1,
)
from .trazo_linea import (
    MedicionTrazo,
    medir_trazo,
    separar_orillas,
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
    "dist_p_recta",
    "euc_space",
    "linea_mc",
    "linea_robusta",
    "linea1",
]
