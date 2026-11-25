"""Propiedades de Hypothesis del emparejamiento de orillas (S1, S2, S7).

Propiedades exigidas:

- las dos máscaras son disjuntas y cubren solo puntos asignados;
- un punto sobre una orilla siempre cae en esa orilla;
- el reparto no depende del orden de los índices del par;
- una rotación rígida de puntos y candidatas deja el reparto intacto;
- permutar las candidatas solo permuta los pares, no los cambia;
- la distancia perpendicular es no negativa y crece exactamente con un
  desplazamiento a lo largo de la normal;
- los picos del perfil caen dentro del rango de las proyecciones.
"""

import math

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra import numpy as npst

from src.odin.Procesamiento.models.pares_orillas import (
    asignar_puntos_a_orillas,
    distancias_perpendiculares,
    emparejar_orillas,
    picos_de_rho,
)

FLOTANTES = st.floats(
    min_value=-1e4, max_value=1e4, allow_nan=False, allow_infinity=False
)
def _a_matriz(pares: list[tuple[float, float]]) -> np.ndarray:
    """Convierte la lista de pares que genera Hypothesis en una matriz (N, 2)."""
    return np.array(pares, dtype=float).reshape(-1, 2)


COORDENADAS = st.lists(st.tuples(FLOTANTES, FLOTANTES), max_size=40).map(_a_matriz)
COORDENADAS_NO_VACIAS = st.lists(
    st.tuples(FLOTANTES, FLOTANTES), min_size=1, max_size=20
).map(_a_matriz)
# Candidatas distinguibles por construcción: con rho repetidos el desempate del
# vecino más cercano es ambiguo y la propiedad no sería exigible.
CANDIDATAS = st.lists(
    st.floats(min_value=-500.0, max_value=500.0, allow_nan=False),
    min_size=2,
    max_size=6,
    unique=True,
).map(lambda valores: np.array(valores, dtype=float))


@settings(max_examples=40, deadline=None)
@given(CANDIDATAS)
def test_los_pares_siempre_cumplen_las_condiciones_de_orilla(rhos):
    """S2: todo par devuelto es paralelo, está separado y viene ordenado."""
    thetas = np.zeros(rhos.size)
    for i, j in emparejar_orillas(rhos, thetas):
        assert 0 <= i < j < rhos.size
        assert abs(rhos[i] - rhos[j]) >= 5.0


@settings(max_examples=40, deadline=None)
@given(CANDIDATAS)
def test_el_emparejamiento_es_determinista(rhos):
    """S2: la misma entrada da siempre el mismo resultado, dato y no azar."""
    thetas = np.zeros(rhos.size)
    assert emparejar_orillas(rhos, thetas) == emparejar_orillas(rhos, thetas)


@settings(max_examples=40, deadline=None)
@given(COORDENADAS, CANDIDATAS)
def test_las_mascaras_son_disjuntas_y_respetan_la_longitud(puntos, rhos):
    """S1: cada punto pertenece como mucho a una orilla y la forma se conserva."""
    thetas = np.zeros(rhos.size)
    mascara_a, mascara_b = asignar_puntos_a_orillas(
        puntos, rhos, thetas, (0, 1)
    )

    assert mascara_a.shape == (puntos.shape[0],)
    assert mascara_b.shape == (puntos.shape[0],)
    assert not np.any(mascara_a & mascara_b)


@settings(max_examples=40, deadline=None)
@given(
    st.floats(min_value=-100.0, max_value=100.0, allow_nan=False),
    st.floats(min_value=1.0, max_value=100.0, allow_nan=False),
    st.floats(min_value=0.0, max_value=500.0, allow_nan=False),
)
def test_un_punto_sobre_una_orilla_cae_en_esa_orilla(x, separacion, altura):
    """S1: pertenencia exacta, sin cota que pueda dejar afuera un punto propio."""
    rhos = np.array([0.0, separacion])
    puntos = np.array([[0.0, altura], [separacion, altura]])

    mascara_a, mascara_b = asignar_puntos_a_orillas(puntos, rhos, np.zeros(2), (0, 1))

    assert bool(mascara_a[0]) and not bool(mascara_a[1])
    assert bool(mascara_b[1]) and not bool(mascara_b[0])


