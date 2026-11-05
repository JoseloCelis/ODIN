"""Capa de modelos del dominio Preprocesamiento.

Lógica matemática pura en NumPy/SciPy. Sin imports de gi, Gtk, Gdk, Adw ni cairo.
"""

from .deri_gauss import DerivGauss
from .convolucion import Conv2D, ConvR, ConvC
from .mag_fase import MagFase, MagFase as MagnitudGradiente

__all__ = [
    "DerivGauss",
    "Conv2D",
    "ConvR",
    "ConvC",
    "MagFase",
    "MagnitudGradiente",
]
