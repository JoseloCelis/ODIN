"""Etapa 7 — houghCircles: transformada de Hough y barrido de radios.

Caracterización del comportamiento esperado (spec hough-circles):

- `hough_circles_vectorizado` devuelve TODOS los picos del acumulador por
  encima de `thres * max`. El llamador debe elegir UN centro: pasar el arreglo
  completo a `find_circle` rompe el broadcasting (R9).
- `estimar_radio` barre una banda de radios y devuelve el de más votos, junto
  con la relación segundo/primero como medida de ambigüedad (R3, R5).
- La banda se deriva del recorte: `r0 = min(alto, ancho) / 2` y se busca en
  `[0.6 * r0, r0]` (R4).
- El radio no puede ser una constante en el orquestador (R2).
- La cadena funciona igual con contraste invertido (R7).
"""

import re
from pathlib import Path

import numpy as np
import pytest

from odin.Preprocesamiento import aproxHough as H
from odin.Preprocesamiento import circleFilter as FC
from odin.Preprocesamiento import circuloSimple as LSC

RAIZ = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _anillo(lado, cx, cy, r, grosor=1.0):
    """Borde de un círculo de radio `r`, de 2 px de espesor."""
    yy, xx = np.mgrid[0:lado, 0:lado]
    d = np.hypot(xx - cx, yy - cy)
    return ((d > r - grosor) & (d <= r + grosor)).astype(np.uint8)


def _recorte_ajustado(r, margen=1.15):
    """Recorte como el que hace el usuario: el círculo casi lo llena (R4)."""
    lado = int(round(2 * margen * r))
    centro = lado / 2.0
    bordes = _anillo(lado, centro, centro, r)
    return bordes, centro, lado / 2.0


def _ambiguedad(picos, paso, mejor, separacion_px=6.0):
    """Relación segundo/primero, ignorando los radios vecinos del mismo pico."""
    pasos = max(1, int(round(separacion_px / paso)))
    otros = [p for j, p in enumerate(picos) if abs(j - mejor) >= pasos]
    return (max(otros) / picos[mejor]) if otros else 0.0


# ---------------------------------------------------------------------------
# R1 — contrato de hough_circles_vectorizado
# ---------------------------------------------------------------------------

def test_detecta_el_centro_de_un_circulo_sintetico():
    bordes = _anillo(200, 100, 100, 60)

    x0, y0, n, acumulador = H.hough_circles_vectorizado(bordes, 60, 0.8)

    assert n == 1
    assert (x0[0], y0[0]) == (100, 100)
    assert acumulador[100, 100] == acumulador.max()


def test_el_acumulador_tiene_la_forma_de_la_imagen():
    bordes = _anillo(120, 60, 60, 30)

    _, _, _, acumulador = H.hough_circles_vectorizado(bordes, 30, 0.8)

    assert acumulador.shape == bordes.shape


def test_rechaza_distancia_menor_a_diez():
    bordes = _anillo(80, 40, 40, 20)

    with pytest.raises(ValueError):
        H.hough_circles_vectorizado(bordes, 20, 0.8, dist=9)


def test_rechaza_umbral_menor_a_medio():
    bordes = _anillo(80, 40, 40, 20)

    with pytest.raises(ValueError):
        H.hough_circles_vectorizado(bordes, 20, 0.49)


def test_sin_bordes_devuelve_cero_picos():
    vacio = np.zeros((50, 50), dtype=np.uint8)

    x0, y0, n, acumulador = H.hough_circles_vectorizado(vacio, 10, 0.8)

    assert n == 0
    assert len(x0) == 0 and len(y0) == 0
    assert acumulador.max() == 0


def test_imagen_de_tamano_cero_no_lanza_excepcion():
    vacio = np.zeros((0, 0), dtype=np.uint8)

    x0, y0, n, _ = H.hough_circles_vectorizado(vacio, 10, 0.8)

    assert n == 0
    assert len(x0) == 0 and len(y0) == 0


# ---------------------------------------------------------------------------
# R9 — el llamador debe quedarse con UN centro
# ---------------------------------------------------------------------------

def test_devuelve_todos_los_picos_cuando_hay_dos_circulos():
    bordes = (_anillo(300, 80, 90, 40) | _anillo(300, 220, 200, 40)).astype(np.uint8)

    x0, y0, n, _ = H.hough_circles_vectorizado(bordes, 40, 0.8)

    assert n == 2
    assert {(x, y) for x, y in zip(x0.tolist(), y0.tolist())} == {(80, 90), (220, 200)}


def test_mejor_centro_elige_el_de_mas_votos():
    x0 = np.array([5, 10])
    y0 = np.array([7, 20])
    acumulador = np.zeros((30, 30), dtype=int)
    acumulador[7, 5] = 3
    acumulador[20, 10] = 9

    x, y, votos = H.mejor_centro(x0, y0, acumulador)

    assert (x, y, votos) == (10, 20, 9)


