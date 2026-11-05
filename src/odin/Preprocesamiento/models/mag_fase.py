"""Magnitud y dirección del gradiente (etapa ②).

Entrada y salida: numpy.ndarray puro. Sin dependencias de UI (gi, Gtk, Gdk,
Adw, cairo, matplotlib).
"""

import numpy as np


def MagFase(GrX, GrY):
    """Magnitud y fase del gradiente.

    Calcula MGr = hypot(GrX, GrY) normalizada a [0, 1] y angle = atan2 en
    grados, rango (-180, 180]. Función pura: sin UI, sin efectos
    secundarios.
    """
    # Entradas vacías: devolvemos tuplas vacías sin dejar que NumPy
    # lance ValueError interno (contrato R5.1, divergencia D3 resuelta).
    if GrX.size == 0 or GrY.size == 0:
        return np.empty(0), np.empty(0)

    # R1: magnitud via hypot (evita desbordes de sqrt(x^2+y^2))
    MGr = np.hypot(GrX, GrY)
    MGr_max = np.max(MGr)  # D2 resuelto: np.abs era redundante (hypot >= 0)
    if MGr_max > 0:
        MGr = MGr / MGr_max

    # R3: ángulo en grados, rango (-180, 180]
    angle = np.atan2(GrY, GrX) * 180 / np.pi
    angle = np.where(angle == -180.0, 180.0, angle)

    return MGr, angle
