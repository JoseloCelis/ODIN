"""
Módulo de preprocesamiento de imágenes
"""
from . import DeriGauss as kernelSeparable
from . import MagFase as MagnitudGradiente
from . import NonMaxSuppressionVectorizado as NonMaxSup
from . import MtoOtsu as Otsu
from . import DThEdgeTrackHyst as DoubleTh
from . import houghCircles as findCircles



__all__ = [
    'kernelSeparable',
    'MagnitudGradiente',
    'NonMaxSup',
    'Otsu',
    'DoubleTh',
    'findCircles'
    ]

print("Preprocesaminento was loaded")