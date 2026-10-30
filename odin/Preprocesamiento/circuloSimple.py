import numpy as np

# Umbral del número de condición medido sobre coordenadas normalizadas
# (centradas en el centroide y escaladas por su RMS radial).
#
# Medido con 216 círculos válidos (r 15-1000 dentro de 2300x2000, 300-5400
# puntos, hueco de 0 a 60°, sigma 0 a 2 px) y 960 rectas con ruido controlado:
#   anillo real de 3150 puntos .................. 1.418
#   peor caso válido del contrato (hueco 60°) ... 1.701
#   arco de medio círculo (semicírculo) ......... 2.395
#   rectas casi colineales ...................... >= 4.056
#   arco con hueco de 240° ...................... 3.672
# El valor 3.0 queda entre los dos mundos y deja pasar incluso un semicírculo.
UMBRAL_CONDICION_NORMALIZADA = 3.0


def Circulo_simple(puntos0):
    """
    Ajusta un círculo a un conjunto de puntos usando mínimos cuadrados.

    Método algebraico de Kåsa: se resuelve el sistema sobredeterminado
    A @ [x_c, y_c, s] = x² + y² con A = [2x, 2y, -1], y el radio sale como
    r = sqrt(x_c² + y_c² - s). Version 100% vectorizada, con validación de
    entrada y guard de colinealidad.

    Parameters:
        puntos0 (numpy.ndarray): Matriz de N x 2 con las coordenadas (X, Y) de los puntos.

    Returns:
        x_c (float): Coordenada X del centro.
        y_c (float): Coordenada Y del centro.
        r (float): Radio del círculo.
        pv (float): Métrica de error de pico a valle (Peak-to-Valley).

    Raises:
        TypeError: si puntos0 no es un numpy.ndarray.
        ValueError: si la forma es inválida, N < 3, los puntos son colineales
            (o coinciden), o el ajuste produce un radicando no positivo.
    """
    # --- Validación de tipo ---
    if not isinstance(puntos0, np.ndarray):
        raise TypeError(
            "circuloSimple: se esperaba un numpy.ndarray de forma (N, 2)"
        )

    # --- Validación de forma ---
    if puntos0.ndim != 2 or puntos0.shape[1] != 2:
        raise ValueError(
            f"circuloSimple: el arreglo debe tener forma (N, 2) con coordenadas (x, y); "
            f"recibido shape {puntos0.shape}"
        )

    nr, _ = puntos0.shape

    # --- Casos degenerados por cantidad de puntos ---
    if nr == 0:
        raise ValueError(
            "circuloSimple: el anillo quedó vacío; revise la detección de bordes o el radio"
        )
    if nr == 2:
        raise ValueError(
            "circuloSimple: dos puntos definen una línea, no un círculo único; "
            "se necesitan al menos 3"
        )
    if nr < 3:
        raise ValueError(
            "circuloSimple: insuficientes puntos para ajuste; se necesitan al menos 3"
        )

    # --- Guard de colinealidad ---
    # El número de condición de la matriz cruda NO sirve como umbral porque
    # depende del centro y del radio: un anillo válido de r = 428 centrado en
    # (1150, 1000) da 6.9e3, y una recta con ruido puede dar 9.3e3. Centrando en
    # el centroide y escalando por el RMS radial, el cond sí separa (ver el
    # umbral medido arriba) y el escalado es geométricamente neutro.
    desplazados = puntos0 - puntos0.mean(axis=0)
    escala = np.sqrt(np.mean(np.sum(desplazados**2, axis=1)))
    if not np.isfinite(escala) or escala <= 0.0:
        raise ValueError(
            "circuloSimple: todos los puntos coinciden; no hay círculo determinable"
        )

    normalizados = desplazados / escala
    A_norm = np.column_stack(
        (2.0 * normalizados[:, 0], 2.0 * normalizados[:, 1], -np.ones(nr))
    )
    condicion = np.linalg.cond(A_norm)
    if not np.isfinite(condicion) or condicion > UMBRAL_CONDICION_NORMALIZADA:
        raise ValueError(
            "circuloSimple: los puntos son colineales; no hay círculo único determinable"
        )

    # --- Construir la matriz A de forma eficiente (N x 3) ---
    # Se ajusta sobre las coordenadas originales para no alterar el resultado
    # numérico histórico; la normalización se usa solo para decidir si el
    # sistema está bien condicionado.
    A = np.zeros((nr, 3))
    A[:, 0] = 2 * puntos0[:, 0]  # Equivalente a la col 1 de MATLAB (X)
    A[:, 1] = 2 * puntos0[:, 1]  # Equivalente a la col 2 de MATLAB (Y)
    A[:, 2] = -1

    # --- Construir el vector y (N,) ---
    # Se usa np.sum con axis=1 para elevar al cuadrado y sumar X e Y en un solo paso
    y_vec = np.sum(puntos0**2, axis=1)

    # --- Resolver por mínimos cuadrados de forma numéricamente estable ---
    # np.linalg.lstsq simula exactamente el operador '\' (backslash) de MATLAB
    sol, _, _, _ = np.linalg.lstsq(A, y_vec, rcond=None)

    x_c = sol[0]
    y_c = sol[1]
    s = sol[2]

    # --- Calcular el radio ---
    # Rama defensiva: con el guard de colinealidad activo no se ha encontrado
    # ninguna entrada alcanzable que produzca radicando <= 0 (0 de 200 000
    # conjuntos aleatorios), pero se conserva por seguridad numérica.
    radicando = x_c**2 + y_c**2 - s
    if radicando <= 0:
        raise ValueError(
            "circuloSimple: resultado matemático inválido; "
            "los puntos no definen un círculo real"
        )

    r = np.sqrt(radicando)

    # --- PASO VECTORIZADO: Calcula la distancia de TODOS los puntos al centro al mismo tiempo ---
    distancias = np.sqrt((puntos0[:, 0] - x_c)**2 + (puntos0[:, 1] - y_c)**2)
    res = np.abs(distancias - r)

    # --- Métrica de error (Pico a Valle) ---
    pv = float(np.max(res) - np.min(res))

    return float(x_c), float(y_c), float(r), float(pv)
