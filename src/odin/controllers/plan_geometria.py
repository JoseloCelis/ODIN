"""Plan de etapas según la geometría seleccionada (spec S4, T5).

Módulo puro del controlador: sin `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`. El
mapeo «geometría + evidencia → plan de etapas» vive aquí para poder probarse
sin UI (criterio 6 del bloque «T5 — criterios de diseño del selector»).

Criterios que implementa:

1. La geometría es una entrada explícita: cuando el operador la fija, el plan
   la obedece sin consultar al clasificador.
2. Automático consulta, no adivina: la propuesta del clasificador se usa solo
   si `EvidenciaGeometria.geometria` no es `None`.
3. Sin decisión no hay excepción: el plan se detiene con ambos candidatos, la
   confianza y la evidencia numérica, para que la vista los muestre.
4. Las dos geometrías son ramas del mismo selector: círculo usa ⑦→⑧→⑨ y
   recta ⑩→⑪; ninguna es el camino por defecto.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np

from ..Procesamiento import EvidenciaGeometria, Geometria

# Ramas del selector (criterio 4). Ninguna es el camino por defecto.
ETAPAS_CIRCULO: Final = (7, 8, 9)
ETAPAS_RECTA: Final = (10, 11)

# Opciones del selector de la vista, en el orden del criterio 5, y su mapeo a
# la entrada del pipeline (`None` es automático).
OPCIONES_GEOMETRIA: Final = ("Círculo", "Recta", "Automático")
GEOMETRIA_POR_OPCION: Final = (Geometria.CIRCULO, Geometria.RECTA, None)

# Orígenes del plan: quién decidió la geometría.
ORIGEN_OPERADOR: Final = "operador"
ORIGEN_AUTOMATICO: Final = "automatico"
ORIGEN_INDETERMINADO: Final = "indeterminado"


@dataclass(frozen=True, slots=True)
class PlanGeometria:
    """Plan de etapas resultante de la decisión de geometría.

    `geometria` es `None` cuando no hay decisión (automático con el
    clasificador en falla cerrado, o sin evidencia). `etapas` queda vacío en
    ese caso: el pipeline se detiene antes de ejecutar ninguna rama.
    `confianza` es `None` cuando la geometría la fijó el operador, porque no
    hubo consulta al clasificador.
    """

    geometria: Geometria | None
    etapas: tuple[int, ...]
    origen: str
    candidatos: tuple[Geometria, ...]
    confianza: float | None
    detalle: str


def _etapas_de(geometria: Geometria) -> tuple[int, ...]:
    """Rama de etapas de una geometría (criterio 4)."""
    return ETAPAS_CIRCULO if geometria is Geometria.CIRCULO else ETAPAS_RECTA


def _nombre(geometria: Geometria) -> str:
    """Nombre en español de la geometría, para los mensajes del operador."""
    return "círculo" if geometria is Geometria.CIRCULO else "recta"


def _etapas_texto(etapas: tuple[int, ...]) -> str:
    return "→".join(str(etapa) for etapa in etapas)


def _fmt_numero(valor: float) -> str:
    """Número en texto legible por el operador, con `inf` explícito."""
    if math.isinf(valor):
        return "inf"
    if math.isnan(valor):
        return "nan"
    return f"{valor:.3f}"


def _evidencia_texto(evidencia: EvidenciaGeometria) -> str:
    """Evidencia numérica en un texto único, para el resumen de la vista."""
    candidatos = " y ".join(_nombre(g) for g in evidencia.candidatos)
    radio = "no finito" if evidencia.radio is None else f"{evidencia.radio:.2f}px"
    return (
        f"candidatos: {candidatos}; confianza {evidencia.confianza:.3f}; "
        f"residual recta {_fmt_numero(evidencia.residual_recta)}px; "
        f"residual círculo {_fmt_numero(evidencia.residual_circulo)}px; "
        f"cobertura {evidencia.cobertura_angular:.1%}; radio {radio}"
    )


def plan_de_etapas(
    geometria: Geometria | None,
    evidencia: EvidenciaGeometria | None = None,
) -> PlanGeometria:
    """Decide la geometría y devuelve el plan de etapas correspondiente.

    Parameters:
        geometria: geometría fijada por el operador (`CIRCULO` o `RECTA`) o
            `None` para automático.
        evidencia: `EvidenciaGeometria` del clasificador, consultada solo cuando
            `geometria` es `None`. Se acepta `None` para el caso en que no se
            consultó.

    Returns:
        `PlanGeometria` con la geometría decidida (o `None`), las etapas de la
        rama, el origen de la decisión, los candidatos, la confianza y un
        detalle en español con la evidencia numérica.

    Nota:
        Nunca lanza excepción: la decisión es total y falla cerrado.
    """
    # Criterio 1: la geometría fijada se obedece sin consultar al clasificador.
    if geometria is not None:
        etapas = _etapas_de(geometria)
        return PlanGeometria(
            geometria=geometria,
            etapas=etapas,
            origen=ORIGEN_OPERADOR,
            candidatos=(geometria,),
            confianza=None,
            detalle=(
                f"geometría fijada por el operador: {_nombre(geometria)}; "
                f"etapas {_etapas_texto(etapas)}"
            ),
        )

    # Sin geometría fijada: automático. Criterio 2: se usa la propuesta solo
    # si el clasificador decidió.
    if evidencia is None:
        return PlanGeometria(
            geometria=None,
            etapas=(),
            origen=ORIGEN_INDETERMINADO,
            candidatos=(Geometria.CIRCULO, Geometria.RECTA),
            confianza=None,
            detalle=(
                "sin decisión automática; el clasificador no devolvió "
                "evidencia; el operador debe elegir"
            ),
        )

    if evidencia.geometria is None:
        # Criterio 3: falla cerrado. Se reportan ambos candidatos con la
        # confianza y la evidencia numérica; no se elige una rama.
        return PlanGeometria(
            geometria=None,
            etapas=(),
            origen=ORIGEN_INDETERMINADO,
            candidatos=evidencia.candidatos,
            confianza=evidencia.confianza,
            detalle=(
                f"sin decisión automática; {_evidencia_texto(evidencia)}; "
                f"el operador debe elegir"
            ),
        )

    geometria_auto = evidencia.geometria
    etapas = _etapas_de(geometria_auto)
    return PlanGeometria(
        geometria=geometria_auto,
        etapas=etapas,
        origen=ORIGEN_AUTOMATICO,
        candidatos=evidencia.candidatos,
        confianza=evidencia.confianza,
        detalle=(
            f"autodetección: {_nombre(geometria_auto)}; "
            f"{_evidencia_texto(evidencia)}; etapas {_etapas_texto(etapas)}"
        ),
    )


def puntos_de_borde(mascara: np.ndarray) -> np.ndarray:
    """Extrae los puntos de borde `(x, y)` de una máscara 2D.

    `np.argwhere` devuelve `(fila, columna)`; se invierte a `(x, y)` para
    respetar la convención de los modelos de geometría.
    """
    mascara = np.asarray(mascara)
    if mascara.ndim != 2:
        raise ValueError("puntos_de_borde:: la máscara debe ser una matriz 2D")
    return np.argwhere(mascara > 0)[:, ::-1].astype(float)
