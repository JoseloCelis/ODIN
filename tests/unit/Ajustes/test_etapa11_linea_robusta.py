"""Etapa ⑪ — linea_robusta: ajuste robusto de recta migrado de MATLAB.

Cubre S2 (poda iterativa con cota decreciente 20 -> 8 px, refit SVD con más
de 3 inliers, dispersión del residual y puntos conservados) y S6 (modelo puro,
numpy, sin UI). Los helpers `dist_p_recta`, `euc_space`, `linea_mc` y el
wrapper `linea1` se prueban en su forma vectorizada.
"""

import numpy as np
import pytest

from src.odin.Ajustes.models.linea_robusta import (
    dist_p_recta,
    euc_space,
    linea_mc,
    linea_robusta,
    linea1,
)


def _recta(punto: tuple[float, float], angulo: float) -> np.ndarray:
    """param [x0, y0, cos_x, cos_y] de una recta que pasa por `punto`."""
    return np.array([punto[0], punto[1], np.cos(angulo), np.sin(angulo)], dtype=float)


# ---------------------------------------------------------------------------
# dist_p_recta
# ---------------------------------------------------------------------------

def test_dist_p_recta_puntos_sobre_la_recta():
    puntos = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
    param = _recta((0.0, 0.0), 0.0)

    distancias = dist_p_recta(puntos, param)

    assert distancias.shape == (4,)
    assert np.allclose(distancias, 0.0, atol=1e-12)


def test_dist_p_recta_distancias_conocidas():
    # Recta vertical x = 5 (punto (5,0), dirección (0,1)).
    param_vertical = np.array([5.0, 0.0, 0.0, 1.0])
    assert dist_p_recta(np.array([[0.0, 0.0]]), param_vertical)[0] == pytest.approx(5.0)

    # Recta horizontal y = 3 (punto (0,3), dirección (1,0)).
    param_horizontal = np.array([0.0, 3.0, 1.0, 0.0])
    assert dist_p_recta(np.array([[0.0, 0.0]]), param_horizontal)[0] == pytest.approx(3.0)

    # Recta y = x (punto (0,0), dirección (1,1)/sqrt(2)): (1,0) está a 1/sqrt(2).
    param_diagonal = _recta((0.0, 0.0), np.pi / 4)
    assert dist_p_recta(np.array([[1.0, 0.0]]), param_diagonal)[0] == pytest.approx(1.0 / np.sqrt(2))


def test_dist_p_recta_vectorizado_coincide_con_escalar():
    puntos = np.array([[0.0, 0.0], [2.0, 5.0], [-3.0, 1.0], [4.0, -2.0]])
    param = _recta((1.0, 1.0), -0.6)

    vectorizado = dist_p_recta(puntos, param)
    escalar = np.array([dist_p_recta(puntos[i:i + 1], param)[0] for i in range(len(puntos))])

    assert np.allclose(vectorizado, escalar)


def test_dist_p_recta_normaliza_la_direccion():
    """La distancia es independiente de la escala de los cosenos directores."""
    puntos = np.array([[0.0, 0.0], [2.0, 2.0]])
    unitario = np.array([5.0, 0.0, 0.0, 1.0])
    escalado = np.array([5.0, 0.0, 0.0, 7.0])

    assert np.allclose(dist_p_recta(puntos, escalado), dist_p_recta(puntos, unitario))


def test_dist_p_recta_direccion_cero_lanza():
    with pytest.raises(ValueError, match="cosenos directores"):
        dist_p_recta(np.array([[0.0, 0.0]]), np.array([0.0, 0.0, 0.0, 0.0]))


def test_dist_p_recta_entrada_vacia():
    assert dist_p_recta(np.empty((0, 2)), _recta((0.0, 0.0), 0.0)).shape == (0,)


def test_dist_p_recta_param_con_forma_invalida():
    with pytest.raises(ValueError, match="4 elementos"):
        dist_p_recta(np.array([[0.0, 0.0]]), np.array([0.0, 0.0, 1.0]))


