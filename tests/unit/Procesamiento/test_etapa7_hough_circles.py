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

from src.odin.Procesamiento.models.hough_circles import (
    hough_circles_vectorizado as aproxHough,
    mejor_centro,
    estimar_radio,
    estimar_radio_dominante,
    UMBRAL_AMBIGUEDAD,
)
from src.odin.Ajustes.models.find_circle import find_circle as FC
from src.odin.Ajustes.models.circulo_simple import Circulo_simple as LSC

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

    x0, y0, n, acumulador = aproxHough(bordes, 60, 0.8)

    assert n == 1
    assert (x0[0], y0[0]) == (100, 100)
    assert acumulador[100, 100] == acumulador.max()


def test_el_acumulador_tiene_la_forma_de_la_imagen():
    bordes = _anillo(120, 60, 60, 30)

    _, _, _, acumulador = aproxHough(bordes, 30, 0.8)

    assert acumulador.shape == bordes.shape


def test_rechaza_distancia_menor_a_diez():
    bordes = _anillo(80, 40, 40, 20)

    with pytest.raises(ValueError):
        aproxHough(bordes, 20, 0.8, dist=9)


def test_rechaza_umbral_menor_a_medio():
    bordes = _anillo(80, 40, 40, 20)

    with pytest.raises(ValueError):
        aproxHough(bordes, 20, 0.49)


def test_rechaza_radio_no_positivo():
    bordes = _anillo(80, 40, 40, 20)

    with pytest.raises(ValueError):
        aproxHough(bordes, 0, 0.8)

    with pytest.raises(ValueError):
        aproxHough(bordes, -5, 0.8)


def test_sin_bordes_devuelve_cero_picos():
    vacio = np.zeros((50, 50), dtype=np.uint8)

    x0, y0, n, acumulador = aproxHough(vacio, 10, 0.8)

    assert n == 0
    assert len(x0) == 0 and len(y0) == 0
    assert acumulador.max() == 0


def test_imagen_de_tamano_cero_no_lanza_excepcion():
    vacio = np.zeros((0, 0), dtype=np.uint8)

    x0, y0, n, _ = aproxHough(vacio, 10, 0.8)

    assert n == 0
    assert len(x0) == 0 and len(y0) == 0


# ---------------------------------------------------------------------------
# R9 — el llamador debe quedarse con UN centro
# ---------------------------------------------------------------------------

def test_devuelve_todos_los_picos_cuando_hay_dos_circulos():
    bordes = (_anillo(300, 80, 90, 40) | _anillo(300, 220, 200, 40)).astype(np.uint8)

    x0, y0, n, _ = aproxHough(bordes, 40, 0.8)

    assert n == 2
    assert {(x, y) for x, y in zip(x0.tolist(), y0.tolist())} == {(80, 90), (220, 200)}


def test_mejor_centro_elige_el_de_mas_votos():
    x0 = np.array([5, 10])
    y0 = np.array([7, 20])
    acumulador = np.zeros((30, 30), dtype=int)
    acumulador[7, 5] = 3
    acumulador[20, 10] = 9

    x, y, votos = mejor_centro(x0, y0, acumulador)

    assert (x, y, votos) == (10, 20, 9)


def test_mejor_centro_sin_picos_devuelve_none():
    vacio = np.zeros((0,), dtype=int)

    assert mejor_centro(vacio, vacio, np.zeros((10, 10), dtype=int)) is None


def test_el_flujo_con_un_solo_centro_no_lanza_excepcion():
    """Pasar el arreglo de centros a find_circle rompía el broadcasting."""
    bordes = (_anillo(300, 80, 90, 40) | _anillo(300, 220, 200, 40)).astype(np.uint8)

    x0, y0, n, acumulador = aproxHough(bordes, 40, 0.8)
    centro = mejor_centro(x0, y0, acumulador)

    puntos = FC(bordes, 40, (centro[0], centro[1]))
    _, _, r, _ = LSC(puntos)

    assert abs(r - 40.0) <= 0.1


# ---------------------------------------------------------------------------
# R3 / R4 — barrido de radios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("r_real", [20, 45, 80])
def test_estimar_radio_recupera_el_radio_conocido(r_real):
    bordes, _, r0 = _recorte_ajustado(r_real)

    radio, pico, _ = estimar_radio(bordes, 0.6 * r0, r0)

    assert abs(radio - r_real) <= 1.0
    assert pico > 0


