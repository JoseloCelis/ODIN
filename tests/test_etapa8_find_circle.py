"""Etapa 8 — findCircle: selección del anillo y su validación.

Caracterización del comportamiento esperado (spec find-circle):

- `find_circle` selecciona los bordes cuya distancia al centro cae en el anillo
  `[re - tol, re + tol]` y devuelve `(N, 2)` en coordenadas de la imagen (R1).
- La tolerancia no puede ser fija: `min(10 px, 0.25 * re)` evita que, con radios
  chicos, el anillo se trague el interior del círculo (R2).
- Una selección que no rodea al círculo (poca cobertura angular, hueco grande)
  debe rechazarse antes de ajustar (R3).
- Menos de 3 puntos no llega al ajuste: `Circulo_simple` falla con un mensaje
  opaco o devuelve r = 0 en silencio (R4).
"""

import numpy as np
import pytest

from odin.Preprocesamiento import circleFilter as FC
from odin.Preprocesamiento import circuloSimple as LSC


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _anillo(lado, cx, cy, r, grosor=1.0):
    """Borde de un círculo de radio `r`, de 2 px de espesor."""
    yy, xx = np.mgrid[0:lado, 0:lado]
    d = np.hypot(xx - cx, yy - cy)
    return ((d > r - grosor) & (d <= r + grosor)).astype(np.uint8)


def _escena_con_manchas(r, manchas=8, semilla=7, interno=None):
    """Círculo de radio `r` más manchas tipo texto fuera del anillo."""
    lado = int(4 * r + 80)
    centro = lado / 2.0
    bordes = _anillo(lado, centro, centro, r)
    if interno:
        bordes |= _anillo(lado, centro, centro, interno)
    rng = np.random.default_rng(semilla)
    colocadas = 0
    intentos = 0
    while colocadas < manchas and intentos < 500:
        px, py = rng.integers(10, lado - 10, 2)
        if np.hypot(px - centro, py - centro) > r + 15:
            bordes[py - 5:py + 5, px - 3:px + 3] = 1
            colocadas += 1
        intentos += 1
    return bordes, (centro, centro)


# ---------------------------------------------------------------------------
# R1 — contrato de find_circle
# ---------------------------------------------------------------------------

def test_devuelve_los_puntos_del_anillo_en_coordenadas_de_la_imagen():
    bordes = _anillo(200, 100, 100, 40)
    puntos = FC.find_circle(bordes, 40.0, (100, 100))

    assert puntos.shape[1] == 2
    d = np.hypot(puntos[:, 0] - 100, puntos[:, 1] - 100)
    assert np.all(np.abs(d - 40.0) <= FC.tolerancia_anillo(40.0))
    assert len(puntos) > 0


def test_devuelve_forma_dos_columnas_cuando_no_hay_bordes():
    vacio = np.zeros((50, 50), dtype=np.uint8)

    puntos = FC.find_circle(vacio, 10.0, (25, 25))

    assert puntos.shape == (0, 2)


def test_devuelve_arreglo_vacio_si_nada_cae_en_el_anillo():
    bordes = _anillo(200, 100, 100, 40)

    puntos = FC.find_circle(bordes, 90.0, (100, 100))

    assert puntos.shape == (0, 2)


def test_el_orden_de_los_puntos_no_afecta_el_ajuste():
    bordes, centro = _escena_con_manchas(60, manchas=0)
    puntos = FC.find_circle(bordes, 60.0, centro)

    directo = LSC.Circulo_simple(puntos)
    invertido = LSC.Circulo_simple(puntos[::-1])

    assert np.allclose(directo[:3], invertido[:3], atol=1e-9)


# ---------------------------------------------------------------------------
# R2 — la tolerancia no puede superar al radio
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("re, esperado", [(8, 2.0), (20, 5.0), (40, 10.0), (428, 10.0)])
def test_tolerancia_es_el_menor_entre_diez_px_y_un_cuarto_del_radio(re, esperado):
    assert FC.tolerancia_anillo(re) == pytest.approx(esperado)


def test_tolerancia_rechaza_radios_no_positivos():
    with pytest.raises(ValueError):
        FC.tolerancia_anillo(0.0)
    with pytest.raises(ValueError):
        FC.tolerancia_anillo(-5.0)


