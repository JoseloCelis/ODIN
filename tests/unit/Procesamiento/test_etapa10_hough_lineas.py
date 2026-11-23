"""Etapa ⑩ — houghLines: transformada de Hough para rectas.

Caracterización del comportamiento esperado (spec migracion-lineas-geometria,
S1 y S6):

- Acumulador (rho, theta) con theta en [-pi/2, pi/2] en paso pi/360 y rho
  cuantizado a 0.5 px (S1).
- Cada candidata expone DOS métricas: el conteo de picos agrupados (`p` del
  original, su criterio de selección) y la masa del acumulador sumada sobre
  las celdas del grupo (S1).
- Antes de seleccionar, las candidatas se fusionan con `reduce` con
  `sigma = 2.7 * max(desv_std)` (S1).
- `hough_lineas` devuelve la candidata con más picos agrupados; ante empate,
  la de mayor masa (S1).
- Rechaza `percent` fuera de [0.6, 0.9] y `max_dist_px` menor a 30 (S1).
- El modelo es NumPy puro: no importa gi, Gtk, Gdk, Adw ni cairo (S6).
"""

import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest

from src.odin.Procesamiento.models.hough_lineas import (
    NUM_THETAS,
    PASO_RHO,
    PASO_THETA,
    CandidatasLineas,
    acumulador_lineas,
    candidatas_lineas,
    hough_lineas,
    reducir_candidatas,
)

RAIZ = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _recta_vertical(ancho, alto, x, y0=10, y1=None):
    """Puntos de una recta vertical `x` entre `y0` e `y1` (inclusive)."""
    y1 = alto - 10 if y1 is None else y1
    y = np.arange(y0, y1 + 1, dtype=float)
    return np.column_stack([np.full(y.size, float(x)), y])


def _recta_horizontal(ancho, alto, y, x0=10, x1=None):
    """Puntos de una recta horizontal `y` entre `x0` y `x1` (inclusive)."""
    x1 = ancho - 10 if x1 is None else x1
    x = np.arange(x0, x1 + 1, dtype=float)
    return np.column_stack([x, np.full(x.size, float(y))])


def _recta_diagonal(ancho, alto, x0, x1):
    """Puntos de la recta `y = x` entre `x0` y `x1` (inclusive)."""
    x = np.arange(x0, x1 + 1, dtype=float)
    return np.column_stack([x, x])


def _diag_len(alto, ancho):
    return int(np.ceil(np.hypot(ancho, alto)))


def _candidatas(rhos, thetas, conteos, masas, desviaciones):
    """Construye un `CandidatasLineas` para probar `reducir_candidatas`."""
    return CandidatasLineas(
        rhos=np.asarray(rhos, dtype=float),
        thetas=np.asarray(thetas, dtype=float),
        conteos=np.asarray(conteos, dtype=np.int64),
        masas=np.asarray(masas, dtype=np.int64),
        desviaciones=np.asarray(desviaciones, dtype=float),
    )


# ---------------------------------------------------------------------------
# S1 — acumulador (rho, theta)
# ---------------------------------------------------------------------------

def test_acumulador_forma_dtype_y_pasos():
    alto, ancho = 60, 80
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = np.array([[10.0, 20.0], [30.0, 40.0]])

    acumulador, rhos, thetas = acumulador_lineas(puntos, imagen)

    assert acumulador.shape == (4 * _diag_len(alto, ancho) + 1, NUM_THETAS)
    assert np.issubdtype(acumulador.dtype, np.integer)
    assert thetas[0] == pytest.approx(-np.pi / 2)
    assert thetas[-1] == pytest.approx(np.pi / 2)
    assert np.allclose(np.diff(thetas), PASO_THETA)
    assert rhos[0] == pytest.approx(-_diag_len(alto, ancho))
    assert rhos[-1] == pytest.approx(_diag_len(alto, ancho))
    assert np.allclose(np.diff(rhos), PASO_RHO)


