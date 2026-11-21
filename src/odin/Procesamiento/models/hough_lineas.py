"""Transformada de Hough para rectas (etapa ⑩, migrada de `houghLines.m`).

Funciones puras: NumPy (procesamiento, no UI). Sin gi, Gtk, Gdk, Adw ni
cairo.

Funciones activas:
    - acumulador_lineas(puntos, imagen)
    - candidatas_lineas(puntos, imagen, percent, max_dist_px)
    - reducir_candidatas(candidatas, sigma)
    - hough_lineas(puntos, imagen, percent, max_dist_px)

Contrato (spec migracion-lineas-geometria, S1):
    - theta en [-pi/2, pi/2] en paso pi/360 (361 valores).
    - rho cuantizado a 0.5 px en [-diag_len, diag_len], con
      diag_len = ceil(hypot(alto, ancho)).
    - cada candidata expone DOS métricas:
        * `conteos`: conteo de picos agrupados (el `p` del original,
          `houghLines.m:92,105`); es el criterio de selección;
        * `masas`: masa del acumulador sumada sobre las celdas del grupo
          (información de fuerza de evidencia).
      Además se expone `desviaciones`, la desviación estándar muestral de rho
      entre los picos del grupo, que alimenta `sigma`.
    - antes de seleccionar, las candidatas se fusionan con `reducir_candidatas`
      y `sigma = 2.7 * max(desviaciones)` (`houghLines.m:114`).
    - `hough_lineas` devuelve la candidata con más picos agrupados; ante
      empate, la de mayor masa.
    - rechaza `percent` fuera de [0.6, 0.9] y `max_dist_px` menor a 30.

Diferencias deliberadas con `houghLines.m`:
    - el original cuantiza rho a 1 px (`rhos = linspace(-diag_len, diag_len,
      diag_len*2)`); S1 fija 0.5 px, que es el `rhos1` comentado del archivo.
    - el guard original `percent < 0.6 && percent > 0.9` nunca se cumple; S1
      exige rechazar fuera de [0.6, 0.9] y se implementa así.
    - no se migra `dibuja` (gráfica de MATLAB).
    - `reduce` no existe como archivo en `CodigoMatlab/`; es una función anidada
      de `houghLines.m`. Se reconstruyó la fusión por proximidad de rho según
      S1: el original ordena por `p` y compara
      `abs(abs(rho_i) - abs(rho_{i-1}))`, mientras que su línea comentada
      ordena por rho, que es el criterio implementado aquí.
    - el ángulo medio usa `arctan2` sobre las medias de seno y coseno;
      `meanAngles` del original es equivalente en [-pi/2, pi/2] y su rama
      degenerada no se reproduce.
"""

from dataclasses import dataclass

import numpy as np

# Paso angular del acumulador: theta en [-pi/2, pi/2] con 361 valores.
PASO_THETA = np.pi / 360.0
NUM_THETAS = 361

# Cuantización de rho: 0.5 px por bin.
PASO_RHO = 0.5

# Guardas de la spec S1, espejo de los umbrales del original.
PERCENT_MIN = 0.6
PERCENT_MAX = 0.9
MAX_DIST_PX_MIN = 30.0

# Factor de la fusión `reduce` del original (`sigma = 2.7 * max(DesvStd)`).
FACTOR_SIGMA = 2.7


@dataclass(frozen=True, slots=True)
class CandidatasLineas:
    """Picos agrupados del acumulador, ordenados por candidata.

    Contenedor inmutable de las candidatas devueltas por `candidatas_lineas`
    y de las fusionadas por `reducir_candidatas`.

    Atributos:
        rhos (numpy.ndarray): Rho medio de cada candidata.
        thetas (numpy.ndarray): Theta medio (dirección) de cada candidata.
        conteos (numpy.ndarray): Conteo de picos agrupados de cada candidata
            (el `p` del original; criterio de selección).
        masas (numpy.ndarray): Masa del acumulador sumada sobre las celdas del
            grupo (fuerza de evidencia).
        desviaciones (numpy.ndarray): Desviación estándar muestral (N-1) de rho
            entre los picos del grupo; 0.0 si el grupo tiene un pico.
    """

    rhos: np.ndarray
    thetas: np.ndarray
    conteos: np.ndarray
    masas: np.ndarray
    desviaciones: np.ndarray


