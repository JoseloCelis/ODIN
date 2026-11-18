"""Property-based tests para la etapa ① kernelSeparable (Hypothesis)."""

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st
from hypothesis.extra import numpy as npst

from src.odin.Preprocesamiento import kernelSeparable


@given(
    arr=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(
            st.integers(min_value=10, max_value=40),
            st.integers(min_value=10, max_value=40),
        ),
        elements=st.floats(min_value=0.0, max_value=255.0, allow_nan=False, allow_infinity=False),
    ),
    sigma=st.floats(min_value=0.5, max_value=4.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20, deadline=None)
def test_prop_kernel_separable_shape_y_finito(arr, sigma):
    """Propiedad: salidas mismo shape que la entrada y finitas para sigma > 0."""
    dx, dy = kernelSeparable(arr, sigma=sigma, wk=0, wConv=0, wr=0)

    assert dx.shape == arr.shape
    assert dy.shape == arr.shape
    assert np.all(np.isfinite(dx))
    assert np.all(np.isfinite(dy))


@given(
    arr=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(
            st.integers(min_value=10, max_value=40),
            st.integers(min_value=10, max_value=40),
        ),
        elements=st.floats(min_value=0.0, max_value=255.0, allow_nan=False, allow_infinity=False),
    ),
    sigma=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=10, deadline=None)
def test_prop_kernel_separable_sigma_no_positivo_devuelve_ceros(arr, sigma):
    """Propiedad: sigma <= 0 produce arreglos de ceros con el mismo shape."""
    dx, dy = kernelSeparable(arr, sigma=sigma, wk=0, wConv=0, wr=0)

    assert dx.shape == arr.shape
    assert dy.shape == arr.shape
    assert np.all(dx == 0)
    assert np.all(dy == 0)
