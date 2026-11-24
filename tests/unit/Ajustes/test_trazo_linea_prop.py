"""Propiedades (Hypothesis) de trazo_linea: invariancia a transformaciones rígidas.

Cubre el caso 8 de `test_trazo_linea.py`: el ancho es invariante a
rotación/traslación rígidas.
"""

import numpy as np
import pytest
from hypothesis import given, strategies as st

from src.odin.Ajustes.models.trazo_linea import medir_trazo


# ---------------------------------------------------------------------------
# Estrategias de generación
# ---------------------------------------------------------------------------

@st.composite
def bandas_gruesas(draw, n=50, medio_ancho=20.0, ruido=0.3):
    """Genera una banda gruesa con ruido."""
    rng = np.random.default_rng(draw(st.integers(min_value=0, max_value=2**32 - 1)))
    x = np.linspace(-50.0, 50.0, n)
    superior = np.column_stack(
        [x, np.full(n, medio_ancho) + rng.normal(0.0, ruido, n)]
    )
    inferior = np.column_stack(
        [x, np.full(n, -medio_ancho) + rng.normal(0.0, ruido, n)]
    )
    return np.vstack([superior, inferior])


@st.composite
def angulos(draw):
    """Genera un ángulo en [-π, π]."""
    return draw(st.floats(min_value=-np.pi, max_value=np.pi, allow_nan=False, allow_infinity=False))


# ---------------------------------------------------------------------------
# Propiedades
# ---------------------------------------------------------------------------

@given(puntos=bandas_gruesas(), angulo=angulos())
def test_ancho_invariante_a_rotacion(puntos, angulo):
    """El ancho es invariante a rotación rígida."""
    # Gradiente horizontal coherente.
    gx = np.zeros(len(puntos))
    gy = np.where(puntos[:, 1] > 0, 1.0, -1.0)
    theta_original = np.pi / 2  # Horizontal.

    # Medición original.
    medicion_original = medir_trazo(puntos, gx, gy, theta_original)
    assert medicion_original is not None

    # Rotamos puntos y gradiente.
    c, s = np.cos(angulo), np.sin(angulo)
    matriz_rotacion = np.array([[c, -s], [s, c]])
    puntos_rotados = puntos @ matriz_rotacion.T
    gx_rotado = gx * c - gy * s
    gy_rotado = gx * s + gy * c
    theta_rotado = theta_original + angulo

    # Medición rotada.
    medicion_rotada = medir_trazo(puntos_rotados, gx_rotado, gy_rotado, theta_rotado)
    assert medicion_rotada is not None

    # El ancho debe ser el mismo (invariante).
    assert medicion_rotada.ancho == pytest.approx(medicion_original.ancho, abs=1e-6)


@given(puntos=bandas_gruesas(), dx=st.floats(-100, 100), dy=st.floats(-100, 100))
def test_ancho_invariante_a_traslacion(puntos, dx, dy):
    """El ancho es invariante a traslación rígida."""
    # Gradiente horizontal coherente.
    gx = np.zeros(len(puntos))
    gy = np.where(puntos[:, 1] > 0, 1.0, -1.0)
    theta = np.pi / 2  # Horizontal.

    # Medición original.
    medicion_original = medir_trazo(puntos, gx, gy, theta)
    assert medicion_original is not None

    # Trasladamos puntos.
    puntos_trasladados = puntos + np.array([dx, dy])

    # Medición trasladada (mismos gradientes, mismo theta).
    medicion_trasladada = medir_trazo(puntos_trasladados, gx, gy, theta)
    assert medicion_trasladada is not None

    # El ancho debe ser el mismo (invariante).
    assert medicion_trasladada.ancho == pytest.approx(medicion_original.ancho, abs=1e-6)
