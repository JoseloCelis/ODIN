"""Supresión de No Máximos (NMS) con interpolación subpíxel (etapa ③).

Contiene:
    - LinearInterpolation(MG, Gx, Gy, angle): NMS por interpolación lineal
      subpíxel (activa en el pipeline).
    - DobleThreshold(M, thresh): umbralizado doble (activa en el pipeline;
      el parámetro `angle` fue eliminado por D3 — sin uso).
    - NMS_Parabolic(MG, angle): NMS con ajuste parabólico de 3 puntos
      (experimental, recuperado tras verificación de utilidad).
    - NMS_Gaussian(MG, angle): NMS con interpolación parabólica en log-espacio
      (experimental, recuperado tras verificación de utilidad).

Todas son funciones puras: numpy.ndarray de entrada/salida, sin dependencias
de UI (gi, Gtk, Gdk, Adw, cairo, matplotlib).
"""

import numpy as np


def NonMaxSup(MG, Gx, Gy, angle):
    """Alias de LinearInterpolation para compatibilidad."""
    return LinearInterpolation(MG, Gx, Gy, angle)


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


def NMS_Parabolic(MG, angle):
    """
    NMS con interpolación parabólica de subpíxel: estima el VALOR del pico
    con ajuste cuadrático de 3 puntos a lo largo del eje del gradiente.

    Recuperado y verificado (spec non-max-sup, design.md §5): en un perfil
    cuadratico con vertex en x0=2.3 reconstruye el valor real del vertex con
    error 0.000000 (LinearInterpolation devuelve el discreto: error 0.0081).
    Supera en simetría y adelgazamiento las mismas baterías que
    LinearInterpolation (20 semillas).

    ADVERTENCIA: el valor interpolado del pico PUEDE EXCEDER max(MG) (es una
    estimación del pico real, no una magnitud normalizada). No es apto como
    entrada de Otsu/DobleThreshold sin recortar; sí es apto para medición
    geométrica de subpíxel (etapas 7-9).

    Parameters:
    MG (numpy.ndarray): Magnitud del gradiente.
    angle (numpy.ndarray): Ángulos en grados (misma convención que MagFase).

    Returns:
    numpy.ndarray: Picos conservados con el valor parabólico estimado; resto 0.
    """
    output = np.zeros_like(MG)
    eps = 1e-5  # Evitar division por cero (protegido: el ajuste solo aplica
                # donde C >= vecinos, es decir curvatura hacia abajo)

    angle_deg = np.mod(angle, 360)

    # Vecinos de la matriz de magnitud
    C  = MG[1:-1, 1:-1]     # Centro (i, j)
    E  = MG[1:-1, 2:]       # Este
    W  = MG[1:-1, :-2]      # Oeste
    N  = MG[:-2, 1:-1]      # Norte
    S  = MG[2:, 1:-1]       # Sur
    NE = MG[:-2, 2:]        # Noreste
    NW = MG[:-2, :-2]       # Noroeste
    SE = MG[2:, 2:]         # Sureste
    SW = MG[2:, :-2]        # Suroeste

    ang = angle_deg[1:-1, 1:-1]

    # --- Sector 0° / 180° (Horizontal) ---
    mask_0 = ((ang > 337.5) | (ang <= 22.5)) | ((ang > 157.5) & (ang <= 202.5))
    denom_0 = 2 * (W - 2 * C + E)
    denom_0 = np.where(denom_0 == 0, eps, denom_0)
    yMax0 = C - ((W - E) ** 2) / (4 * denom_0) # Vértice de la parábola
    # Es un máximo local si C es mayor o igual que sus vecinos inmediatos
    v0 = mask_0 & (C >= W) & (C >= E)

    # --- Sector 45° / 225° (Diagonal) ---
    mask_45 = ((ang >= 22.5) & (ang < 67.5)) | ((ang > 202.5) & (ang <= 247.5))
    denom_45 = 2 * (SW - 2 * C + NE)
    denom_45 = np.where(denom_45 == 0, eps, denom_45)
    yMax45 = C - ((SW - NE) ** 2) / (4 * denom_45)
    v45 = mask_45 & (C >= SW) & (C >= NE)

    # --- Sector 90° / 270° (Vertical) ---
    mask_90 = ((ang > 67.5) & (ang <= 112.5)) | ((ang > 247.5) & (ang <= 292.5))
    denom_90 = 2 * (N - 2 * C + S)
    denom_90 = np.where(denom_90 == 0, eps, denom_90)
    yMax90 = C - ((N - S) ** 2) / (4 * denom_90)
    v90 = mask_90 & (C >= N) & (C >= S)

    # --- Sector 135° / 315° (Diagonal Opuesta) ---
    mask_135 = ((ang > 112.5) & (ang <= 157.5)) | ((ang > 292.5) & (ang <= 337.5))
    denom_135 = 2 * (NW - 2 * C + SE)
    denom_135 = np.where(denom_135 == 0, eps, denom_135)
    yMax135 = C - ((NW - SE) ** 2) / (4 * denom_135)
    v135 = mask_135 & (C >= NW) & (C >= SE)

    # Combinar los píxeles que son picos reales en sus respectivos modelos parabólicos
    keep = v0 | v45 | v90 | v135

    # Guardamos el valor estimado del pico interpolado (yMax) en lugar de la magnitud discreta C
    yMax_total = np.zeros_like(C)
    yMax_total[mask_0] = yMax0[mask_0]
    yMax_total[mask_45] = yMax45[mask_45]
    yMax_total[mask_90] = yMax90[mask_90]
    yMax_total[mask_135] = yMax135[mask_135]

    output[1:-1, 1:-1] = np.where(keep, yMax_total, 0.0)

    return output


