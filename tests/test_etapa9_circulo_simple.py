"""Etapa ⑨ — circuloSimple: ajuste de círculo, validación de entrada y guard de colinealidad."""

import numpy as np
import pytest

from odin.Preprocesamiento import circuloSimple as CS


def _arco(radio, n, inicio=0.0, fin=2 * np.pi, centro=(1150.0, 1000.0)):
    """Puntos sobre un arco de círculo exacto (sin ruido)."""
    t = np.linspace(inicio, fin, n)
    return np.column_stack(
        (centro[0] + radio * np.cos(t), centro[1] + radio * np.sin(t))
    )


# ---------------------------------------------------------------------------
# R1 — entradas degeneradas por tipo, forma o cantidad de puntos
# ---------------------------------------------------------------------------

def test_circulo_simple_0_puntos():
    with pytest.raises(ValueError, match="anillo quedó vacío"):
        CS.Circulo_simple(np.empty((0, 2)))


def test_circulo_simple_1_punto():
    with pytest.raises(ValueError, match="insuficientes puntos"):
        CS.Circulo_simple(np.array([[5.0, 5.0]]))


def test_circulo_simple_2_puntos_tiene_mensaje_propio():
    """R1.5: dos puntos no definen un círculo y el mensaje lo dice."""
    with pytest.raises(ValueError, match="dos puntos definen una línea"):
        CS.Circulo_simple(np.array([[0.0, 0.0], [10.0, 0.0]]))


def test_circulo_simple_entrada_no_ndarray():
    with pytest.raises(TypeError, match="se esperaba un numpy.ndarray"):
        CS.Circulo_simple([[0.0, 0.0], [1.0, 1.0]])


def test_circulo_simple_shape_incorrecta_1d():
    with pytest.raises(ValueError, match="debe tener forma"):
        CS.Circulo_simple(np.array([0.0, 0.0]))


def test_circulo_simple_shape_incorrecta_3columnas():
    with pytest.raises(ValueError, match="debe tener forma"):
        CS.Circulo_simple(np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]))


# ---------------------------------------------------------------------------
# R2 — guard de colinealidad (umbral sobre cond normalizado)
# ---------------------------------------------------------------------------

def test_circulo_simple_3_puntos_colineales_exactos():
    with pytest.raises(ValueError, match="colineales"):
        CS.Circulo_simple(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]))


def test_circulo_simple_tres_puntos_casi_colineales():
    """El caso que históricamente producía r = 282864 con pv = 0.

    Con el guard lanza excepción en vez de devolver un círculo absurdo.
    """
    with pytest.raises(ValueError, match="colineales"):
        CS.Circulo_simple(np.array([[0.0, 0.0], [10.0, 10.0], [20.0, 20.001]]))


def test_circulo_simple_recta_con_ruido_de_muchos_puntos():
    """537/537 triples reales de un trazo recto devolvían círculos absurdos.

    Se reproduce con una recta de 50 puntos y ruido perpendicular de 1e-3 del
    largo: el radicando es positivo, así que solo el guard la detiene.
    """
    rng = np.random.default_rng(3)
    s = np.linspace(0.0, 2000.0, 50)
    recta = np.column_stack((s, 0.3 * s))
    normal = rng.normal(0.0, 1.0, (50, 2))
    normal /= np.linalg.norm(normal, axis=1, keepdims=True)
    puntos = recta + 1e-3 * 2000.0 * normal

    with pytest.raises(ValueError, match="colineales"):
        CS.Circulo_simple(puntos)


def test_circulo_simple_puntos_identicos():
    with pytest.raises(ValueError, match="coinciden"):
        CS.Circulo_simple(np.full((10, 2), 7.0))


# ---------------------------------------------------------------------------
# R3 — el guard no rechaza geometrías válidas
# ---------------------------------------------------------------------------

def test_circulo_simple_tres_no_colineales():
    puntos = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0]])

    x, y, r, pv = CS.Circulo_simple(puntos)

    assert r == pytest.approx(7.0710678118654755, abs=1e-3)
    assert (x, y) == pytest.approx((5.0, 5.0), abs=1e-3)
    assert isinstance(pv, float)


def test_circulo_simple_anillo_completo_no_lanza():
    puntos = _arco(428.31, 300)

    _, _, r, _ = CS.Circulo_simple(puntos)

    assert r == pytest.approx(428.31, abs=1e-6)


def test_circulo_simple_anillo_con_hueco_de_60_grados_no_lanza():
    """Peor caso válido del contrato de la etapa ⑧: hueco de 60°."""
    puntos = _arco(428.31, 300, inicio=0.0, fin=2 * np.pi - np.deg2rad(60.0))

    _, _, r, _ = CS.Circulo_simple(puntos)

    assert r == pytest.approx(428.31, abs=1e-6)


def test_circulo_simple_arco_de_240_grados_no_lanza():
    """Documenta el margen: el guard deja pasar arcos muy por debajo del umbral."""
    puntos = _arco(428.31, 300, inicio=0.0, fin=np.deg2rad(240.0))

    _, _, r, _ = CS.Circulo_simple(puntos)

    assert r == pytest.approx(428.31, abs=1e-6)


def test_circulo_simple_caso_banal_r_pv_razonables():
    puntos = _arco(5.0, 20, centro=(1.0, 2.0))

    x, y, r, pv = CS.Circulo_simple(puntos)

    assert r == pytest.approx(5.0, abs=1e-6)
    assert (x, y) == pytest.approx((1.0, 2.0), abs=1e-6)
    assert pv >= 0.0