def test_estimar_radio_banda_invertida_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        estimar_radio(bordes, 50.0, 10.0)


def test_estimar_radio_radio_no_positivo_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        estimar_radio(bordes, 0.0, 40.0)


def test_estimar_radio_paso_no_positivo_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        estimar_radio(bordes, 10.0, 40.0, paso=0.0)


def test_estimar_radio_sin_bordes_devuelve_ceros():
    vacio = np.zeros((60, 60), dtype=np.uint8)

    radio, pico, ambiguedad = estimar_radio(vacio, 10.0, 30.0)

    assert (radio, pico, ambiguedad) == (0.0, 0, 0.0)


def test_estimar_radio_no_reporta_ambiguedad_con_un_solo_circulo():
    bordes, _, r0 = _recorte_ajustado(45)

    _, _, ambiguedad = estimar_radio(bordes, 0.6 * r0, r0)

    assert ambiguedad < UMBRAL_AMBIGUEDAD


def test_estimar_radio_reporta_ambiguedad_con_dos_circulos_parecidos():
    """El caso 'círculo pequeño dentro del grande', con tamaños comparables."""
    lado = 108
    c = lado / 2.0
    bordes = (_anillo(lado, c, c, 35) | _anillo(lado, c, c, 45)).astype(np.uint8)

    _, _, ambiguedad = estimar_radio(bordes, 0.6 * c, c)

    assert ambiguedad >= UMBRAL_AMBIGUEDAD


# ---------------------------------------------------------------------------
# R2 — el radio no puede ser una constante
# ---------------------------------------------------------------------------

def test_el_orquestador_no_usa_un_radio_constante():
    ruta_ctrl = RAIZ / "src" / "odin" / "controllers" / "main_controller.py"
    if not ruta_ctrl.exists():
        pytest.skip(f"Controlador no encontrado en {ruta_ctrl}")
    fuente = ruta_ctrl.read_text(encoding="utf-8")

    assert "estimar_radio" in fuente
    assert not re.search(r"^\s*diametro\s*=\s*\d", fuente, re.MULTILINE)


# ---------------------------------------------------------------------------
# R7 — contraste invertido y cadena completa
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("disco_claro", [True, False])
def test_cadena_completa_con_y_sin_contraste_invertido(disco_claro):
    from src.odin.Preprocesamiento.models import deri_gauss as KS
    from src.odin.Preprocesamiento.models import mag_fase as MF
    from src.odin.Procesamiento.models import edge_track_hyst as DTh
    from src.odin.Procesamiento.models import non_max_sup as NMS
    from src.odin.Procesamiento.models import otsu_rosin as OT

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
    radio, _, _ = estimar_radio(bordes, 0.6 * r0, r0)
    x0, y0, _, acumulador = aproxHough(bordes, radio, 0.8)
    centro = mejor_centro(x0, y0, acumulador)
    puntos = FC(bordes, radio, (centro[0], centro[1]))
    _, _, r_ajustado, _ = LSC(puntos)

    assert abs(r_ajustado - r_real) <= 0.5


# ---------------------------------------------------------------------------
# R10 — barrido de dos escalas, para recortes holgados
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("r_real, factor", [(40, 6.0), (60, 4.0), (25, 8.0)])
def test_estimar_radio_dominante_admite_recorte_holgado(r_real, factor):
    """r/r0 llega a 0.25: el círculo ocupa un cuarto del lado del recorte."""
    lado = int(round(factor * r_real))
    bordes = _anillo(lado, lado / 2.0, lado / 2.0, r_real)

    radio, pico, _ = estimar_radio_dominante(bordes, lado / 2.0)

    assert abs(radio - r_real) <= 1.5
    assert pico > 0


def test_estimar_radio_dominante_no_se_engancha_con_manchas_tipo_texto():
    lado = 300
    c = lado / 2.0
    bordes = _anillo(lado, c, c, 60)
    rng = np.random.default_rng(3)
    for _ in range(6):
        px, py = rng.integers(20, 280, 2)
        bordes[py - 6:py + 6, px - 4:px + 4] = 1

    radio, _, _ = estimar_radio_dominante(bordes, c)

    assert abs(radio - 60) <= 1.5


