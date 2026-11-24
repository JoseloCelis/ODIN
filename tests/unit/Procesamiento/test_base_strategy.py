"""Contrato de la estrategia de detección de bordes (AGENTS.md §4, decisión L6).

La clase abstracta existe para alojar métodos alternativos de detección —como
los momentos de Zernike— sin modificar vistas ni controladores. Estas pruebas
fijan el contrato, no un algoritmo concreto.
"""

import numpy as np
import pytest

from src.odin.Procesamiento.models.strategies import DeteccionStrategy


def test_la_estrategia_abstracta_no_se_puede_instanciar():
    """Una estrategia sin `detectar` no es una estrategia."""
    with pytest.raises(TypeError):
        DeteccionStrategy()


def test_una_subclase_sin_detectar_tampoco_se_puede_instanciar():
    class Incompleta(DeteccionStrategy):
        pass

    with pytest.raises(TypeError):
        Incompleta()


def test_una_subclase_concreta_devuelve_la_mascara_de_bordes():
    class Constante(DeteccionStrategy):
        def detectar(self, imagen_np: np.ndarray, **kwargs: object) -> np.ndarray:
            return np.zeros_like(imagen_np)

    imagen = np.zeros((4, 5))
    salida = Constante().detectar(imagen)

    assert salida.shape == imagen.shape
    assert not salida.any()


def test_los_kwargs_llegan_a_la_estrategia():
    """Cada estrategia recibe sus propios parámetros por palabra clave."""
    class Registradora(DeteccionStrategy):
        def __init__(self) -> None:
            self.visto: dict[str, object] = {}

        def detectar(self, imagen_np: np.ndarray, **kwargs: object) -> np.ndarray:
            self.visto = dict(kwargs)
            return np.zeros_like(imagen_np)

    estrategia = Registradora()
    estrategia.detectar(np.zeros((3, 3)), sigma=2.0, umbral=0.5)

    assert estrategia.visto == {"sigma": 2.0, "umbral": 0.5}
