"""Test de aceptación: el trazo se mide entre las orillas de su par (T4, S4)."""

import numpy as np

from src.odin.Ajustes.models.trazo_linea import medir_trazo
from src.odin.Procesamiento.models.pares_orillas import (
    asignar_puntos_a_orillas,
    emparejar_orillas,
    picos_de_rho,
)

ANCHO_TRAZO = 20.5
TOLERANCIA_PX = 0.2


def _trazo_vertical(x_inicial: float, alto: int = 100) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Orillas izquierda y derecha de un trazo vertical, con su gradiente.

    El gradiente apunta hacia +x: `-1` en la orilla izquierda y `+1` en la
    derecha, que es el signo del que se vale `separar_orillas`.
    """
    ys = np.arange(alto, dtype=float)
    orilla_izq = np.stack([np.full_like(ys, x_inicial), ys], axis=1)
    orilla_der = np.stack([np.full_like(ys, x_inicial + ANCHO_TRAZO), ys], axis=1)
    puntos = np.vstack([orilla_izq, orilla_der])
    gx = np.concatenate([np.full(alto, -1.0), np.full(alto, 1.0)])
    gy = np.zeros(puntos.shape[0], dtype=float)
    return puntos, gx, gy


def _escena_dos_trazos() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Un trazo en x=0 y otro a 200 px, ambos del mismo ancho."""
    primero = _trazo_vertical(0.0)
    segundo = _trazo_vertical(200.0)
    puntos = np.vstack([primero[0], segundo[0]])
    gx = np.concatenate([primero[1], segundo[1]])
    gy = np.concatenate([primero[2], segundo[2]])
    return puntos, gx, gy


def test_el_ancho_medido_es_el_del_trazo_y_no_el_de_la_escena():
    """S4: con dos trazos en la imagen, se mide el ancho de uno, no la distancia."""
    puntos, gx, gy = _escena_dos_trazos()
    theta = 0.0
    rhos_picos, conteos_picos = picos_de_rho(puntos, theta)
    thetas_picos = np.full(rhos_picos.shape, theta)
    pares = emparejar_orillas(rhos_picos, thetas_picos, conteos_picos)
    assert pares, "el sintético debe producir al menos un par de orillas"

    # Se mide el trazo que contiene la candidata principal (rho = 0).
    principal = int(np.argmin(np.abs(rhos_picos - 0.0)))
    par = next(p for p in pares if principal in p)
    mascara_a, mascara_b = asignar_puntos_a_orillas(puntos, rhos_picos, thetas_picos, par)
    mascara_par = mascara_a | mascara_b
    assert np.count_nonzero(mascara_par) >= 2

    medicion = medir_trazo(puntos[mascara_par], gx[mascara_par], gy[mascara_par], theta)

    assert medicion is not None
    assert abs(medicion.ancho - ANCHO_TRAZO) <= TOLERANCIA_PX


def _rho_medio(medicion) -> float:
    """rho medio entre las dos líneas ajustadas.

    Para `theta = 0` el rho de cada recta es la primera componente de su
    parámetro, que es justo la coordenada x de la orilla ajustada.
    """
    return float((medicion.linea_a[0] + medicion.linea_b[0]) / 2.0)


def test_el_centro_medido_cae_en_el_trazo_del_par():
    """S4: el centro medido está entre las dos orillas del trazo, no en la escena."""
    puntos, gx, gy = _escena_dos_trazos()
    theta = 0.0
    rhos_picos, conteos_picos = picos_de_rho(puntos, theta)
    thetas_picos = np.full(rhos_picos.shape, theta)
    pares = emparejar_orillas(rhos_picos, thetas_picos, conteos_picos)
    principal = int(np.argmin(np.abs(rhos_picos - 0.0)))
    par = next(p for p in pares if principal in p)
    mascara = np.zeros(puntos.shape[0], dtype=bool)
    for mascara_orilla in asignar_puntos_a_orillas(puntos, rhos_picos, thetas_picos, par):
        mascara |= mascara_orilla

    medicion = medir_trazo(puntos[mascara], gx[mascara], gy[mascara], theta)

    assert medicion is not None
    assert abs(_rho_medio(medicion) - ANCHO_TRAZO / 2.0) <= TOLERANCIA_PX


def test_sin_los_picos_el_centro_cae_entre_los_trazos():
    """S4: caracteriza el defecto que justifica la feature.

    Con la nube completa, `separar_orillas` promedia las orillas de los dos
    trazos y sitúa el centro a mitad de camino entre ambos.
    """
    puntos, gx, gy = _escena_dos_trazos()
    medicion = medir_trazo(puntos, gx, gy, 0.0)

    assert medicion is not None
    # Centro esperado del par: 10.25 px. Sin acotar cae cerca de 110 px.
    assert _rho_medio(medicion) > 100.0
