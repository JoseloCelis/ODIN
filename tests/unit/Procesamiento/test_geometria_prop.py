"""Propiedades de Hypothesis del clasificador de geometría (spec S4, bloque T4).

Las cinco propiedades exigidas por el bloque de diseño:

- confianza siempre en [0, 1];
- invariancia ante rotación y reflexión rígidas;
- nunca lanza en entradas degeneradas;
- monotonicidad del ganador al deformar un círculo en una recta;
- falla cerrado como invariante (confianza < umbral ⇒ sin decisión y ambos
  candidatos).
"""

import math

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra import numpy as npst

from src.odin.Procesamiento.models.geometria import (
    EvidenciaGeometria,
    Geometria,
    clasificar_geometria,
)

INF = math.inf

# Puntos finitos, no degenerados por construcción (se evitan duplicados exactos
# con una caja continua) y con al menos 3 filas.
PUNTOS = npst.arrays(
    dtype=np.float64,
    shape=st.tuples(st.integers(min_value=3, max_value=40), st.just(2)),
    elements=st.floats(min_value=-500.0, max_value=500.0, allow_nan=False, allow_infinity=False),
)


@given(puntos=PUNTOS)
@settings(max_examples=60, deadline=None)
def test_prop_confianza_siempre_en_cero_a_uno(puntos):
    evidencia = clasificar_geometria(puntos)

    assert 0.0 <= evidencia.confianza <= 1.0
    if evidencia.geometria is None:
        assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA)
    else:
        assert evidencia.candidatos == (evidencia.geometria,)


@given(
    puntos=PUNTOS,
    angulo=st.floats(min_value=-np.pi, max_value=np.pi, allow_nan=False, allow_infinity=False),
    reflejar=st.booleans(),
    desplazamiento=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(st.just(2)),
        elements=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    ),
)
@settings(max_examples=40, deadline=None)
def test_prop_invariancia_rotacion_y_reflexion(puntos, angulo, reflejar, desplazamiento):
    base = clasificar_geometria(puntos)

    coseno, seno = np.cos(angulo), np.sin(angulo)
    rotacion = np.array([[coseno, -seno], [seno, coseno]])
    if reflejar:
        rotacion = rotacion @ np.array([[1.0, 0.0], [0.0, -1.0]])
    transformados = puntos @ rotacion.T + desplazamiento

    # Una traslación puede volver idénticos dos puntos que sí eran distintos,
    # porque sumar un desplazamiento grande absorbe una diferencia subnormal
    # (un par que difiere en 1e-308 deja de diferir al sumarle 1.0). Eso no es
    # una falla del clasificador sino aritmética de punto flotante: la
    # invariancia se exige solo cuando la transformación conserva cuántos
    # puntos distintos hay.
    assume(
        np.unique(transformados, axis=0).shape[0]
        == np.unique(puntos, axis=0).shape[0]
    )

    evidencia = clasificar_geometria(transformados)

    assert evidencia.geometria is base.geometria
    assert evidencia.confianza == pytest.approx(base.confianza, rel=1e-6, abs=1e-7)
    assert evidencia.residual_recta == pytest.approx(base.residual_recta, rel=1e-6, abs=1e-7)
    assert evidencia.residual_circulo == pytest.approx(base.residual_circulo, rel=1e-6, abs=1e-7)
    if base.radio is None:
        assert evidencia.radio is None
    else:
        assert evidencia.radio == pytest.approx(base.radio, rel=1e-6, abs=1e-7)
    # Nota: `cobertura_angular` es un histograma de 72 binos alineado al eje
    # absoluto; su fracción ocupada puede variar en un bin ante rotación. La
    # invariancia exigida es la de la decisión, no la de esta evidencia gruesa.


@given(
    caso=st.integers(min_value=0, max_value=3),
    n=st.integers(min_value=0, max_value=8),
    semilla=st.integers(min_value=0, max_value=10**6),
)
@settings(max_examples=60, deadline=None)
def test_prop_degenerados_nunca_lanzan(caso, n, semilla):
    rng = np.random.default_rng(semilla)
    if caso == 0:  # menos de 3 puntos
        puntos = rng.normal(size=(n, 2))
    elif caso == 1:  # valores no finitos
        puntos = rng.normal(size=(max(n, 1), 2))
        puntos[0, 0] = np.nan
    elif caso == 2:  # duplicados
        puntos = np.tile(rng.normal(size=2), (max(n, 3), 1))
    else:  # colineales exactos
        t = np.linspace(0.0, 1.0, max(n, 3))
        puntos = np.column_stack([t, 2.0 * t + 1.0])

    evidencia = clasificar_geometria(puntos)

    assert isinstance(evidencia, EvidenciaGeometria)
    assert 0.0 <= evidencia.confianza <= 1.0


@given(
    radio=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    angulo_inicial=st.floats(min_value=-np.pi, max_value=np.pi, allow_nan=False, allow_infinity=False),
    n=st.integers(min_value=20, max_value=60),
)
@settings(max_examples=25, deadline=None)
def test_prop_ganador_monotono(radio, angulo_inicial, n):
    """Al deformar un círculo en su recta proyectada, el ganador no oscila."""
    angulos = angulo_inicial + np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    circulo = np.column_stack([radio * np.cos(angulos), radio * np.sin(angulos)])
    recta = np.column_stack([radio * np.cos(angulos), np.zeros(n)])

    ganadores = []
    for t in np.linspace(0.0, 1.0, 21):
        evidencia = clasificar_geometria((1.0 - t) * circulo + t * recta)
        if evidencia.geometria is not None:
            ganadores.append(evidencia.geometria)

    orden = {Geometria.CIRCULO: 0, Geometria.RECTA: 1}
    assert all(orden[a] <= orden[b] for a, b in zip(ganadores, ganadores[1:]))


@given(
    puntos=PUNTOS,
    umbral=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=60, deadline=None)
def test_prop_falla_cerrado_como_invariante(puntos, umbral):
    evidencia = clasificar_geometria(puntos, umbral_confianza=umbral)

    # Si la confianza queda por debajo del umbral, el clasificador no elige.
    if evidencia.confianza < umbral:
        assert evidencia.geometria is None
        assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA)
    # Si elige, es porque alcanzó el umbral (el recíproco no es invariante:
    # las entradas degeneradas fallan cerrado incluso con umbral 0).
    if evidencia.geometria is not None:
        assert evidencia.confianza >= umbral
        assert evidencia.candidatos == (evidencia.geometria,)
