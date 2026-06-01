"""
Módulo de preprocesamiento de imágenes
"""
from . import DeriGauss as kernelSeparable
from . import MagFase as MagnitudGradiente
from . import NonMaxSuppressionVectorizado as NonMaxSup
from . import MtoOtsu as Otsu
from . import DThEdgeTrackHyst as DoubleTh



__all__ = [
    'kernelSeparable',
    'MagnitudGradiente',
    'NonMaxSup',
    'Otsu',
    'DoubleTh'    
]

print("Preprocesaminento was loaded")