def test_dist_p_recta_no_modifica_los_argumentos():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0]])
    param = _recta((0.0, 0.0), 0.3)
    puntos_copia = puntos.copy()
    param_copia = param.copy()

    dist_p_recta(puntos, param)

    assert np.array_equal(puntos, puntos_copia)
    assert np.array_equal(param, param_copia)


# ---------------------------------------------------------------------------
# euc_space
# ---------------------------------------------------------------------------

def test_euc_space_rho_theta_conocidos():
    # theta = 0: normal (1,0), el pie de la perpendicular es (rho, 0), dirección (0,1).
    assert np.allclose(euc_space(5.0, 0.0), [5.0, 0.0, 0.0, 1.0], atol=1e-12)

    # theta = pi/2: normal (0,1), el pie es (0, rho), dirección (-1,0).
    assert np.allclose(euc_space(5.0, np.pi / 2), [0.0, 5.0, -1.0, 0.0], atol=1e-12)


def test_euc_space_el_punto_es_el_pie_de_la_perpendicular():
    for rho, theta in [(3.0, 0.4), (-7.0, -1.1), (12.0, 1.5)]:
        parametro = euc_space(rho, theta)
        normal = np.array([np.cos(theta), np.sin(theta)])
        assert np.dot(normal, parametro[:2]) == pytest.approx(rho)


def test_euc_space_direccion_unitaria():
    for theta in np.linspace(-np.pi / 2, np.pi / 2, 17):
        direccion = euc_space(2.0, theta)[2:4]
        assert np.linalg.norm(direccion) == pytest.approx(1.0)


def test_euc_space_valores_no_finitos_lanzan():
    with pytest.raises(ValueError, match="finitos"):
        euc_space(np.nan, 0.0)
    with pytest.raises(ValueError, match="finitos"):
        euc_space(1.0, np.inf)


# ---------------------------------------------------------------------------
# linea_mc (lineaMC)
# ---------------------------------------------------------------------------

def test_linea_mc_recupera_centroide_y_direccion():
    puntos = np.array([[0.0, 3.0], [1.0, 5.0], [2.0, 7.0], [3.0, 9.0], [4.0, 11.0]])

    parametro = linea_mc(puntos)

    assert parametro.shape == (4,)
    assert np.allclose(parametro[:2], [2.0, 7.0], atol=1e-12)
    esperado = np.array([1.0, 2.0]) / np.sqrt(5.0)
    assert abs(np.dot(parametro[2:4], esperado)) == pytest.approx(1.0, abs=1e-12)


def test_linea_mc_direccion_unitaria():
    puntos = np.array([[0.0, 0.0], [10.0, 1.0], [20.0, -1.0], [30.0, 0.5]])

    parametro = linea_mc(puntos)

    assert np.linalg.norm(parametro[2:4]) == pytest.approx(1.0)


def test_linea_mc_direccion_principal():
    """Con una nube alargada la dirección es la de máxima varianza."""
    rng = np.random.default_rng(7)
    s = np.linspace(0.0, 500.0, 60)
    puntos = np.column_stack((s, 0.1 * s + rng.normal(0.0, 0.01, 60)))

    parametro = linea_mc(puntos)

    esperado = np.array([1.0, 0.1]) / np.hypot(1.0, 0.1)
    assert abs(np.dot(parametro[2:4], esperado)) == pytest.approx(1.0, abs=1e-6)


def test_linea_mc_un_punto_lanza():
    with pytest.raises(ValueError, match="al menos 2 puntos"):
        linea_mc(np.array([[3.0, 4.0]]))


def test_linea_mc_no_modifica_la_entrada():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    copia = puntos.copy()

    linea_mc(puntos)

    assert np.array_equal(puntos, copia)


# ---------------------------------------------------------------------------
# linea_robusta
# ---------------------------------------------------------------------------

