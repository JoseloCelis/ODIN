"""Paquete de ajustes geométricos (regresiones y ajuste de puntos a líneas y círculos).

Alias públicos (según AGENTS.md):
    find_circle, segmento_mas_largo, cobertura_angular, validar_anillo,
    tolerancia_anillo, Circulo_simple
"""

from .models import (
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
