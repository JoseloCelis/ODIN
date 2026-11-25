"""Emparejamiento de orillas de un trazo a partir de los picos de Hough.

Funciones puras: NumPy (geometría, no UI). Sin gi, Gtk, Gdk, Adw ni cairo.
Identificadores, comentarios y docstrings en español.

El problema que resuelve: una candidata de Hough es una recta `(rho, theta)`.
Las dos orillas de un trazo son dos candidatas casi paralelas (misma theta) y
separadas en `rho`. Este módulo empareja esas candidatas y asigna cada punto de
borde a la orilla más cercana de su par, sin cotas de distancia en px: la
pertenencia la decide el vecino más cercano entre las candidatas ya detectadas.

No se supone nada sobre los trazos: cuántos hay, cuánto miden y cómo se separan
cambia de una imagen a otra y entre trazos de la misma imagen. El ancho de un
trazo es justamente lo que se quiere medir, así que ninguna constante en px
puede describirlo; la única ventana admisible es la que aporta el propio dato
(la semianchura del pico de cada orilla).
"""

from __future__ import annotations

import numpy as np

from .hough_lineas import PASO_RHO, PERCENT_MIN

# Tolerancia angular para considerar dos candidatas paralelas. Justificación: las
# orillas reales de un trazo son casi paralelas y el acumulador cuantiza theta en
# `pi/360` (0.0087 rad); 0.1 rad cubre el error de cuantización con margen amplio
# sin llegar a mezclar direcciones visiblemente distintas.
TOLERANCIA_THETA: float = 0.1

# Separación mínima en `rho` para que dos candidatas sean orillas distintas y no
# el mismo borde contado dos veces. Un trazo tiene ancho positivo, y por debajo
# de este valor la diferencia cae dentro del ancho del pico del acumulador.
SEPARACION_MINIMA: float = 5.0


def _como_array(valor: np.ndarray | list[float], nombre: str) -> np.ndarray:
    """Normaliza a un array 1D de flotantes y valida que no esté vacío por forma."""
    arreglo = np.asarray(valor, dtype=float).ravel()
    if arreglo.ndim != 1:
        raise ValueError(f"pares_orillas::{nombre} debe ser un array 1D")
    return arreglo


def picos_de_rho(
    puntos: np.ndarray,
    theta: float,
    paso: float = PASO_RHO,
    percent: float = PERCENT_MIN,
) -> tuple[np.ndarray, np.ndarray]:
    """Máximos locales del perfil de `rho` de los puntos proyectados sobre `theta`.

    Con `theta` fijo, la coordenada normal de cada punto es
    `rho = x·cos(theta) + y·sin(theta)`. El histograma de esos valores es la
    columna del acumulador de Hough para ese ángulo, así que sus máximos locales
    son las rectas paralelas a `theta` que sostienen los bordes: las orillas de
    los trazos, a la resolución de un bin y sin depender del agrupamiento de
    `candidatas_lineas` (que fusiona picos a menos de 30 px y por eso no puede
    separar las dos orillas de un trazo fino).

    Parámetros:
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        theta (float): Ángulo de la normal, en rad.
        paso (float): Ancho del bin en `rho`, en px; por defecto el paso del
            acumulador de Hough.
        percent (float): Fracción del pico máximo que actúa como umbral, en
            `[0.6, 0.9]`; el mismo criterio relativo que usa `candidatas_lineas`.

    Retorna:
        tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]: `rhos`, `conteos` y
        `semianchuras` de cada máximo local, ordenados por `rho` ascendente. La
        semianchura es la mitad del ancho del pico a media altura (HWHM) en px,
        es decir el soporte real de esa orilla en el perfil; es lo que permite
        rechazar la textura que no sostiene ningún pico sin fijar una cota.
        Vacíos si el perfil no tiene máximos por encima del umbral.
    """
    puntos = np.asarray(puntos, dtype=float)
    if puntos.ndim != 2 or puntos.shape[1] != 2:
        raise ValueError("pares_orillas:: puntos debe tener forma (N, 2)")
    if not 0.6 <= percent <= 0.9:
        raise ValueError("pares_orillas:: percent debe estar en [0.6, 0.9]")
    if puntos.shape[0] == 0:
        vacio = np.empty(0, dtype=float)
        return vacio, vacio.copy(), vacio.copy()

    proyeccion = puntos[:, 0] * np.cos(theta) + puntos[:, 1] * np.sin(theta)
    indices = np.rint(proyeccion / paso).astype(np.int64)
    desplazamiento = int(indices.min())
    perfil = np.bincount(indices - desplazamiento).astype(float)

    # Se rellena con un bin nulo a cada lado para que el primer y el último bin
    # del perfil también puedan ser máximos locales: si no, se perdería la
    # orilla que coincide con el extremo del rango de rho.
    extendido = np.concatenate(([0.0], perfil, [0.0]))
    umbral = percent * float(perfil.max())
    es_pico = (
        (extendido[1:-1] > extendido[:-2])
        & (extendido[1:-1] >= extendido[2:])
        & (extendido[1:-1] >= umbral)
    )
    if not np.any(es_pico):
        vacio = np.empty(0, dtype=float)
        return vacio, vacio.copy(), vacio.copy()

    # Un borde real puede partirse en dos bins contiguos por la cuantización
    # del voto; se conserva el de mayor conteo para no contar la misma orilla
    # dos veces.
    posiciones: list[int] = []
    for posicion in np.flatnonzero(es_pico).tolist():
        if posiciones and posicion == posiciones[-1] + 1:
            if perfil[posicion] > perfil[posiciones[-1]]:
                posiciones[-1] = posicion
            continue
        posiciones.append(posicion)

    arreglo = np.asarray(posiciones, dtype=np.int64)

    # Semianchura a media altura de cada pico: se camina desde el pico mientras el
    # perfil no baje de la mitad de su altura. Un borde nítido da una semianchura
    # de un bin; un borde inclinado o desenfocado la da mayor, así que la ventana
    # se adapta a cada orilla y a cada imagen sin constantes en px.
    semianchuras = np.empty(arreglo.size, dtype=float)
    for indice, posicion in enumerate(arreglo.tolist()):
        mitad = perfil[posicion] / 2.0
        izquierda = posicion
        while izquierda > 0 and perfil[izquierda - 1] >= mitad:
            izquierda -= 1
        derecha = posicion
        while derecha < perfil.size - 1 and perfil[derecha + 1] >= mitad:
            derecha += 1
        semianchuras[indice] = max(posicion - izquierda, derecha - posicion, 1) * paso

    rhos = (arreglo + desplazamiento) * paso
    return rhos, perfil[arreglo], semianchuras


