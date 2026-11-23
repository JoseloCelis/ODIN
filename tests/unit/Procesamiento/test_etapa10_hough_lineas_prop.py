"""Property-based tests para la etapa ⑩ Hough de rectas (Hypothesis).

Invariantes aritméticos del acumulador, de las candidatas y de la fusión
`reduce` (spec migracion-lineas-geometria, S1):

- forma y dtype del acumulador: (4 * diag_len + 1, 361), entero.
- theta en [-pi/2, pi/2] con paso pi/360; rho con paso 0.5 px.
- conservación de votos: cada punto vota una vez por theta.
- candidatas: formas consistentes, conteo de picos >= 1, masa >= 1, desviación
  >= 0, rho y theta dentro del rango del acumulador.
- `hough_lineas` devuelve la candidata con más picos y, en empate, la de
  mayor masa.
- `reducir_candidatas` nunca aumenta el número de candidatas y conserva la
  suma de picos y de masa.
- entrada vacía y puntos no finitos tienen comportamiento definido.
"""

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st
from hypothesis.extra import numpy as npst

from src.odin.Procesamiento.models.hough_lineas import (
    NUM_THETAS,
    PASO_RHO,
    PASO_THETA,
    CandidatasLineas,
    acumulador_lineas,
    candidatas_lineas,
    hough_lineas,
    reducir_candidatas,
)


def _puntos_en_imagen(alto, ancho, puntos_unitarios):
    """Escala puntos en [0, 1) a [0, ancho-1] x [0, alto-1]."""
    return puntos_unitarios * np.array([ancho - 1.0, alto - 1.0])


@given(
    alto=st.integers(min_value=1, max_value=40),
    ancho=st.integers(min_value=1, max_value=40),
    puntos_unitarios=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(st.integers(min_value=0, max_value=120), st.just(2)),
        elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    ),
)
@settings(max_examples=25, deadline=None)
def test_prop_acumulador_forma_pasos_y_conservacion(alto, ancho, puntos_unitarios):
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _puntos_en_imagen(alto, ancho, puntos_unitarios)
    diag_len = int(np.ceil(np.hypot(ancho, alto)))

    acumulador, rhos, thetas = acumulador_lineas(puntos, imagen)

    assert acumulador.shape == (4 * diag_len + 1, NUM_THETAS)
    assert np.issubdtype(acumulador.dtype, np.integer)
    assert np.all(acumulador >= 0)
    assert thetas[0] == pytest.approx(-np.pi / 2)
    assert thetas[-1] == pytest.approx(np.pi / 2)
    assert np.allclose(np.diff(thetas), PASO_THETA)
    assert np.allclose(np.diff(rhos), PASO_RHO)
    assert acumulador.sum() == puntos.shape[0] * NUM_THETAS


@given(
    alto=st.integers(min_value=1, max_value=40),
    ancho=st.integers(min_value=1, max_value=40),
    puntos_unitarios=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(st.integers(min_value=0, max_value=120), st.just(2)),
        elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    ),
)
@settings(max_examples=25, deadline=None)
def test_prop_candidatas_invariantes(alto, ancho, puntos_unitarios):
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _puntos_en_imagen(alto, ancho, puntos_unitarios)
    diag_len = int(np.ceil(np.hypot(ancho, alto)))

    candidatas = candidatas_lineas(puntos, imagen)

    assert candidatas.rhos.shape == candidatas.thetas.shape == candidatas.conteos.shape
    assert candidatas.rhos.shape == candidatas.masas.shape == candidatas.desviaciones.shape
    assert np.issubdtype(candidatas.conteos.dtype, np.integer)
    assert np.issubdtype(candidatas.masas.dtype, np.integer)
    if candidatas.rhos.size == 0:
        assert hough_lineas(puntos, imagen) is None
        return

    assert np.all(candidatas.conteos >= 1)
    assert np.all(candidatas.masas >= 1)
    assert np.all(candidatas.desviaciones >= 0.0)
    assert np.all(np.abs(candidatas.rhos) <= diag_len + 1e-9)
    assert np.all(candidatas.thetas >= -np.pi / 2 - 1e-9)
    assert np.all(candidatas.thetas <= np.pi / 2 + 1e-9)
    # Los grupos son disjuntos y están ordenados por rho creciente.
    assert np.all(np.diff(candidatas.rhos) > 0.0)


@given(
    alto=st.integers(min_value=1, max_value=40),
    ancho=st.integers(min_value=1, max_value=40),
    puntos_unitarios=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(st.integers(min_value=0, max_value=120), st.just(2)),
        elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    ),
)
@settings(max_examples=25, deadline=None)
def test_prop_hough_lineas_es_la_candidata_de_mas_picos(alto, ancho, puntos_unitarios):
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _puntos_en_imagen(alto, ancho, puntos_unitarios)

    candidatas = candidatas_lineas(puntos, imagen)
    resultado = hough_lineas(puntos, imagen)

    if candidatas.rhos.size == 0:
        assert resultado is None
        return

    orden = np.lexsort((-candidatas.masas, -candidatas.conteos))
    indice = int(orden[0])
    assert resultado[0] == pytest.approx(candidatas.rhos[indice])
    assert resultado[1] == pytest.approx(candidatas.thetas[indice])
    assert resultado[2] == int(candidatas.conteos[indice])
    assert resultado[3] == int(candidatas.masas[indice])
    assert resultado[4] == pytest.approx(candidatas.desviaciones[indice])


@given(
    rhos=npst.arrays(
        dtype=np.float64,
        shape=st.integers(min_value=0, max_value=20),
        elements=st.floats(min_value=-500.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    ),
    sigma=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=25, deadline=None)
def test_prop_reducir_candidatas_conserva_sumas(rhos, sigma):
    n = rhos.size
    candidatas = CandidatasLineas(
        rhos=rhos,
        thetas=np.linspace(-np.pi / 2, np.pi / 2, max(n, 1))[:n],
        conteos=np.ones(n, dtype=np.int64),
        masas=np.ones(n, dtype=np.int64),
        desviaciones=np.zeros(n, dtype=float),
    )

    fusion = reducir_candidatas(candidatas, sigma)

    assert fusion.rhos.shape == fusion.thetas.shape == fusion.conteos.shape
    assert fusion.rhos.shape == fusion.masas.shape == fusion.desviaciones.shape
    assert fusion.rhos.size <= n
    assert fusion.conteos.sum() == n
    assert fusion.masas.sum() == n
    assert np.all(fusion.conteos >= 1)
    assert np.all(fusion.desviaciones >= 0.0)
    if fusion.rhos.size > 1:
        assert np.all(np.diff(fusion.rhos) > 0.0)


def test_prop_entrada_vacia_devuelve_none():
    imagen = np.zeros((30, 30), dtype=np.uint8)
    puntos = np.empty((0, 2), dtype=float)

    assert hough_lineas(puntos, imagen) is None


@given(
    valor=st.one_of(st.just(np.nan), st.just(np.inf), st.just(-np.inf)),
)
@settings(max_examples=20, deadline=None)
def test_prop_puntos_no_finitos_lanzan_error(valor):
    imagen = np.zeros((30, 30), dtype=np.uint8)
    puntos = np.array([[valor, 1.0]])

    with pytest.raises(ValueError):
        hough_lineas(puntos, imagen)
