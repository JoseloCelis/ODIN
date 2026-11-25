"""Clasificador de geometría (círculo vs. recta) — spec migracion-lineas-geometria, S4 y S6.

Cubre el bloque «T4 — criterios de diseño del clasificador»:

1. Residuales por mediana: recta por PCA/SVD y círculo por el ajuste
   algebraico de `odin.Ajustes` (mediana, no media).
2. Admisibilidad del círculo: radio mayor que `factor_radio_max · extensión`
   o radio no finito ⇒ residual del círculo `inf`.
3. Confianza `(peor - mejor) / peor`, con `1.0` si el peor es infinito y
   `0.0` si ambos lo son.
4. Falla cerrado: `confianza < umbral` ⇒ `geometria=None` y ambos candidatos.
5. Degenerados no lanzan: menos de 3 puntos, valores no finitos o duplicados
   devuelven confianza `0` con ambos candidatos.

Además, el caso que motiva la admisibilidad: un conjunto puramente colineal
 debe clasificarse como recta, no como un círculo gigante.
"""

import math
import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest

from src.odin.Procesamiento.models.geometria import (
    EvidenciaGeometria,
    Geometria,
    clasificar_geometria,
)

RAIZ = Path(__file__).resolve().parents[3]
INF = math.inf


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _circulo(n, radio, centro=(0.0, 0.0), a0=0.0, a1=2.0 * np.pi):
    """Puntos equiespaciados en un círculo (o arco) de centro y radio dados."""
    angulos = np.linspace(a0, a1, n, endpoint=False)
    return np.column_stack(
        [centro[0] + radio * np.cos(angulos), centro[1] + radio * np.sin(angulos)]
    )


def _recta_horizontal(n, y=0.0, x0=-50.0, x1=50.0):
    """Puntos equiespaciados sobre la recta horizontal `y`."""
    return np.column_stack([np.linspace(x0, x1, n), np.full(n, float(y))])


def _banda_gruesa(n, medio_ancho=20.0, ruido=0.3, semilla=0):
    """Dos orillas paralelas (banda) con ruido gaussiano perpendicular."""
    rng = np.random.default_rng(semilla)
    x = np.linspace(-50.0, 50.0, n)
    superior = np.column_stack(
        [x, np.full(n, medio_ancho) + rng.normal(0.0, ruido, n)]
    )
    inferior = np.column_stack(
        [x, np.full(n, -medio_ancho) + rng.normal(0.0, ruido, n)]
    )
    return np.vstack([superior, inferior])


def _desviaciones_banda(puntos):
    """Desviaciones a la banda de medio-ancho uniforme (criterio S1).

    `signed` es la distancia perpendicular con signo a la recta media (PCA);
    `median(|signed|)` es el medio-ancho, y la desviación de cada punto es
    `||signed| - median(|signed|)|`. El residual de recta es la mediana de
    estas desviaciones.
    """
    centrado = puntos - puntos.mean(axis=0)
    _, _, vh = np.linalg.svd(centrado, full_matrices=False)
    signed = centrado @ vh[-1]
    return np.abs(np.abs(signed) - np.median(np.abs(signed)))


# ---------------------------------------------------------------------------
# Contrato
# ---------------------------------------------------------------------------

def test_geometria_enum_y_contrato_del_dataclass():
    """`Geometria` es la enumeración CIRCULO/RECTA y `EvidenciaGeometria` es frozen+slotted."""
    assert Geometria.CIRCULO.name == "CIRCULO"
    assert Geometria.RECTA.name == "RECTA"

    assert hasattr(EvidenciaGeometria, "__slots__")
    assert hasattr(EvidenciaGeometria, "__dataclass_fields__")
    campos = list(EvidenciaGeometria.__dataclass_fields__)
    assert campos == [
        "geometria",
        "confianza",
        "candidatos",
        "residual_recta",
        "residual_circulo",
        "cobertura_angular",
        "radio",
        "detalle",
    ]

    evidencia = clasificar_geometria(_circulo(50, 20.0))
    with pytest.raises(FrozenInstanceError):
        evidencia.confianza = 0.0  # type: ignore[misc]


def test_firma_y_punto_de_entrada():
    """La función recibe puntos y devuelve un `EvidenciaGeometria`."""
    evidencia = clasificar_geometria(_circulo(50, 20.0))

    assert isinstance(evidencia, EvidenciaGeometria)
    assert isinstance(evidencia.detalle, str) and evidencia.detalle
    assert isinstance(evidencia.candidatos, tuple)