def distancias_perpendiculares(
    puntos: np.ndarray,
    rhos: np.ndarray,
    thetas: np.ndarray,
) -> np.ndarray:
    """Distancia perpendicular de cada punto a cada candidata.

    Calcula `|x·cos(theta) + y·sin(theta) - rho|`, la definición de distancia de
    una recta en coordenadas normales.

    Parámetros:
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        rhos (numpy.ndarray): `(K,)` rho de cada candidata, en px.
        thetas (numpy.ndarray): `(K,)` theta de cada candidata, en rad.

    Retorna:
        numpy.ndarray: Matriz `(N, K)` de distancias, en px.
    """
    puntos = np.asarray(puntos, dtype=float)
    if puntos.ndim != 2 or puntos.shape[1] != 2:
        raise ValueError("pares_orillas:: puntos debe tener forma (N, 2)")
    rhos = _como_array(rhos, "rhos")
    thetas = _como_array(thetas, "thetas")
    if rhos.shape != thetas.shape:
        raise ValueError("pares_orillas:: rhos y thetas deben tener la misma longitud")
    if puntos.shape[0] == 0:
        return np.empty((0, rhos.size), dtype=float)

    coseno = np.cos(thetas)
    seno = np.sin(thetas)
    proyeccion = puntos[:, 0:1] * coseno[None, :] + puntos[:, 1:2] * seno[None, :]
    return np.abs(proyeccion - rhos[None, :])


