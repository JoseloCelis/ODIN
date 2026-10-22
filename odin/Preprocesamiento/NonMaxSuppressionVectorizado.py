import numpy as np

def LinearInterpolation(MG, Gx, Gy, angle):
    """
    Supresión de No Máximos: interpolación lineal subpíxel entre los dos
    vecinos discretos que estrangulan la dirección de la línea del gradiente
    (ángulo mod 180°), en los dos extremos de dicha línea.

    Convención de ángulos (igual que MagFase): 0° = +x (columnas/Este),
    90° = +fila (hacia abajo/Sur), 45° = Sureste, etc.

    Parameters:
    MG (numpy.ndarray): Magnitud del gradiente.
    Gx (numpy.ndarray): Gradiente en X (reservado por compatibilidad; el
        cálculo usa únicamente `angle`).
    Gy (numpy.ndarray): Gradiente en Y (idem).
    angle (numpy.ndarray): Ángulos en grados (rango [0, 360) o [-180, 180]).

    Returns:
    numpy.ndarray: Matriz de magnitudes filtrada: los picos locales conservan
    su magnitud; el resto (y el borde de 1 píxel) queda en 0.
    """
    output = np.zeros_like(MG)

    # 8 vecinos direccionales indexados por su ángulo/45 (0..7):
    # 0=E, 1=SE, 2=S, 3=SW, 4=W, 5=NW, 6=N, 7=NE
    C = MG[1:-1, 1:-1]
    vecinos = np.stack([
        MG[1:-1, 2:],    # 0:   Este
        MG[2:, 2:],      # 1:   Sureste
        MG[2:, 1:-1],    # 2:   Sur
        MG[2:, :-2],     # 3:   Suroeste
        MG[1:-1, :-2],   # 4:   Oeste
        MG[:-2, :-2],    # 5:   Noroeste
        MG[:-2, 1:-1],   # 6:   Norte
        MG[:-2, 2:],     # 7:   Noreste
    ])

    # La comparación es sobre el EJE del gradiente (mod 180°), no sobre el
    # vector: así el cuadrante (signo de Gx/Gy) no cambia los vecinos y el
    # detector es simétrico por construcción (spec non-max-sup, R3/D1)
    phi = np.mod(angle, 180.0)[1:-1, 1:-1]
    sector = np.floor(phi / 45.0).astype(int)   # dirección de referencia d1 (0..3)
    f = (phi - 45.0 * sector) / 45.0            # fracción angular de interpolación [0, 1)

    filas = np.arange(C.shape[0])[:, None]
    cols = np.arange(C.shape[1])[None, :]

    # Vecinos que estrangan la dirección en cada extremo del eje
    i1 = sector            # d1 = 45·sector  (0°, 45°, 90° o 135°)
    i2 = sector + 1        # d2 = d1 + 45°   (45°, 90°, 135° o 180°)
    N1 = vecinos[i1, filas, cols]
    N2 = vecinos[i2, filas, cols]
    # Extremo opuesto del eje: +180° = +4 posiciones en el arreglo circular
    N1p = vecinos[(i1 + 4) % 8, filas, cols]
    N2p = vecinos[(i2 + 4) % 8, filas, cols]

    # Interpolación lineal en cada extremo
    v_este = N2 * f + N1 * (1.0 - f)
    v_opuesto = N2p * f + N1p * (1.0 - f)

    # Tie-breaking consistente en los 4 sectores (>=: nunca pierde máximos)
    keep = (C >= v_este) & (C >= v_opuesto)

    output[1:-1, 1:-1] = np.where(keep, C, 0.0)

    return output


def DobleThreshold(M, thresh):
    """
    Umbralizado doble vectorizado sobre la magnitud normalizada.

    Parameters:
    M (numpy.ndarray): Matriz con la magnitud del gradiente en [0, 1].
    thresh (float): Umbral superior.

    Returns:
    gnh (numpy.ndarray): Matriz binaria con los bordes fuertes (valores 1.0).
    gnl (numpy.ndarray): Matriz con las intensidades de los bordes débiles.
    """
    # Forzar límite superior del umbral
    if thresh > 1.0:
        thresh = 1.0
        
    uthresh = thresh
    # Umbral inferior = thresh² (decision documentada en el spec
    # non-max-sup, R5.3; el valor original era 0.4·thresh)
    lthresh = thresh * thresh
    
    
    nr, nc = M.shape
    gnl = np.zeros((nr, nc))
    gnh = np.zeros((nr, nc))
    
    gnh[M >= uthresh] = 1.0
    gnl[(M >= lthresh) & (M < uthresh)] = M[(M >= lthresh) & (M < uthresh)]
    
    return gnh, gnl