# ---------------------------------------------------------------------------
# Criterio 1 — residuales por mediana
# ---------------------------------------------------------------------------

def test_circulo_perfecto_clasifica_circulo():
    evidencia = clasificar_geometria(_circulo(200, 50.0))

    assert evidencia.geometria is Geometria.CIRCULO
    assert evidencia.residual_circulo == pytest.approx(0.0, abs=1e-9)
    assert evidencia.residual_recta > 0.0
    assert evidencia.radio == pytest.approx(50.0, rel=1e-6)
    assert evidencia.cobertura_angular == pytest.approx(1.0)


def test_recta_con_ruido_clasifica_recta():
    rng = np.random.default_rng(7)
    puntos = _recta_horizontal(200) + rng.normal(0.0, 0.3, (200, 2))

    evidencia = clasificar_geometria(puntos)

    assert evidencia.geometria is Geometria.RECTA
    assert evidencia.residual_recta < 1.0
    assert evidencia.residual_circulo == INF


def test_residual_recta_es_la_mediana_no_la_media():
    """Con un solo punto suelto, la mediana ignora el valor atípico y la media no.

    El residual de recta es la mediana de las desviaciones a la banda; la
    media de esas mismas desviaciones se dispara por el atípico.
    """
    puntos = np.vstack(
        [_recta_horizontal(100, x0=0.0, x1=99.0), np.array([[50.0, 100.0]])]
    )
    desviaciones = _desviaciones_banda(puntos)
    mediana = float(np.median(desviaciones))
    media = float(np.mean(desviaciones))
    assert mediana < media  # la distribución está sesgada por el atípico

    evidencia = clasificar_geometria(puntos)

    assert evidencia.residual_recta == pytest.approx(mediana)
    assert evidencia.residual_recta != pytest.approx(media)


def test_linea_gruesa_de_dos_orillas_clasifica_recta():
    """Una línea gruesa (dos orillas con ruido) es una recta, no un círculo.

    El criterio de banda mide la dispersión de las orillas respecto del
    medio-ancho, no la distancia a una recta de grosor cero: con dos orillas
    paralelas con ruido, el residual es la dispersión de orilla (~0.2px) y la
    recta gana con confianza alta, mientras que el criterio anterior daba
    ≈ medio ancho (20px) y fallaba cerrado.
    """
    puntos = _banda_gruesa(120, medio_ancho=20.0, ruido=0.3, semilla=0)

    evidencia = clasificar_geometria(puntos)

    assert evidencia.geometria is Geometria.RECTA
    assert evidencia.residual_recta < 1.0
    assert evidencia.confianza > 0.75


def test_residual_circulo_es_la_mediana_no_la_media():
    """El residual del círculo es la mediana de |distancia - radio|."""
    from src.odin.Ajustes import LSC

    puntos = np.vstack([_circulo(90, 50.0), _circulo(10, 60.0)])
    x_c, y_c, r, _pv = LSC(puntos)
    distancias = np.hypot(puntos[:, 0] - x_c, puntos[:, 1] - y_c)
    residuales = np.abs(distancias - r)
    mediana = float(np.median(residuales))
    media = float(np.mean(residuales))
    assert mediana < media

    evidencia = clasificar_geometria(puntos)

    assert evidencia.residual_circulo == pytest.approx(mediana)
    assert evidencia.residual_circulo != pytest.approx(media)


# ---------------------------------------------------------------------------
# Criterio 2 — admisibilidad del círculo
# ---------------------------------------------------------------------------

def test_admisibilidad_rechaza_radio_mayor_al_factor_por_extension():
    """Un círculo genuino deja de ser admisible si el factor es minúsculo."""
    puntos = _circulo(200, 50.0)

    evidencia = clasificar_geometria(puntos, factor_radio_max=0.1)

    assert evidencia.residual_circulo == INF
    assert evidencia.geometria is Geometria.RECTA


def test_admisibilidad_rechaza_arco_superficial():
    """Un arco de 1° y radio 1000 px es una recta, no un círculo gigante."""
    puntos = _circulo(50, 1000.0, a0=-0.01, a1=0.01)

    evidencia = clasificar_geometria(puntos)

    assert evidencia.residual_circulo == INF
    assert evidencia.geometria is Geometria.RECTA


