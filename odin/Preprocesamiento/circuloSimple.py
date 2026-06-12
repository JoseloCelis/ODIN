import numpy as np

def Circulo_simple(puntos0):
    """
    Ajusta un círculo a un conjunto de puntos usando mínimos cuadrados.
    Versión optimizada y 100% vectorizada.
    
    Parameters:
        puntos0 (numpy.ndarray): Matriz de N x 2 con las coordenadas (X, Y) de los puntos.
        
    Returns:
        x (float): Coordenada X del centro.
        y (float): Coordenada Y del centro.
        r (float): Radio del círculo.
        pv (float): Métrica de error de pico a valle (Peak-to-Valley).
    """
    nr, nc = puntos0.shape
    
    # 1. Construir la matriz A de forma eficiente (N x 3)
    A = np.zeros((nr, 3))
    A[:, 0] = 2 * puntos0[:, 0]  # Equivalente a la col 1 de MATLAB (X)
    A[:, 1] = 2 * puntos0[:, 1]  # Equivalente a la col 2 de MATLAB (Y)
    A[:, 2] = -1
    
    # 2. Construir el vector y (N,)
    # Se usa np.sum con axis=1 para elevar al cuadrado y sumar X e Y en un solo paso
    y_vec = np.sum(puntos0**2, axis=1)
    
    # 3. Resolver por mínimos cuadrados de forma numéricamente estable
    # np.linalg.lstsq simula exactamente el operador '\' (backslash) de MATLAB
    sol, _, _, _ = np.linalg.lstsq(A, y_vec, rcond=None)
    
    x_c = sol[0]
    y_c = sol[1]
    s = sol[2]
    
    # 4. Calcular el radio
    r = np.sqrt(x_c**2 + y_c**2 - s)
    
    # 5. PASO VECTORIZADO: Reemplaza el bucle 'for' de MATLAB
    # Calcula la distancia de TODOS los puntos al centro al mismo tiempo
    distancias = np.sqrt((puntos0[:, 0] - x_c)**2 + (puntos0[:, 1] - y_c)**2)
    res = np.abs(distancias - r)
    
    # 6. Métrica de error (Pico a Valle)
    pv = np.max(res) - np.min(res)
    
    return x_c, y_c, r, pv
