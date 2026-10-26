"""Integración del pipeline completo: etapas 1 -> 5.

La imagen sintética (un rectángulo blanco sobre fondo negro) ejercita las
cinco etapas en cadena y fija un snapshot de caracterización: si el conteo de
bordes cambia, hay que entender el efecto antes de actualizar el número.
"""

import numpy as np

from odin.Preprocesamiento import (
    kernelSeparable as KS,
    MagnitudGradiente as MF,
    NonMaxSup as NMS,
    Otsu as OT,
)


def _rectangulo():
    imagen = np.zeros((80, 100))
    imagen[20:60, 30:70] = 1.0
    return imagen


def test_pipeline_etapas_1_a_5():
    imagen = _rectangulo()

    gx, gy = KS.DerivGauss(imagen, 2, 0, 0, 0)
    mg, angulo = MF.MagFase(gx, gy)
    gn = NMS.LinearInterpolation(mg, gx, gy, angulo)
    umbral_otsu, umbral_rosin = OT.umbralRosinYOtsu(gn)
    gh, gl = NMS.DobleThreshold(gn, umbral_otsu)

    assert gx.shape == gy.shape == mg.shape == gn.shape == imagen.shape
    assert 0.0 < umbral_otsu <= 1.0
    assert 0.0 < umbral_rosin <= 1.0

    # La supresión solo conserva valores que ya existían en la magnitud.
    assert np.all(np.isin(gn, mg))
    # El borde de 1 píxel queda fuera de la supresión.
    assert np.all(gn[0, :] == 0.0) and np.all(gn[-1, :] == 0.0)
    assert np.all(gn[:, 0] == 0.0) and np.all(gn[:, -1] == 0.0)

    # Snapshot de caracterización de las etapas 1 a 5.
    assert int(np.count_nonzero(gh)) == 268
    assert int(np.count_nonzero(gl)) == 0
