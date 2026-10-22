import numpy as np

def LinearInterpolation(MG, Gx, Gy, angle):
    """
    Supresión de No Máximos: Sectores angulares de Canny clásicos
    con precisión de interpolación lineal subpíxel.
    
    Parameters:
    MG (numpy.ndarray): Magnitud del gradiente.
    Gx (numpy.ndarray): Gradiente en X.
    Gy (numpy.ndarray): Gradiente en Y.
    angle (numpy.ndarray): Ángulos en grados (rango [0, 360) o [-180, 180]).
    
    Returns:
    numpy.ndarray: Matriz de magnitudes filtrada con los picos máximos.
    """
    output = np.zeros_like(MG)
    
    # 1. Asegurar ángulos en el rango estándar [0, 360) como en tu NonMaxSupDTh
    angle_deg = np.mod(angle, 360)
    
    # 2. Calcular los pesos locales para la interpolación (Evitando división por cero)
    abs_Gx = np.abs(Gx)
    abs_Gy = np.abs(Gy)
    max_G = np.maximum(abs_Gx, abs_Gy)
    max_G_safe = np.where(max_G == 0, 1.0, max_G)
    
    w_x = abs_Gx / max_G_safe  # Relación de peso en el eje X
    w_y = abs_Gy / max_G_safe  # Relación de peso en el eje Y

    # 3. Rebanado (Slices) de los 8 vecinos de la matriz de magnitud
    c  = MG[1:-1, 1:-1]     # Centro (i, j)
    E  = MG[1:-1, 2:]       # (i, j+1)
    W  = MG[1:-1, :-2]      # (i, j-1)
    N  = MG[:-2, 1:-1]      # (i-1, j)
    S  = MG[2:, 1:-1]       # (i+1, j)
    NE = MG[:-2, 2:]        # (i-1, j+1)
    NW = MG[:-2, :-2]       # (i-1, j-1)
    SE = MG[2:, 2:]         # (i+1, j+1)
    SW = MG[2:, :-2]        # (i+1, j-1)
    
    # Slices de control para la zona interna
    ang = angle_deg[1:-1, 1:-1]
    weight_x = w_x[1:-1, 1:-1]
    weight_y = w_y[1:-1, 1:-1]
    
    # 4. Clasificación por Sectores con Interpolación
    
    # --- Sector 0° / 180° (Horizontal) ---
    mask_0 = ((ang > 337.5) | (ang <= 22.5)) | ((ang > 157.5) & (ang <= 202.5))
    yBot0 = (SE - E) * weight_y + E
    yTop0 = (NW - W) * weight_y + W
    v0 = mask_0 & (c >= yBot0) & (c >= yTop0)
    
    # --- Sector 45° / 225° ---
    mask_45 = ((ang >= 22.5) & (ang < 67.5)) | ((ang > 202.5) & (ang <= 247.5))
    yBot45 = (SE - S) * weight_x + S
    yTop45 = (NW - N) * weight_x + N
    v45 = mask_45 & (c > yBot45) & (c > yTop45)
    
    # --- Sector 90° / 270° (Vertical) ---
    mask_90 = ((ang > 67.5) & (ang <= 112.5)) | ((ang > 247.5) & (ang <= 292.5))
    yBot90 = (SE - S) * weight_x + S
    yTop90 = (NW - N) * weight_x + N
    v90 = mask_90 & (c > yBot90) & (c > yTop90)
    
    # --- Sector 135° / 315° ---
    mask_135 = ((ang > 112.5) & (ang <= 157.5)) | ((ang > 292.5) & (ang <= 337.5))
    yBot135 = (SW - W) * weight_y + W
    yTop135 = (NE - E) * weight_y + E
    v135 = mask_135 & (c > yBot135) & (c > yTop135)
    
    # 5. Combinar los máximos locales de todos los sectores
    keep = v0 | v45 | v90 | v135
    
    # Asignar los picos conservados a la salida
    output[1:-1, 1:-1] = np.where(keep, c, 0.0)
    
    return output
    

