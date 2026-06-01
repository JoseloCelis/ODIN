import numpy as np

def Interpolation(MG, Gx, Gy, angle):
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
    lthresh = thresh * thresh
    
    nr, nc = M.shape
    gnl = np.zeros((nr, nc))
    gnh = np.zeros((nr, nc))
    
    # Asegurar que los ángulos estén en el rango [0, 360)
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
    is_max[1:-1, 1:-1] |= mask_135[1:-1, 1:-1] & (M[1:-1, 1:-1] > M[2:, :-2]) & (M[1:-1, 1:-1] > M[:-2, 2:])
    
    # Aplicar el Doble Umbral simultáneamente usando máscaras booleanas globales
    high_mask = is_max & (M >= uthresh)
    low_mask = is_max & (M >= lthresh) & (M < uthresh)
    
    # Asignación final de bordes
    gnh[high_mask] = 1.0
    gnl[low_mask] = M[low_mask]
    
    return gnh, gnl