def test_admisibilidad_con_radio_no_finito():
    """Sin ajuste circular (colineales) el residual del círculo es infinito."""
    evidencia = clasificar_geometria(_recta_horizontal(100))

    assert evidencia.radio is None
    assert not math.isfinite(evidencia.residual_circulo)
    assert evidencia.residual_circulo == INF


# ---------------------------------------------------------------------------
# Criterio 3 — confianza
# ---------------------------------------------------------------------------

def test_confianza_uno_cuando_el_peor_residual_es_infinito():
    evidencia = clasificar_geometria(_recta_horizontal(100))

    assert evidencia.confianza == 1.0


def test_confianza_cero_cuando_ambos_residuales_son_infinitos():
    evidencia = clasificar_geometria(np.array([[0.0, 0.0], [1.0, 1.0]]))

    assert evidencia.residual_recta == INF
    assert evidencia.residual_circulo == INF
    assert evidencia.confianza == 0.0


def test_confianza_es_la_separacion_relativa_de_residuales():
    rng = np.random.default_rng(11)
    puntos = _circulo(200, 50.0) + rng.normal(0.0, 0.5, (200, 2))

    evidencia = clasificar_geometria(puntos)

    mejor = min(evidencia.residual_recta, evidencia.residual_circulo)
    peor = max(evidencia.residual_recta, evidencia.residual_circulo)
    esperada = (peor - mejor) / peor
    assert evidencia.confianza == pytest.approx(esperada)
    assert 0.0 <= evidencia.confianza <= 1.0


# ---------------------------------------------------------------------------
# Criterio 4 — falla cerrado
# ---------------------------------------------------------------------------

def test_falla_cerrado_bajo_el_umbral():
    rng = np.random.default_rng(11)
    puntos = _circulo(200, 50.0) + rng.normal(0.0, 0.5, (200, 2))

    evidencia = clasificar_geometria(puntos, umbral_confianza=1.0)

    assert evidencia.geometria is None
    assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA)


def test_falla_cerrado_expone_la_misma_evidencia():
    """El umbral no altera la evidencia, solo la decisión."""
    rng = np.random.default_rng(11)
    puntos = _circulo(200, 50.0) + rng.normal(0.0, 0.5, (200, 2))

    abierto = clasificar_geometria(puntos)
    cerrado = clasificar_geometria(puntos, umbral_confianza=1.0)

    assert abierto.geometria is Geometria.CIRCULO
    assert abierto.candidatos == (Geometria.CIRCULO,)
    assert cerrado.residual_recta == pytest.approx(abierto.residual_recta)
    assert cerrado.residual_circulo == pytest.approx(abierto.residual_circulo)
    assert cerrado.confianza == pytest.approx(abierto.confianza)


# ---------------------------------------------------------------------------
# Criterio 5 — degenerados no lanzan
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("puntos", [
    np.empty((0, 2)),
    np.array([[1.0, 2.0]]),
    np.array([[0.0, 0.0], [1.0, 1.0]]),
])
def test_menos_de_tres_puntos_devuelve_confianza_cero(puntos):
    evidencia = clasificar_geometria(puntos)

    assert evidencia.geometria is None
    assert evidencia.confianza == 0.0
    assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA)


@pytest.mark.parametrize("valor", [np.nan, np.inf, -np.inf])
def test_valores_no_finitos_devuelven_confianza_cero(valor):
    puntos = np.array([[0.0, 0.0], [1.0, 1.0], [valor, 2.0]])

    evidencia = clasificar_geometria(puntos)

    assert evidencia.geometria is None
    assert evidencia.confianza == 0.0
    assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA)


@pytest.mark.parametrize("puntos", [
    np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]),
    np.array([[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]),
    np.array([[5.0, 5.0], [5.0, 5.0], [5.0, 5.0], [5.0, 5.0]]),
])
def test_puntos_duplicados_devuelven_confianza_cero(puntos):
    evidencia = clasificar_geometria(puntos)

    assert evidencia.geometria is None
    assert evidencia.confianza == 0.0
    assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA)


def test_extension_menor_a_la_tolerancia_es_degenerada():
    """Un conjunto confinado a menos de `tolerancia_px` no tiene geometría clasificable."""
    puntos = np.array([[0.0, 0.0], [0.5, 0.0], [0.0, 0.5]])

    evidencia = clasificar_geometria(puntos)

    assert evidencia.geometria is None
    assert evidencia.confianza == 0.0


