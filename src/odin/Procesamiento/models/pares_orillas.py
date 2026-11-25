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
        `semianchuras` de cada orilla, ordenados por `rho` ascendente. Una orilla
        es una región conexa del perfil por encima del umbral, no un máximo
        local: así un borde desenfocado, que reparte su gradiente en una rampa y
        produce varios máximos locales, cuenta como la orilla única que es. `rho`
        es el centroide de la región ponderado por votos, en px. La semianchura
        es la mitad del ancho de la región a media altura de su propio pico, en
        px: mide el desenfoque de esa orilla y es la ventana con la que se decide
        qué puntos le pertenecen, sin ninguna cota fija. Vacíos si el perfil no
        tiene regiones por encima del umbral.
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

    # Una orilla no es un máximo local: es una región conexa por encima del
    # umbral de ruido. Un borde nítido ocupa un bin; uno desenfocado ocupa una
    # rampa entera y produce varios máximos locales que son la MISMA orilla
    # (medido sobre 500mm_Imag0000.bmp, cuyas dos transiciones dan cinco picos
    # cada una). Agrupar por región y no por máximo local evita inventar orillas
    # donde solo hay desenfoque.
    # Un bin nulo entre dos bins con densidad no es un hueco del dato: los puntos
    # de borde tienen coordenadas enteras y el bin mide `paso`, así que la malla
    # de los puntos puede no coincidir con la del acumulador y dejar bins vacíos
    # alternados (sobre 500mm_Imag0000.bmp ocurre en todo el perfil). La densidad
    # es continua, así que ese bin se interpola con sus vecinos.
    hueco = np.zeros(perfil.size, dtype=bool)
    if perfil.size >= 3:
        hueco[1:-1] = (perfil[1:-1] == 0.0) & (perfil[:-2] > 0.0) & (perfil[2:] > 0.0)
        if np.any(hueco):
            perfil[hueco] = 0.5 * (perfil[:-2][hueco[1:-1]] + perfil[2:][hueco[1:-1]])

    umbral = percent * float(perfil.max())
    es_soporte = np.concatenate(([False], perfil >= umbral, [False]))
    cambios = np.flatnonzero(np.diff(es_soporte.astype(np.int8)))
    if cambios.size == 0:
        vacio = np.empty(0, dtype=float)
        return vacio, vacio.copy(), vacio.copy()

    inicios = cambios[0::2]
    finales = cambios[1::2] - 1

    # Posición de cada orilla: centroide de su región ponderado por votos, que es
    # subpíxel y no depende de dónde cayó el bin más alto.
    posiciones = np.empty(inicios.size, dtype=float)
    conteos = np.empty(inicios.size, dtype=float)
    semianchuras = np.empty(inicios.size, dtype=float)
    for indice, (inicio, final) in enumerate(zip(inicios.tolist(), finales.tolist())):
        pesos = perfil[inicio:final + 1]
        bins = np.arange(inicio, final + 1, dtype=float)
        centro = float(np.dot(bins, pesos) / pesos.sum())
        posiciones[indice] = centro
        conteos[indice] = float(pesos.sum())

        # Semianchura a media altura del pico propio de la orilla, y no del global:
        # así cada una mide su desenfoque. Nítida: un bin. Desenfocada: la rampa
        # entera, y esa amplitud es la incertidumbre real del ancho. Se expande
        # fuera de la región del umbral de ruido, porque el desenfoque está
        # justamente en los bins que ese umbral deja afuera; se detiene al caer de
        # media altura o al empezar a subir, que es el valle entre dos orillas.
        mitad = 0.5 * float(pesos.max())
        desde = inicio + int(np.argmax(pesos))
        izquierda = desde
        while izquierda > 0 and perfil[izquierda - 1] >= mitad and perfil[izquierda - 1] <= perfil[izquierda]:
            izquierda -= 1
        derecha = desde
        while (
            derecha < perfil.size - 1
            and perfil[derecha + 1] >= mitad
            and perfil[derecha + 1] <= perfil[derecha]
        ):
            derecha += 1
        semianchuras[indice] = max(centro - izquierda, derecha - centro, 1.0) * paso

    rhos = (posiciones + desplazamiento) * paso
    return rhos, conteos, semianchuras


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
        # El desempate es por rho y no por índice: así el emparejamiento depende
        # solo de las distancias y no del orden en que llegaron las candidatas.
        j = min(compatibles, key=lambda k: (abs(rhos[i] - rhos[k]), rhos[k]))
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