def _validar_puntos(puntos: np.ndarray) -> np.ndarray:
    """Devuelve los puntos como matriz `(N, 2)` de valores finitos."""
    arr = np.asarray(puntos, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("hough_lineas:: puntos debe ser un arreglo (N, 2)")
    if not np.isfinite(arr).all():
        raise ValueError("hough_lineas:: los puntos deben ser finitos")
    return arr


def _dimensiones(imagen: np.ndarray) -> tuple[int, int]:
    """Devuelve `(alto, ancho)`; el modelo solo usa la forma de la imagen."""
    arr = np.asarray(imagen)
    if arr.ndim != 2:
        raise ValueError("hough_lineas:: imagen debe ser una matriz 2D")
    return int(arr.shape[0]), int(arr.shape[1])


def _validar_parametros(percent: float, max_dist_px: float) -> tuple[float, float]:
    """Validación de las guardas de S1: percent en [0.6, 0.9] y dist >= 30."""
    percent = float(percent)
    max_dist_px = float(max_dist_px)
    if not np.isfinite(percent) or percent < PERCENT_MIN or percent > PERCENT_MAX:
        raise ValueError("hough_lineas:: percent debe estar entre 0.6 y 0.9")
    if not np.isfinite(max_dist_px) or max_dist_px < MAX_DIST_PX_MIN:
        raise ValueError("hough_lineas:: max_dist_px debe ser mayor o igual a 30 px")
    return percent, max_dist_px


def _angulo_medio(thetas: np.ndarray) -> float:
    """Media circular de ángulos con `arctan2` de las medias de seno y coseno."""
    return float(np.arctan2(np.sin(thetas).mean(), np.cos(thetas).mean()))


def acumulador_lineas(puntos: np.ndarray, imagen: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construye el acumulador de Hough en el espacio (rho, theta).

    Parámetros:
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`
            de los puntos de borde.
        imagen (numpy.ndarray): Imagen 2D; solo se usa su forma para acotar
            el rango de rho con la diagonal.

    Retorna:
        acumulador (numpy.ndarray): Matriz `(4 * diag_len + 1, 361)` de enteros
            con los votos por cada `(rho, theta)`.
        rhos (numpy.ndarray): Valores de rho de cada fila, de `-diag_len` a
            `diag_len` en paso de 0.5 px.
        thetas (numpy.ndarray): Valores de theta de cada columna, de `-pi/2` a
            `pi/2` en paso de `pi/360`.
    """
    puntos = _validar_puntos(puntos)
    alto, ancho = _dimensiones(imagen)
    diag_len = int(np.ceil(np.hypot(ancho, alto)))
    num_rho = 4 * diag_len + 1
    rhos = -diag_len + PASO_RHO * np.arange(num_rho, dtype=float)
    thetas = np.linspace(-np.pi / 2.0, np.pi / 2.0, NUM_THETAS)
    acumulador = np.zeros((num_rho, NUM_THETAS), dtype=np.int64)

    if puntos.shape[0] == 0:
        return acumulador, rhos, thetas

    cos_t = np.cos(thetas)
    sin_t = np.sin(thetas)
    x = puntos[:, 0]
    y = puntos[:, 1]

    # Votación vectorizada: cada punto emite un voto por cada theta.
    rho_real = x[:, None] * cos_t[None, :] + y[:, None] * sin_t[None, :]
    idx_rho = np.rint(rho_real / PASO_RHO).astype(np.int64) + 2 * diag_len
    np.clip(idx_rho, 0, num_rho - 1, out=idx_rho)
    idx_theta = np.broadcast_to(np.arange(NUM_THETAS), idx_rho.shape)
    np.add.at(acumulador, (idx_rho, idx_theta), 1)

    return acumulador, rhos, thetas


def candidatas_lineas(puntos: np.ndarray, imagen: np.ndarray, percent: float = PERCENT_MIN,
                      max_dist_px: float = MAX_DIST_PX_MIN) -> CandidatasLineas:
    """Agrupa los picos del acumulador y devuelve todas las candidatas.

    Dos picos consecutivos (ordenados por rho) forman el mismo grupo cuando su
    distancia en rho es menor o igual a `max_dist_px`.

    Parámetros:
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        imagen (numpy.ndarray): Imagen 2D; solo se usa su forma.
        percent (float): Fracción del máximo del acumulador que actúa como
            umbral de pico; debe estar en [0.6, 0.9].
        max_dist_px (float): Distancia máxima en px para agrupar picos; debe
            ser mayor o igual a 30.

    Retorna:
        candidatas (CandidatasLineas): Las candidatas agrupadas, con los
            arrays `rhos`, `thetas`, `conteos`, `masas` y `desviaciones`.
    """
    percent, max_dist_px = _validar_parametros(percent, max_dist_px)
    acumulador, rhos, thetas = acumulador_lineas(puntos, imagen)

    vacio = CandidatasLineas(
        rhos=np.empty(0, dtype=float),
        thetas=np.empty(0, dtype=float),
        conteos=np.empty(0, dtype=np.int64),
        masas=np.empty(0, dtype=np.int64),
        desviaciones=np.empty(0, dtype=float),
    )
    maximo = int(acumulador.max())
    if maximo == 0:
        return vacio

    umbral = maximo * percent
    filas, columnas = np.nonzero(acumulador >= umbral)
    if filas.size == 0:
        return vacio

    # Orden por rho creciente; `nonzero` ya devuelve columnas ascendentes.
    orden = np.argsort(filas, kind="stable")
    filas = filas[orden]
    columnas = columnas[orden]
    rhos_pico = rhos[filas]
    thetas_pico = thetas[columnas]
    votos_pico = acumulador[filas, columnas]

    cortes = np.flatnonzero(np.diff(rhos_pico) > max_dist_px) + 1
    grupos = np.split(np.arange(filas.size), cortes)

    rhos_c = np.empty(len(grupos), dtype=float)
    thetas_c = np.empty(len(grupos), dtype=float)
    conteo_c = np.empty(len(grupos), dtype=np.int64)
    masa_c = np.empty(len(grupos), dtype=np.int64)
    desviaciones = np.empty(len(grupos), dtype=float)
    for i, grupo in enumerate(grupos):
        rhos_c[i] = rhos_pico[grupo].mean()
        thetas_c[i] = _angulo_medio(thetas_pico[grupo])
        conteo_c[i] = int(grupo.size)
        masa_c[i] = int(votos_pico[grupo].sum())
        desviaciones[i] = (
            0.0 if grupo.size == 1 else float(np.std(rhos_pico[grupo], ddof=1))
        )

    return CandidatasLineas(
        rhos=rhos_c,
        thetas=thetas_c,
        conteos=conteo_c,
        masas=masa_c,
        desviaciones=desviaciones,
    )


def reducir_candidatas(candidatas: CandidatasLineas, sigma: float) -> CandidatasLineas:
    """Fusiona candidatas cuya rho difiere en menos o igual a `sigma`.

    Reconstrucción de la fusión `reduce` que `houghLines.m:114` aplica antes de
    seleccionar: se ordenan las candidatas por rho y se fusionan las
    consecutivas cuya diferencia de rho no supera `sigma`, sumando el conteo de
    picos y la masa de votos y promediando rho y theta.

    Parámetros:
        candidatas (CandidatasLineas): Candidatas tal como las devuelve
            `candidatas_lineas`.
        sigma (float): Distancia máxima de fusión; en el pipeline es
            `2.7 * max(candidatas.desviaciones)`.

    Retorna:
        Un nuevo `CandidatasLineas` fusionado. La desviación de un grupo de una
        sola candidata se conserva; la de un grupo fusionado es la desviación
        estándar muestral de las rho fusionadas.
    """
    rhos = np.asarray(candidatas.rhos, dtype=float)
    thetas = np.asarray(candidatas.thetas, dtype=float)
    conteo_picos = np.asarray(candidatas.conteos, dtype=np.int64)
    masa_votos = np.asarray(candidatas.masas, dtype=np.int64)
    desviaciones = np.asarray(candidatas.desviaciones, dtype=float)
    sigma = float(sigma)

    if rhos.size <= 1 or sigma < 0.0:
        return CandidatasLineas(
            rhos=rhos,
            thetas=thetas,
            conteos=conteo_picos,
            masas=masa_votos,
            desviaciones=desviaciones,
        )

    orden = np.argsort(rhos, kind="stable")
    rhos = rhos[orden]
    thetas = thetas[orden]
    conteo_picos = conteo_picos[orden]
    masa_votos = masa_votos[orden]
    desviaciones = desviaciones[orden]

    cortes = np.flatnonzero(np.diff(rhos) > sigma) + 1
    grupos = np.split(np.arange(rhos.size), cortes)

    rhos_r = np.empty(len(grupos), dtype=float)
    thetas_r = np.empty(len(grupos), dtype=float)
    conteo_r = np.empty(len(grupos), dtype=np.int64)
    masa_r = np.empty(len(grupos), dtype=np.int64)
    desviaciones_r = np.empty(len(grupos), dtype=float)
    for i, grupo in enumerate(grupos):
        rhos_r[i] = rhos[grupo].mean()
        thetas_r[i] = _angulo_medio(thetas[grupo])
        conteo_r[i] = int(conteo_picos[grupo].sum())
        masa_r[i] = int(masa_votos[grupo].sum())
        desviaciones_r[i] = (
            float(desviaciones[grupo][0])
            if grupo.size == 1
            else float(np.std(rhos[grupo], ddof=1))
        )

    return CandidatasLineas(
        rhos=rhos_r,
        thetas=thetas_r,
        conteos=conteo_r,
        masas=masa_r,
        desviaciones=desviaciones_r,
    )


def hough_lineas(puntos: np.ndarray, imagen: np.ndarray, percent: float = PERCENT_MIN,
                 max_dist_px: float = MAX_DIST_PX_MIN) -> tuple[float, float, int, int, float] | None:
    """Devuelve la recta candidata con más picos agrupados.

    Parámetros:
        puntos (numpy.ndarray): Matriz `(N, 2)` con las coordenadas `(x, y)`.
        imagen (numpy.ndarray): Imagen 2D; solo se usa su forma.
        percent (float): Fracción del máximo del acumulador; en [0.6, 0.9].
        max_dist_px (float): Distancia máxima de agrupación; mayor o igual a
            30.

    Retorna:
        `(rho, theta, conteo_picos, masa_votos, desviacion)` de la candidata
        con más picos agrupados; en empate, la de mayor masa. `None` si no hay
        puntos o ninguna celda supera el umbral.
    """
    candidatas = candidatas_lineas(puntos, imagen, percent, max_dist_px)
    if candidatas.rhos.size == 0:
        return None

    sigma = FACTOR_SIGMA * float(candidatas.desviaciones.max())
    fusionadas = reducir_candidatas(candidatas, sigma)

    # Clave primaria: más picos; desempate: mayor masa.
    orden = np.lexsort((-fusionadas.masas, -fusionadas.conteos))
    indice = int(orden[0])

    return (
        float(fusionadas.rhos[indice]),
        float(fusionadas.thetas[indice]),
        int(fusionadas.conteos[indice]),
        int(fusionadas.masas[indice]),
        float(fusionadas.desviaciones[indice]),
    )