# ---------------------------------------------------------------------------
# El caso que motiva la admisibilidad
# ---------------------------------------------------------------------------

def test_colineales_puros_clasifican_como_recta_no_circulo_gigante():
    """Un conjunto puramente colineal es una recta; el círculo queda inhabilitado."""
    evidencia = clasificar_geometria(_recta_horizontal(200))

    assert evidencia.geometria is Geometria.RECTA
    assert evidencia.residual_recta == pytest.approx(0.0, abs=1e-9)
    assert evidencia.residual_circulo == INF
    assert evidencia.radio is None
    assert evidencia.confianza == 1.0


# ---------------------------------------------------------------------------
# S6 — aislamiento de la capa de modelo
# ---------------------------------------------------------------------------

def test_el_modelo_no_importa_capas_de_ui():
    ruta = RAIZ / "src" / "odin" / "Procesamiento" / "models" / "geometria.py"
    fuente = ruta.read_text(encoding="utf-8")

    importados = re.findall(
        r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", fuente, re.MULTILINE
    )
    prohibidos = {"gi", "cairo", "Gtk", "Gdk", "Adw"}

    assert not (set(importados) & prohibidos)


def test_el_modelo_consume_el_ajuste_por_el_alias_publico():
    """El ajuste circular se consume por `odin.Ajustes`, no por el módulo."""
    import odin.Ajustes as ajustes_publico
    from src.odin.Procesamiento.models import geometria

    assert geometria.LSC is ajustes_publico.LSC


def test_alias_publico_del_dominio():
    """La clasificación se expone por la cadena de alias del dominio."""
    from src.odin.Procesamiento import Geometria as GeometriaAlias
    from src.odin.Procesamiento import EvidenciaGeometria as EvidenciaAlias
    from src.odin.Procesamiento import clasificar_geometria as clasificar_alias
    from src.odin.Procesamiento.models import Geometria as GeometriaModelo

    assert GeometriaAlias is Geometria
    assert EvidenciaAlias is EvidenciaGeometria
    assert clasificar_alias is clasificar_geometria
    assert GeometriaModelo is Geometria


def test_la_traslacion_que_colapsa_puntos_se_reporta_degenerada():
    """Trasladar puede volver idénticos dos puntos distintos, por redondeo.

    Un par que difiere en 1e-308 deja de diferir al sumarle 1.0. El
    clasificador lo reporta como degenerado en vez de inventar geometría; una
    traslación que sí conserva los puntos distintos no cambia la decisión.
    """
    casi_colineales = [[3.0, 0.0], [1.11253693e-308, 0.0], [0.0, 0.0]]
    colapsados = [[x + 1.0, y + 1.0] for x, y in casi_colineales]
    base = clasificar_geometria(casi_colineales)

    assert clasificar_geometria(colapsados).geometria is None

    sanos = [[3.0, 0.0], [0.5, 0.0], [0.0, 0.0]]
    desplazados = [[x + 1.0, y + 1.0] for x, y in sanos]
    movido = clasificar_geometria(desplazados)

    assert movido.geometria is clasificar_geometria(sanos).geometria
    assert movido.geometria is Geometria.RECTA


def test_un_empate_a_nivel_de_ruido_falla_cerrado_y_no_decide():
    """Criterio 3 — un empate por debajo de la resolución del cálculo no decide.

    Los dos contraejemplos son los que Hypothesis redujo en las semillas 2 y 3
    de `test_prop_invariancia_rotacion_y_reflexion`. En ambos los dos modelos
    ajustan a nivel de ruido de máquina (residuales `0` y `~1e-16`), así que la
    confianza no comparaba geometrías sino redondeo, y una transformación rígida
    la hacía cruzar el umbral.

    Fijado aquí: cuando la diferencia de residuales no supera el ruido del
    propio cálculo, no hay evidencia de geometría y se falla cerrado con
    confianza `0`, de forma determinista e invariante.
    """
    # Semilla 3: triángulo rectángulo de catetos 2px. Tres puntos determinan una
    # circunferencia exacta, así que el residual del círculo es idénticamente 0.
    triangulo = np.array([[2.0, 0.0], [0.0, 2.0], [0.0, 0.0]])
    coseno, seno = math.cos(1.0), math.sin(1.0)
    rotado = triangulo @ np.array([[coseno, -seno], [seno, coseno]]).T

    for etiqueta, puntos in (("base", triangulo), ("rotado", rotado)):
        evidencia = clasificar_geometria(puntos)
        assert evidencia.geometria is None, etiqueta
        assert evidencia.confianza == pytest.approx(0.0, abs=1e-12), etiqueta
        assert evidencia.candidatos == (Geometria.CIRCULO, Geometria.RECTA), etiqueta