def _inliers_con_outliers() -> tuple[np.ndarray, np.ndarray]:
    """100 inliers con ruido y 50 outliers lejanos sobre la recta y = 0.5x + 10."""
    rng = np.random.default_rng(11)
    x = np.linspace(0.0, 100.0, 100)
    inliers = np.column_stack((x, 0.5 * x + 10.0 + rng.normal(0.0, 0.5, 100)))
    x_out = rng.uniform(0.0, 100.0, 50)
    outliers = np.column_stack((x_out, 0.5 * x_out + 10.0 + rng.uniform(40.0, 80.0, 50)))
    puntos = np.vstack((inliers, outliers))
    return puntos, inliers


def test_linea_robusta_recupera_la_recta_y_poda_outliers():
    puntos, inliers = _inliers_con_outliers()
    parametro_inicial = _recta((0.0, 10.0), np.arctan2(0.5, 1.0))

    parametro, r, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    assert parametro.shape == (4,)
    assert sobrevivientes.shape == (100, 2)
    assert np.allclose(sobrevivientes, inliers)

    esperado = np.array([1.0, 0.5]) / np.hypot(1.0, 0.5)
    assert abs(np.dot(parametro[2:4], esperado)) == pytest.approx(1.0, abs=1e-6)
    # El punto de la recta ajustada sigue sobre la recta real.
    assert parametro[1] - (0.5 * parametro[0] + 10.0) == pytest.approx(0.0, abs=0.5)
    assert 0.0 <= r < 5.0


def test_linea_robusta_refit_svd_coincide_con_linea_mc():
    puntos, _ = _inliers_con_outliers()
    parametro_inicial = _recta((0.0, 10.0), np.arctan2(0.5, 1.0))

    parametro, _, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    # Con más de 3 inliers el último refit es exactamente linea_mc(sobrevivientes).
    assert len(sobrevivientes) > 3
    assert np.allclose(parametro, linea_mc(sobrevivientes))


def test_linea_robusta_dispersion_es_pico_a_valle_de_los_residuales():
    puntos, _ = _inliers_con_outliers()
    parametro_inicial = _recta((0.0, 10.0), np.arctan2(0.5, 1.0))

    parametro, r, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    residuales = dist_p_recta(sobrevivientes, parametro)
    assert r == pytest.approx(float(np.max(residuales) - np.min(residuales)))


def test_linea_robusta_cota_poda_mas_alla_de_8px():
    inliers = np.column_stack((np.arange(100.0), np.zeros(100)))
    parametro_inicial = _recta((0.0, 0.0), 0.0)

    lejano = np.vstack((inliers, [[50.0, 8.5]]))
    _, _, sobrevivientes = linea_robusta(lejano, parametro_inicial)
    assert sobrevivientes.shape == (100, 2)

    cercano = np.vstack((inliers, [[50.0, 7.5]]))
    _, _, sobrevivientes = linea_robusta(cercano, parametro_inicial)
    assert sobrevivientes.shape == (101, 2)


def test_linea_robusta_se_detiene_al_caer_la_fraccion_de_inliers():
    """Con 11 puntos en la primera cota y 1 en la segunda, el bucle se detiene."""
    ts = np.linspace(0.0, 100.0, 5)
    puntos = np.vstack(
        (
            np.array([[50.0, 0.0]]),
            np.column_stack((ts, np.full(5, 19.999))),
            np.column_stack((ts, np.full(5, -19.999))),
        )
    )
    parametro_inicial = _recta((50.0, 0.0), 0.0)

    parametro, r, sobrevivientes = linea_robusta(puntos, parametro_inicial)

    assert sobrevivientes.shape == (1, 2)
    assert np.allclose(sobrevivientes[0], [50.0, 0.0], atol=1e-9)
    assert abs(parametro[2]) == pytest.approx(1.0, abs=1e-9)
    assert abs(parametro[3]) == pytest.approx(0.0, abs=1e-9)
    assert r == pytest.approx(0.0)


def test_linea_robusta_entrada_vacia_lanza():
    with pytest.raises(ValueError, match="al menos 3 puntos"):
        linea_robusta(np.empty((0, 2)), _recta((0.0, 0.0), 0.0))


def test_linea_robusta_dos_puntos_lanzan():
    with pytest.raises(ValueError, match="al menos 3 puntos"):
        linea_robusta(np.array([[0.0, 0.0], [1.0, 1.0]]), _recta((0.0, 0.0), 0.0))


