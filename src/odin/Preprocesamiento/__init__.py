"""Módulo de preprocesamiento de imágenes.

Alias públicos (según AGENTS.md):
    kernelSeparable -> DeriGauss
"""

from .models.deri_gauss import DerivGauss as kernelSeparable

__all__ = [
    "kernelSeparable",
]
