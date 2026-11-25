"""Tests de emparejamiento de orillas por picos de Hough (T2, S1-S2)."""

import numpy as np
import pytest

from src.odin.Procesamiento.models.pares_orillas import (
    SEPARACION_MINIMA,
    TOLERANCIA_THETA,
    asignar_puntos_a_orillas,
    distancias_perpendiculares,
    emparejar_orillas,
    picos_de_rho,
)


def _puntos_en(xs, ys):
    """Devuelve la matriz (N, 2) con el producto cartesiano de xs e ys."""
    return np.array([[x, y] for x in xs for y in ys], dtype=float)


def test_emparejar_detecta_par_paralelo_separado():
    """S2: dos candidatas paralelas y separadas en rho son un par."""
    pares = emparejar_orillas(np.array([0.0, 20.5]), np.array([0.0, 0.0]))
    assert pares == [(0, 1)]


def test_emparejar_no_empareja_theta_diferente():
    """S2: direcciones distintas no son orillas del mismo trazo."""
    thetas = np.array([0.0, TOLERANCIA_THETA * 4.0])
    assert emparejar_orillas(np.array([0.0, 20.5]), thetas) == []


def test_emparejar_no_empareja_rho_cercano():
    """S2: picos más cerca que SEPARACION_MINIMA son el mismo borde."""
    rhos = np.array([0.0, SEPARACION_MINIMA * 0.5])
    assert emparejar_orillas(rhos, np.array([0.0, 0.0])) == []


def test_emparejar_elige_la_orilla_vecina_y_no_cruza_trazos():
    """S2: con cuatro picos paralelos los pares son vecinos, nunca cruzados."""
    rhos = np.array([0.0, 20.0, 200.0, 220.0])
    pares = emparejar_orillas(rhos, np.zeros(4))
    assert set(pares) == {(0, 1), (2, 3)}
    assert (0, 3) not in pares and (1, 2) not in pares


def test_emparejar_ordena_por_evidencia():
    """S2: el par con más evidencia va primero."""
    rhos = np.array([0.0, 20.0, 200.0, 220.0])
    conteos = np.array([1.0, 1.0, 50.0, 50.0])
    pares = emparejar_orillas(rhos, np.zeros(4), conteos)
    assert pares[0] == (2, 3)


def test_distancias_perpendiculares_es_la_distancia_a_la_recta():
    """S1: la distancia perpendicular de una recta vertical es |x - rho|."""
    puntos = np.array([[10.0, 0.0], [12.0, 50.0], [30.0, 7.0]])
    distancias = distancias_perpendiculares(puntos, np.array([10.0, 20.0]), np.zeros(2))
    assert distancias.shape == (3, 2)
    np.testing.assert_allclose(distancias[:, 0], [0.0, 2.0, 20.0])
    np.testing.assert_allclose(distancias[:, 1], [10.0, 8.0, 10.0])


def test_picos_de_rho_no_parte_un_borde_en_dos_bins_contiguos():
    """S2: un borde que cae entre dos bins se reporta como un solo pico."""
    ys = np.arange(60, dtype=float)
    puntos = np.stack([np.full_like(ys, 10.4), ys], axis=1)
    rhos, conteos = picos_de_rho(puntos, 0.0)
    assert rhos.size == 1
    assert abs(rhos[0] - 10.4) <= 0.5
    assert int(conteos[0]) == 60


def test_picos_de_rho_separa_las_dos_orillas_de_un_trazo():
    """S2: dos bordes a 20.5 px son dos picos distintos, no uno fusionado."""
    ys = np.arange(50, dtype=float)
    puntos = np.vstack([
        np.stack([np.full_like(ys, 0.0), ys], axis=1),
        np.stack([np.full_like(ys, 20.5), ys], axis=1),
    ])
    rhos, _ = picos_de_rho(puntos, 0.0)
    assert rhos.size == 2
    assert abs(rhos[1] - rhos[0] - 20.5) <= 0.5


def test_asignar_devuelve_mascaras_complementarias():
    """S1: cada punto del par cae en una sola de las dos máscaras."""
    puntos = _puntos_en([0.0, 20.0], range(10))
    mascara_a, mascara_b = asignar_puntos_a_orillas(
        puntos, np.array([0.0, 20.0]), np.zeros(2), (0, 1)
    )
    assert mascara_a.shape == (puntos.shape[0],)
    assert mascara_a.dtype == bool and mascara_b.dtype == bool
    assert not np.any(mascara_a & mascara_b)
    assert np.count_nonzero(mascara_a) == 10
    assert np.count_nonzero(mascara_b) == 10
    assert np.all(puntos[mascara_a][:, 0] == 0.0)
    assert np.all(puntos[mascara_b][:, 0] == 20.0)


def test_asignar_descarta_puntos_de_otro_trazo():
    """S1: un punto más cercano a otra candidata queda fuera de ambas máscaras."""
    puntos = np.concatenate([_puntos_en([0.0, 20.0], range(5)), _puntos_en([200.0], range(5))])
    rhos = np.array([0.0, 20.0, 200.0])
    mascara_a, mascara_b = asignar_puntos_a_orillas(puntos, rhos, np.zeros(3), (0, 1))
    assert not np.any(mascara_a[10:])
    assert not np.any(mascara_b[10:])
    assert np.count_nonzero(mascara_a | mascara_b) == 10


def test_asignar_no_usa_una_cota_de_distancia():
    """S1: un punto lejísimos de la orilla sigue perteneciendo si es el más cercano."""
    puntos = np.array([[5000.0, 0.0]], dtype=float)
    mascara_a, mascara_b = asignar_puntos_a_orillas(
        puntos, np.array([0.0, 20.0]), np.zeros(2), (0, 1)
    )
    assert bool(mascara_b[0]) is True
    assert bool(mascara_a[0]) is False


def test_asignar_sin_puntos_devuelve_mascaras_vacias():
    """S1: sin puntos no hay nada que asignar y no se levanta excepción."""
    vacios = np.empty((0, 2), dtype=float)
    mascara_a, mascara_b = asignar_puntos_a_orillas(
        vacios, np.array([0.0, 20.0]), np.zeros(2), (0, 1)
    )
    assert mascara_a.size == 0 and mascara_b.size == 0


def test_asignar_rechaza_par_fuera_de_rango():
    """S1: un par que no referencia candidatas existentes es un error."""
    with pytest.raises(ValueError):
        asignar_puntos_a_orillas(
            _puntos_en([0.0], [0.0]), np.array([0.0, 20.0]), np.zeros(2), (0, 5)
        )
