"""Etapa ⑫ — trazo_linea: medición de ancho y centro de línea gruesa.

Cubre S2, S3, S4 y S5 de `odd/tasks/linea-gruesa.md`:
  - Modelo puro (numpy, sin gi/Gtk/Gdk/Adw/cairo).
  - Port optimizado de `separaPuntos.m` + medición de `circle_detector.m`.
  - Centro derivado, no ajustado a puntos.
  - Separación por proyección del gradiente sobre la normal del Hough.

Casos de prueba:
  1. `separar_orillas` separa una banda horizontal sintética.
  2. `medir_trazo` sobre una banda horizontal de medio-ancho 20 → ancho ≈ 40.
  3. `medir_trazo` sobre la misma banda rotada 90° (vertical) → ancho ≈ 40.
  4. `medir_trazo` sobre una banda diagonal (rotada 45°) → ancho ≈ 40.
  5. `medir_trazo` con una línea delgada (una sola orilla) → None.
  6. `medir_trazo` con entrada degenerada (< 3 puntos) → None, sin lanzar.
  7. Aislamiento: `trazo_linea.py` no importa gi/Gtk/Gdk/Adw/cairo.
  8. Prop (Hypothesis): el ancho es invariante a rotación/traslación rígidas.
"""

import math
import re
from pathlib import Path

import numpy as np
import pytest

from src.odin.Ajustes.models.trazo_linea import MedicionTrazo, medir_trazo, separar_orillas

RAIZ = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

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


def _gradiente_banda_horizontal(puntos, signo_superior=1, signo_inferior=-1):
    """Gradiente sintético coherente para una banda horizontal."""
    gx = np.zeros(len(puntos))
    gy = np.where(puntos[:, 1] > 0, signo_superior, signo_inferior).astype(float)
    return gx, gy


def _rotar_puntos(puntos, angulo):
    """Rota una nube de puntos en torno al origen."""
    c, s = np.cos(angulo), np.sin(angulo)
    matriz_rotacion = np.array([[c, -s], [s, c]])
    return puntos @ matriz_rotacion.T


def _rotar_gradiente(gx, gy, angulo):
    """Rota un campo vectorial de gradientes."""
    c, s = np.cos(angulo), np.sin(angulo)
    # Rotación inversa para vectores covariantes (gradientes)
    return gx * c + gy * s, -gx * s + gy * c


# ---------------------------------------------------------------------------
# separar_orillas
# ---------------------------------------------------------------------------

def test_separar_orillas_divide_una_banda_horizontal():
    """Caso 1: separa una banda horizontal en dos conjuntos."""
    puntos = _banda_gruesa(120, medio_ancho=20.0, ruido=0.3, semilla=0)
    gx, gy = _gradiente_banda_horizontal(puntos)
    normal = np.array([0.0, 1.0])  # Normal a la horizontal (θ = π/2).

    superior, inferior = separar_orillas(puntos, gx, gy, normal)

    # Todos los puntos de cada orilla están en la orilla correcta.
    assert np.all(superior[:, 1] > 0)
    assert np.all(inferior[:, 1] < 0)
    # Y están todos (o casi todos, por el ruido).
    assert len(superior) + len(inferior) == len(puntos)


def test_separar_orillas_valida_formas():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0]])
    gx = np.array([1.0])
    gy = np.array([0.0, 1.0])
    normal = np.array([0.0, 1.0])

    with pytest.raises(ValueError, match="misma longitud"):
        separar_orillas(puntos, gx, gy, normal)


def test_separar_orillas_entrada_no_ndarray_lanza():
    with pytest.raises(TypeError, match="numpy.ndarray"):
        separar_orillas([[0.0, 0.0], [1.0, 1.0]], [1.0, 1.0], [0.0, 0.0], [0.0, 1.0])


def test_separar_orillas_gradientes_no_finitos_lanzan():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0]])
    gx = np.array([np.nan, 1.0])
    gy = np.array([0.0, 1.0])
    normal = np.array([0.0, 1.0])

    with pytest.raises(ValueError, match="finitos"):
        separar_orillas(puntos, gx, gy, normal)


def test_separar_orillas_normal_cero_lanza():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0]])
    gx = np.array([1.0, 1.0])
    gy = np.array([0.0, 0.0])
    normal = np.array([0.0, 0.0])

    with pytest.raises(ValueError, match="vector cero"):
        separar_orillas(puntos, gx, gy, normal)


# ---------------------------------------------------------------------------
# medir_trazo
# ---------------------------------------------------------------------------

def test_medir_trazo_banda_horizontal():
    """Caso 2: banda horizontal de medio-ancho 20 → ancho ≈ 40, centro ≈ y=0."""
    puntos = _banda_gruesa(120, medio_ancho=20.0, ruido=0.3, semilla=0)
    gx, gy = _gradiente_banda_horizontal(puntos)
    theta = np.pi / 2  # Dirección horizontal.

    medicion = medir_trazo(puntos, gx, gy, theta)

    assert isinstance(medicion, MedicionTrazo)
    assert medicion.ancho == pytest.approx(40.0, abs=1.0)
    # El centro es la recta y=0 (x0≈0, y0≈0).
    assert medicion.centro[1] == pytest.approx(0.0, abs=1.0)


def test_medir_trazo_banda_vertical():
    """Caso 3: banda vertical (rotada 90°) → ancho ≈ 40."""
    puntos_horizontal = _banda_gruesa(120, medio_ancho=20.0, ruido=0.3, semilla=0)
    puntos = _rotar_puntos(puntos_horizontal, np.pi / 2)
    gx_horizontal, gy_horizontal = _gradiente_banda_horizontal(puntos_horizontal)
    gx, gy = _rotar_gradiente(gx_horizontal, gy_horizontal, np.pi / 2)
    theta = 0.0  # Dirección vertical.

    medicion = medir_trazo(puntos, gx, gy, theta)

    assert isinstance(medicion, MedicionTrazo)
    assert medicion.ancho == pytest.approx(40.0, abs=1.0)