def test_los_votos_se_conservan():
    """Cada punto vota una vez por cada theta: total = N * 361."""
    alto, ancho = 60, 80
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = np.array([[10.0, 20.0], [30.0, 40.0], [59.0, 59.0]])

    acumulador, _, _ = acumulador_lineas(puntos, imagen)

    assert acumulador.sum() == puntos.shape[0] * NUM_THETAS
    assert acumulador.max() <= puntos.shape[0]


def test_el_acumulador_es_no_negativo():
    alto, ancho = 40, 40
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = np.array([[5.0, 5.0], [30.0, 20.0]])

    acumulador, _, _ = acumulador_lineas(puntos, imagen)

    assert np.all(acumulador >= 0)


# ---------------------------------------------------------------------------
# S1 — detección de rectas
# ---------------------------------------------------------------------------

def test_detecta_recta_vertical():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 100)  # 181 puntos

    rho, theta, conteo, masa, desviacion = hough_lineas(puntos, imagen)

    assert rho == pytest.approx(100.0, abs=0.6)
    assert theta == pytest.approx(0.0, abs=0.02)
    assert conteo == 1
    assert masa == 181
    assert desviacion == pytest.approx(0.0, abs=1e-9)


def test_detecta_recta_diagonal():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_diagonal(ancho, alto, 20, 180)  # 161 puntos

    rho, theta, conteo, masa, desviacion = hough_lineas(puntos, imagen)

    assert theta == pytest.approx(-np.pi / 4, abs=0.02)
    assert rho == pytest.approx(0.0, abs=0.6)
    assert conteo == 1
    assert masa == 161
    assert desviacion == pytest.approx(0.0, abs=1e-9)


def test_recta_horizontal_cae_en_el_borde_de_theta():
    """Con theta en [-pi/2, pi/2], la horizontal tiene dos representaciones."""
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_horizontal(ancho, alto, 100)  # 181 puntos

    rho, theta, conteo, masa, _ = hough_lineas(puntos, imagen)

    assert abs(rho) == pytest.approx(100.0, abs=0.6)
    assert abs(theta) == pytest.approx(np.pi / 2, abs=0.02)
    assert conteo == 1
    assert masa == 181


def test_recta_con_ruido_aumenta_la_desviacion():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    limpio = _recta_vertical(ancho, alto, 100)
    rng = np.random.default_rng(7)
    y = np.arange(10, 191, dtype=float)
    ruidoso = np.column_stack([100.0 + rng.uniform(-5.0, 5.0, size=y.size), y])

    _, _, _, _, desviacion_limpia = hough_lineas(limpio, imagen)
    rho_ruidoso, _, _, _, desviacion_ruidosa = hough_lineas(ruidoso, imagen)

    assert desviacion_limpia == pytest.approx(0.0, abs=1e-9)
    assert desviacion_ruidosa > 0.5
    assert abs(rho_ruidoso - 100.0) < 10.0


# ---------------------------------------------------------------------------
# S1 — guards de parámetros
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("percent", [0.59, 0.91, -0.1, 1.5, np.nan])
def test_rechaza_percent_fuera_de_rango(percent):
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 100)

    with pytest.raises(ValueError):
        hough_lineas(puntos, imagen, percent=percent)


@pytest.mark.parametrize("percent", [0.6, 0.9])
def test_acepta_percent_en_los_extremos(percent):
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 100)

    rho, theta, conteo, masa, _ = hough_lineas(puntos, imagen, percent=percent)

    assert rho == pytest.approx(100.0, abs=0.6)
    assert theta == pytest.approx(0.0, abs=0.02)
    assert conteo == 1
    assert masa == 181


def test_rechaza_max_dist_px_menor_a_30():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 100)

    with pytest.raises(ValueError):
        hough_lineas(puntos, imagen, max_dist_px=29.9)

    with pytest.raises(ValueError):
        hough_lineas(puntos, imagen, max_dist_px=np.nan)


def test_acepta_max_dist_px_30():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 100)

    rho, theta, conteo, masa, _ = hough_lineas(puntos, imagen, max_dist_px=30.0)

    assert rho == pytest.approx(100.0, abs=0.6)
    assert theta == pytest.approx(0.0, abs=0.02)
    assert conteo == 1
    assert masa == 181