def test_estimar_radio_dominante_sin_bordes_devuelve_ceros():
    vacio = np.zeros((200, 200), dtype=np.uint8)

    assert estimar_radio_dominante(vacio, 100.0) == (0.0, 0, 0.0)


def test_estimar_radio_dominante_r0_no_positivo_lanza_error():
    bordes = _anillo(100, 50, 50, 40)

    with pytest.raises(ValueError):
        estimar_radio_dominante(bordes, 0.0)


def test_estimar_radio_dominante_reporta_ambiguedad_entre_estructuras():
    lado = 216
    c = lado / 2.0
    bordes = (_anillo(lado, c, c, 35) | _anillo(lado, c, c, 45)).astype(np.uint8)

    _, _, ambiguedad = estimar_radio_dominante(bordes, c)

    assert ambiguedad >= UMBRAL_AMBIGUEDAD


# ---------------------------------------------------------------------------
# R6 — campo de diámetro: lo detectado y lo escrito por el usuario
# ---------------------------------------------------------------------------

try:
    from src.odin.controllers.main_controller import EstadoDiametro, resolver_radio
    _CONTROLADOR_DISPONIBLE = True
except (ImportError, Exception):
    _CONTROLADOR_DISPONIBLE = False

_requiere_controlador = pytest.mark.skipif(
    not _CONTROLADOR_DISPONIBLE,
    reason="src.odin.controllers.main_controller no disponible o dependencias de UI no inicializadas",
)


@_requiere_controlador
def test_el_estado_del_diametro_arranca_vacio():
    estado = EstadoDiametro()

    assert not estado.es_manual
    assert estado.diametro_para_procesar() is None
    assert estado.valor_visible() == 0.0


@_requiere_controlador
def test_el_valor_detectado_no_cuenta_como_decision_del_usuario():
    estado = EstadoDiametro()
    estado.registrar_detectado(855.7)

    assert not estado.es_manual
    assert estado.diametro_para_procesar() is None
    assert estado.valor_visible() == 855.7


@_requiere_controlador
def test_el_valor_del_usuario_gana_sobre_el_detectado():
    estado = EstadoDiametro()
    estado.registrar_detectado(855.7)
    estado.declarar_usuario(500.0)

    assert estado.es_manual
    assert estado.diametro_para_procesar() == 500.0
    assert estado.valor_visible() == 500.0


@_requiere_controlador
def test_volver_a_auto_descarta_el_valor_manual():
    estado = EstadoDiametro()
    estado.registrar_detectado(855.7)
    estado.declarar_usuario(500.0)

    estado.volver_a_auto()

    assert not estado.es_manual
    assert estado.valor_visible() == 855.7


@_requiere_controlador
def test_un_diametro_cero_o_negativo_vuelve_a_automatico():
    estado = EstadoDiametro()
    estado.declarar_usuario(500.0)
    estado.declarar_usuario(0.0)

    assert not estado.es_manual


@_requiere_controlador
def test_el_estado_avisa_cuando_la_deteccion_es_ambigua():
    ambiguo = EstadoDiametro()
    ambiguo.registrar_detectado(855.7, ambiguo=True)
    seguro = EstadoDiametro()
    seguro.registrar_detectado(855.7, ambiguo=False)

    assert "revisar" in ambiguo.texto_estado()
    assert "revisar" not in seguro.texto_estado()


@_requiere_controlador
def test_resolver_radio_omite_el_barrido_con_diametro_del_usuario():
    from src.odin.Procesamiento.models.hough_circles import UMBRAL_AMBIGUEDAD
    from src.odin.Procesamiento.models import hough_circles as aproxHough

    bordes = _anillo(240, 120, 120, 40)

    radio, pico, ambiguedad, origen = resolver_radio(1234.0, bordes, 120.0,
                                                     aproxHough)

    assert origen == "usuario"
    assert radio == 617.0
    assert (pico, ambiguedad) == (0, 0.0)


@_requiere_controlador
def test_resolver_radio_barre_cuando_no_hay_diametro_del_usuario():
    from src.odin.Procesamiento.models.hough_circles import UMBRAL_AMBIGUEDAD
    from src.odin.Procesamiento.models import hough_circles as aproxHough

    bordes = _anillo(240, 120, 120, 40)

    radio, pico, _, origen = resolver_radio(None, bordes, 120.0, aproxHough)

    assert origen == "automatico"
    assert abs(radio - 40) <= 1.5
    assert pico > 0
