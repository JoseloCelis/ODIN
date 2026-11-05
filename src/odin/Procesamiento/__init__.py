"""Paquete de procesamiento de imagen (detección de bordes y análisis).

Alias públicos (según AGENTS.md):
    LinearInterpolation, DobleThreshold, NMS_Parabolic, NMS_Gaussian,
    umbralRosinYOtsu, umbralOtsu, EdgeTrack_Hyst,
    hough_circles_vectorizado, mejor_centro, estimar_radio,
    estimar_radio_dominante, UMBRAL_AMBIGUEDAD, SEPARACION_AMBIGUEDAD_PX
"""

from .models import (
    LinearInterpolation,
    DobleThreshold,
    NMS_Parabolic,
    NMS_Gaussian,
    umbralRosinYOtsu,
    umbralOtsu,
    EdgeTrack_Hyst,
    hough_circles_vectorizado,
    mejor_centro,
    estimar_radio,
    estimar_radio_dominante,
    UMBRAL_AMBIGUEDAD,
    SEPARACION_AMBIGUEDAD_PX,
)

__all__ = [
    "LinearInterpolation",
    "DobleThreshold",
    "NMS_Parabolic",
    "NMS_Gaussian",
    "umbralRosinYOtsu",
    "umbralOtsu",
    "EdgeTrack_Hyst",
    "hough_circles_vectorizado",
    "mejor_centro",
    "estimar_radio",
    "estimar_radio_dominante",
    "UMBRAL_AMBIGUEDAD",
    "SEPARACION_AMBIGUEDAD_PX",
]