# ---------------------------------------------------------------------------
# S1 — las dos métricas de la candidata
# ---------------------------------------------------------------------------

def test_candidata_expone_conteo_de_picos_y_masa():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 100)  # 181 puntos

    candidatas = candidatas_lineas(puntos, imagen)

    assert candidatas.rhos.size == 1
    assert candidatas.conteos[0] == 1          # un único pico agrupado
    assert candidatas.masas[0] == 181          # masa = votos del acumulador en ese pico
    assert candidatas.desviaciones[0] == pytest.approx(0.0, abs=1e-9)


def test_la_masa_es_la_suma_del_acumulador_en_el_grupo():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = _recta_vertical(ancho, alto, 40, y0=10, y1=89)  # 80 puntos

    acumulador, rhos, thetas = acumulador_lineas(puntos, imagen)
    umbral = acumulador.max() * 0.6
    filas, columnas = np.nonzero(acumulador >= umbral)
    masa_esperada = int(acumulador[filas, columnas].sum())

    candidatas = candidatas_lineas(puntos, imagen)

    assert candidatas.conteos[0] == filas.size
    assert candidatas.masas[0] == masa_esperada


def test_ranking_por_conteo_de_picos():
    """La vertical tiene 3 picos y la diagonal 1: gana la vertical."""
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    vertical = _recta_vertical(ancho, alto, 40, y0=10, y1=89)   # 80 puntos
    diagonal = _recta_diagonal(ancho, alto, 20, 109)             # 90 puntos
    puntos = np.vstack([vertical, diagonal])

    candidatas = candidatas_lineas(puntos, imagen)
    assert set(candidatas.conteos.tolist()) == {3, 1}

    rho, theta, conteo_mejor, masa_mejor, _ = hough_lineas(puntos, imagen)

    assert rho == pytest.approx(40.0, abs=0.6)
    assert conteo_mejor == 3
    assert masa_mejor == int(candidatas.masas[candidatas.conteos.argmax()])


def test_empate_por_conteo_se_resuelve_por_masa():
    """Ambas rectas tienen 1 pico: gana la de mayor masa (la más larga)."""
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    larga = _recta_vertical(ancho, alto, 40)                     # 181 puntos
    corta = _recta_vertical(ancho, alto, 120, y0=25, y1=174)     # 150 puntos
    puntos = np.vstack([larga, corta])

    rho, theta, conteo, masa, _ = hough_lineas(puntos, imagen)

    assert rho == pytest.approx(40.0, abs=0.6)
    assert conteo == 1
    assert masa == 181


# ---------------------------------------------------------------------------
# S1 — agrupación de picos y desviación estándar de rho
# ---------------------------------------------------------------------------

def test_dos_rectas_separadas_generan_dos_candidatas():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = np.vstack([
        _recta_vertical(ancho, alto, 40),
        _recta_vertical(ancho, alto, 120),
    ])

    candidatas = candidatas_lineas(puntos, imagen)

    assert candidatas.rhos.size == 2
    assert set(np.round(candidatas.rhos, 1)) == {40.0, 120.0}
    assert np.all(candidatas.conteos == 1)
    assert np.all(candidatas.masas == 181)


def test_dos_rectas_cercanas_se_unen_con_max_dist_grande():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = np.vstack([
        _recta_vertical(ancho, alto, 40),
        _recta_vertical(ancho, alto, 120),
    ])

    candidatas = candidatas_lineas(puntos, imagen, max_dist_px=90.0)

    assert candidatas.rhos.size == 1
    assert candidatas.rhos[0] == pytest.approx(80.0, abs=0.1)
    assert candidatas.conteos[0] == 2
    assert candidatas.masas[0] == 362
    # std muestral (N-1) de {40, 120}
    assert candidatas.desviaciones[0] == pytest.approx(np.sqrt(3200.0), abs=0.1)


