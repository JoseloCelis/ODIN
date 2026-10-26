"""Etapa 3 — NonMaxSup: supresión de no máximos y doble umbral.

Contratos verificados (spec non-max-sup):
- Interpolación sobre el EJE del gradiente (ángulo mod 180°): el cuadrante no
  altera los vecinos.
- Empates conservadores (>=): una meseta constante no pierde píxeles.
- Simetría espejo: reflejar la imagen transforma el ángulo θ en 180° − θ.
- Equivalencia exacta con una referencia escalar independiente.
- Doble umbral: fuertes M >= umbral, débiles umbral² <= M < umbral, disjuntos.
- NMS_Parabolic / NMS_Gaussian: estimación del valor del pico en subpíxel.
"""

import numpy as np
import pytest

from odin.Preprocesamiento import NonMaxSup as NMS
from utilidades import nms_referencia_escalar


def _perfil_cuadratico(x):
    """Parábola con vértice en x0 = 2.3 y valor 10.0."""
    return -(x - 2.3) ** 2 + 10.0


def _perfil_gaussiano(x, sigma=0.8, x0=2.3):
    return 10.0 * np.exp(-((x - x0) ** 2) / (2.0 * sigma ** 2))


def test_conserva_el_pico_aislado():
    mg = np.zeros((5, 5))
    mg[2, 2] = 1.0

    salida = NMS.LinearInterpolation(mg, mg, mg, np.zeros_like(mg))

    assert np.count_nonzero(salida) == 1
    assert salida[2, 2] == 1.0


@pytest.mark.parametrize("angulo", [0.0, 90.0])
def test_meseta_constante_se_conserva_completa(angulo):
    mg = np.zeros((7, 7))
    mg[2:5, 2:5] = 1.0

    salida = NMS.LinearInterpolation(mg, mg, mg, np.full_like(mg, angulo))

    # Empate conservador: los 9 píxeles de la meseta sobreviven.
    assert np.count_nonzero(salida) == 9


def test_simetria_espejo_entre_80_y_100_grados():
    rng = np.random.default_rng(7)
    mg = rng.random((15, 15))

    # Reflejar horizontalmente transforma el ángulo θ en 180° − θ.
    salida_80 = NMS.LinearInterpolation(mg, mg, mg, np.full_like(mg, 80.0))
    salida_100 = NMS.LinearInterpolation(
        np.fliplr(mg), np.fliplr(mg), np.fliplr(mg), np.full_like(mg, 100.0)
    )

    assert np.allclose(np.fliplr(salida_100), salida_80, rtol=0, atol=1e-12)


def test_equivalencia_con_referencia_escalar_en_100_casos():
    for semilla in range(100):
        rng = np.random.default_rng(semilla)
        mg = rng.random((12, 12))
        angulo = rng.uniform(0.0, 360.0, size=(12, 12))

        obtenido = NMS.LinearInterpolation(mg, mg, mg, angulo)
        esperado = nms_referencia_escalar(mg, angulo)

        assert np.allclose(obtenido, esperado, rtol=0, atol=1e-12), (
            f"discrepancia con la referencia escalar en la semilla {semilla}"
        )


def test_doble_umbral_particiona_fuertes_y_debiles():
    mg = np.array([[0.0, 0.2, 0.4, 0.5, 0.9, 1.0]])

    gh, gl = NMS.DobleThreshold(mg, 0.5)

    assert np.array_equal(gh, (mg >= 0.5).astype(float))
    esperado_debil = np.where((mg >= 0.25) & (mg < 0.5), mg, 0.0)
    assert np.array_equal(gl, esperado_debil)
    assert not np.any((gh > 0) & (gl > 0))


def test_doble_umbral_limita_el_umbral_a_uno():
    mg = np.array([[0.0, 0.5, 1.0]])

    gh, gl = NMS.DobleThreshold(mg, 2.0)

    assert gh.tolist() == [[0.0, 0.0, 1.0]]
    assert np.all(gl == 0.0)


def test_nms_parabolico_reconstruye_el_vertice():
    mg = np.zeros((3, 5))
    mg[1, 1:4] = [_perfil_cuadratico(1.0), _perfil_cuadratico(2.0),
                  _perfil_cuadratico(3.0)]

    salida = NMS.NMS_Parabolic(mg, np.zeros_like(mg))  # eje horizontal (0°)
    valores = salida[salida != 0.0]

    assert valores.size == 1
    # El vértice real de la parábola es 10.0; el valor discreto es 9.91.
    assert valores[0] == pytest.approx(10.0, abs=1e-9)

    discreto = NMS.LinearInterpolation(mg, mg, mg, np.zeros_like(mg))
    assert discreto[1, 2] == pytest.approx(_perfil_cuadratico(2.0))


def test_nms_gaussiano_reconstruye_el_vertice_de_un_perfil_gaussiano():
    mg = np.zeros((3, 5))
    mg[1, 1:4] = [_perfil_gaussiano(1.0), _perfil_gaussiano(2.0),
                  _perfil_gaussiano(3.0)]

    salida = NMS.NMS_Gaussian(mg, np.zeros_like(mg))
    valores = salida[salida != 0.0]

    assert valores.size == 1
    # En espacio logarítmico una gaussiana es una parábola exacta; la pequeña
    # desviación viene del estabilizador log(MG + 1e-6).
    assert valores[0] == pytest.approx(_perfil_gaussiano(2.3), abs=1e-5)


def test_nms_gaussiano_esta_cerca_en_un_perfil_cuadratico():
    mg = np.zeros((3, 5))
    mg[1, 1:4] = [_perfil_cuadratico(1.0), _perfil_cuadratico(2.0),
                  _perfil_cuadratico(3.0)]

    salida = NMS.NMS_Gaussian(mg, np.zeros_like(mg))
    valores = salida[salida != 0.0]
    discreto = NMS.LinearInterpolation(mg, mg, mg, np.zeros_like(mg))[1, 2]

    assert valores.size == 1
    # El perfil no es gaussiano, así que el ajuste log-parabólico aproxima el
    # vértice (error medido 0.014) mejor de lo que lo hace el valor discreto
    # (error 0.090), pero sin la exactitud del ajuste cuadrático.
    error_gaussiano = abs(valores[0] - 10.0)
    error_discreto = abs(discreto - 10.0)
    assert error_gaussiano < error_discreto
    assert valores[0] == pytest.approx(10.0, abs=0.05)