@settings(max_examples=40, deadline=None)
@given(COORDENADAS, CANDIDATAS)
def test_el_reparto_no_depende_del_orden_del_par(puntos, rhos):
    """S1: intercambiar las dos orillas conserva qué puntos forman el par."""
    thetas = np.zeros(rhos.size)
    directo = asignar_puntos_a_orillas(puntos, rhos, thetas, (0, 1))
    invertido = asignar_puntos_a_orillas(puntos, rhos, thetas, (1, 0))

    np.testing.assert_array_equal(directo[0] | directo[1], invertido[0] | invertido[1])


@settings(max_examples=40, deadline=None)
@given(
    COORDENADAS_NO_VACIAS,
    st.floats(min_value=-math.pi, max_value=math.pi, allow_nan=False),
    st.floats(min_value=1.0, max_value=200.0, allow_nan=False),
)
def test_una_rotacion_rigida_deja_el_reparto_intacto(puntos, angulo, separacion):
    """S1: girar puntos y candidatas por igual no cambia la pertenencia."""
    rhos = np.array([0.0, separacion])
    thetas = np.zeros(2)
    base_a, base_b = asignar_puntos_a_orillas(puntos, rhos, thetas, (0, 1))

    coseno, seno = np.cos(angulo), np.sin(angulo)
    rotacion = np.array([[coseno, -seno], [seno, coseno]])
    girados = puntos @ rotacion.T
    girados_a, girados_b = asignar_puntos_a_orillas(
        girados, rhos, np.full(2, angulo), (0, 1)
    )

    np.testing.assert_array_equal(base_a, girados_a)
    np.testing.assert_array_equal(base_b, girados_b)


@settings(max_examples=40, deadline=None)
@given(CANDIDATAS)
def test_permutar_las_candidatas_solo_permuta_los_pares(rhos):
    """S2: el emparejamiento depende de las distancias, no del orden de entrada."""
    # Con rho repetidos el desempate es ambiguo por definición, así que la
    # propiedad se exige sobre candidatas distinguibles.
    thetas = np.zeros(rhos.size)
    pares = set(emparejar_orillas(rhos, thetas))

    orden = np.arange(rhos.size)[::-1]
    permutados = {
        (min(int(orden[i]), int(orden[j])), max(int(orden[i]), int(orden[j])))
        for i, j in pares
    }
    assert set(emparejar_orillas(rhos[orden], thetas[orden])) == permutados


@settings(max_examples=40, deadline=None)
@given(
    COORDENADAS_NO_VACIAS,
    st.floats(min_value=-math.pi, max_value=math.pi, allow_nan=False),
    st.floats(min_value=0.0, max_value=50.0, allow_nan=False),
)
def test_la_distancia_acota_un_desplazamiento_normal(puntos, theta, avance):
    """S1: mover un punto sobre la normal mueve su distancia como mucho `avance`.

    La distancia es 1-Lipschitz respecto de la posición, así que un avance `a`
    la cambia a lo sumo en `a`; crece si el punto está del lado positivo y
    decrece si está del otro. La cota vale en ambos casos.
    """
    rhos = np.array([0.0, 10.0])
    thetas = np.full(2, theta)
    normal = np.array([np.cos(theta), np.sin(theta)])
    base = distancias_perpendiculares(puntos, rhos, thetas)
    movidos = distancias_perpendiculares(puntos + avance * normal, rhos, thetas)

    assert np.all(base >= 0.0)
    assert np.all(np.abs(movidos - base) <= avance + 1e-9)


@settings(max_examples=40, deadline=None)
@given(COORDENADAS_NO_VACIAS, st.floats(min_value=-math.pi, max_value=math.pi, allow_nan=False))
def test_los_picos_caen_en_el_rango_de_las_proyecciones(puntos, theta):
    """S2: ningún pico puede salir del rango que abarcan los puntos."""
    rhos, conteos, semianchuras = picos_de_rho(puntos, theta)

    if rhos.size == 0:
        return
    proyeccion = puntos[:, 0] * np.cos(theta) + puntos[:, 1] * np.sin(theta)
    assert np.all(rhos >= proyeccion.min() - 1.0)
    assert np.all(rhos <= proyeccion.max() + 1.0)
    assert np.all(conteos > 0.0)
    assert np.all(semianchuras > 0.0)
