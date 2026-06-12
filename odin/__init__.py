# Importamos las funciones principales para que se puedan llamar desde src directamente
from .utils import handle
from .Preprocesamiento import kernelSeparable, MagnitudGradiente, Otsu, NonMaxSup, DoubleTh, aproxHough, circleFilter, LSC
#from .Preprocesamiento import Convolucion2D

__all__ = [
    'handle',
    'kernelSeparable',
    'MagnitudGradiente',
    'Otsu',
    'NonMaxSup',
    'DoubleTh',
    'aproxHough',
    'circleFilter',
    'LSC'
]

# Definimos la versión de tu software
__version__ = "1.0.0"
__author__ = "JCelis / ODIN Team"

# Mensaje de inicialización (opcional)
print(f"Inicializando paquete ODIN Core v{__version__}...")