def NMS_Parabolic(MG, angle):
    """
    Supresión de No Máximos con Interpolación Parabólica de Subpíxel.
    Utiliza un ajuste cuadrático de 3 puntos en la dirección del gradiente.
    """
    output = np.zeros_like(MG)
    eps = 1e-5  # Evitar división por cero
    
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
    # Vecinos involucrados: Oeste (W), Centro (C), Este (E)
    mask_0 = ((ang > 337.5) | (ang <= 22.5)) | ((ang > 157.5) & (ang <= 202.5))
    denom_0 = 2 * (W - 2 * C + E)
    denom_0 = np.where(denom_0 == 0, eps, denom_0)
    yMax0 = C - ((W - E) ** 2) / (4 * denom_0) # Vértice de la parábola
    # Es un máximo local si C es mayor o igual que sus vecinos inmediatos
    v0 = mask_0 & (C >= W) & (C >= E)
    
    # --- Sector 45° / 225° (Diagonal) ---
    # Vecinos involucrados: Suroeste (SW), Centro (C), Noreste (NE)
    mask_45 = ((ang >= 22.5) & (ang < 67.5)) | ((ang > 202.5) & (ang <= 247.5))
    denom_45 = 2 * (SW - 2 * C + NE)
    denom_45 = np.where(denom_45 == 0, eps, denom_45)
    yMax45 = C - ((SW - NE) ** 2) / (4 * denom_45)
    v45 = mask_45 & (C >= SW) & (C >= NE)
    
    # --- Sector 90° / 270° (Vertical) ---
    # Vecinos involucrados: Norte (N), Centro (C), Sur (S)
    mask_90 = ((ang > 67.5) & (ang <= 112.5)) | ((ang > 247.5) & (ang <= 292.5))
    denom_90 = 2 * (N - 2 * C + S)
    denom_90 = np.where(denom_90 == 0, eps, denom_90)
    yMax90 = C - ((N - S) ** 2) / (4 * denom_90)
    v90 = mask_90 & (C >= N) & (C >= S)
    
    # --- Sector 135° / 315° (Diagonal Opuesta) ---
    # Vecinos involucrados: Noroeste (NW), Centro (C), Sureste (SE)
    mask_135 = ((ang > 112.5) & (ang <= 157.5)) | ((ang > 292.5) & (ang <= 337.5))
    denom_135 = 2 * (NW - 2 * C + SE)
    denom_135 = np.where(denom_135 == 0, eps, denom_135)
    yMax135 = C - ((NW - SE) ** 2) / (4 * denom_135)
    v135 = mask_135 & (C >= NW) & (C >= SE)
    
    # Combinar los píxeles que son picos reales en sus respectivos modelos parabólicos
    keep = v0 | v45 | v90 | v135
    
    # Guardamos el valor estimado del pico interpolado (yMax) en lugar de la magnitud discreta C
    # Esto te dará valores de gradiente mucho más finos y precisos
    yMax_total = np.zeros_like(C)
    yMax_total[mask_0] = yMax0[mask_0]
    yMax_total[mask_45] = yMax45[mask_45]
    yMax_total[mask_90] = yMax90[mask_90]
    yMax_total[mask_135] = yMax135[mask_135]
    
    output[1:-1, 1:-1] = np.where(keep, yMax_total, 0.0)
    
    return output

