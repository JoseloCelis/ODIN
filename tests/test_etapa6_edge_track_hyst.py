"""Etapa 6 — DoubleTh.EdgeTrack_Hyst: histéresis de bordes.

Caracterización del comportamiento en producción (spec edge-track-hyst):
- Recibe MÁSCARAS (cualquier valor > 0 significa "presente").
- Los fuertes se conservan siempre; sin fuertes la salida es vacía.
- Un débil se conserva si está a distancia Chebyshev <= 2 de un fuerte
  (dilatación 5x5).
- Una isla débil 8-conexa se conserva entera si toca esa zona; entera si no.
- Islas separadas por huecos no se unen (contrato R5: la recursiva sí las
  unía, pero no es la implementación en producción).
- Salida uint8 en {0, 255}, misma forma, sin modificar los argumentos.
- Entrada vacía: arreglo vacío, sin excepción (R6, divergencia D1).
"""

import numpy as np
import pytest

from odin.Preprocesamiento import DoubleTh as DTh
from odin.Preprocesamiento import NonMaxSup as NMS

DEBIL = 0.30   # 0.25 <= DEBIL < 0.5
FUERTE = 0.90
UMBRAL = 0.5


def _mascaras(magnitudes, umbral=UMBRAL):
    """Convierte magnitudes en las dos máscaras que produce la etapa 5."""
    return NMS.DobleThreshold(np.asarray(magnitudes, dtype=float), umbral)


def _salida_de(magnitudes):
    strong, weak = _mascaras(magnitudes)
    return strong, weak, DTh.EdgeTrack_Hyst(strong, weak)


@pytest.mark.parametrize("distancia, conservado", [
    (1, True), (2, True), (3, False), (4, False), (5, False),
])
def test_radio_chebyshev_en_el_eje(distancia, conservado):
    mg = np.zeros((41, 41))
    mg[20, 20] = FUERTE
    mg[20, 20 + distancia] = DEBIL

    _, _, salida = _salida_de(mg)

    assert bool(salida[20, 20 + distancia] > 0) is conservado


@pytest.mark.parametrize("distancia, conservado", [(1, True), (2, True), (3, False)])
def test_radio_chebyshev_en_la_diagonal(distancia, conservado):
    mg = np.zeros((41, 41))
    mg[20, 20] = FUERTE
    mg[20 + distancia, 20 + distancia] = DEBIL

    _, _, salida = _salida_de(mg)

    assert bool(salida[20 + distancia, 20 + distancia] > 0) is conservado


def test_isla_continua_se_conserva_completa():
    mg = np.zeros((41, 41))
    mg[20, 20] = FUERTE
    mg[20, 22:34] = DEBIL  # 12 débiles contiguos, el último a 13 px del fuerte

    _, _, salida = _salida_de(mg)

    assert int(np.count_nonzero(salida)) == 13  # 1 fuerte + 12 débiles


def test_isla_fuera_de_alcance_se_descarta():
    mg = np.zeros((41, 41))
    mg[20, 20] = FUERTE
    mg[30, 30] = DEBIL

    _, _, salida = _salida_de(mg)

    assert salida[20, 20] == 255
    assert salida[30, 30] == 0
    assert int(np.count_nonzero(salida)) == 1


def test_un_hueco_de_hasta_tres_pixeles_no_une_islas():
    mg = np.zeros((41, 41))
    mg[20, 20] = FUERTE
    mg[20, 22] = DEBIL   # a 2 px del fuerte: se conserva
    mg[20, 25] = DEBIL   # a 3 px del anterior, a 5 px del fuerte: se descarta

    _, _, salida = _salida_de(mg)

    assert salida[20, 22] == 255
    assert salida[20, 25] == 0


def test_conserva_todos_los_fuertes():
    rng = np.random.default_rng(2)
    strong = (rng.random((30, 30)) > 0.85).astype(float)
    weak = (rng.random((30, 30)) > 0.5).astype(float) * DEBIL

    salida = DTh.EdgeTrack_Hyst(strong, weak)

    assert np.all(salida[strong > 0] == 255)


def test_sin_fuertes_devuelve_salida_vacia():
    weak = np.full((10, 10), DEBIL)

    salida = DTh.EdgeTrack_Hyst(np.zeros((10, 10)), weak)

    assert np.count_nonzero(salida) == 0


def test_sin_debiles_devuelve_solo_los_fuertes():
    strong = np.zeros((10, 10))
    strong[5, 5] = 1.0

    salida = DTh.EdgeTrack_Hyst(strong, np.zeros((10, 10)))

    assert salida[5, 5] == 255
    assert int(np.count_nonzero(salida)) == 1


def test_salida_es_uint8_con_valores_0_y_255():
    mg = np.zeros((20, 20))
    mg[10, 10] = FUERTE
    mg[10, 11] = DEBIL

    strong, weak, salida = _salida_de(mg)

    assert salida.shape == strong.shape
    assert salida.dtype == np.uint8
    assert set(np.unique(salida).tolist()) <= {0, 255}


def test_no_modifica_los_argumentos():
    mg = np.zeros((20, 20))
    mg[10, 10] = FUERTE
    mg[10, 11] = DEBIL
    strong, weak = _mascaras(mg)
    copia_strong, copia_weak = strong.copy(), weak.copy()

    DTh.EdgeTrack_Hyst(strong, weak)

    assert np.array_equal(strong, copia_strong)
    assert np.array_equal(weak, copia_weak)


def test_entrada_vacia_no_lanza_excepcion():
    vacio = np.zeros((0, 0))

    salida = DTh.EdgeTrack_Hyst(vacio, vacio)

    assert salida.shape == vacio.shape
    assert np.count_nonzero(salida) == 0


def test_integracion_con_el_pipeline():
    imagen = np.zeros((80, 100))
    imagen[20:60, 30:70] = 1.0

    from odin.Preprocesamiento import (
        kernelSeparable as KS,
        MagnitudGradiente as MF,
        Otsu as OT,
    )

    gx, gy = KS.DerivGauss(imagen, 2, 0, 0, 0)
    mg, angulo = MF.MagFase(gx, gy)
    gn = NMS.LinearInterpolation(mg, gx, gy, angulo)
    umbral, _ = OT.umbralRosinYOtsu(gn)
    strong, weak = NMS.DobleThreshold(gn, umbral)

    salida = DTh.EdgeTrack_Hyst(strong, weak)

    # Todo fuerte sobrevive y nada fuera de las dos máscaras aparece.
    assert np.all(salida[strong > 0] == 255)
    assert np.all((salida > 0)[(strong > 0) | (weak > 0)])
