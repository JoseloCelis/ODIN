"""Paquete de preprocesamiento (etapas ①-②).

Alias públicos (según AGENTS.md §4):
    kernelSeparable -> DerivGauss
    MagnitudGradiente -> MagFase

El resto de la API pública del pipeline vive en su dominio:
    from odin.Procesamiento import NonMaxSup, Otsu, DoubleTh, aproxHough
    from odin.Ajustes import circleFilter, LSC
"""

from .models.deri_gauss import DerivGauss as kernelSeparable
from .models.mag_fase import MagFase as MagnitudGradiente

__all__ = [
    "kernelSeparable",
    "MagnitudGradiente",
]
