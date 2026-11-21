"""Contrato de las estrategias de detección de bordes.

Modelo puro: NumPy puro, sin `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`. Una
estrategia recibe la imagen y devuelve una máscara de bordes con su misma
forma; el controlador alterna entre estrategias sin que las vistas cambien
(AGENTS.md §4, «Patrón Estrategia»).

La clase existe para alojar métodos de detección alternativos —como los
momentos de Zernike— sin tocar el pipeline actual, que hoy llega hasta la
supresión de no máximos.
"""

from abc import ABC, abstractmethod

import numpy as np


class DeteccionStrategy(ABC):
    """Familia de algoritmos de detección de bordes intercambiables."""

    @abstractmethod
    def detectar(self, imagen_np: np.ndarray, **kwargs: object) -> np.ndarray:
        """Devuelve la máscara de bordes de la imagen.

        Parameters:
            imagen_np: imagen de entrada, típicamente en escala de grises.
            **kwargs: parámetros propios de cada estrategia (umbrales,
                tamaños de ventana, etcétera).

        Returns:
            Arreglo de bordes con la misma forma que `imagen_np`.

        Raises:
            NotImplementedError: la clase base no implementa detección; cada
                subclase concreta debe hacerlo.
        """
        raise NotImplementedError
