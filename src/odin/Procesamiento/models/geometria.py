"""Clasificador de geometría con evidencia y falla cerrado.

Modelo puro: NumPy puro, sin gi, Gtk, Gdk, Adw ni cairo. Recibe una nube de
puntos (N, 2) y propone `Geometria.CIRCULO` o `Geometria.RECTA` junto con su
confianza y la evidencia que la sustenta (spec migracion-lineas-geometria, S4).

Criterios de diseño (bloque «T4 — criterios de diseño del clasificador»):

1. Residuales por mediana. La recta se ajusta por PCA/SVD y el círculo por el
   ajuste algebraico de Kåsa consumido por el alias público `odin.Ajustes.LSC`.
   Se usa la mediana, no la media, para que un puñado de puntos sueltos no
   decida.
2. Admisibilidad del círculo. Si `radio > factor_radio_max · extensión` o el
   radio no es finito, el residual del círculo pasa a `inf`. Sin este paso
   toda recta es un círculo de radio enorme y el clasificador elegiría
   círculo siempre.
3. Confianza `(peor - mejor) / peor`, con `1.0` cuando el peor es infinito y
   `0.0` cuando ambos lo son.
4. Falla cerrado. `confianza < umbral_confianza` ⇒ `geometria=None` y se
   exponen ambos candidatos para que el operador decida.
5. Degenerados no lanzan. Menos de 3 puntos, valores no finitos o duplicados
   devuelven confianza `0` con ambos candidatos. Un conjunto puramente
   colineal no es degenerado: el criterio 2 lo deja sin círculo admisible y
   se clasifica como recta.

Decisiones de interpretación (reportadas al orquestador):

- `extensión` es la diagonal de la caja envolvente en el marco de componentes
  principales, que es invariante ante rotación y reflexión rígidas.
- `tolerancia_px` es la extensión mínima clasificable: un conjunto confinado a
  menos de esa distancia no tiene geometría determinable.
- `candidatos` es `(geometria,)` cuando hay decisión y `(CIRCULO, RECTA)`
  cuando se falla cerrado.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Final

import numpy as np

from odin.Ajustes import LSC, cobertura_angular

UMBRAL_CONFIANZA: Final = 0.75
TOLERANCIA_PX: Final = 2.0
FACTOR_RADIO_MAX: Final = 4.0


class Geometria(Enum):
    """Geometrías candidatas que el clasificador puede proponer."""

    CIRCULO = "circulo"
    RECTA = "recta"


@dataclass(frozen=True, slots=True)
class EvidenciaGeometria:
    """Evidencia que sustenta la geometría propuesta.

    `geometria` es `None` cuando la confianza queda por debajo del umbral y el
    clasificador falla cerrado. `candidatos` expone la decisión o, si no hay
    decisión, ambas geometrías para que el operador elija.
    """

    geometria: Geometria | None
    confianza: float
    candidatos: tuple[Geometria, ...]
    residual_recta: float
    residual_circulo: float
    cobertura_angular: float
    radio: float | None
    detalle: str


def _motivo_degenerado(arreglo: np.ndarray) -> str | None:
    """Motivo de degeneración de la entrada, o `None` si es clasificable."""
    if arreglo.ndim != 2 or arreglo.shape[1] != 2:
        return "la entrada debe ser una matriz (N, 2) de coordenadas (x, y)"
    if arreglo.shape[0] < 3:
        return f"se necesitan al menos 3 puntos; se recibieron {arreglo.shape[0]}"
    if not np.all(np.isfinite(arreglo)):
        return "la entrada contiene valores no finitos (nan o inf)"
    if np.unique(arreglo, axis=0).shape[0] < 3:
        return "la entrada tiene menos de 3 puntos distintos (duplicados)"
    return None


def _resultado_degenerado(motivo: str) -> EvidenciaGeometria:
    """Evidencia neutra para una entrada que no se puede clasificar."""
    return EvidenciaGeometria(
        geometria=None,
        confianza=0.0,
        candidatos=(Geometria.CIRCULO, Geometria.RECTA),
        residual_recta=math.inf,
        residual_circulo=math.inf,
        cobertura_angular=0.0,
        radio=None,
        detalle=f"entrada degenerada: {motivo}",
    )


def clasificar_geometria(
    puntos: np.ndarray,
    *,
    umbral_confianza: float = UMBRAL_CONFIANZA,
    tolerancia_px: float = TOLERANCIA_PX,
    factor_radio_max: float = FACTOR_RADIO_MAX,
) -> EvidenciaGeometria:
    """Propone la geometría de una nube de puntos con confianza y evidencia.

    Parameters:
        puntos: matriz (N, 2) de coordenadas (x, y). No se modifica.
        umbral_confianza: confianza mínima para decidir; por debajo se falla
            cerrado exponiendo ambos candidatos.
        tolerancia_px: extensión mínima clasificable, en píxeles.
        factor_radio_max: el círculo deja de ser admisible cuando su radio
            supera este factor por la extensión del conjunto.

    Returns:
        `EvidenciaGeometria` con la geometría propuesta (o `None`), la
        confianza, los candidatos, los residuales por mediana, la cobertura
        angular, el radio ajustado y un detalle en español.

    Nota:
        Nunca lanza excepción: las entradas degeneradas devuelven confianza `0`
        con ambos candidatos.
    """
    try:
        arreglo = np.asarray(puntos, dtype=float)
    except (TypeError, ValueError):
        return _resultado_degenerado("la entrada no es una matriz numérica (N, 2)")

    motivo = _motivo_degenerado(arreglo)
    if motivo is not None:
        return _resultado_degenerado(motivo)

    # Recta por PCA/SVD: el residual es la mediana de las distancias
    # perpendiculares a la dirección de mínima varianza.
    centroide = arreglo.mean(axis=0)
    centrado = arreglo - centroide
    _, _, vh = np.linalg.svd(centrado, full_matrices=False)
    normal = vh[-1]
    distancias_recta = np.abs(centrado @ normal)
    residual_recta = float(np.median(distancias_recta))

    # Extensión invariante ante rotación y reflexión: diagonal de la caja
    # envolvente medida en el marco de componentes principales.
    rotado = centrado @ vh.T
    extension = float(np.hypot(np.ptp(rotado[:, 0]), np.ptp(rotado[:, 1])))
    if extension <= tolerancia_px:
        return _resultado_degenerado(
            f"la extensión ({extension:.3f}px) no supera la tolerancia "
            f"({tolerancia_px:.3f}px)"
        )

    # Círculo por el ajuste algebraico del dominio Ajustes. Si el ajuste no es
    # posible (colinealidad exacta, por ejemplo), el residual pasa a infinito.
    radio: float | None = None
    centro_circulo: tuple[float, float] | None = None
    residual_circulo = math.inf
    try:
        # El ajuste algebraico de Kåsa no es invariante ante traslación: sus
        # ecuaciones normales usan las coordenadas absolutas, así que mover la
        # nube puede cambiar el radio y con él la decisión. Se ajusta sobre la
        # nube ya centrada y se devuelve el centro al marco original.
        x_local, y_local, r, _pv = LSC(centrado)
        x_c = float(x_local) + centroide[0]
        y_c = float(y_local) + centroide[1]
        radio = float(r)
        centro_circulo = (x_c, y_c)
        distancias_circulo = np.hypot(arreglo[:, 0] - x_c, arreglo[:, 1] - y_c)
        residual_circulo = float(np.median(np.abs(distancias_circulo - r)))
    except (ValueError, TypeError, np.linalg.LinAlgError):
        radio = None
        centro_circulo = None
        residual_circulo = math.inf

    # Criterio 2: admisibilidad del círculo.
    if radio is None or not math.isfinite(radio) or radio > factor_radio_max * extension:
        residual_circulo = math.inf

    # Criterio 3: confianza como separación relativa de residuales.
    mejor = min(residual_recta, residual_circulo)
    peor = max(residual_recta, residual_circulo)
    if math.isinf(peor) and math.isinf(mejor):
        confianza = 0.0
    elif math.isinf(peor):
        confianza = 1.0
    elif peor <= 0.0:
        confianza = 0.0
    else:
        confianza = (peor - mejor) / peor
    confianza = float(min(1.0, max(0.0, confianza)))

    if centro_circulo is None:
        cobertura = 0.0
    else:
        cobertura, _hueco = cobertura_angular(arreglo, centro_circulo)

    # Criterio 4: falla cerrado.
    if confianza < umbral_confianza:
        return EvidenciaGeometria(
            geometria=None,
            confianza=confianza,
            candidatos=(Geometria.CIRCULO, Geometria.RECTA),
            residual_recta=residual_recta,
            residual_circulo=residual_circulo,
            cobertura_angular=cobertura,
            radio=radio,
            detalle=(
                f"confianza {confianza:.3f} por debajo del umbral "
                f"{umbral_confianza:.2f}; se exponen ambos candidatos"
            ),
        )

    geometria = Geometria.CIRCULO if residual_circulo < residual_recta else Geometria.RECTA
    if geometria is Geometria.CIRCULO:
        radio_texto = f"{radio:.2f}" if radio is not None else "no finito"
        detalle = (
            f"círculo admitido (radio {radio_texto}px, "
            f"cobertura {cobertura:.1%}); confianza {confianza:.3f}"
        )
    else:
        detalle = f"recta (residual {residual_recta:.3f}px); confianza {confianza:.3f}"

    return EvidenciaGeometria(
        geometria=geometria,
        confianza=confianza,
        candidatos=(geometria,),
        residual_recta=residual_recta,
        residual_circulo=residual_circulo,
        cobertura_angular=cobertura,
        radio=radio,
        detalle=detalle,
    )
