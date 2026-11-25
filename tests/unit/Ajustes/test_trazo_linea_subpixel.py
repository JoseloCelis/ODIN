"""Tests para el refinamiento subpíxel de bordes y medición de trazo grueso."""

import numpy as np
import pytest

from src.odin.Ajustes.models.trazo_linea import (
    refinar_bordes_subpixel,
    medir_trazo,
    MedicionTrazo,
)


def test_refinamiento_con_picos_fraccionarios():
    """Test con bordes sintéticos que tienen picos en posiciones fraccionarias."""
    # Crear imagen con dos orillas definidas a 10.5 y 30.5 px
    alto, ancho = 50, 50
    magnitud = np.zeros((alto, ancho))
    
    # Crear picos gaussianos en x=10.5 y x=30.5
    for y in range(alto):
        for x in range(ancho):
            # Pico en x=10.5
            magnitud[y, x] += np.exp(-((x - 10.5)**2 + (y - 25)**2) / 2)
            # Pico en x=30.5
            magnitud[y, x] += np.exp(-((x - 30.5)**2 + (y - 25)**2) / 2)
    
    # Puntos de borde enteros (iniciales)
    puntos = np.array([
        [10, 25],  # Cerca del primer pico
        [30, 25],  # Cerca del segundo pico
    ], dtype=float)
    
    # Gradientes apuntando hacia la derecha (simulando bordes verticales)
    gx = np.array([1.0, 1.0])
    gy = np.array([0.0, 0.0])
    
    # Refinar bordes
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    
    # Verificar que los puntos se han movido cerca de las posiciones fraccionarias
    assert puntos_refinados[0, 0] == pytest.approx(10.5, abs=0.2)
    assert puntos_refinados[1, 0] == pytest.approx(30.5, abs=0.2)
    
    # Las coordenadas y no deberían cambiar mucho
    assert puntos_refinados[0, 1] == pytest.approx(25.0, abs=0.1)
    assert puntos_refinados[1, 1] == pytest.approx(25.0, abs=0.1)


def test_sin_refinamiento_con_gradiente_nulo():
    """Puntos con gradiente nulo no deben refinarse."""
    alto, ancho = 10, 10
    magnitud = np.ones((alto, ancho))
    puntos = np.array([[5.0, 5.0]])
    gx = np.array([0.0])
    gy = np.array([0.0])
    
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    
    # Deben permanecer sin cambios
    assert np.allclose(puntos_refinados, puntos)


def test_sin_refinamiento_con_pico_plano():
    """Picos planos (denominador cercano a cero) no deben refinarse."""
    alto, ancho = 10, 10
    magnitud = np.ones((alto, ancho))  # Todos los valores iguales
    puntos = np.array([[5.0, 5.0]])
    gx = np.array([1.0])
    gy = np.array([0.0])
    
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    
    # Deben permanecer sin cambios
    assert np.allclose(puntos_refinados, puntos)


def test_muestreo_en_bordes_de_imagen():
    """No debe haber errores al muestrear cerca de los bordes."""
    alto, ancho = 10, 10
    magnitud = np.random.rand(alto, ancho)
    puntos = np.array([
        [0.0, 0.0],      # Esquina
        [ancho-1, alto-1]  # Esquina opuesta
    ])
    gx = np.array([1.0, -1.0])
    gy = np.array([0.0, 0.0])
    
    # Esto no debe lanzar excepción
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    
    # Solo verificamos que se ejecutó sin errores
    assert puntos_refinados.shape == (2, 2)


def test_no_regresion_con_coordenadas_enteras():
    """Con coordenadas enteras y gradientes consistentes, el resultado debe ser estable."""
    alto, ancho = 20, 20
    magnitud = np.zeros((alto, ancho))
    
    # Crear un borde vertical claro en x=10
    magnitud[:, 10] = 1.0
    
    # Puntos en el borde
    puntos = np.array([
        [10, 5],
        [10, 10],
        [10, 15]
    ], dtype=float)
    
    # Gradientes horizontales
    gx = np.array([1.0, 1.0, 1.0])
    gy = np.array([0.0, 0.0, 0.0])
    
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    
    # Los puntos no deberían moverse mucho ya que están bien posicionados
    assert np.all(np.abs(puntos_refinados[:, 0] - 10.0) < 0.5)
    assert np.allclose(puntos_refinados[:, 1], puntos[:, 1])  # y no cambia

    
def test_validacion_de_formas():
    """Las formas de los arrays deben ser validadas correctamente."""
    alto, ancho = 10, 10
    magnitud = np.ones((alto, ancho))
    puntos = np.array([[5.0, 5.0]])
    gx = np.array([1.0, 2.0])  # Incorrecto: longitud diferente
    gy = np.array([0.0])
    
    with pytest.raises(ValueError, match="misma longitud"):
        refinar_bordes_subpixel(puntos, gx, gy, magnitud)


def test_validacion_de_magnitud_2d():
    """La magnitud debe ser una imagen 2D."""
    puntos = np.array([[5.0, 5.0]])
    gx = np.array([1.0])
    gy = np.array([0.0])
    magnitud = np.array([1.0])  # 1D array
    
    with pytest.raises(ValueError, match="magnitud debe ser una imagen 2D"):
        refinar_bordes_subpixel(puntos, gx, gy, magnitud)


# ---------------------------------------------------------------------------
# Tests de convergencia del pipeline completo: refinar_bordes_subpixel + medir_trazo
# ---------------------------------------------------------------------------