def NMS_Gaussian(MG, angle):
    """
    NMS con interpolación parabólica en espacio logarítmico (perfil de
    intensidad modelado como gaussiano: su logaritmo es cuadrático).

    Recuperado y verificado (spec non-max-sup, design.md §5): error 0.0011
    contra el vertex real del perfil cuadrático de prueba (NMS_Parabolic da
    0.000000; el discreto, 0.0081). Mismas propiedades de simetría y
    adelgazamiento que LinearInterpolation en 20 semillas aleatorias.

    ADVERTENCIA: como NMS_Parabolic, el valor interpolado puede exceder
    max(MG); apto para medición de subpíxel, no como entrada de umbrales.

    Parameters:
    MG (numpy.ndarray): Magnitud del gradiente.
    angle (numpy.ndarray): Ángulos en grados (misma convención que MagFase).

    Returns:
    numpy.ndarray: Picos conservados con el valor estimado; resto 0.
    """
    output = np.zeros_like(MG)
    eps = 1e-5

    # Estabilizar las magnitudes para evitar log(0)
    MG_log = np.log(MG + 1e-6)
    angle_deg = np.mod(angle, 360)

    # Extraer vecinos en el espacio logarítmico para el cálculo matemático
    C_l  = MG_log[1:-1, 1:-1]
    E_l  = MG_log[1:-1, 2:]
    W_l  = MG_log[1:-1, :-2]
    N_l  = MG_log[:-2, 1:-1]
    S_l  = MG_log[2:, 1:-1]
    NE_l = MG_log[:-2, 2:]
    NW_l = MG_log[:-2, :-2]
    SE_l = MG_log[2:, 2:]
    SW_l = MG_log[2:, :-2]

    # Extraer vecinos en magnitud real para validar la condición de máximo local
    C  = MG[1:-1, 1:-1]
    E  = MG[1:-1, 2:]
    W  = MG[1:-1, :-2]
    N  = MG[:-2, 1:-1]
    S  = MG[2:, 1:-1]
    NE = MG[:-2, 2:]
    NW = MG[:-2, :-2]
    SE = MG[2:, 2:]
    SW = MG[2:, :-2]

    ang = angle_deg[1:-1, 1:-1]
    yMax_total = np.zeros_like(C)

    # --- Sector 0° / 180° ---
    mask_0 = ((ang > 337.5) | (ang <= 22.5)) | ((ang > 157.5) & (ang <= 202.5))
    denom_0 = 2 * (W_l - 2 * C_l + E_l)
    denom_0 = np.where(denom_0 == 0, eps, denom_0)
    yMax0_log = C_l - ((W_l - E_l) ** 2) / (4 * denom_0)
    v0 = mask_0 & (C >= W) & (C >= E)
    yMax_total[mask_0] = np.exp(yMax0_log[mask_0]) # Regresamos al espacio lineal exponencial

    # --- Sector 45° / 225° ---
    mask_45 = ((ang >= 22.5) & (ang < 67.5)) | ((ang > 202.5) & (ang <= 247.5))
    denom_45 = 2 * (SW_l - 2 * C_l + NE_l)
    denom_45 = np.where(denom_45 == 0, eps, denom_45)
    yMax45_log = C_l - ((SW_l - NE_l) ** 2) / (4 * denom_45)
    v45 = mask_45 & (C >= SW) & (C >= NE)
    yMax_total[mask_45] = np.exp(yMax45_log[mask_45])

    # --- Sector 90° / 270° ---
    mask_90 = ((ang > 67.5) & (ang <= 112.5)) | ((ang > 247.5) & (ang <= 292.5))
    denom_90 = 2 * (N_l - 2 * C_l + S_l)
    denom_90 = np.where(denom_90 == 0, eps, denom_90)
    yMax90_log = C_l - ((N_l - S_l) ** 2) / (4 * denom_90)
    v90 = mask_90 & (C >= N) & (C >= S)
    yMax_total[mask_90] = np.exp(yMax90_log[mask_90])

    # --- Sector 135° / 315° ---
    mask_135 = ((ang > 112.5) & (ang <= 157.5)) | ((ang > 292.5) & (ang <= 337.5))
    denom_135 = 2 * (NW_l - 2 * C_l + SE_l)
    denom_135 = np.where(denom_135 == 0, eps, denom_135)
    yMax135_log = C_l - ((NW_l - SE_l) ** 2) / (4 * denom_135)
    v135 = mask_135 & (C >= NW) & (C >= SE)
    yMax_total[mask_135] = np.exp(yMax135_log[mask_135])

    keep = v0 | v45 | v90 | v135
    output[1:-1, 1:-1] = np.where(keep, yMax_total, 0.0)

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
