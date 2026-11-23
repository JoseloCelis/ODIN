"""Ajuste robusto de recta (etapa ⑪).

Función pura: numpy puro (ajuste geométrico, no UI). Sin gi, Gtk, Gdk, Adw
ni cairo.

Port de `CodigoMatlab/Linea_robusta.m` y sus helpers `lineaMC.m`,
`EucSpace.m`, `dist_p_recta.m` y el wrapper `Linea1.m` (spec
linea-robusta, S2 y S6).

Contrato:
  - `linea_robusta(puntos, param)` recibe una recta inicial (punto y cosenos
    directores) y refina la recta podando iterativamente los puntos cuya
    distancia supera una cota que decrece de 20 px a 8 px en pasos de 0.1,
    mientras la fracción de inliers se mantiene por encima de 0.2. Con más de
    3 inliers el refit es SVD (centroide + dirección principal).
  - Devuelve `(param, r, sobrevivientes)`: los parámetros de la recta, la
    dispersión del residual (pico a valle) y los puntos conservados.
  - `dist_p_recta`, `euc_space` y `linea_mc` son los helpers puros.

Desviaciones deliberadas del MATLAB original (documentadas, ver `odd/tasks/
migracion-lineas-geometria.md`):
  - `EucSpace.m` rellena `param(1,4) = 1 - param(1,3)^2`, que para un ángulo
    intermedio no es un coseno director (norma != 1) y además no es
    perpendicular a la normal, así que la "distancia" resultante era falsa.
    Aquí se devuelve el coseno director real `cos(theta)`.
  - `Linea_robusta.m` calcula `r` con una partición de los residuales por la
    coordenada X y `max(pi)`/`max(pd)`, una métrica que no es la dispersión y
    puede ser negativa antes del `abs`. Aquí `r` es el pico a valle de los
    residuales contra la recta final devuelta.
  - `Linea1.m` llamaba `EucSpace` con todas las filas pero esa función
    sobrescribía el resultado en cada iteración: repetía la última candidata.
    Aquí cada fila de `valores` produce su propio resultado.

No se migra `linea.m` (S5: código muerto) ni `separaPuntos.m` (S3: postergado).
"""

import numpy as np

# Constantes del algoritmo (spec linea-robusta, S2; values de Linea_robusta.m).
PORCENTAJE_MIN = 0.2
COTA_INICIAL_PX = 20.0
COTA_LIM_PX = 8.0
PASO_COTA_PX = 0.1

# Número de inliers a partir del cual se refita por SVD. El original usa
# `if (k > 3)` con `k = inliers + 1`, es decir, 3 inliers o más.
MINIMO_INLIERS_REFIT = 3


def _como_puntos(puntos: np.ndarray, nombre: str) -> np.ndarray:
    """Valida y convierte una nube de puntos (N, 2) a float.

    Compartida por todos los helpers para no repetir las guardas. No impone
    una cantidad mínima de puntos: la decide cada función.
    """
    if not isinstance(puntos, np.ndarray):
        raise TypeError(f"{nombre}:: se esperaba un numpy.ndarray de forma (N, 2)")

    if puntos.ndim != 2 or puntos.shape[1] != 2:
        raise ValueError(
            f"{nombre}:: el arreglo debe tener forma (N, 2) con coordenadas (x, y); "
            f"recibido {puntos.shape}"
        )

    puntos = np.asarray(puntos, dtype=float)
    if not np.all(np.isfinite(puntos)):
        raise ValueError(f"{nombre}:: los puntos deben ser finitos (sin NaN ni Inf)")

    return puntos


def _como_param(param: np.ndarray, nombre: str) -> np.ndarray:
    """Valida y aplana la recta [x0, y0, cos_x, cos_y] a un arreglo (4,)."""
    param = np.asarray(param, dtype=float).reshape(-1)

    if param.size != 4:
        raise ValueError(
            f"{nombre}:: se esperaba un param de 4 elementos "
            f"[x0, y0, cos_x, cos_y]; recibido {param.size}"
        )
    if not np.all(np.isfinite(param)):
        raise ValueError(
            f"{nombre}:: los parámetros de la recta deben ser finitos (sin NaN ni Inf)"
        )

    return param


