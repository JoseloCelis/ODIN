"""Etapa 2 — MagFase: magnitud normalizada y fase en grados.

Contratos verificados (spec mag-fase):
- Magnitud = hypot(Gx, Gy) normalizada por su máximo absoluto.
- Ángulo en grados con la convención de atan2 (0° = +x, 90° = +fila).
- Imagen plana: magnitud y ángulo en cero.
- Rango [0, 1] para la magnitud y [-180, 180] para el ángulo.
- Entrada vacía: arreglos vacíos, sin excepción.
"""

import numpy as np
import pytest

from odin.Preprocesamiento import MagnitudGradiente as MF


def test_triangulo_3_4_5():
    gx = np.array([[3.0]])
    gy = np.array([[4.0]])

    mg, angulo = MF.MagFase(gx, gy)

    assert mg[0, 0] == pytest.approx(1.0)  # 5 normalizado por su propio máximo
    assert angulo[0, 0] == pytest.approx(53.13010235415598)


def test_imagen_plana_queda_en_cero():
    ceros = np.zeros((6, 7))

    mg, angulo = MF.MagFase(ceros, ceros)

    assert np.all(mg == 0.0)
    assert np.all(angulo == 0.0)  # atan2(0, 0) = 0


@pytest.mark.parametrize("semilla", [0, 1, 2])
def test_rangos_y_normalizacion(semilla):
    rng = np.random.default_rng(semilla)
    gx = rng.normal(size=(30, 40))
    gy = rng.normal(size=(30, 40))

    mg, angulo = MF.MagFase(gx, gy)

    assert mg.min() >= 0.0
    assert mg.max() == pytest.approx(1.0)
    assert angulo.min() >= -180.0
    assert angulo.max() <= 180.0

    # Desnormalizar con el máximo devuelve la magnitud de la etapa anterior.
    escala = np.max(np.abs(np.hypot(gx, gy)))
    assert np.allclose(mg * escala, np.hypot(gx, gy), rtol=0, atol=1e-12)


def test_entrada_vacia_devuelve_arreglos_vacios():
    mg, angulo = MF.MagFase(np.empty(0), np.empty(0))

    assert mg.size == 0
    assert angulo.size == 0


def test_angulo_nunca_es_menos_180():
    # atan2(-0.0, negativo) devuelve -180 en NumPy; el spec exige (-180, 180],
    # así que -180 debe mapearse a 180.
    gx = np.array([[-1.0, -2.0]])
    gy = np.array([[-0.0, -0.0]])

    _, angulo = MF.MagFase(gx, gy)

    assert not np.any(angulo == -180.0), f"ángulo -180 no permitido: {angulo}"
    assert np.all(angulo <= 180.0)
