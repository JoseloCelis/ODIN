"""Transformada de Hough y barrido de radios (etapa ⑦).

Funciones puras: NumPy + SciPy (procesamiento, no UI). Sin gi, Gtk, Gdk,
Adw ni cairo.

Funciones activas (en producción):
    - hough_circles_vectorizado(im_binary, r, thres, dist)
    - mejor_centro(x0, y0, acumulador)
    - estimar_radio(im_binary, r_min, r_max, paso, thres, dist,
                    separacion_px)
    - estimar_radio_dominante(im_binary, r0, fraccion_min,
                              paso_grueso_rel, candidatos, paso_fino,
                              thres, dist)

Código muerto del módulo (R8, no movido, pendiente autorización para borrar):
    - houghCircles (traducción MATLAB con bucles Python)
    - houghpeaks, imregionalmax (solo usadas por houghCircles)
"""

import numpy as np
from scipy.ndimage import maximum_filter

# Umbral de ambigüedad del barrido de radios (spec hough-circles, R5): si el
# segundo candidato supera esta fracción del primero, la detección se reporta
# como ambigua en lugar de presentarse como certera.
UMBRAL_AMBIGUEDAD = 0.8

# Separación mínima, en píxeles, para considerar que dos radios son candidatos
# distintos y no el mismo pico repartido entre radios vecinos.
SEPARACION_AMBIGUEDAD_PX = 6.0


def hough_circles_vectorizado(im_binary, r, thres=0.5, dist=20):
    """
    Detecta círculos en una imagen binaria de bordes usando la Transformada
    de Hough.

    Parámetros:
        im_binary (numpy.ndarray): Imagen binaria (mapa de bordes).
        r (int o float): Radio del círculo a detectar.
        thres (float): Umbral relativo al valor máximo del acumulador
            (0.5 a 1.0).
        dist (int): Distancia mínima entre centros de círculos detectados.

    Retorna:
        x0_detected (numpy.ndarray): Coordenadas X de los centros.
        y0_detected (numpy.ndarray): Coordenadas Y de los centros.
        n (int): Número de círculos detectados.
        accumulator (numpy.ndarray): Matriz de votación del espacio de Hough.
    """
    if dist < 10:
        raise ValueError("HOUGHCIRCLE:: Distance value must be bigger or equal to 10 px")

    if thres < 0.5:
        raise ValueError("HOUGHCIRCLE:: Treshold value must be bigger or equal to 0.5")

    if r <= 0:
        raise ValueError("HOUGHCIRCLE:: Radius value must be bigger than 0 px")

    # Asegurarnos de que sea una matriz booleana
    im_binary = np.asarray(im_binary, dtype=bool)

    # Entrada vacía: np.max no tiene identidad para tamaño cero (spec
    # hough-circles, R1.4). Se devuelve la salida vacía, como en la etapa 6.
    if im_binary.size == 0:
        vacio = np.empty(0, dtype=int)
        return vacio, vacio, 0, np.zeros(im_binary.shape, dtype=int)

    num_row, num_col = im_binary.shape

    # 1. Encontrar los índices (y, x) de los píxeles que son bordes
    y_index, x_index = np.nonzero(im_binary)

    # 2. Vectorización: Precalcular el seno y coseno para ángulos de 0 a 359 grados
    theta = np.deg2rad(np.arange(0, 360))
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    # 3. Broadcasting: Calcular (a, b) para TODOS los puntos y TODOS los
    # ángulos a la vez
    a = np.round(x_index[:, None] - (r * cos_t)).astype(int)
    b = np.round(y_index[:, None] - (r * sin_t)).astype(int)

    # 4. Filtrar las coordenadas que caen fuera de los límites de la imagen
    valid_mask = (a >= 0) & (a < num_col) & (b >= 0) & (b < num_row)
    a_valid = a[valid_mask]
    b_valid = b[valid_mask]

    # 5. Llenar el acumulador de forma vectorizada
    accumulator = np.zeros((num_row, num_col), dtype=int)
    np.add.at(accumulator, (b_valid, a_valid), 1)

    # 6. Encontrar los picos locales (Reemplaza el bucle while de agrupación
    # de MATLAB)
    local_max = maximum_filter(accumulator, size=dist) == accumulator

    # 7. Aplicar el umbral (Threshold)
    threshold_value = np.max(accumulator) * thres

    # Un pico válido es un máximo local que supera el umbral y tiene votos > 0
    peak_mask = local_max & (accumulator >= threshold_value) & (accumulator > 0)

    # Extraer las coordenadas finales
    y0_detected, x0_detected = np.nonzero(peak_mask)
    n = len(y0_detected)

    return x0_detected, y0_detected, n, accumulator


def mejor_centro(x0, y0, acumulador):
    """Devuelve `(x, y, votos)` del pico con más votos, o `None` sin picos.

    `hough_circles_vectorizado` devuelve TODOS los picos, en orden de barrido
    de la imagen (no de votos). El llamador debe quedarse con uno solo: pasar
    el arreglo completo a `find_circle` rompe el broadcasting (spec
    hough-circles, R9).
    """
    x0 = np.asarray(x0)
    y0 = np.asarray(y0)

    if x0.size == 0 or y0.size == 0:
        return None

    votos = np.asarray(acumulador)[y0, x0]
    mejor = int(np.argmax(votos))

    return int(x0[mejor]), int(y0[mejor]), int(votos[mejor])


