import numpy as np


def Circulo_simple(puntos0):
    """
    Ajusta un círculo a un conjunto de puntos usando mínimos cuadrados.
    Versión optimizada y 100% vectorizada, con validación de entrada.

    Parameters:
        puntos0 (numpy.ndarray): Matriz de N x 2 con las coordenadas (X, Y) de los puntos.
        
    Returns:
        x_c (float): Coordenada X del centro.
        y_c (float): Coordenada Y del centro.
        r (float): Radio del círculo.
        pv (float): Métrica de error de pico a valle (Peak-to-Valley).
    
    Raises:
        TypeError: si puntos0 no es un numpy.ndarray.
        ValueError: si la forma es inválida, N < 3, colinealidad o radicando negativo.
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

    nr, nc = puntos0.shape

    # Caso: vacío o muy pocos puntos
    if nr == 0:
        raise ValueError(
            "circuloSimple: el anillo quedó vacío; revise la detección de bordes o el radio"
        )
    if nr < 3:
        raise ValueError(
            "circuloSimple: insuficientes puntos para ajuste; se necesitan al menos 3"
        )

    # --- Construir la matriz A de forma eficiente (N x 3) ---
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