def _muestrear_bilineal(
    imagen: np.ndarray, x: np.ndarray, y: np.ndarray
) -> np.ndarray:
    """Interpola la imagen en coordenadas continuas `(x, y)`.

    Recorta a los bordes de la imagen, que es el comportamiento correcto para el
    muestreo de una franja que puede empezar o terminar en el límite del recorte.
    """
    alto, ancho = imagen.shape
    x = np.clip(np.asarray(x, dtype=float), 0.0, ancho - 1.0)
    y = np.clip(np.asarray(y, dtype=float), 0.0, alto - 1.0)

    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    x1 = np.minimum(x0 + 1, ancho - 1)
    y1 = np.minimum(y0 + 1, alto - 1)
    peso_x = x - x0
    peso_y = y - y0

    return (
        imagen[y0, x0] * (1.0 - peso_x) * (1.0 - peso_y)
        + imagen[y0, x1] * peso_x * (1.0 - peso_y)
        + imagen[y1, x0] * (1.0 - peso_x) * peso_y
        + imagen[y1, x1] * peso_x * peso_y
    )


def intensidad_interior(
    imagen: np.ndarray,
    puntos: np.ndarray,
    rhos: np.ndarray,
    thetas: np.ndarray,
    par: tuple[int, int],
    semianchuras: np.ndarray | None = None,
) -> float:
    """Intensidad mediana del interior de una franja, en unidades de la imagen.

    El interior de un par de orillas es la línea media entre las dos: `rho_m` es
    el promedio de los dos `rho` y la posición de muestreo es
    `rho_m·n + t·d`, con `n = (cos θ, sin θ)` la normal y `d = (−sin θ, cos θ)` la
    dirección. Los valores de `t` no se inventan: son las proyecciones de los
    puntos que el par tiene asignados, o sea las posiciones donde el dato existe.
    Muestrear sobre esos `t` mide la franja solo donde hay borde que la sostenga.

    Parámetros:
        imagen (numpy.ndarray): Matriz `(H, W)` con la intensidad de la escena.
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        rhos (numpy.ndarray): `(K,)` rho de cada orilla, en px.
        thetas (numpy.ndarray): `(K,)` theta de cada orilla, en rad.
        par (tuple[int, int]): Índices de las dos orillas de la franja.
        semianchuras (numpy.ndarray | None): `(K,)` semianchura de cada pico; si se
            pasa, acota la pertenencia igual que en `asignar_puntos_a_orillas`.

    Retorna:
        float: Mediana de la intensidad muestreada, o `nan` si el par no tiene
        puntos asignados y por lo tanto no hay interior que medir.
    """
    imagen = np.asarray(imagen, dtype=float)
    if imagen.ndim != 2:
        raise ValueError("pares_orillas:: imagen debe ser 2D (intensidad)")

    mascara_a, mascara_b = asignar_puntos_a_orillas(
        puntos, rhos, thetas, par, semianchuras
    )
    del_par = mascara_a | mascara_b
    if not np.any(del_par):
        return float("nan")

    indice_a, indice_b = int(par[0]), int(par[1])
    theta = 0.5 * (float(thetas[indice_a]) + float(thetas[indice_b]))
    rho_medio = 0.5 * (float(rhos[indice_a]) + float(rhos[indice_b]))

    normal = np.array([np.cos(theta), np.sin(theta)], dtype=float)
    direccion = np.array([-np.sin(theta), np.cos(theta)], dtype=float)
    sobre_la_franja = np.asarray(puntos, dtype=float)[del_par]
    parametro = sobre_la_franja @ direccion

    base = rho_medio * normal
    posiciones = base[None, :] + parametro[:, None] * direccion[None, :]
    muestras = _muestrear_bilineal(imagen, posiciones[:, 0], posiciones[:, 1])
    return float(np.median(muestras))