def _validar_direccion(param: np.ndarray, nombre: str) -> None:
    """La dirección no puede ser el vector cero (no define recta)."""
    norma = float(np.hypot(param[2], param[3]))
    if norma == 0.0 or not np.isfinite(norma):
        raise ValueError(f"{nombre}:: los cosenos directores no pueden ser (0, 0)")


def dist_p_recta(puntos: np.ndarray, param: np.ndarray) -> np.ndarray:
    """Distancia perpendicular de cada punto a la recta `param`.

    `param` es `[x0, y0, cos_x, cos_y]` (punto + cosenos directores). La
    dirección se normaliza dentro de la función, de modo que la distancia es
    independiente de la escala de los cosenos. Fórmula del original:

        sqrt(|dx^2 + dy^2 - (cos_x*dx + cos_y*dy)^2|)

    que con dirección unitaria es el valor absoluto del producto cruzado.
    Devuelve un arreglo (N,). No modifica los argumentos.
    """
    puntos = _como_puntos(puntos, "dist_p_recta")
    param = _como_param(param, "dist_p_recta")
    _validar_direccion(param, "dist_p_recta")

    norma = float(np.hypot(param[2], param[3]))
    a = param[2] / norma
    b = param[3] / norma

    dx = puntos[:, 0] - param[0]
    dy = puntos[:, 1] - param[1]

    return np.sqrt(np.abs(dx * dx + dy * dy - (a * dx + b * dy) ** 2))


def euc_space(rho: float, theta: float) -> np.ndarray:
    """Convierte (rho, theta) del espacio de Hough a la recta euclídea.

    Devuelve `[x0, y0, cos_x, cos_y]`:
      - `(x0, y0)` es el pie de la perpendicular desde el origen, el punto de
        la recta más cercano al origen (`rho * (cos(theta), sin(theta))`).
      - `(-sin(theta), cos(theta))` es el coseno director unitario de la
        recta, perpendicular a la normal `(cos(theta), sin(theta))`.

    Se corrige el `param(1,4) = 1 - param(1,3)^2` del original, que no era un
    coseno director (ver la docstring del módulo).
    """
    rho = float(rho)
    theta = float(theta)
    if not np.isfinite(rho) or not np.isfinite(theta):
        raise ValueError("euc_space:: rho y theta deben ser finitos")

    return np.array(
        [
            rho * np.cos(theta),
            rho * np.sin(theta),
            -np.sin(theta),
            np.cos(theta),
        ]
    )


def linea_mc(puntos: np.ndarray) -> np.ndarray:
    """Ajusta una recta por mínimos cuadrados (SVD) a una nube de puntos.

    Devuelve `[x0, y0, cos_x, cos_y]`: el centroide y la dirección principal
    (el vector singular derecho con mayor valor singular). Equivale a
    `lineaMC.m`, con la salida de `np.linalg.svd` (que devuelve V^H, así que
    la dirección principal es la primera fila de `vh`).
    """
    puntos = _como_puntos(puntos, "linea_mc")
    if puntos.shape[0] < 2:
        raise ValueError("linea_mc:: se necesitan al menos 2 puntos para definir una recta")

    centroide = puntos.mean(axis=0)
    centrados = puntos - centroide

    _, s, vh = np.linalg.svd(centrados, full_matrices=False)
    direccion = vh[0] if s[0] > s[1] else vh[1]

    return np.array(
        [centroide[0], centroide[1], direccion[0], direccion[1]], dtype=float
    )


