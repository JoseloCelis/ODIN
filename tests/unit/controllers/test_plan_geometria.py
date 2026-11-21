"""Selector de geometría (spec migracion-lineas-geometria, S4 y T5).

Cubre el bloque «T5 — criterios de diseño del selector» en su parte pura:

1. La geometría es una entrada explícita: cuando el operador la fija, se
   obedece sin consultar al clasificador.
2. Automático consulta, no adivina: la propuesta del clasificador se usa solo
   si decidió; si falla cerrado, el plan no elige.
3. Sin decisión no hay excepción: el plan detiene el pipeline con ambos
   candidatos, la confianza y la evidencia numérica.
4. Las dos geometrías son ramas del mismo selector: círculo ⑦→⑧→⑨ y recta
   ⑩→⑪; ninguna es el camino por defecto.
6. La decisión es una función pura, sin GTK, testeable sin UI.
"""

import math
import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest

from src.odin.Procesamiento import EvidenciaGeometria, Geometria
from src.odin.controllers.plan_geometria import (
    ETAPAS_CIRCULO,
    ETAPAS_RECTA,
    GEOMETRIA_POR_OPCION,
    OPCIONES_GEOMETRIA,
    ORIGEN_AUTOMATICO,
    ORIGEN_INDETERMINADO,
    ORIGEN_OPERADOR,
    PlanGeometria,
    plan_de_etapas,
    puntos_de_borde,
)

RAIZ = Path(__file__).resolve().parents[3]
INF = math.inf


def _evidencia(
    geometria: Geometria | None,
    *,
    confianza: float = 0.9,
    candidatos: tuple[Geometria, ...] | None = None,
    residual_recta: float = 1.0,
    residual_circulo: float = 2.0,
    cobertura: float = 0.5,
    radio: float | None = 10.0,
) -> EvidenciaGeometria:
    """Evidencia de prueba con los campos que el plan debe reportar."""
    if candidatos is None:
        candidatos = (geometria,) if geometria is not None else (
            Geometria.CIRCULO,
            Geometria.RECTA,
        )
    return EvidenciaGeometria(
        geometria=geometria,
        confianza=confianza,
        candidatos=candidatos,
        residual_recta=residual_recta,
        residual_circulo=residual_circulo,
        cobertura_angular=cobertura,
        radio=radio,
        detalle="evidencia de prueba",
    )


# ---------------------------------------------------------------------------
# Contrato del plan
# ---------------------------------------------------------------------------

def test_el_plan_es_un_dataclass_inmutable():
    assert hasattr(PlanGeometria, "__slots__")
    plan = plan_de_etapas(Geometria.CIRCULO)
    with pytest.raises(FrozenInstanceError):
        plan.geometria = Geometria.RECTA  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Criterio 1 — la geometría es una entrada explícita
# ---------------------------------------------------------------------------

def test_el_operador_fija_circulo_y_el_clasificador_no_se_consulta():
    """Una geometría fijada se obedece aunque la evidencia diga lo contrario."""
    plan = plan_de_etapas(Geometria.CIRCULO, _evidencia(Geometria.RECTA))

    assert plan.geometria is Geometria.CIRCULO
    assert plan.etapas == ETAPAS_CIRCULO == (7, 8, 9)
    assert plan.candidatos == (Geometria.CIRCULO,)
    assert plan.origen == ORIGEN_OPERADOR


def test_el_operador_fija_recta():
    plan = plan_de_etapas(Geometria.RECTA, _evidencia(Geometria.CIRCULO))

    assert plan.geometria is Geometria.RECTA
    assert plan.etapas == ETAPAS_RECTA == (10, 11)
    assert plan.candidatos == (Geometria.RECTA,)
    assert plan.origen == ORIGEN_OPERADOR


def test_la_geometria_fijada_no_expone_confianza_del_clasificador():
    """Sin consulta no hay confianza: el campo es None, no un número inventado."""
    plan = plan_de_etapas(Geometria.CIRCULO, _evidencia(Geometria.CIRCULO, confianza=0.1))

    assert plan.confianza is None


# ---------------------------------------------------------------------------
# Criterio 2 — automático consulta, no adivina
# ---------------------------------------------------------------------------

def test_automatico_usa_la_propuesta_cuando_el_clasificador_decide_circulo():
    plan = plan_de_etapas(None, _evidencia(Geometria.CIRCULO, confianza=0.9))

    assert plan.geometria is Geometria.CIRCULO
    assert plan.etapas == ETAPAS_CIRCULO
    assert plan.origen == ORIGEN_AUTOMATICO
    assert plan.confianza == pytest.approx(0.9)


def test_automatico_usa_la_propuesta_cuando_el_clasificador_decide_recta():
    plan = plan_de_etapas(None, _evidencia(Geometria.RECTA, confianza=0.8))

    assert plan.geometria is Geometria.RECTA
    assert plan.etapas == ETAPAS_RECTA
    assert plan.origen == ORIGEN_AUTOMATICO