def test_con_radio_chico_el_anillo_no_se_traga_un_circulo_interno():
    """Medido: la tolerancia fija de 10 px daba 55% de contaminación."""
    bordes, centro = _escena_con_manchas(8, manchas=0, interno=20)

    puntos = FC.find_circle(bordes, 10.0, centro)

    d = np.hypot(puntos[:, 0] - centro[0], puntos[:, 1] - centro[1])
    internos = int((np.abs(d - 20.0) <= 1.5).sum())
    assert internos == 0
    x, y, r, _ = LSC.Circulo_simple(puntos)
    assert abs(r - 8.0) <= 1.0


def test_con_radio_grande_la_tolerancia_es_la_de_siempre():
    bordes, centro = _escena_con_manchas(60, manchas=0)

    con_auto = FC.find_circle(bordes, 60.0, centro)
    con_fija = FC.find_circle(bordes, 60.0, centro, tolerancia=10.0)

    assert len(con_auto) == len(con_fija)


def test_la_tolerancia_explicita_manda():
    bordes, centro = _escena_con_manchas(60, manchas=0)

    estrecho = FC.find_circle(bordes, 60.0, centro, tolerancia=1.0)
    amplio = FC.find_circle(bordes, 60.0, centro, tolerancia=10.0)

    assert 0 < len(estrecho) <= len(amplio)


# ---------------------------------------------------------------------------
# R3 — cobertura angular del anillo
# ---------------------------------------------------------------------------

def test_un_anillo_completo_cubre_todos_los_sectores():
    bordes = _anillo(200, 100, 100, 40)
    puntos = FC.find_circle(bordes, 40.0, (100, 100))

    cobertura, hueco = FC.cobertura_angular(puntos, (100, 100))

    assert cobertura == pytest.approx(1.0)
    assert hueco == pytest.approx(0.0)


def test_la_cobertura_delata_un_anillo_de_basura():
    """Medido: con el radio desviado 12 px, la cobertura cae por debajo del 10%."""
    bordes, centro = _escena_con_manchas(12)
    puntos = FC.find_circle(bordes, 24.0, centro)

    cobertura, hueco = FC.cobertura_angular(puntos, centro)

    assert cobertura < FC.UMBRAL_COBERTURA
    assert hueco > FC.HUECO_MAX_DEG


def test_cobertura_sin_puntos_es_cero_y_hueco_completo():
    vacio = np.empty((0, 2))

    assert FC.cobertura_angular(vacio, (0, 0)) == (0.0, 360.0)


def test_validar_anillo_acepta_un_circulo_completo():
    bordes = _anillo(200, 100, 100, 40)
    puntos = FC.find_circle(bordes, 40.0, (100, 100))

    ok, motivo = FC.validar_anillo(puntos, (100, 100))

    assert ok is True
    assert motivo == ""


def test_validar_anillo_rechaza_un_arco_por_cobertura():
    """Un arco de 195° cubre 54.2%, igual que el glifo real de img100."""
    centro = (100.0, 100.0)
    puntos = np.array([
        (centro[0] + 60 * np.cos(np.radians(g)),
         centro[1] + 60 * np.sin(np.radians(g)))
        for g in np.arange(0.0, 195.0, 0.5)
    ])

    ok, motivo = FC.validar_anillo(puntos, centro)

    assert ok is False
    assert "cubren" in motivo


def test_validar_anillo_rechaza_un_hueco_grande_aunque_cubra_bastante():
    """Cubre 80.5% (pasa el umbral) pero deja un hueco de 70°: decide el hueco."""
    centro = (100.0, 100.0)
    puntos = np.array([
        (centro[0] + 60 * np.cos(np.radians(g)),
         centro[1] + 60 * np.sin(np.radians(g)))
        for g in np.arange(0.0, 290.0, 0.5)
    ])

    cobertura, hueco = FC.cobertura_angular(puntos, centro)
    ok, motivo = FC.validar_anillo(puntos, centro)

    assert cobertura >= FC.UMBRAL_COBERTURA
    assert hueco > FC.HUECO_MAX_DEG
    assert ok is False
    assert "hueco" in motivo


def test_validar_anillo_rechaza_cobertura_insuficiente():
    centro = (100.0, 100.0)
    # Cuatro manchas: poca cobertura con huecos grandes.
    puntos = np.array([[160.0, 100.0], [40.0, 100.0], [100.0, 160.0], [100.0, 40.0]])

    ok, motivo = FC.validar_anillo(puntos, centro)

    assert ok is False
    assert "cubren" in motivo or "hueco" in motivo