def NMS_Gaussian(MG, angle):
    """
    NMS con Interpolación Gaussiana de Subpíxel mediante espacio logarítmico.
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

def Interpolation_old(MG, Gx, Gy, angle):
    #    Supresión de No Máximos (NMS) con interpolación lineal subpíxel.
    
    #row, col = MG.shape
    output = np.zeros_like(MG)
    
    #angle = np.degrees(angle)
    
    # Evitar división por cero: creamos una copia de MG donde los ceros son 1
    # Esto no afecta el resultado porque donde MG es 0, el output final será 0
    MG_safe = np.where(MG == 0, 1.0, MG)
    
    # Normalizar gradientes
    Gx_max = np.max(np.abs(Gx))
    Gy_max = np.max(np.abs(Gy))
    if Gx_max > 0:
        Gx = Gx / Gx_max
    if Gy_max > 0:
        Gy = Gy / Gy_max
    
    x_est_y = np.abs(Gy / MG_safe)
    x_est_x = np.abs(Gx / MG_safe) 

    # Creamos las matrices desplazadas (Slices) para los vecinos (i, j)
    # Ignoramos los bordes (equivalente a for i=2:row-1 en MATLAB, que es 1:-1 en Python)
    c  = MG[1:-1, 1:-1]     # Centro (i, j)
    
    # Vecinos para interpolación
    E  = MG[1:-1, 2:]       # (i, j+1)
    W  = MG[1:-1, :-2]      # (i, j-1)
    N  = MG[:-2, 1:-1]      # (i-1, j)
    S  = MG[2:, 1:-1]       # (i+1, j)
    NE = MG[:-2, 2:]        # (i-1, j+1)
    NW = MG[:-2, :-2]       # (i-1, :-2)
    SE = MG[2:, 2:]         # (i+1, j+1)
    SW = MG[2:, :-2]        # (i+1, :-2)
    
    # Slices correspondientes para ángulos y estimaciones
    ang = angle[1:-1, 1:-1]
    x_y = x_est_y[1:-1, 1:-1]
    x_x = x_est_x[1:-1, 1:-1]
    
    # --- SECTOR 1: 0° a 45° y -135° a -180° ---
    m1 = ((ang >= 0) & (ang <= 45)) | ((ang < -135) & (ang >= -180))
    yBot1 = (SE - E) * x_y + E
    yTop1 = (NW - W) * x_y + W
    v1 = (c >= yBot1) & (c >= yTop1) & m1
    
    # --- SECTOR 2: 45° a 90° y -90° a -135° ---
    m2 = ((ang > 45) & (ang <= 90)) | ((ang < -90) & (ang >= -135))
    yBot2 = (SE - S) * x_x + S
    yTop2 = (NW - N) * x_x + N
    v2 = (c >= yBot2) & (c >= yTop2) & m2
    
    # --- SECTOR 3: 90° a 135° y -45° a -90° ---
    m3 = ((ang > 90) & (ang <= 135)) | ((ang < -45) & (ang >= -90))
    yBot3 = (SW - S) * x_x + S
    yTop3 = (NE - N) * x_x + N
    v3 = (c >= yBot3) & (c >= yTop3) & m3
    
    # --- SECTOR 4: 135° a 180° y 0° a -45° ---
    m4 = ((ang > 135) & (ang <= 180)) | ((ang < 0) & (ang >= -45))
    yBot4 = (SW - W) * x_y + W
    yTop4 = (NE - E) * x_y + E
    v4 = (c >= yBot4) & (c >= yTop4) & m4
    
    # Unir todas las máscaras donde se cumple la condición de máximo local
    keep = v1 | v2 | v3 | v4
    
    # Asignar valores a la matriz de salida (el centro interno de la imagen)
    output[1:-1, 1:-1] = np.where(keep, c, 0)
    return output

def DobleThreshold(M, angle, thresh):
    """
    Realiza la Supresión de No Máximos y Umbralizado Doble de forma vectorizada.
    
    Parameters:
    M (numpy.ndarray): Matriz con la magnitud del gradiente.
    angle (numpy.ndarray): Matriz con los ángulos del gradiente en grados.
    thresh (float): Umbral superior base.
    
    Returns:
    gnh (numpy.ndarray): Matriz binaria con los bordes fuertes (valores 1.0).
    gnl (numpy.ndarray): Matriz con las intensidades de los bordes débiles.
    """
    # Forzar límite superior del umbral
    if thresh > 1.0:
        thresh = 1.0
        
    uthresh = thresh
    #lthresh = thresh * 0.4
    lthresh = thresh * thresh
    
    
    nr, nc = M.shape
    gnl = np.zeros((nr, nc))
    gnh = np.zeros((nr, nc))
    
    """# Asegurar que los ángulos estén en el rango [0, 360)
    angle_deg = np.mod(angle, 360)
    
    # Crear máscaras para cada una de las 4 direcciones principales
    # Horizontal (0 y 180 grados)
    mask_0 = ((angle_deg > 337.5) | (angle_deg <= 22.5)) | ((angle_deg > 157.5) & (angle_deg <= 202.5))
    
    # 45 grados
    mask_45 = ((angle_deg >= 22.5) & (angle_deg < 67.5)) | ((angle_deg > 202.5) & (angle_deg <= 247.5))
    
    # 90 grados
    mask_90 = ((angle_deg > 67.5) & (angle_deg <= 112.5)) | ((angle_deg > 247.5) & (angle_deg <= 292.5))
    
    # 135 grados
    mask_135 = ((angle_deg > 112.5) & (angle_deg <= 157.5)) | ((angle_deg > 292.5) & (angle_deg <= 337.5))
    
    # Inicializar matriz para guardar los máximos locales
    is_max = np.zeros((nr, nc), dtype=bool)
    
    # Evitar los bordes exteriores mediante rebanado (Slicing) de 1 a -1
    
    # Vectorización Horizontal: Comparar con vecinos izquierda (j-1) y derecha (j+1)
    is_max[1:-1, 1:-1] |= mask_0[1:-1, 1:-1] & (M[1:-1, 1:-1] >= M[1:-1, :-2]) & (M[1:-1, 1:-1] >= M[1:-1, 2:])
    
    # Vectorización 45°: Comparar con diagonal arriba-izquierda (i-1, j-1) y abajo-derecha (i+1, j+1)
    is_max[1:-1, 1:-1] |= mask_45[1:-1, 1:-1] & (M[1:-1, 1:-1] > M[:-2, :-2]) & (M[1:-1, 1:-1] > M[2:, 2:])
    
    # Vectorización 90°: Comparar con vecinos arriba (i-1) y abajo (i+1)
    is_max[1:-1, 1:-1] |= mask_90[1:-1, 1:-1] & (M[1:-1, 1:-1] > M[:-2, 1:-1]) & (M[1:-1, 1:-1] > M[2:, 1:-1])
    
    # Vectorización 135°: Comparar con diagonal abajo-izquierda (i+1, j-1) y arriba-derecha (i-1, j+1)
    is_max[1:-1, 1:-1] |= mask_135[1:-1, 1:-1] & (M[1:-1, 1:-1] > M[2:, :-2]) & (M[1:-1, 1:-1] > M[:-2, 2:])"""
    
    
    gnh[M >= uthresh] = 1.0
    gnl[(M >= lthresh) & (M < uthresh)] = M[(M >= lthresh) & (M < uthresh)]
    #gnl[(M >= lthresh) & (M < uthresh)] = 1 
    
    # Aplicar el Doble Umbral simultáneamente usando máscaras booleanas globales
    """high_mask = is_max & (M >= uthresh)
    low_mask = is_max & (M >= lthresh) & (M < uthresh)
    
    # Asignación final de bordes
    gnh[high_mask] = 1.0
    gnl[low_mask] = M[low_mask]"""
    
    return gnh, gnl
