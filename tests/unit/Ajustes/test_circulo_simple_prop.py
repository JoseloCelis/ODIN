"""Property-based tests para la etapa ⑨ Circulo_simple / LSC (Hypothesis)."""

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st

from src.odin.Ajustes import Circulo_simple


@given(
    radius=st.floats(min_value=10.0, max_value=150.0, allow_nan=False, allow_infinity=False),
    cx=st.floats(min_value=50.0, max_value=400.0, allow_nan=False, allow_infinity=False),
    cy=st.floats(min_value=50.0, max_value=400.0, allow_nan=False, allow_infinity=False),
    n_points=st.integers(min_value=30, max_value=120),
    noise=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=30, deadline=None)
def test_prop_lsc_recupera_circulo_perfecto_o_con_ruido(radius, cx, cy, n_points, noise, seed):
    """Propiedad: Circulo_simple recupera centro y radio de puntos sobre un círculo."""
    rng = np.random.default_rng(seed)
    angles = np.sort(rng.uniform(0.0, 2.0 * np.pi, n_points))
    xs = cx + radius * np.cos(angles)
    ys = cy + radius * np.sin(angles)
    if noise > 0.0:
        xs = xs + rng.normal(0.0, noise, n_points)
        ys = ys + rng.normal(0.0, noise, n_points)
    points = np.column_stack([xs, ys])

    fit_x, fit_y, fit_r, pv = Circulo_simple(points)

    atol = 2.0 if noise > 0.0 else 1e-6
    assert np.isclose(fit_x, cx, atol=atol)
    assert np.isclose(fit_y, cy, atol=atol)
    assert np.isclose(fit_r, radius, atol=atol)
    assert np.isfinite(pv)
