"""Etapa 4 — Otsu y Rosin (MtoOtsu).

Contratos verificados (spec otsu-rosin):
- Histograma solo de píxeles activos (IG > 0), 256 bins.
- Otsu = máximo de la varianza interclase; coincide con una referencia
  independiente por barrido sobre valores reales cuando el óptimo es agudo.
- Meseta de Otsu: con clusters compactos la varianza es plana y cualquier
  punto de la meseta es un umbral válido (no es un defecto).
- El umbral escala con la entrada.
- Valor constante: el umbral es exactamente ese valor y nunca negativo.
- Sin píxeles activos: (0.0, 0.0).
- Rosin: criterio solo diagnóstico; en histogramas bimodales cae en el flanco
  del pico dominante.
"""

import numpy as np
import pytest

from src.odin.Procesamiento.models import otsu_rosin as OT
from utilidades import otsu_referencia, varianza_interclase


def _bimodal(sigma_cluster, n_por_cluster, semilla=7):
    rng = np.random.default_rng(semilla)
    datos = np.concatenate([
        rng.normal(0.25, sigma_cluster, n_por_cluster),
        rng.normal(0.75, sigma_cluster, n_por_cluster),
    ])
    return datos.clip(1e-6, None)


@pytest.mark.parametrize("sigma_cluster", [0.12, 0.20])
def test_otsu_coincide_con_la_referencia_si_el_optimo_es_agudo(sigma_cluster):
    datos = _bimodal(sigma_cluster, 2000)

    umbral, _ = OT.umbralRosinYOtsu(datos.reshape(-1, 1))
    referencia = otsu_referencia(datos)

    ancho_bin = (datos.max() - datos.min()) / 256
    assert abs(umbral - referencia) <= 1.5 * ancho_bin


def test_meseta_de_otsu_es_un_maximo_plano():
    datos = _bimodal(0.05, 2000)

    umbral, _ = OT.umbralRosinYOtsu(datos.reshape(-1, 1))

    # Clusters compactos y separados: la varianza interclase es plana entre
    # ellos. Cualquier punto de la meseta es un umbral válido (R3).
    assert varianza_interclase(datos, umbral) == pytest.approx(
        varianza_interclase(datos, 0.5), rel=1e-6
    )
    # Y ese valor es el máximo del criterio, no un punto arbitrario.
    assert varianza_interclase(datos, umbral) >= varianza_interclase(datos, 0.2)


def test_el_umbral_escala_con_la_entrada():
    datos = _bimodal(0.12, 1000, semilla=3)

    umbral, _ = OT.umbralRosinYOtsu(datos.reshape(-1, 1))
    umbral_x10, _ = OT.umbralRosinYOtsu((datos * 10.0).reshape(-1, 1))

    assert umbral > 0.0
    assert umbral_x10 == pytest.approx(10.0 * umbral, rel=1e-12)


@pytest.mark.parametrize("valor", [1e-6, 0.001, 0.005, 0.05, 0.5, 0.7, 1.0, 3.7])
def test_valor_constante_devuelve_ese_valor_exacto(valor):
    otsu, rosin = OT.umbralRosinYOtsu(np.full((20, 20), valor))

    assert otsu == valor
    assert rosin == valor
    assert otsu >= 0.0


def test_umbral_otsu_en_casi_constante_con_rango_minimo_no_lanza_excepcion():
    """R5/D1 (extension): la guarda debe cubrir el caso de rango minimo
    (casi-constante) que hace fallar a np.histogram con 256 bins."""
    ig = np.concatenate([np.full(100, 0.5), np.full(100, 0.5 + 1e-16)])

    umbral = OT.umbralOtsu(ig)

    assert np.isfinite(umbral)


@pytest.mark.parametrize("entrada", [
    np.zeros((10, 10)),
    np.array([]),
    -np.ones((5, 5)),
])
def test_sin_pixeles_activos_devuelve_cero(entrada):
    assert OT.umbralRosinYOtsu(entrada) == (0.0, 0.0)


def test_umbral_otsu_publico_coincide_con_la_primera_salida():
    datos = _bimodal(0.12, 1000, semilla=5)
    entrada = datos.reshape(-1, 1)

    solo_otsu = OT.umbralOtsu(entrada)
    otsu, _ = OT.umbralRosinYOtsu(entrada)

    assert solo_otsu == otsu


def test_nan_se_descarta_sin_propagar():
    entrada = np.array([[0.2, np.nan], [0.8, 0.3]])

    otsu, rosin = OT.umbralRosinYOtsu(entrada)

    assert np.isfinite(otsu)
    assert np.isfinite(rosin)


def test_rosin_cae_en_el_flanco_del_pico_dominante():
    rng = np.random.default_rng(11)
    datos = np.concatenate([
        rng.normal(0.10, 0.012, 6000),
        rng.normal(0.60, 0.06, 800),
    ]).clip(1e-6, None)
    entrada = datos.reshape(-1, 1)

    _, rosin = OT.umbralRosinYOtsu(entrada)
    counts, _, xcenters = OT._preparar_histograma(entrada)
    pico = xcenters[np.argmax(counts)]
    cola = xcenters[np.flatnonzero(counts > 0)[-1]]

    # Rosin es un criterio para histogramas unimodales: en datos bimodales
    # queda en el flanco del pico dominante, no en el valle entre clusters.
    assert pico < rosin < cola
    assert rosin < 0.3