def linea_robusta(
    puntos: np.ndarray,
    param: np.ndarray,
    porcentaje: float = PORCENTAJE_MIN,
    cota_inicial: float = COTA_INICIAL_PX,
    cota_lim: float = COTA_LIM_PX,
    paso: float = PASO_COTA_PX,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Ajuste robusto de recta por poda iterativa (S2).

    Parameters:
        puntos (numpy.ndarray): Nube (N, 2) de puntos (x, y). Se requieren al
            menos 3.
        param (numpy.ndarray): Recta inicial `[x0, y0, cos_x, cos_y]`.
        porcentaje (float): Fracción mínima de inliers que debe conservarse
            (0.2 en el original).
        cota_inicial (float): Cota de distancia inicial, en px (20).
        cota_lim (float): Cota mínima, en px (8).
        paso (float): Decremento de la cota por iteración, en px (0.1).

    Returns:
        param (numpy.ndarray): Recta final `[x0, y0, cos_x, cos_y]`.
        r (float): Dispersión del residual (pico a valle) de los puntos
            conservados contra la recta final.
        sobrevivientes (numpy.ndarray): Puntos (M, 2) que sobrevivieron a la
            última poda, en el orden de entrada.

    Raises:
        TypeError: si `puntos` no es un numpy.ndarray.
        ValueError: si la forma o los valores de `puntos` o `param` son
            inválidos, si los parámetros del algoritmo son inconsistentes, o
            si no sobrevive ningún punto.
    """
    puntos = _como_puntos(puntos, "linea_robusta")
    if puntos.shape[0] < 3:
        raise ValueError(
            "linea_robusta:: se necesitan al menos 3 puntos para ajustar una recta"
        )

    param = _como_param(param, "linea_robusta")
    _validar_direccion(param, "linea_robusta")

    porcentaje = float(porcentaje)
    cota_inicial = float(cota_inicial)
    cota_lim = float(cota_lim)
    paso = float(paso)

    if not 0.0 < porcentaje < 1.0:
        raise ValueError("linea_robusta:: porcentaje debe estar entre 0 y 1")
    if paso <= 0.0:
        raise ValueError("linea_robusta:: paso debe ser positivo")
    if not np.isfinite(cota_inicial) or not np.isfinite(cota_lim):
        raise ValueError("linea_robusta:: las cotas deben ser finitas")
    if not cota_lim < cota_inicial:
        raise ValueError("linea_robusta:: cota_lim debe ser menor que cota_inicial")

    n = puntos.shape[0]
    nrp = n
    cota = cota_inicial
    k = n  # `k` del original: inliers + 1
    param_actual = param.copy()
    sobrevivientes = puntos

    while k > nrp * porcentaje and cota > cota_lim:
        distancias = dist_p_recta(puntos, param_actual)
        mascara = distancias <= cota
        sobrevivientes = puntos[mascara]
        k = sobrevivientes.shape[0] + 1

        if k > MINIMO_INLIERS_REFIT:
            param_actual = linea_mc(sobrevivientes)

        # El original fija la referencia de inliers cuando `nr == nrp`; se
        # conserva el comportamiento literal (la referencia se actualiza en
        # la primera iteración y también si alguna iteración deja
        # exactamente `nr - 1` puntos).
        if n == nrp:
            nrp = k

        cota -= paso

    if sobrevivientes.shape[0] == 0:
        raise ValueError(
            "linea_robusta:: no quedaron puntos dentro de la cota; "
            "revise la recta inicial"
        )

    residuales = dist_p_recta(sobrevivientes, param_actual)
    r = float(np.max(residuales) - np.min(residuales))

    return param_actual, r, sobrevivientes


def linea1(
    puntos: np.ndarray, valores: np.ndarray
) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    """Aplica `linea_robusta` a cada candidata (rho, theta) de `valores`.

    Port del wrapper `Linea1.m`. El original repetía la última candidata porque
    `EucSpace` sobrescribía su salida en cada iteración; aquí cada fila
    produce su propio resultado.

    `valores` es (N, 2) con `(rho, theta)` por fila. Devuelve:
      - `parametros` (N, 4): recta final de cada candidata.
      - `r` (N,): dispersión del residual de cada candidata.
      - `finales` (lista de N arreglos (M, 2)): puntos conservados de cada
        candidata (pueden tener distinto largo).
    """
    valores = np.asarray(valores, dtype=float)
    if valores.ndim == 1:
        valores = valores.reshape(1, -1)
    if valores.ndim != 2 or valores.shape[1] != 2:
        raise ValueError(
            f"linea1:: 'valores' debe tener forma (N, 2) con (rho, theta); "
            f"recibido {valores.shape}"
        )
    if not np.all(np.isfinite(valores)):
        raise ValueError("linea1:: los valores (rho, theta) deben ser finitos")

    n = valores.shape[0]
    parametros = np.empty((n, 4), dtype=float)
    r = np.empty(n, dtype=float)
    finales: list[np.ndarray] = []

    for k in range(n):
        parametro, r[k], sobrevivientes = linea_robusta(
            puntos, euc_space(valores[k, 0], valores[k, 1])
        )
        parametros[k] = parametro
        finales.append(sobrevivientes)

    return parametros, r, finales