# ---------------------------------------------------------------------------
# R4 — una selección insuficiente no llega al ajuste
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [0, 1, 2])
def test_validar_anillo_rechaza_menos_de_tres_puntos(n):
    puntos = np.column_stack((np.arange(n, dtype=float) + 100.0,
                              np.full(n, 100.0)))

    ok, motivo = FC.validar_anillo(puntos, (100, 100))

    assert ok is False
    assert "punto" in motivo


@pytest.mark.parametrize("n", [1, 2])
def test_el_ortodoxo_con_menos_de_tres_puntos_lanza_valueerror(n):
    """Con el nuevo contrato, Circulo_simple lanza ValueError para N < 3."""
    puntos = np.array([[10.0, 10.0], [20.0, 20.0]])[:n]

    with pytest.raises(ValueError, match="insuficientes puntos"):
        LSC.Circulo_simple(puntos)


def test_tres_puntos_casi_colineales_producen_un_circulo_absurdo_con_pv_cero():
    """Medido: centro en (-200010, 200020), r = 282864, pv = 0.000000.

    La cobertura angular lo rechaza sin depender de la etapa ⑨.
    """
    puntos = np.array([[0.0, 0.0], [10.0, 10.0], [20.0, 20.001]])

    _, _, r, pv = LSC.Circulo_simple(puntos)
    ok, _ = FC.validar_anillo(puntos, (10.0, 10.0))

    assert r > 1000
    assert pv == pytest.approx(0.0)
    assert ok is False


# ---------------------------------------------------------------------------
# R5 — un solo centro
# ---------------------------------------------------------------------------

def test_find_circle_espera_un_par_de_escalares():
    bordes = _anillo(200, 100, 100, 40)

    with pytest.raises(ValueError):
        FC.find_circle(bordes, 40.0, (np.array([100, 150]), np.array([100, 150])))


# ---------------------------------------------------------------------------
# R6 — el modo sin radio es explícito y vive en su propia función
# ---------------------------------------------------------------------------

def test_find_circle_exige_el_radio():
    """Sin radio no hay anillo: antes se activaba otro algoritmo en silencio."""
    bordes = _anillo(200, 100, 100, 40)

    with pytest.raises(ValueError, match="radio"):
        FC.find_circle(bordes, None, (100, 100))


def test_find_circle_rechaza_radio_cero():
    bordes = _anillo(200, 100, 100, 40)

    with pytest.raises(ValueError, match="segmento_mas_largo"):
        FC.find_circle(bordes, 0, (100, 100))


def test_find_circle_rechaza_radio_negativo():
    bordes = _anillo(200, 100, 100, 40)

    with pytest.raises(ValueError, match="segmento_mas_largo"):
        FC.find_circle(bordes, -30.0, (100, 100))


def test_segmento_mas_largo_se_queda_con_el_grupo_mas_numeroso():
    puntos = np.array([
        [0, 0], [1, 0], [2, 0],
        [100, 9], [101, 10], [102, 11], [103, 12],
    ], dtype=float)

    grupo = FC.segmento_mas_largo(puntos)

    assert grupo.shape == (4, 2)
    assert np.all(grupo[:, 0] >= 100)


def test_un_hueco_de_exactamente_seis_px_no_corta():
    """Corrección medida: el test interno es '> 6', así que 6 no separa.

    La asimetría `< 6` (eje X) vs `<= 6` (eje Y) del código original es
    cosmética: ambas normalizan a 1 antes del mismo `> 6`.
    """
    puntos = np.array([[0, 0], [6, 0], [12, 0], [18, 0]], dtype=float)

    assert len(FC.segmento_mas_largo(puntos)) == 4


def test_segmento_mas_largo_conserva_las_coordenadas_xy():
    puntos = np.array([[500, 10], [501, 10], [502, 10]], dtype=float)

    grupo = FC.segmento_mas_largo(puntos)

    assert np.all(grupo[:, 0] > 400)   # la columna 0 es X
    assert np.all(grupo[:, 1] < 100)


def test_segmento_mas_largo_con_arreglo_vacio():
    assert FC.segmento_mas_largo(np.empty((0, 2))).shape == (0, 2)