def test_mejor_centro_sin_picos_devuelve_none():
    vacio = np.zeros((0,), dtype=int)

    assert H.mejor_centro(vacio, vacio, np.zeros((10, 10), dtype=int)) is None


def test_el_flujo_con_un_solo_centro_no_lanza_excepcion():
    """Pasar el arreglo de centros a find_circle rompía el broadcasting."""
    bordes = (_anillo(300, 80, 90, 40) | _anillo(300, 220, 200, 40)).astype(np.uint8)

    x0, y0, n, acumulador = H.hough_circles_vectorizado(bordes, 40, 0.8)
    centro = H.mejor_centro(x0, y0, acumulador)

    puntos = FC.find_circle(bordes, 40, (centro[0], centro[1]))
    _, _, r, _ = LSC.Circulo_simple(puntos)

    assert abs(r - 40.0) <= 0.1


# ---------------------------------------------------------------------------
# R3 / R4 — barrido de radios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("r_real", [20, 45, 80])
def test_estimar_radio_recupera_el_radio_conocido(r_real):
    bordes, _, r0 = _recorte_ajustado(r_real)

    radio, pico, _ = H.estimar_radio(bordes, 0.6 * r0, r0)

    assert abs(radio - r_real) <= 1.0
    assert pico > 0


def test_estimar_radio_banda_invertida_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        H.estimar_radio(bordes, 50.0, 10.0)


def test_estimar_radio_radio_no_positivo_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        H.estimar_radio(bordes, 0.0, 40.0)


def test_estimar_radio_paso_no_positivo_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        H.estimar_radio(bordes, 10.0, 40.0, paso=0.0)


def test_estimar_radio_sin_bordes_devuelve_ceros():
    vacio = np.zeros((60, 60), dtype=np.uint8)

    radio, pico, ambiguedad = H.estimar_radio(vacio, 10.0, 30.0)

    assert (radio, pico, ambiguedad) == (0.0, 0, 0.0)


def test_estimar_radio_no_reporta_ambiguedad_con_un_solo_circulo():
    bordes, _, r0 = _recorte_ajustado(45)

    _, _, ambiguedad = H.estimar_radio(bordes, 0.6 * r0, r0)

    assert ambiguedad < H.UMBRAL_AMBIGUEDAD


def test_estimar_radio_reporta_ambiguedad_con_dos_circulos_parecidos():
    """El caso 'círculo pequeño dentro del grande', con tamaños comparables."""
    lado = 108
    c = lado / 2.0
    bordes = (_anillo(lado, c, c, 35) | _anillo(lado, c, c, 45)).astype(np.uint8)

    _, _, ambiguedad = H.estimar_radio(bordes, 0.6 * c, c)

    assert ambiguedad >= H.UMBRAL_AMBIGUEDAD


# ---------------------------------------------------------------------------
# R2 — el radio no puede ser una constante
# ---------------------------------------------------------------------------

def test_el_orquestador_no_usa_un_radio_constante():
    fuente = (RAIZ / "odin" / "main.py").read_text(encoding="utf-8")

    assert "estimar_radio" in fuente
    assert not re.search(r"^\s*diametro\s*=\s*\d", fuente, re.MULTILINE)


# ---------------------------------------------------------------------------
# R7 — contraste invertido y cadena completa
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("disco_claro", [True, False])
def test_cadena_completa_con_y_sin_contraste_invertido(disco_claro):
    from odin.Preprocesamiento import (
        DoubleTh as DTh,
        kernelSeparable as KS,
        MagnitudGradiente as MF,
        NonMaxSup as NMS,
        Otsu as OT,
    )

    r_real = 45
    lado = int(round(2.2 * r_real))
    radio_px = lado / 2.0
    yy, xx = np.mgrid[0:lado, 0:lado]
    d = np.hypot(xx - radio_px, yy - radio_px)
    fondo, objeto = (0.1, 0.9) if disco_claro else (0.9, 0.1)
    imagen = np.where(d <= r_real, objeto, fondo).astype(float)

    gx, gy = KS.DerivGauss(imagen, 2, 0, 0, 0)
    mg, angulo = MF.MagFase(gx, gy)
    gn = NMS.LinearInterpolation(mg, gx, gy, angulo)
    umbral, _ = OT.umbralRosinYOtsu(gn)
    strong, weak = NMS.DobleThreshold(gn, umbral)
    bordes = DTh.EdgeTrack_Hyst(strong, weak)

    r0 = lado / 2.0
    radio, _, _ = H.estimar_radio(bordes, 0.6 * r0, r0)
    x0, y0, _, acumulador = H.hough_circles_vectorizado(bordes, radio, 0.8)
    centro = H.mejor_centro(x0, y0, acumulador)
    puntos = FC.find_circle(bordes, radio, (centro[0], centro[1]))
    _, _, r_ajustado, _ = LSC.Circulo_simple(puntos)

    assert abs(r_ajustado - r_real) <= 0.5