def test_automatico_no_adivina_cuando_el_clasificador_falla_cerrado():
    plan = plan_de_etapas(
        None,
        _evidencia(None, confianza=0.2, candidatos=(Geometria.CIRCULO, Geometria.RECTA)),
    )

    assert plan.geometria is None
    assert plan.etapas == ()
    assert plan.candidatos == (Geometria.CIRCULO, Geometria.RECTA)
    assert plan.origen == ORIGEN_INDETERMINADO
    assert plan.confianza == pytest.approx(0.2)


def test_automatico_con_clasificador_real_decide_circulo():
    """Integración T4→T5: un círculo real se propone y se planifica como ⑦→⑧→⑨."""
    from src.odin.Procesamiento import clasificar_geometria

    angulos = np.linspace(0.0, 2.0 * np.pi, 100, endpoint=False)
    circulo = np.column_stack([50.0 * np.cos(angulos), 50.0 * np.sin(angulos)])

    plan = plan_de_etapas(None, clasificar_geometria(circulo))

    assert plan.geometria is Geometria.CIRCULO
    assert plan.etapas == (7, 8, 9)
    assert plan.origen == ORIGEN_AUTOMATICO


def test_automatico_con_clasificador_real_decide_recta():
    """Integración T4→T5: una recta real se propone y se planifica como ⑩→⑪."""
    from src.odin.Procesamiento import clasificar_geometria

    recta = np.column_stack([np.linspace(-50.0, 50.0, 100), np.zeros(100)])

    plan = plan_de_etapas(None, clasificar_geometria(recta))

    assert plan.geometria is Geometria.RECTA
    assert plan.etapas == (10, 11)
    assert plan.origen == ORIGEN_AUTOMATICO


# ---------------------------------------------------------------------------
# Criterio 3 — sin decisión no hay excepción críptica
# ---------------------------------------------------------------------------

def test_sin_decision_el_plan_expone_candidatos_confianza_y_evidencia():
    plan = plan_de_etapas(
        None,
        _evidencia(
            None,
            confianza=0.2,
            candidatos=(Geometria.CIRCULO, Geometria.RECTA),
            residual_recta=1.25,
            residual_circulo=INF,
            cobertura=0.3,
            radio=None,
        ),
    )

    assert plan.geometria is None
    detalle = plan.detalle.lower()
    assert "círculo" in detalle
    assert "recta" in detalle
    assert "0.200" in detalle          # confianza
    assert "1.250" in detalle          # residual de la recta
    assert "inf" in detalle            # residual del círculo no admisible
    assert "30.0%" in detalle          # cobertura angular


def test_sin_decision_no_lanza_ni_elige_una_rama():
    """El plan es total: nunca levanta excepción, incluso sin evidencia."""
    plan = plan_de_etapas(None, None)

    assert plan.geometria is None
    assert plan.etapas == ()
    assert plan.candidatos == (Geometria.CIRCULO, Geometria.RECTA)


# ---------------------------------------------------------------------------
# Criterio 4 — las dos geometrías son ramas del mismo selector
# ---------------------------------------------------------------------------

def test_circulo_usa_las_etapas_7_8_9():
    assert plan_de_etapas(Geometria.CIRCULO).etapas == (7, 8, 9)


def test_recta_usa_las_etapas_10_11():
    assert plan_de_etapas(Geometria.RECTA).etapas == (10, 11)


def test_ninguna_geometria_es_el_camino_por_defecto():
    """Sin geometría fijada y sin evidencia no hay etapas: no se asume círculo."""
    plan = plan_de_etapas(None, None)

    assert plan.etapas == ()
    assert plan.geometria is None


# ---------------------------------------------------------------------------
# Criterio 6 — la decisión es una función pura
# ---------------------------------------------------------------------------

def test_el_plan_no_importa_capas_de_ui():
    ruta = RAIZ / "src" / "odin" / "controllers" / "plan_geometria.py"
    fuente = ruta.read_text(encoding="utf-8")

    importados = re.findall(
        r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", fuente, re.MULTILINE
    )
    prohibidos = {"gi", "cairo", "Gtk", "Gdk", "Adw"}

    assert not (set(importados) & prohibidos)


def test_el_plan_se_prueba_sin_display():
    """Importar y decidir no requiere un display GDK ni constructores de GTK."""
    plan = plan_de_etapas(Geometria.RECTA)

    assert isinstance(plan, PlanGeometria)
    assert plan.etapas == (10, 11)


# ---------------------------------------------------------------------------
# Selector de la vista y extracción de puntos de borde
# ---------------------------------------------------------------------------

def test_mapeo_de_las_opciones_del_selector():
    assert OPCIONES_GEOMETRIA == ("Círculo", "Recta", "Automático")
    assert GEOMETRIA_POR_OPCION == (
        Geometria.CIRCULO,
        Geometria.RECTA,
        None,
    )


def test_puntos_de_borde_devuelve_coordenadas_x_y():
    mascara = np.zeros((3, 4), dtype=float)
    mascara[1, 2] = 1.0
    mascara[2, 0] = 1.0

    puntos = puntos_de_borde(mascara)

    assert puntos.dtype == np.float64
    assert puntos.tolist() == [[2.0, 1.0], [0.0, 2.0]]


def test_puntos_de_borde_vacio_devuelve_un_arreglo_vacio():
    puntos = puntos_de_borde(np.zeros((5, 5)))

    assert puntos.shape == (0, 2)
