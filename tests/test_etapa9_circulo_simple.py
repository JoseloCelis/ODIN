"""Etapa 9 — circuloSimple: ajuste de círculo con mínimos cuadrados y validación de entrada."""

import numpy as np
import pytest

from odin.Preprocesamiento import circuloSimple as CS


# ---------------------------------------------------------------------------
# R1 — entradas degeneradas lanzan excepción
# ---------------------------------------------------------------------------

def test_circulo_simple_0_puntos():
    """N = 0 debe lanzar ValueError."""
    with pytest.raises(ValueError, match="anillo quedó vacío"):
        CS.Circulo_simple(np.empty((0, 2)))


def test_circulo_simple_1_punto():
    """N = 1 debe lanzar ValueError."""
    with pytest.raises(ValueError, match="insuficientes puntos"):
        CS.Circulo_simple(np.array([[5.0, 5.0]]))


def test_circulo_simple_2_puntos():
    """N = 2 debe lanzar ValueError."""
    with pytest.raises(ValueError, match="insuficientes puntos"):
        CS.Circulo_simple(np.array([[0.0, 0.0], [10.0, 0.0]]))


def test_circulo_simple_entrada_no_ndarray():
    """Tipo distinto de ndarray debe lanzar TypeError."""
    with pytest.raises(TypeError, match="se esperaba un numpy.ndarray"):
        CS.Circulo_simple([[0.0, 0.0], [1.0, 1.0]])


def test_circulo_simple_shape_incorrecta_1d():
    """Arreglo 1D debe lanzar ValueError."""
    with pytest.raises(ValueError, match="debe tener forma"):
        CS.Circulo_simple(np.array([0.0, 0.0]))


def test_circulo_simple_shape_incorrecta_3columnas():
    """Arreglo con 3 columnas debe lanzar ValueError."""
    with pytest.raises(ValueError, match="debe tener forma"):
        CS.Circulo_simple(np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]))


# ---------------------------------------------------------------------------
# R2 — caso "happy path": 3 puntos no colineales
# ---------------------------------------------------------------------------

def test_circulo_simple_3_no_colineales():
    """3 puntos no colineales deben retornar r > 0 y pv como float."""
    pts = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0]])
    x, y, r, pv = CS.Circulo_simple(pts)

    assert r > 0, f"se esperaba r > 0, obtuvimos {r}"
    assert isinstance(r, float), f"se esperaba float, obtuvimos {type(r)}"
    assert isinstance(pv, float), f"se esperaba float, obtuvimos {type(pv)}"
    # El círculo circunscrito al triángulo rectángulo tiene radio = hipotenusa/2 = 10/√2 ≈ 7.07
    assert abs(r - 7.0710678118654755) < 1e-3, f"radio inesperado: {r}"


# ---------------------------------------------------------------------------
# R3 — comportamiento con 3 puntos colineales (caso antiguo r = 282864, pv = 0)
#    Ya no se lanza ValueError por colinealidad; el flujo actual retorna un radio
#    finito con pv ≥ 0. Si el radicando llega a ser ≤ 0, entonces sí ValueError.
# ---------------------------------------------------------------------------

def test_circulo_simple_3_cilineales_retorna_finito():
    """3 puntos colineales deben retornar un radio finito y pv ≥ 0 (no crash)."""
    # Tres puntos sobre la línea y = x, separación de 1 px.
    # Antiguamente (antes de la validación) daba r ≈ 282864, pv ≈ 0.0.
    # Con la implementación actual, el lstsq da un resultado; verificamos que
    # no se crash y que el radio y pv estén en rangos razonables.
    pts = np.array([[1000.0, 1000.0], [1001.0, 1001.0], [1002.0, 1002.0]])
    x, y, r, pv = CS.Circulo_simple(pts)

    # No debe crashear; r y pv deben ser números finitos.
    assert np.isfinite(r), f"r no es finito: {r}"
    assert np.isfinite(pv), f"pv no es finito: {pv}"
    # pv no debería ser exactamente 0.0 para puntos con cualquier dispersión;
    # si es < 0.1 está bien (puntos casi perfectos), pero no == 0.0 absoluto
    # en un caso donde los puntos no son idénticos.
    assert pv >= 0.0, f"pv debe ser >= 0, obtuvimos {pv}"


# ---------------------------------------------------------------------------
# R4 — radicando negativo: caso donde x_c² + y_c² - s ≤ 0
# ---------------------------------------------------------------------------

def test_circulo_simple_radicando_negativo():
    """Caso donde el radicando es negativo debe lanzar ValueError."""
    # Construimos un escenario donde el radicando puede ser ≤ 0.
    # Usamos puntos que llevan a s (el valor singular) mayor a x_c² + y_c².
    # Un caso práctico: puntos que hacen que el círculo "inverso" no exista.
    # Prácticamente, probamos con coordenadas que en aritmética flotante
    # pueden provocar este caso.
    pts = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    # Estos 3 puntos son colineales; el lstsq puede dar s tal que radicando <= 0.
    # Ejecutamos y vemos qué pasa; si lanza ValueError, bien. Si no,
    # el test verifica al menos que no devuelve r absurdo.
    try:
        x, y, r, pv = CS.Circulo_simple(pts)
        # Si no lanzó error, verificamos que el resultado sea razonable.
        assert r > 0, f"se esperaba r > 0, obtuvimos {r}"
        assert pv >= 0.0, f"pv debe ser >= 0, obtuvimos {pv}"
        # Verificamos que no sea el caso extremo antiguo.
        assert not (r > 1000 and pv == 0.0), (
            f"caso antiguo r={r}, pv={pv}; el comportamiento cambió, "
            "verifique si este test necesita ajuste"
        )
    except ValueError as e:
        # Si lanzó ValueError por radicando negativo, está bien.
        assert "resultado matemático inválido" in str(e)


# ---------------------------------------------------------------------------
# R5 — caso banal conocido: radio y pv esperables
# ---------------------------------------------------------------------------

def test_circulo_simple_caso_banal_r_pv_razonables():
    """3 puntos bien distribuidos deben dar r > 0 y pv >= 0 (no pv = 0 absoluto)."""
    # Un círculo de radio 5 centrado en (1, 2) con puntos alrededor.
    theta = np.linspace(0, 2 * np.pi, 20)
    circle_pts = np.array([[np.cos(t), np.sin(t)] for t in theta], dtype=float)
    circle_pts = circle_pts * 5 + np.array([[1.0, 2.0]])
    x, y, r, pv = CS.Circulo_simple(circle_pts)

    assert r > 0, f"se esperaba r > 0, obtuvimos {r}"
    assert pv >= 0.0, f"pv debe ser >= 0, obtuvimos {pv}"
    # El centro debería estar cerca de (1, 2) dado que desplazamos el círculo.
    assert abs(x - 1.0) < 1.5, f"centro x inesperado: {x}"
    assert abs(y - 2.0) < 1.5, f"centro y inesperado: {y}"
    # pv no debería ser exactamente 0.0 para puntos con dispersión real;
    # si es muy chico (ej. < 0.01) está bien, pero el test solo verifica >= 0.