def test_linea_robusta_entrada_no_ndarray_lanza_type_error():
    with pytest.raises(TypeError, match="numpy.ndarray"):
        linea_robusta([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]], _recta((0.0, 0.0), 0.0))


def test_linea_robusta_shape_invalida_lanza():
    with pytest.raises(ValueError, match="forma"):
        linea_robusta(np.array([0.0, 0.0, 1.0]), _recta((0.0, 0.0), 0.0))


def test_linea_robusta_puntos_no_finitos_lanzan():
    puntos = np.array([[0.0, 0.0], [1.0, np.nan], [2.0, 2.0]])
    with pytest.raises(ValueError, match="finitos"):
        linea_robusta(puntos, _recta((0.0, 0.0), 0.0))


def test_linea_robusta_param_con_forma_invalida_lanza():
    with pytest.raises(ValueError, match="4 elementos"):
        linea_robusta(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), np.array([0.0, 0.0, 1.0]))


def test_linea_robusta_param_no_finito_lanza():
    param = np.array([0.0, 0.0, np.inf, 0.0])
    with pytest.raises(ValueError, match="finitos"):
        linea_robusta(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), param)


def test_linea_robusta_direccion_cero_lanza():
    with pytest.raises(ValueError, match="cosenos directores"):
        linea_robusta(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), np.array([0.0, 0.0, 0.0, 0.0]))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"porcentaje": 0.0},
        {"porcentaje": 1.0},
        {"paso": 0.0},
        {"cota_lim": 20.0},
        {"cota_lim": 25.0},
    ],
)
def test_linea_robusta_parametros_invalidos_lanzan(kwargs):
    with pytest.raises(ValueError):
        linea_robusta(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), _recta((0.0, 0.0), 0.0), **kwargs)


def test_linea_robusta_sin_puntos_dentro_de_la_cota_lanza():
    puntos = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    # Recta inicial a 100 px de todos los puntos.
    parametro_inicial = _recta((0.0, 100.0), 0.0)

    with pytest.raises(ValueError, match="no quedaron puntos"):
        linea_robusta(puntos, parametro_inicial)


def test_linea_robusta_no_modifica_la_entrada():
    puntos, _ = _inliers_con_outliers()
    copia = puntos.copy()
    parametro_inicial = _recta((0.0, 10.0), np.arctan2(0.5, 1.0))
    param_copia = parametro_inicial.copy()

    linea_robusta(puntos, parametro_inicial)

    assert np.array_equal(puntos, copia)
    assert np.array_equal(parametro_inicial, param_copia)


# ---------------------------------------------------------------------------
# linea1 (wrapper de Linea1.m)
# ---------------------------------------------------------------------------

def test_linea1_devuelve_un_resultado_por_candidata():
    puntos, _ = _inliers_con_outliers()
    valores = np.array(
        [
            [-8.94427191, -1.10714872],  # y = 0.5x + 10 en forma normal
            [10.0, 0.0],                 # recta x = 10 (sin relación con los puntos)
        ]
    )

    parametros, r, finales = linea1(puntos, valores)

    assert parametros.shape == (2, 4)
    assert r.shape == (2,)
    assert len(finales) == 2
    for k in range(2):
        esperado = linea_robusta(puntos, euc_space(*valores[k]))
        assert np.allclose(parametros[k], esperado[0])
        assert r[k] == pytest.approx(esperado[1])
        assert np.allclose(finales[k], esperado[2])


def test_linea1_acepta_una_sola_candidata():
    puntos, _ = _inliers_con_outliers()
    valores = np.array([[-8.94427191, -1.10714872]])

    parametros, r, finales = linea1(puntos, valores)

    assert parametros.shape == (1, 4)
    assert r.shape == (1,)
    assert len(finales) == 1


def test_linea1_valores_con_forma_invalida_lanza():
    with pytest.raises(ValueError, match="forma"):
        linea1(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), np.array([1.0, 2.0, 3.0]))