def estimar_radio(im_binary, r_min, r_max, paso=2.0, thres=0.99, dist=20,
                  separacion_px=SEPARACION_AMBIGUEDAD_PX):
    """Estima el radio dominante barriendo la banda `[r_min, r_max]`.

    Devuelve `(radio, pico, ambiguedad)`:

    - `radio`: el radio cuyo pico del acumulador es mayor (0.0 si no hay
      bordes).
    - `pico`: votos de ese radio.
    - `ambiguedad`: relación entre el segundo candidato y el primero. Los
      radios vecinos (a menos de `separacion_px`) no cuentan como candidatos
      distintos: son el mismo pico repartido por la discretización.

    La banda la deriva el llamador del recorte: `r0 = min(alto, ancho) / 2`
    y `[0.6 * r0, r0]` (spec hough-circles, R4).

    Limitación conocida: el pico bruto crece con el radio (más puntos de
    borde), así que un círculo grande domina a uno mucho más chico y la
    ambigüedad no se reporta. Ver `design.md` §3.4.
    """
    r_min = float(r_min)
    r_max = float(r_max)
    paso = float(paso)

    if not np.isfinite([r_min, r_max, paso]).all():
        raise ValueError("estimar_radio:: los límites y el paso deben ser finitos")
    if r_min <= 0:
        raise ValueError("estimar_radio:: r_min debe ser mayor que 0")
    if r_min > r_max:
        raise ValueError("estimar_radio:: r_min no puede superar a r_max")
    if paso <= 0:
        raise ValueError("estimar_radio:: el paso debe ser mayor que 0")

    im_binary = np.asarray(im_binary)
    if im_binary.size == 0 or not np.any(im_binary > 0):
        return 0.0, 0, 0.0

    radios = np.arange(r_min, r_max + paso * 0.5, paso)
    picos = np.array([
        int(hough_circles_vectorizado(im_binary, float(radio), thres, dist)[3].max())
        for radio in radios
    ])

    mejor = int(np.argmax(picos))
    if picos[mejor] <= 0:
        return 0.0, 0, 0.0

    pasos_separacion = max(1, int(round(separacion_px / paso)))
    otros = [p for j, p in enumerate(picos) if abs(j - mejor) >= pasos_separacion]
    segundo = max(otros) if otros else 0

    return float(radios[mejor]), int(picos[mejor]), float(segundo / picos[mejor])


def estimar_radio_dominante(im_binary, r0, fraccion_min=0.08, paso_grueso_rel=0.02,
                            candidatos=2, paso_fino=None, thres=0.99, dist=20):
    """Estima el radio dominante de un recorte, holgado o ajustado.

    Barrido en dos escalas (spec hough-circles, R10):

    1. **Grueso**: recorre `[fraccion_min * r0, r0]` con un paso proporcional a
       `r0`, así el costo no crece con el tamaño de la imagen.
    2. **Fino**: refina los `candidatos` máximos gruesos mejor separados, con
       un paso absoluto pequeño.

    Refinar varios candidatos es lo que hace robusta la decisión: en el
    recorte holgado de `img100`, el barrido grueso daba 68 votos al disco y 58
    al texto (1.17:1), mientras que al refinar quedan 211 contra 80 (2.6:1).

    Devuelve `(radio, pico, ambiguedad)` con el mismo contrato que
    `estimar_radio`. La ambigüedad se calcula entre estructuras ya refinadas y
    separadas, no entre radios vecinos.
    """
    r0 = float(r0)
    if not np.isfinite(r0) or r0 <= 0:
        raise ValueError("estimar_radio_dominante:: r0 debe ser mayor que 0")

    r_max = r0
    r_min = max(4.0, fraccion_min * r0)
    if r_min >= r_max:
        r_min = max(1.0, r_max / 2.0)

    paso_grueso = max(4.0, paso_grueso_rel * r0)
    if paso_fino is None:
        paso_fino = max(1.0, min(4.0, paso_grueso / 5.0))

    radios = np.arange(r_min, r_max + paso_grueso * 0.5, paso_grueso)
    picos = np.array([
        int(hough_circles_vectorizado(im_binary, float(radio), thres, dist)[3].max())
        for radio in radios
    ])

    if picos.size == 0 or picos.max() <= 0:
        return 0.0, 0, 0.0

    # Candidatos gruesos: los picos más altos, separados al menos dos pasos
    # para no refinar tres veces la misma estructura.
    candidatos_idx = []
    for j in np.argsort(-picos):
        if all(abs(radios[j] - radios[e]) >= 2 * paso_grueso for e in candidatos_idx):
            candidatos_idx.append(int(j))
        if len(candidatos_idx) >= max(1, int(candidatos)):
            break

    refinados = []
    for j in candidatos_idx:
        bajo = max(r_min, radios[j] - paso_grueso)
        alto = min(r_max, radios[j] + paso_grueso)
        refinados.append(estimar_radio(im_binary, bajo, alto, paso_fino, thres, dist))

    refinados.sort(key=lambda salida: -salida[1])

    # Dos candidatos pueden converger al mismo radio: cuentan como uno solo.
    unicos = []
    for radio, pico, _ in refinados:
        if all(abs(radio - otro) >= 2 * paso_fino for otro, _ in unicos):
            unicos.append((radio, pico))

    radio, pico = unicos[0]
    segundo = unicos[1][1] if len(unicos) > 1 else 0

    return float(radio), int(pico), float(segundo / pico)
