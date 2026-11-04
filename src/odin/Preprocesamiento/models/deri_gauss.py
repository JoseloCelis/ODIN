"""Kernel derivada-gaussiana separable (etapa ①).

Entrada y salida: numpy.ndarray puro. Sin dependencias de UI (gi, Gtk, Gdk,
Adw, cairo, matplotlib).
"""

import numpy as np

from .convolucion import Conv2D


def DerivGauss(E, sigma, wk, wConv, wr):
    """Gradiente con kernel derivada-gaussiana separable.

    Recibe y retorna numpy.ndarray. Pureza de modelo: sin UI.
    """
    nr, nc = E.shape[:2]

    # Validar sigma ANTES de dimensionar gk/dgk con n = 3*sigma
    # (con sigma negativo, np.zeros(n*2+1) lanzaría ValueError antes del guard)
    if sigma <= 0:
        return np.zeros_like(E), np.zeros_like(E)

    #//////////////////////// genera kernel derivada gaussiana
    ds = 0
    s2 = 2 * pow(sigma, 2)
    n = int(3 * sigma)
    gk = np.zeros((n * 2) + 1)
    dgk = np.zeros((n * 2) + 1)
    k = 0
    s = 0
    for i in range(-n, n + 1):
        gk[k] = np.exp(-(i ** 2) / s2)
        s = s + gk[k]
        k = k + 1
    k = 0
    s2 = 1.0 / pow(sigma, 2)
    for i in range(-n, n + 1):
        gk[k] = gk[k] / s
        dgk[k] = -s2 * i * gk[k]
        k = k + 1

    nk = int(3 * sigma)

    DGX = np.zeros((nr, nc))
    DGY = np.zeros((nr, nc))

    DGX = Conv2D(E, dgk, gk, nk, nr, nc)
    DGY = Conv2D(E, gk, dgk, nk, nr, nc)

    return DGX, DGY
