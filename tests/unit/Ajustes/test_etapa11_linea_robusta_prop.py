"""Propiedades (Hypothesis) para el ajuste robusto de recta (etapa ⑪).

Fija invariantes aritméticos de S2/S6: los puntos colineales se conservan
colineales, la dispersión del residual es no negativa y finita, y las entradas
degeneradas (no finitas, dirección nula) fallan con ValueError.
"""

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st

from src.odin.Ajustes.models.linea_robusta import (
    dist_p_recta,
    euc_space,
    linea_robusta,
)


def _param_de_recta(pendiente: float, ordenada: float) -> np.ndarray:
    """Recta y = pendiente * x + ordenada en param [x0, y0, cos_x, cos_y]."""
    norma = np.hypot(1.0, pendiente)
    return np.array([0.0, ordenada, 1.0 / norma, pendiente / norma])


@given(
    pendiente=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False),
    ordenada=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    n=st.integers(min_value=5, max_value=40),
    semilla=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=25, deadline=None)
def test_prop_puntos_colineales_exactos_siguen_colineales(pendiente, ordenada, n, semilla):
    """Los puntos exactamente sobre la recta sobreviven y la recta no se mueve."""
    rng = np.random.default_rng(semilla)
    x = rng.uniform(-100.0, 100.0, n)
    puntos = np.column_stack((x, pendiente * x + ordenada))
    parametro_inicial = _param_de_recta(pendiente, ordenada)

    parametro, r, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    assert sobrevivientes.shape == (n, 2)
    assert np.allclose(sobrevivientes, puntos)
    # El SVD introduce error de redondeo del orden de 1e-6 con estas escalas.
    assert r == pytest.approx(0.0, abs=1e-4)
    esperado = np.array([1.0, pendiente]) / np.hypot(1.0, pendiente)
    assert abs(float(np.dot(parametro[2:4], esperado))) == pytest.approx(1.0, abs=1e-9)


@given(
    pendiente=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False),
    ordenada=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    n=st.integers(min_value=10, max_value=40),
    ruido=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    semilla=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=25, deadline=None)
def test_prop_colineales_con_ruido_recuperan_la_direccion(pendiente, ordenada, n, ruido, semilla):
    """Con ruido acotado la dirección recuperada es paralela a la real."""
    rng = np.random.default_rng(semilla)
    x = rng.uniform(-100.0, 100.0, n)
    y = pendiente * x + ordenada + rng.normal(0.0, ruido, n)
    puntos = np.column_stack((x, y))
    parametro_inicial = _param_de_recta(pendiente, ordenada)

    parametro, r, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    assert sobrevivientes.shape[1] == 2
    assert np.isfinite(r)
    assert r >= 0.0
    esperado = np.array([1.0, pendiente]) / np.hypot(1.0, pendiente)
    assert abs(float(np.dot(parametro[2:4], esperado))) > 0.99


@given(
    pendiente=st.floats(min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    ordenada=st.floats(min_value=-30.0, max_value=30.0, allow_nan=False, allow_infinity=False),
    n=st.integers(min_value=6, max_value=30),
    ruido=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    semilla=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=25, deadline=None)
def test_prop_dispersion_es_pico_a_valle_no_negativa(pendiente, ordenada, n, ruido, semilla):
    """r = max(residuales) - min(residuales) de los puntos conservados."""
    rng = np.random.default_rng(semilla)
    x = rng.uniform(-80.0, 80.0, n)
    y = pendiente * x + ordenada + rng.normal(0.0, ruido, n)
    puntos = np.column_stack((x, y))
    parametro_inicial = _param_de_recta(pendiente, ordenada)

    parametro, r, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    residuales = dist_p_recta(sobrevivientes, parametro)
    assert r >= 0.0
    assert np.isfinite(r)
    assert r == pytest.approx(float(np.max(residuales) - np.min(residuales)))


_no_finito = st.one_of(st.just(np.nan), st.just(np.inf), st.just(-np.inf))


@given(valor=_no_finito)
@settings(max_examples=10, deadline=None)
def test_prop_puntos_no_finitos_lanzan(valor):
    puntos = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    puntos[1, 0] = valor

    with pytest.raises(ValueError, match="finitos"):
        linea_robusta(puntos, _param_de_recta(1.0, 0.0))


@given(valor=_no_finito)
@settings(max_examples=10, deadline=None)
def test_prop_param_no_finito_lanza(valor):
    param = np.array([0.0, 0.0, 1.0, 0.0])
    param[0] = valor

    with pytest.raises(ValueError, match="finitos"):
        linea_robusta(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), param)


@given(
    rho=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    theta=st.floats(min_value=-np.pi / 2, max_value=np.pi / 2, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=25, deadline=None)
def test_prop_euc_space_direccion_unitaria_y_punto_en_la_recta(rho, theta):
    parametro = euc_space(rho, theta)

    assert np.linalg.norm(parametro[2:4]) == pytest.approx(1.0)
    normal = np.array([np.cos(theta), np.sin(theta)])
    assert float(np.dot(normal, parametro[:2])) == pytest.approx(rho)


@given(
    x=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    y=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    angulo=st.floats(min_value=-np.pi, max_value=np.pi, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=25, deadline=None)
def test_prop_dist_p_recta_invariante_al_sentido_de_la_direccion(x, y, angulo):
    punto = np.array([[x, y]])
    param = np.array([0.0, 0.0, np.cos(angulo), np.sin(angulo)])
    param_opuesto = np.array([0.0, 0.0, -np.cos(angulo), -np.sin(angulo)])

    assert dist_p_recta(punto, param)[0] == pytest.approx(dist_p_recta(punto, param_opuesto)[0])
