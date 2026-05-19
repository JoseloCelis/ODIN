"""
Módulo de preprocesamiento de imágenes
"""
from . import DeriGauss as kernelSeparable
from . import MagFase as MagFaseGradiente
#from .Convolucion import Convolucion2D

__all__ = [
    'kernelSeparable',
    'MagFaseGradiente'
    #'Convolucion2D'
]

print("Preprocesaminento was loaded")