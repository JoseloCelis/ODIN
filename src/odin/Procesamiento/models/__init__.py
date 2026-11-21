"""Capa de modelos del dominio Procesamiento.

Lógica matemática pura en NumPy/SciPy. Sin imports de gi, Gtk, Gdk, Adw ni cairo.
"""

from .non_max_sup import (
    NonMaxSup,
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
from .hough_lineas import (
    CandidatasLineas,
    acumulador_lineas,
    candidatas_lineas,
    hough_lineas,
    reducir_candidatas,
    NUM_THETAS,
    PASO_RHO,
    PASO_THETA,
)
from .geometria import (
    EvidenciaGeometria,
    Geometria,
    clasificar_geometria,
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
    "CandidatasLineas",
    "acumulador_lineas",
    "candidatas_lineas",
    "hough_lineas",
    "reducir_candidatas",
    "NUM_THETAS",
    "PASO_RHO",
    "PASO_THETA",
    "EvidenciaGeometria",
    "Geometria",
    "clasificar_geometria",
]
