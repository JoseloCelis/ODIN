"""Módulo de preprocesamiento de imágenes.

Alias públicos (según AGENTS.md):
    kernelSeparable -> DeriGauss
    MagnitudGradiente -> MagFase
    NonMaxSup -> NonMaxSup
    umbralRosinYOtsu, umbralOtsu -> Otsu
    EdgeTrack_Hyst -> DoubleTh
    hough_circles_vectorizado, mejor_centro, estimar_radio, estimar_radio_dominante, UMBRAL_AMBIGUEDAD, SEPARACION_AMBIGUEDAD_PX -> aproxHough
    find_circle -> circleFilter
    circuloSimple -> LSC
"""

from .models.deri_gauss import DerivGauss as kernelSeparable
from .models.mag_fase import MagFase as MagnitudGradiente
from ..Procesamiento.models.non_max_sup import NonMaxSup
from ..Procesamiento.models.otsu_rosin import umbralRosinYOtsu as Otsu, umbralOtsu
from ..Procesamiento.models.edge_track_hyst import EdgeTrack_Hyst as DoubleTh
from ..Procesamiento.models.hough_circles import (
    hough_circles_vectorizado as aproxHough,
    mejor_centro,
    estimar_radio,
    estimar_radio_dominante,
    UMBRAL_AMBIGUEDAD,
    SEPARACION_AMBIGUEDAD_PX,
)
from ..Ajustes.models.find_circle import find_circle as circleFilter, tolerancia_anillo
from ..Ajustes.models.circulo_simple import Circulo_simple as circuloSimple

__all__ = [
    "kernelSeparable",
    "MagnitudGradiente",
    "NonMaxSup",
    "Otsu",
    "umbralRosinYOtsu",
    "umbralOtsu",
    "DoubleTh",
    "EdgeTrack_Hyst",
    "aproxHough",
    "hough_circles_vectorizado",
    "mejor_centro",
    "estimar_radio",
    "estimar_radio_dominante",
    "UMBRAL_AMBIGUEDAD",
    "SEPARACION_AMBIGUEDAD_PX",
    "circleFilter",
    "find_circle",
    "circuloSimple",
    "Circulo_simple",
    "tolerancia_anillo",
]
