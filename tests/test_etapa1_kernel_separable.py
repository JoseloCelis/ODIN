"""Tests de propiedad para la etapa ① kernelSeparable (refactor src/odin/)."""

import numpy as np
import pytest

from src.odin.Preprocesamiento import kernelSeparable


def test_derivgauss_retorna_arrays_mismo_tamano():
    """kernelSeparable devuelve (DGX, DGY) con la misma forma que la entrada."""
    img = np.random.rand(64, 64).astype(np.float64)
    dx, dy = kernelSeparable(img, sigma=1.0, wk=0, wConv=0, wr=0)
    assert dx.shape == img.shape
    assert dy.shape == img.shape


def test_derivgauss_sigma_cero_retorna_ceros():
    """sigma <= 0 devuelve arrays de ceros (guard corto-circuito)."""
    img = np.ones((32, 32)).astype(np.float64)
    dx, dy = kernelSeparable(img, sigma=0.0, wk=0, wConv=0, wr=0)
    assert np.allclose(dx, np.zeros_like(img))
    assert np.allclose(dy, np.zeros_like(img))


def test_derivgauss_sigma_negativo_retorna_ceros():
    """sigma negativo devuelve arrays de ceros (no lanza ValueError)."""
    img = np.ones((32, 32)).astype(np.float64)
    dx, dy = kernelSeparable(img, sigma=-2.5, wk=0, wConv=0, wr=0)
    assert np.allclose(dx, np.zeros_like(img))
    assert np.allclose(dy, np.zeros_like(img))


def test_derivgauss_sigma_flotante_no_truna():
    """D4 resuelto: sigma flotante (p. ej. 1.5, 2.5) no lanza TypeError."""
    img = np.random.rand(32, 32).astype(np.float64)
    dx, dy = kernelSeparable(img, sigma=1.5, wk=0, wConv=0, wr=0)
    assert dx.shape == img.shape
    assert dy.shape == img.shape
    assert isinstance(dx, np.ndarray)
    assert isinstance(dy, np.ndarray)


def test_derivgauss_sigma_flotante_resultado_finito():
    """D4 resuelto: sigma flotante produce valores finitos (no NaN)."""
    img = np.random.rand(32, 32).astype(np.float64)
    dx, dy = kernelSeparable(img, sigma=2.5, wk=0, wConv=0, wr=0)
    assert np.all(np.isfinite(dx))
    assert np.all(np.isfinite(dy))


def test_derivgauss_tipos_salida_son_ndarray():
    """Las salidas son numpy.ndarray puro (modelo aislado de UI)."""
    img = np.random.rand(16, 16).astype(np.float64)
    dx, dy = kernelSeparable(img, sigma=1.0, wk=0, wConv=0, wr=0)
    assert isinstance(dx, np.ndarray)
    assert isinstance(dy, np.ndarray)