def test_la_traslacion_pura_no_decide_por_redondeo_sobre_puntos_duplicados():
    """El mismo empate no puede decidirse por una traslación de (1, 1).

    Semilla 2: cinco puntos con tres copias de uno de ellos. La mediana de las
    desviaciones quedaba decidida por las copias y el residual de banda daba `0`
    exacto; desplazar la nube cambiaba el último bit y con él la decisión, de
    `RECTA` con confianza `1.0` a ninguna decisión.
    """
    base = np.array([[3.0, 0.0], [0.0, 2.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])
    desplazado = base + np.array([1.0, 1.0])

    for etiqueta, puntos in (("base", base), ("desplazado", desplazado)):
        evidencia = clasificar_geometria(puntos)
        assert evidencia.geometria is None, etiqueta
        assert evidencia.confianza == pytest.approx(0.0, abs=1e-12), etiqueta


def test_la_colinealidad_exacta_sigue_siendo_una_recta_limpia():
    """El piso de ruido no alcanza a la colinealidad: ahí el círculo es `inf`.

    Tres puntos colineales son la evidencia más limpia de una recta (L13): el
    ajuste de Kåsa no puede dar radio y el residual del círculo es infinito, así
    que la separación de residuales es total y no un empate.
    """
    evidencia = clasificar_geometria(np.array([[3.0, 0.0], [0.5, 0.0], [0.0, 0.0]]))

    assert evidencia.geometria is Geometria.RECTA
    assert evidencia.confianza == pytest.approx(1.0)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Defecto conocido y distinto del empate: con covarianza isotrópica "
        "(cuadrado, polígono regular) la dirección principal del SVD es "
        "arbitraria, así que el residual de banda depende de la rotación "
        "(0.000 px en el cuadrado alineado, 0.434 px rotado 0.449 rad) y la "
        "decisión cambia de ninguna a CIRCULO. Requiere decidir qué residual "
        "de recta es invariante cuando el eigenvalor es degenerado."
    ),
)
def test_un_conjunto_con_covarianza_isotropica_deberia_ser_invariante():
    """Limitación medida: el residual de recta no es invariante en simetría exacta.

    El piso de ruido resuelve el empate cuando los dos residuales son ruido,
    pero acá el residual de recta rotado ya no es ruido: la recta de PCA de un
    cuadrado tiene dirección arbitraria porque los dos eigenvalores son iguales.
    """
    cuadrado = np.array([[1.0, 1.0], [1.0, -1.0], [-1.0, -1.0], [-1.0, 1.0]])
    coseno, seno = math.cos(math.pi / 7), math.sin(math.pi / 7)
    rotado = cuadrado @ np.array([[coseno, -seno], [seno, coseno]]).T + np.array([3.0, -7.0])

    base = clasificar_geometria(cuadrado)
    movido = clasificar_geometria(rotado)

    assert movido.geometria is base.geometria
    assert movido.confianza == pytest.approx(base.confianza, rel=1e-6, abs=1e-7)


def test_un_circulo_lejos_del_origen_sigue_siendo_un_circulo():
    """El ajuste algebraico usa coordenadas absolutas: centrarlo lo estabiliza.

    Sin centrar, un círculo desplazado lejos del origen degrada el ajuste de
    Kåsa y puede cambiar la decisión; con el centrado, la evidencia es la misma
    cerca y lejos.
    """
    angulos = [i * 2.0 * math.pi / 24.0 for i in range(24)]
    circulo = [[50.0 * math.cos(a), 50.0 * math.sin(a)] for a in angulos]
    lejano = [[x + 1e6, y + 1e6] for x, y in circulo]

    cerca = clasificar_geometria(circulo)
    lejos = clasificar_geometria(lejano)

    assert cerca.geometria is Geometria.CIRCULO
    assert lejos.geometria is Geometria.CIRCULO
    assert abs(lejos.confianza - cerca.confianza) <= 1e-6
    assert abs(lejos.residual_circulo - cerca.residual_circulo) <= 1e-6
