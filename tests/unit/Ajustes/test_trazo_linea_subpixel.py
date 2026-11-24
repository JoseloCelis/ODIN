"""Tests para el refinamiento subpíxel de bordes."""

import numpy as np
import pytest

from src.odin.Ajustes.models.trazo_linea import refinar_bordes_subpixel


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
