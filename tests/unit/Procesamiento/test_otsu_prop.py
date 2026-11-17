"""Property-based tests para la etapa ④ Otsu/Rosin (Hypothesis)."""

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st
from hypothesis.extra import numpy as npst

from src.odin.Procesamiento import umbralRosinYOtsu, umbralOtsu


@given(
    arr=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(
            st.integers(min_value=16, max_value=40),
            st.integers(min_value=16, max_value=40),
        ),
        elements=st.floats(min_value=0.0, max_value=255.0, allow_nan=False, allow_inf=False),
    ),
)
@settings(max_examples=30, deadline=None)
def test_prop_umbral_rosin_y_otsu_finitos_y_no_negativos(arr):
    """Propiedad: umbralRosinYOtsu devuelve (otsu, rosin) finitos y >= 0."""
    resultado = umbralRosinYOtsu(arr)

    assert isinstance(resultado, tuple)
    assert len(resultado) == 2
    for umbral in resultado:
        assert np.isfinite(umbral)
        assert umbral >= 0.0


@given(
    arr=npst.arrays(
        dtype=np.float64,
        shape=st.tuples(
            st.integers(min_value=16, max_value=40),
            st.integers(min_value=16, max_value=40),
        ),
        elements=st.floats(min_value=0.0, max_value=255.0, allow_nan=False, allow_inf=False),
    ),
)
@settings(max_examples=30, deadline=None)
def test_prop_umbral_otsu_finito_y_no_negativo(arr):
    """Propiedad: umbralOtsu devuelve un float finito y >= 0."""
    umbral = umbralOtsu(arr)

    assert np.isfinite(umbral)
    assert umbral >= 0.0
