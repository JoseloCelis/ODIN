"""Paquete de procesamiento de imagen (detección de bordes y análisis).

Alias públicos (según AGENTS.md §4):
    LinearInterpolation, DobleThreshold, NMS_Parabolic, NMS_Gaussian,
    NonMaxSup (alias de compatibilidad/etapa ③-⑤),
    umbralRosinYOtsu, umbralOtsu, EdgeTrack_Hyst,
    hough_circles_vectorizado, mejor_centro, estimar_radio,
    estimar_radio_dominante, UMBRAL_AMBIGUEDAD, SEPARACION_AMBIGUEDAD_PX,
    Otsu (umbralRosinYOtsu), DoubleTh (EdgeTrack_Hyst),
    aproxHough (hough_circles_vectorizado)
"""

from .models import (
    NonMaxSup,
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
    umbralRosinYOtsu as Otsu,
    EdgeTrack_Hyst as DoubleTh,
    hough_circles_vectorizado as aproxHough,
)

__all__ = [
    "NonMaxSup",
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
    "Otsu",
    "DoubleTh",
    "aproxHough",
]