def test_hough_lineas_cuadra_con_la_candidata_de_mas_picos():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    puntos = np.vstack([
        _recta_vertical(ancho, alto, 40),
        _recta_vertical(ancho, alto, 120, y0=25, y1=174),
    ])

    candidatas = candidatas_lineas(puntos, imagen)
    rho, theta, conteo_mejor, masa_mejor, desviacion = hough_lineas(puntos, imagen)

    orden = np.lexsort((-candidatas.masas, -candidatas.conteos))
    indice = int(orden[0])
    assert rho == pytest.approx(candidatas.rhos[indice])
    assert theta == pytest.approx(candidatas.thetas[indice])
    assert conteo_mejor == int(candidatas.conteos[indice])
    assert masa_mejor == int(candidatas.masas[indice])
    assert desviacion == pytest.approx(candidatas.desviaciones[indice])


# ---------------------------------------------------------------------------
# S1 — reduce (fusión de candidatas cercanas)
# ---------------------------------------------------------------------------

def test_reducir_fusiona_candidatas_cercanas():
    candidatas = _candidatas(
        rhos=[40.0, 45.0],
        thetas=[0.0, 0.0],
        conteos=[3, 2],
        masas=[100, 80],
        desviaciones=[1.0, 1.0],
    )

    fusion = reducir_candidatas(candidatas, sigma=10.0)

    assert fusion.rhos.size == 1
    assert fusion.rhos[0] == pytest.approx(42.5)
    assert fusion.conteos[0] == 5
    assert fusion.masas[0] == 180


def test_reducir_no_fusiona_candidatas_lejanas():
    candidatas = _candidatas(
        rhos=[40.0, 120.0],
        thetas=[0.0, 0.1],
        conteos=[3, 2],
        masas=[100, 80],
        desviaciones=[1.0, 1.0],
    )

    fusion = reducir_candidatas(candidatas, sigma=30.0)

    assert fusion.rhos.size == 2
    assert np.allclose(fusion.rhos, [40.0, 120.0])
    assert np.array_equal(fusion.conteos, [3, 2])
    assert np.array_equal(fusion.masas, [100, 80])


def test_reducir_combina_conteo_y_masa():
    candidatas = _candidatas(
        rhos=[10.0, 15.0, 100.0],
        thetas=[0.0, 0.0, 0.2],
        conteos=[3, 2, 4],
        masas=[100, 80, 90],
        desviaciones=[1.0, 1.0, 2.0],
    )

    fusion = reducir_candidatas(candidatas, sigma=10.0)

    assert fusion.rhos.size == 2
    assert fusion.rhos[0] == pytest.approx(12.5)
    assert fusion.conteos[0] == 5
    assert fusion.masas[0] == 180
    assert fusion.rhos[1] == pytest.approx(100.0)
    assert fusion.conteos[1] == 4
    assert fusion.masas[1] == 90


def test_reducir_una_sola_candidata_la_devuelve_igual():
    candidatas = _candidatas(
        rhos=[55.0],
        thetas=[0.3],
        conteos=[7],
        masas=[123],
        desviaciones=[4.0],
    )

    fusion = reducir_candidatas(candidatas, sigma=50.0)

    assert np.allclose(fusion.rhos, [55.0])
    assert np.array_equal(fusion.conteos, [7])
    assert np.array_equal(fusion.masas, [123])


