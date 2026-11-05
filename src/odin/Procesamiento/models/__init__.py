"""Capa de modelos del dominio Procesamiento.

Lógica matemática pura en NumPy/SciPy. Sin imports de gi, Gtk, Gdk, Adw ni cairo.
"""

from .non_max_sup import (
    LinearInterpolation,
    DobleThreshold,
    NMS_Parabolic,
    NMS_Gaussian,
)
from .otsu_rosin import umbralRosinYOtsu, umbralOtsu
from .edge_track_hyst import EdgeTrack_Hyst
from .hough_circles import (
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