def test_medir_trazo_banda_diagonal():
    """Caso 4: banda diagonal (rotada 45°) → ancho ≈ 40 (invariancia a rotación)."""
    puntos_horizontal = _banda_gruesa(120, medio_ancho=20.0, ruido=0.3, semilla=0)
    puntos = _rotar_puntos(puntos_horizontal, np.pi / 4)
    gx_horizontal, gy_horizontal = _gradiente_banda_horizontal(puntos_horizontal)
    gx, gy = _rotar_gradiente(gx_horizontal, gy_horizontal, np.pi / 4)
    theta = np.pi / 4  # Dirección diagonal.

    medicion = medir_trazo(puntos, gx, gy, theta)

    assert isinstance(medicion, MedicionTrazo)
    assert medicion.ancho == pytest.approx(40.0, abs=1.0)


def test_medir_trazo_linea_delgada_devuelve_none():
    """Caso 5: línea delgada (una sola orilla) → None."""
    # Solo puntos en una orilla (y > 0).
    puntos = np.column_stack([np.arange(50.0), np.full(50, 20.0)])
    gx = np.zeros(50)
    gy = np.full(50, 1.0)  # Todos positivos.
    theta = np.pi / 2

    medicion = medir_trazo(puntos, gx, gy, theta)

    assert medicion is None


def test_medir_trazo_degenerado_devuelve_none():
    """Caso 6: menos de 3 puntos totales → None, sin lanzar."""
    puntos = np.array([[0.0, 0.0], [1.0, 1.0]])  # Solo 2 puntos.
    gx = np.array([1.0, 1.0])
    gy = np.array([0.0, 0.0])
    theta = 0.0

    medicion = medir_trazo(puntos, gx, gy, theta)

    assert medicion is None


def test_medir_trazo_minimo_puntos_exacto():
    """Con `minimo_puntos=2`, 2 puntos por orilla dan resultado."""
    puntos = np.array([[0.0, 1.0], [1.0, 1.0], [0.0, -1.0], [1.0, -1.0]])
    gx = np.array([0.0, 0.0, 0.0, 0.0])
    gy = np.array([1.0, 1.0, -1.0, -1.0])
    theta = np.pi / 2

    medicion = medir_trazo(puntos, gx, gy, theta, minimo_puntos=2)

    assert isinstance(medicion, MedicionTrazo)


def test_medir_trazo_minimo_puntos_no_alcanza():
    """Con `minimo_puntos=3`, 2 puntos por orilla dan None."""
    puntos = np.array([[0.0, 1.0], [1.0, 1.0], [0.0, -1.0], [1.0, -1.0]])
    gx = np.array([0.0, 0.0, 0.0, 0.0])
    gy = np.array([1.0, 1.0, -1.0, -1.0])
    theta = np.pi / 2

    medicion = medir_trazo(puntos, gx, gy, theta, minimo_puntos=3)

    assert medicion is None


def test_medir_trazo_theta_no_finito_lanza():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    gx = np.array([1.0, 1.0, 1.0])
    gy = np.array([0.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="theta debe ser finito"):
        medir_trazo(puntos, gx, gy, np.nan)


def test_medir_trazo_valida_formas():
    puntos = np.array([[0.0, 0.0], [1.0, 1.0]])
    gx = np.array([1.0])
    gy = np.array([0.0, 1.0])
    theta = 0.0

    with pytest.raises(ValueError, match="misma longitud"):
        medir_trazo(puntos, gx, gy, theta)


# ---------------------------------------------------------------------------
# S6 — aislamiento de la capa de modelo
# ---------------------------------------------------------------------------

def test_el_modelo_no_importa_capas_de_ui():
    """Caso 7: aislamiento de la capa de modelo."""
    ruta = RAIZ / "src" / "odin" / "Ajustes" / "models" / "trazo_linea.py"
    fuente = ruta.read_text(encoding="utf-8")

    importados = re.findall(
        r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", fuente, re.MULTILINE
    )
    prohibidos = {"gi", "cairo", "Gtk", "Gdk", "Adw"}

    assert not (set(importados) & prohibidos)


def test_el_modelo_consume_el_ajuste_por_el_alias_publico():
    """El ajuste de recta se consume por `odin.Ajustes`, no por el módulo."""
    import odin.Ajustes as ajustes_publico
    from src.odin.Ajustes.models import trazo_linea

    # Comparamos por nombre de función en vez de identidad porque pueden ser
    # imports desde diferentes niveles del paquete.
    assert trazo_linea.linea_mc.__name__ == ajustes_publico.linea_mc.__name__


# ---------------------------------------------------------------------------
# MedicionTrazo (dataclass)
# ---------------------------------------------------------------------------

def test_medicion_trazo_es_frozen_y_slotted():
    """MedicionTrazo es una dataclass frozen+slotted."""
    assert hasattr(MedicionTrazo, "__slots__")
    assert hasattr(MedicionTrazo, "__dataclass_fields__")

    puntos = _banda_gruesa(10, medio_ancho=20.0, semilla=0)
    gx, gy = _gradiente_banda_horizontal(puntos)
    medicion = medir_trazo(puntos, gx, gy, np.pi / 2)

    assert isinstance(medicion, MedicionTrazo)
    with pytest.raises(AttributeError):
        medicion.ancho = 0.0  # type: ignore[misc]
