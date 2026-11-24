"""Paquete de ajustes geométricos (regresiones y ajuste de puntos a líneas y círculos).

Alias públicos (según AGENTS.md §4):
    find_circle, segmento_mas_largo, cobertura_angular, validar_anillo,
    tolerancia_anillo, Circulo_simple, LSC,
    circleFilter (find_circle), circuloSimple (Circulo_simple),
    dist_p_recta, euc_space, linea_mc, linea_robusta, linea1
"""

from .models import (
    find_circle,    segmento_mas_largo,
    cobertura_angular,
    validar_anillo,
    tolerancia_anillo,
    TOLERANCIA_MAX_PX,
    FRACCION_TOLERANCIA_RADIO,
    UMBRAL_COBERTURA,
    HUECO_MAX_DEG,
    MINIMO_PUNTOS,
    Circulo_simple,
    UMBRAL_CONDICION_NORMALIZADA,
    dist_p_recta,
    euc_space,
    linea_mc,
    linea_robusta,
    linea1,
)

# Alias públicos documentados en AGENTS.md (tabla de 9 etapas)
LSC = Circulo_simple
circuloSimple = Circulo_simple
circleFilter = find_circle

# T3 - Línea gruesa (trazo)
from .models import (
    MedicionTrazo,
    medir_trazo,
    separar_orillas,
    refinar_bordes_subpixel,
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
    "LSC",
    "circuloSimple",
    "circleFilter",
    "dist_p_recta",
    "euc_space",
    "linea_mc",
    "linea_robusta",
    "linea1",
    "MedicionTrazo",
    "medir_trazo",
    "separar_orillas",
    "refinar_bordes_subpixel",
]
