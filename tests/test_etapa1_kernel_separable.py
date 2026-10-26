"""Etapa 1 — kernelSeparable (DerivGauss): gradiente derivada-gaussiana.

Contratos verificados (spec kernel-separable):
- Convención de CONVOLUCIÓN (no correlación) y separabilidad, contra una
  referencia independiente construida con np.convolve.
- Equivalencia con OpenCV invirtiendo los kernels (OpenCV correlaciona).
- Relleno de ceros en los bordes: el soporte del kernel no se sale de él.
- sigma <= 0 devuelve ceros sin lanzar excepción.
"""

import numpy as np
import pytest

from odin.Preprocesamiento import kernelSeparable as KS
from utilidades import derivada_gaussiana_referencia, kernels_gaussianos


@pytest.mark.parametrize("sigma", [1, 2, 3])
def test_coincide_con_convolucion_de_referencia(sigma):
    rng = np.random.default_rng(1234 + sigma)
    imagen = rng.random((20, 25))

    dgx, dgy = KS.DerivGauss(imagen, sigma, 0, 0, 0)
    ref_x, ref_y = derivada_gaussiana_referencia(imagen, sigma)

    assert np.allclose(dgx, ref_x, rtol=0, atol=1e-12)
    assert np.allclose(dgy, ref_y, rtol=0, atol=1e-12)


@pytest.mark.parametrize("sigma", [1, 2])
def test_coincide_con_opencv_con_kernels_invertidos(sigma):
    cv2 = pytest.importorskip("cv2")
    rng = np.random.default_rng(99 + sigma)
    imagen = rng.random((18, 22))

    gk, dgk = kernels_gaussianos(sigma)
    # ODIN convoluciona y rellena con ceros; OpenCV correlaciona y por defecto
    # usa BORDER_REFLECT_101 -> se invierten los kernels y se fija el borde.
    ref_x = cv2.sepFilter2D(
        imagen, -1, dgk[::-1].copy(), gk[::-1].copy(),
        borderType=cv2.BORDER_CONSTANT,
    )
    ref_y = cv2.sepFilter2D(
        imagen, -1, gk[::-1].copy(), dgk[::-1].copy(),
        borderType=cv2.BORDER_CONSTANT,
    )

    dgx, dgy = KS.DerivGauss(imagen, sigma, 0, 0, 0)

    assert np.allclose(dgx, ref_x, rtol=0, atol=1e-12)
    assert np.allclose(dgy, ref_y, rtol=0, atol=1e-12)


def test_soporte_del_impulso_no_excede_el_kernel():
    sigma = 2
    n = 3 * sigma
    imagen = np.zeros((15, 15))
    imagen[0, 0] = 1.0

    dgx, dgy = KS.DerivGauss(imagen, sigma, 0, 0, 0)

    # Impulso en la esquina con relleno de ceros: la respuesta solo puede
    # ocupar el soporte del kernel, es decir filas y columnas [0, n].
    for gradiente in (dgx, dgy):
        assert np.all(gradiente[n + 1:, :] == 0.0)
        assert np.all(gradiente[:, n + 1:] == 0.0)

    assert np.any(dgx != 0.0)


@pytest.mark.parametrize("sigma", [0, -1, -0.5])
def test_sigma_no_positivo_devuelve_ceros(sigma):
    imagen = np.ones((8, 9))

    dgx, dgy = KS.DerivGauss(imagen, sigma, 0, 0, 0)

    assert dgx.shape == imagen.shape
    assert dgy.shape == imagen.shape
    assert np.all(dgx == 0.0)
    assert np.all(dgy == 0.0)