def seleccionar_trazo_por_intensidad(
    imagen: np.ndarray,
    puntos: np.ndarray,
    rhos: np.ndarray,
    thetas: np.ndarray,
    pares: list[tuple[int, int]],
    conteos: np.ndarray | None = None,
    semianchuras: np.ndarray | None = None,
) -> tuple[int, int] | None:
    """Elige el par de orillas que corresponde a un trazo, mirando la imagen (S9).

    La evidencia de Hough mide alineación de bordes, no intensidad, así que no
    distingue una franja oscura de una clara: en `600mm_Imag0000.bmp` todos los
    pares consecutivos de orillas son franjas y el par de mayor evidencia resultó
    ser una franja clara intermedia (96.69 px) en vez del trazo (58.37 px).

    Criterio: se mide la intensidad del interior de cada par y se compara con la
    mediana de la escena, que es el fondo. Las franjas se agrupan en dos familias
    por el lado del fondo en que caen —más oscuras o más claras—, cada familia se
    identifica por su miembro más contrastado, y gana la familia que más se aparta
    del fondo. Dentro de esa familia manda la evidencia, como en `emparejar_orillas`.

    La polaridad se **deriva** de la imagen y no se supone: con un trazo claro
    sobre fondo oscuro la familia ganadora es la clara, sin intervención del
    operador. Si ninguna franja se aparta del fondo, el criterio se abstiene
    (`None`) y el llamador conserva la evidencia de Hough: no hay base para
    descartarla.

    Parámetros:
        imagen (numpy.ndarray): Matriz `(H, W)` con la intensidad de la escena.
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        rhos (numpy.ndarray): `(K,)` rho de cada orilla, en px.
        thetas (numpy.ndarray): `(K,)` theta de cada orilla, en rad.
        pares (list[tuple[int, int]]): Pares de orillas candidatos.
        conteos (numpy.ndarray | None): `(K,)` evidencia de cada orilla.
        semianchuras (numpy.ndarray | None): `(K,)` semianchura de cada pico.

    Retorna:
        tuple[int, int] | None: El par del trazo, o `None` si no hay pares o si
        ninguna franja se aparta del fondo.
    """
    rhos = _como_array(rhos, "rhos")
    thetas = _como_array(thetas, "thetas")
    if rhos.shape != thetas.shape:
        raise ValueError("pares_orillas:: rhos y thetas deben tener la misma longitud")
    if conteos is not None:
        conteos = _como_array(conteos, "conteos")
        if conteos.shape != rhos.shape:
            raise ValueError("pares_orillas:: conteos debe tener la longitud de rhos")
    candidatos = list(pares)
    if not candidatos:
        return None

    mediana_escena = float(np.median(np.asarray(imagen, dtype=float)))

    desviaciones = np.empty(len(candidatos), dtype=float)
    for indice, par in enumerate(candidatos):
        interior = intensidad_interior(
            imagen, puntos, rhos, thetas, par, semianchuras
        )
        desviaciones[indice] = interior - mediana_escena

    medibles = np.isfinite(desviaciones)
    if not np.any(medibles):
        return None

    # Dos familias: las franjas más oscuras que el fondo y las más claras. El
    # signo lo pone la imagen, no una convención de polaridad.
    mas_oscura = medibles & (desviaciones < 0.0)
    mas_clara = medibles & (desviaciones > 0.0)

    def contraste(familia: np.ndarray) -> float:
        """Contraste de la familia: el de su miembro más apartado del fondo."""
        return float(np.max(np.abs(desviaciones[familia]))) if np.any(familia) else -1.0

    # Empate exacto: se prefiere el lado oscuro, que es el caso nominal del
    # proyecto (trazo oscuro sobre fondo claro) cuando la escena no desempata.
    familia = mas_oscura if contraste(mas_oscura) >= contraste(mas_clara) else mas_clara
    indices_familia = np.flatnonzero(familia)
    if indices_familia.size == 0:
        return None

    def clave(indice: int) -> tuple[float, float]:
        """Evidencia del par; el rho menor desempata de forma estable (S8)."""
        par = candidatos[int(indice)]
        evidencia = float(conteos[par[0]] + conteos[par[1]]) if conteos is not None else 0.0
        return (evidencia, -float(min(rhos[par[0]], rhos[par[1]])))

    elegido = max(indices_familia.tolist(), key=clave)
    return candidatos[int(elegido)]