def _crear_trazo_sintetico(
    x_izq: float,
    x_der: float,
    y_centro: float = 50.0,
    largo: float = 20.0,
    sigma_x: float = 1.0,
    sigma_y: float = 5.0,
    alto: int = 100,
    ancho: int = 100,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Crea una imagen sintética con un trazo grueso (dos orillas paralelas).

    Returns:
        (magnitud, puntos_iniciales, gx, gy)
    """
    magnitud = np.zeros((alto, ancho))
    
    # Dos bordes verticales en x_izq y x_der
    y_inicio = int(y_centro - largo / 2)
    y_fin = int(y_centro + largo / 2)
    
    for y in range(max(0, y_inicio), min(alto, y_fin)):
        for x in range(ancho):
            # Orilla izquierda (gradiente hacia la derecha -> gx positivo)
            magnitud[y, x] += np.exp(-((x - x_izq)**2 / (2 * sigma_x**2) + (y - y_centro)**2 / (2 * sigma_y**2)))
            # Orilla derecha (gradiente hacia la izquierda -> gx negativo)
            magnitud[y, x] += np.exp(-((x - x_der)**2 / (2 * sigma_x**2) + (y - y_centro)**2 / (2 * sigma_y**2)))
    
    # Puntos iniciales enteros a lo largo de ambas orillas
    y_coords = np.arange(y_inicio, y_fin, 1.0)
    puntos_izq = np.column_stack([np.full_like(y_coords, round(x_izq)), y_coords])
    puntos_der = np.column_stack([np.full_like(y_coords, round(x_der)), y_coords])
    puntos = np.vstack([puntos_izq, puntos_der]).astype(float)
    
    # Gradientes: orilla izquierda -> derecha (positivo), orilla derecha -> izquierda (negativo)
    gx_izq = np.ones(len(y_coords))
    gx_der = -np.ones(len(y_coords))
    gx = np.concatenate([gx_izq, gx_der])
    gy = np.zeros(len(puntos))
    
    return magnitud, puntos, gx, gy


def test_convergencia_ancho_trazo_fraccionario():
    """El ancho medido converge al valor real con tolerancia ±0.2 px.

    Crea un trazo sintético con orillas en x=20.5 y x=41.0 (separación 20.5 px),
    ejecuta el pipeline completo (refinar_bordes_subpixel + medir_trazo) y
    verifica que el ancho medido está dentro de ±0.2 px del valor real.
    """
    ancho_real = 20.5
    magnitud, puntos, gx, gy = _crear_trazo_sintetico(
        x_izq=20.5, x_der=41.0, y_centro=50.0, largo=20.0
    )
    
    # Pipeline completo: refinar -> medir
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    theta = 0.0  # Trazo vertical
    medicion = medir_trazo(puntos_refinados, gx, gy, theta)
    
    assert isinstance(medicion, MedicionTrazo), "La medición no debería ser None"
    assert medicion.ancho == pytest.approx(ancho_real, abs=0.2), (
        f"Ancho medido {medicion.ancho:.3f} px, esperado {ancho_real} px ±0.2"
    )


def test_no_regresion_orillas_enteras():
    """Con orillas en coordenadas enteras exactas, el resultado no cambia.

    Crea un trazo con orillas en x=20.0 y x=40.0 (separación 20.0 px exacta),
    verifica que el ancho medido sea 20.0 ± 0.2 px (no regresión).
    """
    ancho_real = 20.0
    magnitud, puntos, gx, gy = _crear_trazo_sintetico(
        x_izq=20.0, x_der=40.0, y_centro=50.0, largo=20.0
    )
    
    # Pipeline completo
    puntos_refinados = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    theta = 0.0
    medicion = medir_trazo(puntos_refinados, gx, gy, theta)
    
    assert isinstance(medicion, MedicionTrazo)
    assert medicion.ancho == pytest.approx(ancho_real, abs=0.2), (
        f"Regresión: ancho medido {medicion.ancho:.3f} px, esperado {ancho_real} px ±0.2"
    )

def test_el_desplazamiento_queda_acotado_al_intervalo_de_la_parabola():
    """El vértice se acota a ±0.5 px: fuera del intervalo muestreado no hay pico único.

    Con m0=0.0, m1=0.1 y m2=1.0 el vértice de la parábola cae en -0.625, fuera
    del intervalo [-1, 1] que define a sus tres muestras. Sin la cota el punto
    salta 0.625 px y, en la imagen real, hasta 125 px (plateaus y segundas
    orillas), arrastrando el ajuste SVD de la orilla.
    """
    magnitud = np.zeros((5, 5))
    magnitud[2, 1] = 0.0
    magnitud[2, 2] = 0.1
    magnitud[2, 3] = 1.0

    puntos = np.array([[2.0, 2.0]])
    gx = np.array([1.0])
    gy = np.array([0.0])

    refinado = refinar_bordes_subpixel(puntos, gx, gy, magnitud)
    desplazamiento = float(np.hypot(refinado[0, 0] - 2.0, refinado[0, 1] - 2.0))

    assert desplazamiento <= 0.5 + 1e-12, (
        f"desplazamiento {desplazamiento:.4f} px excede el intervalo de la parábola"
    )
    assert refinado[0, 0] == pytest.approx(1.5, abs=1e-9)
    assert refinado[0, 1] == pytest.approx(2.0, abs=1e-9)