def emparejar_orillas(
    rhos: np.ndarray,
    thetas: np.ndarray,
    conteos: np.ndarray | None = None,
) -> list[tuple[int, int]]:
    """Empareja las candidatas de Hough que forman las orillas de un mismo trazo.

    Cada candidata se empareja con su **vecina más cercana en rho** entre las que
    cumplen las dos condiciones de orilla:

        - `|theta_i - theta_j| < TOLERANCIA_THETA` (casi paralelas), y
        - `|rho_i - rho_j| >= SEPARACION_MINIMA` (bordes distintos).

    Emparejar con la vecina más cercana, y no con cualquier candidata compatible,
    evita cruzar orillas de trazos distintos: con cuatro picos paralelos en
    `rho = 0, 20, 200, 220` los pares son `(0, 20)` y `(200, 220)`, nunca
    `(0, 220)`.

    Parámetros:
        rhos (numpy.ndarray): `(K,)` rho de cada candidata, en px.
        thetas (numpy.ndarray): `(K,)` theta de cada candidata, en rad.
        conteos (numpy.ndarray | None): `(K,)` evidencia de cada candidata; se
            usa solo para ordenar el resultado.

    Retorna:
        list[tuple[int, int]]: Pares `(i, j)` con `i < j`, ordenados por
        evidencia combinada descendente; sin evidencia, por `rho` ascendente.
    """
    rhos = _como_array(rhos, "rhos")
    thetas = _como_array(thetas, "thetas")
    if rhos.shape != thetas.shape:
        raise ValueError("pares_orillas:: rhos y thetas deben tener la misma longitud")
    if conteos is not None:
        conteos = _como_array(conteos, "conteos")
        if conteos.shape != rhos.shape:
            raise ValueError("pares_orillas:: conteos debe tener la longitud de rhos")

    total = rhos.size
    pares: list[tuple[int, int]] = []
    vistos: set[tuple[int, int]] = set()

    for i in range(total):
        compatibles = [
            j
            for j in range(total)
            if j != i
            and abs(thetas[i] - thetas[j]) < TOLERANCIA_THETA
            and abs(rhos[i] - rhos[j]) >= SEPARACION_MINIMA
        ]
        if not compatibles:
            continue
        j = min(compatibles, key=lambda k: abs(rhos[i] - rhos[k]))
        par = (min(i, j), max(i, j))
        if par in vistos:
            continue
        vistos.add(par)
        pares.append(par)

    def clave(par: tuple[int, int]) -> tuple[float, float]:
        """Evidencia combinada del par; el rho menor desempata de forma estable."""
        evidencia = float(conteos[par[0]] + conteos[par[1]]) if conteos is not None else 0.0
        return (evidencia, -float(min(rhos[par[0]], rhos[par[1]])))

    pares.sort(key=clave, reverse=True)
    return pares


def asignar_puntos_a_orillas(
    puntos: np.ndarray,
    rhos: np.ndarray,
    thetas: np.ndarray,
    par: tuple[int, int],
    semianchuras: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Asigna cada punto de borde a una de las dos orillas del par.

    Un punto pertenece al par solo si su candidata más cercana —entre **todas**
    las candidatas, no solo las del par— es una de las dos orillas. Si su
    candidata más cercana es otra, el punto pertenece a otro trazo y se descarta.
    Dentro del par, se asigna a la orilla con menor distancia perpendicular.

    Parámetros:
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        rhos (numpy.ndarray): `(K,)` rho de todas las candidatas, en px.
        thetas (numpy.ndarray): `(K,)` theta de todas las candidatas, en rad.
        par (tuple[int, int]): Índices de las dos orillas.
        semianchuras (numpy.ndarray | None): `(K,)` semianchura a media altura de
            cada pico, en px. Si se pasa, un punto pertenece a una orilla solo si
            su distancia perpendicular no supera esa semianchura: así se descarta
            la textura que no sostiene el pico. Si es `None` no se acota.

    Retorna:
        tuple[numpy.ndarray, numpy.ndarray]: Dos máscaras booleanas de longitud
        `N`, una por orilla, con `True` en los puntos asignados. Son
        mutuamente excluyentes y preservan el orden de entrada, así que sirven
        para indexar también los gradientes del mismo tamaño.
    """
    puntos = np.asarray(puntos, dtype=float)
    distancias = distancias_perpendiculares(puntos, rhos, thetas)
    rhos = _como_array(rhos, "rhos")

    indice_a, indice_b = int(par[0]), int(par[1])
    if not 0 <= indice_a < rhos.size or not 0 <= indice_b < rhos.size:
        raise ValueError("pares_orillas:: el par debe referenciar candidatas existentes")

    if puntos.shape[0] == 0:
        vacia = np.zeros(0, dtype=bool)
        return vacia, vacia.copy()

    mas_cercana = np.argmin(distancias, axis=1)
    en_par = (mas_cercana == indice_a) | (mas_cercana == indice_b)

    distancia_a = distancias[:, indice_a]
    distancia_b = distancias[:, indice_b]
    mascara_a = en_par & (distancia_a <= distancia_b)
    mascara_b = en_par & (distancia_b < distancia_a)

    if semianchuras is not None:
        semianchuras = _como_array(semianchuras, "semianchuras")
        if semianchuras.shape != rhos.shape:
            raise ValueError("pares_orillas:: semianchuras debe tener la longitud de rhos")
        mascara_a = mascara_a & (distancia_a <= semianchuras[indice_a])
        mascara_b = mascara_b & (distancia_b <= semianchuras[indice_b])

    return mascara_a, mascara_b