def test_hough_lineas_aplica_reduce_antes_de_seleccionar():
    """Con candidatas que sí se fusionan: el resultado es el fusionado."""
    rng = np.random.default_rng(1)
    n_ruido, ruido, x_limpia, n_limpia = 1500, 120, 230, 10
    alto = 10 + max(n_ruido, n_limpia) + 10
    ancho = 300
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    y1 = np.arange(10, 10 + n_ruido, dtype=float)
    ruidoso = np.column_stack([100.0 + rng.uniform(-ruido, ruido, size=y1.size), y1])
    y2 = np.arange(10, 10 + n_limpia, dtype=float)
    limpia = np.column_stack([np.full(y2.size, float(x_limpia)), y2])
    puntos = np.vstack([ruidoso, limpia])

    candidatas = candidatas_lineas(puntos, imagen)
    sigma = 2.7 * float(candidatas.desviaciones.max())
    fusion = reducir_candidatas(candidatas, sigma)
    assert fusion.rhos.size < candidatas.rhos.size  # la fusión realmente ocurre

    orden = np.lexsort((-fusion.masas, -fusion.conteos))
    indice = int(orden[0])

    rho, theta, conteo_mejor, masa_mejor, desviacion = hough_lineas(puntos, imagen)

    assert rho == pytest.approx(float(fusion.rhos[indice]))
    assert theta == pytest.approx(float(fusion.thetas[indice]))
    assert conteo_mejor == int(fusion.conteos[indice])
    assert masa_mejor == int(fusion.masas[indice])
    assert desviacion == pytest.approx(float(fusion.desviaciones[indice]))


# ---------------------------------------------------------------------------
# S1 — casos degenerados
# ---------------------------------------------------------------------------

def test_sin_puntos_no_devuelve_candidatas():
    imagen = np.zeros((50, 50), dtype=np.uint8)
    puntos = np.empty((0, 2), dtype=float)

    candidatas = candidatas_lineas(puntos, imagen)

    assert candidatas.rhos.size == 0
    assert candidatas.thetas.size == 0
    assert candidatas.conteos.size == 0
    assert candidatas.masas.size == 0
    assert candidatas.desviaciones.size == 0
    assert hough_lineas(puntos, imagen) is None


def test_una_imagen_de_un_solo_pixel_no_lanza_excepcion():
    imagen = np.zeros((1, 1), dtype=np.uint8)
    puntos = np.array([[0.0, 0.0]])

    acumulador, rhos, thetas = acumulador_lineas(puntos, imagen)

    assert acumulador.shape == (4 * _diag_len(1, 1) + 1, NUM_THETAS)
    assert acumulador.sum() == NUM_THETAS
    assert rhos.size == 4 * _diag_len(1, 1) + 1


def test_rechaza_puntos_no_finitos():
    imagen = np.zeros((50, 50), dtype=np.uint8)

    with pytest.raises(ValueError):
        hough_lineas(np.array([[1.0, np.nan], [2.0, 3.0]]), imagen)

    with pytest.raises(ValueError):
        hough_lineas(np.array([[np.inf, 1.0]]), imagen)


def test_rechaza_puntos_de_shape_invalido():
    imagen = np.zeros((50, 50), dtype=np.uint8)

    with pytest.raises(ValueError):
        hough_lineas(np.array([1.0, 2.0]), imagen)

    with pytest.raises(ValueError):
        hough_lineas(np.array([[1.0, 2.0, 3.0]]), imagen)


def test_rechaza_imagen_no_matricial():
    puntos = np.array([[1.0, 2.0]])

    with pytest.raises(ValueError):
        hough_lineas(puntos, np.zeros((10, 10, 3), dtype=np.uint8))


# ---------------------------------------------------------------------------
# S6 — aislamiento de la capa de modelo
# ---------------------------------------------------------------------------

def test_candidatas_es_un_dataclass_inmutable():
    alto, ancho = 200, 200
    imagen = np.zeros((alto, ancho), dtype=np.uint8)
    candidatas = candidatas_lineas(_recta_vertical(ancho, alto, 100), imagen)

    assert hasattr(CandidatasLineas, "__slots__")
    assert hasattr(candidatas, "__dataclass_fields__")
    with pytest.raises(FrozenInstanceError):
        candidatas.rhos = np.array([1.0])


def test_el_modelo_no_importa_capas_de_ui():
    ruta = RAIZ / "src" / "odin" / "Procesamiento" / "models" / "hough_lineas.py"
    fuente = ruta.read_text(encoding="utf-8")

    importados = re.findall(
        r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", fuente, re.MULTILINE
    )
    prohibidos = {"gi", "cairo", "Gtk", "Gdk", "Adw"}

    assert not (set(importados) & prohibidos)
