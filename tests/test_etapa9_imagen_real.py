"""Etapa ⑨ — circuloSimple sobre datos reales e imagen real.

Dos niveles:

1. **Datos reales (rápido)**: listas de bordes Gabor medidas sobre imágenes
   reales del servicio de micrometrología. Se ajusta el círculo directamente.
2. **Imagen real de punta a punta (lento)**: `img100.bmp` recortada alrededor
   del círculo real, pipeline ①→⑨ completo. Se activa con
   `ODIN_TEST_LENTO=1` porque el pipeline en Python puro tarda ~20 s.

Ambos se saltan si el dataset (`odin/data/`, gitignorado) no está presente.
"""

import os
from pathlib import Path

import numpy as np
import pytest

from odin.Preprocesamiento import circuloSimple as CS

RAIZ = Path(__file__).resolve().parents[1]
BASE_DATOS = RAIZ / "odin" / "data" / "images" / "Circulos Servicio Micrometrologia"

# Valores medidos con el ajuste actual (deterministas, mismo archivo).
# r100: la lista de bordes reales de `img100.bmp`; r050: círculo chico.
CASOS_REALES = [
    ("img-r100-ListaBordesGabor4junppp.txt", (503.8527, 509.3971, 428.2332)),
    ("img-r050-ListaBordesGabor4junppp.txt", (256.8915, 303.5525, 213.9477)),
]


def _cargar_puntos(nombre):
    ruta = BASE_DATOS / nombre
    if not ruta.exists():
        pytest.skip(f"dataset real no disponible: {ruta}")
    return np.loadtxt(ruta)


@pytest.mark.parametrize("nombre,esperado", CASOS_REALES)
def test_ajuste_sobre_bordes_reales(nombre, esperado):
    """El ajuste reproduce centro y radio medidos sobre bordes reales."""
    puntos = _cargar_puntos(nombre)
    x_esp, y_esp, r_esp = esperado

    x, y, r, pv = CS.Circulo_simple(puntos)

    assert (x, y) == pytest.approx((x_esp, y_esp), abs=0.05)
    assert r == pytest.approx(r_esp, abs=0.05)
    assert pv >= 0.0


@pytest.mark.parametrize("nombre,esperado", CASOS_REALES)
def test_las_dos_implementaciones_coinciden_sobre_datos_reales(nombre, esperado):
    """La copia refactorizada (`src/`) debe dar lo mismo que la histórica.

    Protege la refactorización: si una de las dos cambia, este test lo delata
    antes de que el pipeline use una versión distinta de la otra.
    """
    from src.odin.Ajustes.models import circulo_simple as CS_SRC

    puntos = _cargar_puntos(nombre)

    historico = CS.Circulo_simple(puntos)
    refactor = CS_SRC.Circulo_simple(puntos)

    assert refactor == pytest.approx(historico, abs=0.0)


# ---------------------------------------------------------------------------
# Imagen real de punta a punta (opt-in: ODIN_TEST_LENTO=1)
# ---------------------------------------------------------------------------

IMAGEN_REAL = BASE_DATOS / "img100.bmp"
# Recorte 1100x1100 centrado en el círculo real medido (global 2660.86, 1611.47).
ORIGEN_RECORTE = (2111, 1061)
LADO_RECORTE = 1100


@pytest.mark.skipif(
    os.environ.get("ODIN_TEST_LENTO") != "1",
    reason="pipeline completo lento; activar con ODIN_TEST_LENTO=1",
)
def test_pipeline_completo_sobre_imagen_real():
    """①→⑨ sobre `img100.bmp`: reproduce el círculo real medido.

    Valores de referencia medidos con sigma=3 sobre el recorte:
      radio estimado 429.0, centro (551, 550), ajuste r=428.1769, pv=1.8856.
    """
    import cv2

    from odin.Preprocesamiento import (
        DoubleTh as DT,
        MagnitudGradiente as MF,
        NonMaxSup as NMS,
        Otsu as OT,
        aproxHough as AH,
        circleFilter as FC,
        kernelSeparable as KS,
    )

    if not IMAGEN_REAL.exists():
        pytest.skip(f"imagen real no disponible: {IMAGEN_REAL}")

    imagen = cv2.imread(str(IMAGEN_REAL), cv2.IMREAD_GRAYSCALE)
    assert imagen is not None
    cx, cy = ORIGEN_RECORTE
    recorte = imagen[cy:cy + LADO_RECORTE, cx:cx + LADO_RECORTE]

    # Etapas ①→⑥: bordes.
    gx, gy = KS.DerivGauss(recorte, 3, 1, 1, 360)
    mg, angulo = MF.MagFase(gx, gy)
    gn = NMS.LinearInterpolation(mg, gx, gy, angulo)
    umbral_otsu, _ = OT.umbralRosinYOtsu(gn)
    fuertes, debiles = NMS.DobleThreshold(gn, umbral_otsu)
    bordes = DT.EdgeTrack_Hyst(fuertes, debiles)

    # Etapa ⑦: radio y centro.
    radio, _pico, ambiguedad = AH.estimar_radio_dominante(bordes, min(bordes.shape) / 2)
    assert radio == pytest.approx(429.0, abs=0.5)
    assert ambiguedad < AH.UMBRAL_AMBIGUEDAD

    x_hough, y_hough, _votos, acumulador = AH.hough_circles_vectorizado(
        bordes, radio, 0.8
    )
    centro = AH.mejor_centro(x_hough, y_hough, acumulador)
    assert centro is not None
    assert centro[:2] == pytest.approx((551, 550), abs=1)

    # Etapa ⑧: anillo validado.
    puntos = FC.find_circle(bordes, radio, (centro[0], centro[1]))
    anillo_ok, motivo = FC.validar_anillo(puntos, (centro[0], centro[1]))
    assert anillo_ok, motivo
    assert len(puntos) == pytest.approx(3150, abs=20)

    # Etapa ⑨: ajuste final.
    x, y, r, pv = CS.Circulo_simple(puntos)
    assert (x, y) == pytest.approx((549.86, 550.47), abs=0.1)
    assert r == pytest.approx(428.1769, abs=0.01)
    assert pv == pytest.approx(1.8856, abs=0.01)
