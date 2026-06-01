import numpy as np

def Interpolation(MG, Gx, Gy, angle):
    """
    Non-Maximum Suppression with interpolation for Canny edge detection.
    
    Parameters:
        MG: Magnitude of gradient (2D numpy array)
        angle: Angle of gradient in degrees (2D numpy array)
        Gx: Gradient in x direction (2D numpy array)
        Gy: Gradient in y direction (2D numpy array)
    
    Returns:
        output: Suppressed magnitude (2D numpy array)
    """
    row, col = MG.shape
    output = np.zeros((row, col), dtype=MG.dtype)
    
    # Normalizar Gx y Gy
    Gx = Gx / np.max(Gx)
    Gy = Gy / np.max(Gy)
    
    # Iterar sobre píxeles interiores (evitando bordes)
    for i in range(1, row-1):
        for j in range(1, col-1):
            ang = angle[i, j]
            
            # Primer caso: 0° a 45° o -180° a -135°
            if (ang >= 0 and ang <= 45) or (ang < -135 and ang >= -180):
                yBot = np.array([MG[i, j+1], MG[i+1, j+1]])
                yTop = np.array([MG[i, j-1], MG[i-1, j-1]])
                x_est = abs(Gy[i, j] / MG[i, j])
                
                bot_val = (yBot[1] - yBot[0]) * x_est + yBot[0]
                top_val = (yTop[1] - yTop[0]) * x_est + yTop[0]
                
                if MG[i, j] >= bot_val and MG[i, j] >= top_val:
                    output[i, j] = MG[i, j]
                else:
                    output[i, j] = 0
                    
            # Segundo caso: 45° a 90° o -135° a -90°
            elif (ang > 45 and ang <= 90) or (ang < -90 and ang >= -135):
                yBot = np.array([MG[i+1, j], MG[i+1, j+1]])
                yTop = np.array([MG[i-1, j], MG[i-1, j-1]])
                x_est = abs(Gx[i, j] / MG[i, j])
                
                bot_val = (yBot[1] - yBot[0]) * x_est + yBot[0]
                top_val = (yTop[1] - yTop[0]) * x_est + yTop[0]
                
                if MG[i, j] >= bot_val and MG[i, j] >= top_val:
                    output[i, j] = MG[i, j]
                else:
                    output[i, j] = 0
                    
            # Tercer caso: 90° a 135° o -90° a -45°
            elif (ang > 90 and ang <= 135) or (ang < -45 and ang >= -90):
                yBot = np.array([MG[i+1, j], MG[i+1, j-1]])
                yTop = np.array([MG[i-1, j], MG[i-1, j+1]])
                x_est = abs(Gx[i, j] / MG[i, j])
                
                bot_val = (yBot[1] - yBot[0]) * x_est + yBot[0]
                top_val = (yTop[1] - yTop[0]) * x_est + yTop[0]
                
                if MG[i, j] >= bot_val and MG[i, j] >= top_val:
                    output[i, j] = MG[i, j]
                else:
                    output[i, j] = 0
                    
            # Cuarto caso: 135° a 180° o -45° a 0°
            elif (ang > 135 and ang <= 180) or (ang < 0 and ang >= -45):
                yBot = np.array([MG[i, j-1], MG[i+1, j-1]])
                yTop = np.array([MG[i, j+1], MG[i-1, j+1]])
                x_est = abs(Gy[i, j] / MG[i, j])
                
                bot_val = (yBot[1] - yBot[0]) * x_est + yBot[0]
                top_val = (yTop[1] - yTop[0]) * x_est + yTop[0]
                
                if MG[i, j] >= bot_val and MG[i, j] >= top_val:
                    output[i, j] = MG[i, j]
                else:
                    output[i, j] = 0
    
    return output

def DobleThreshold(M, angle, thresh):
    """
    Traducción directa del código MATLAB sin optimizaciones.
    Se aplicaron las correcciones técnicas clave:
    - Lógica de 135 grados completada
    - Bloques de umbral anidados agregados
    - Cierre de ciclos estructurales
    """
    nr, nc = M.shape
    gnl = np.zeros((nr, nc))
    gnh = np.zeros((nr, nc))
    
    if thresh > 1.0:
        thresh = 1.0
    
    uthresh = thresh
    lthresh = thresh * thresh
    
    for i in range(1, nr - 1):  # Equivalente a 2:nr-1 en MATLAB
        for j in range(1, nc - 1):  # Equivalente a 2:nc-1 en MATLAB
            dirGradiente = angle[i, j]
            if dirGradiente < 0:
                dirGradiente = 360 + dirGradiente
            
            # Horizontal (0 or 180 degrees)
            if ((dirGradiente > 337.5) or (dirGradiente <= 22.5)) or \
               ((dirGradiente > 157.5) and (dirGradiente <= 202.5)):
                if (M[i, j] >= M[i, j+1]) and (M[i, j] >= M[i, j-1]):
                    if M[i, j] >= lthresh:
                        if M[i, j] >= uthresh:
                            gnh[i, j] = 1
                        else:
                            gnl[i, j] = M[i, j]
            
            # 45 degrees
            if ((dirGradiente >= 22.5) and (dirGradiente < 67.5)) or \
               ((dirGradiente > 202.5) and (dirGradiente <= 247.5)):
                if (M[i, j] > M[i+1, j+1]) and (M[i, j] > M[i-1, j-1]):
                    if M[i, j] >= lthresh:
                        if M[i, j] >= uthresh:
                            gnh[i, j] = 1
                        else:
                            gnl[i, j] = M[i, j]
            
            # 90 degrees
            if ((dirGradiente > 67.5) and (dirGradiente <= 112.5)) or \
               ((dirGradiente > 247.5) and (dirGradiente <= 292.5)):
                if (M[i, j] > M[i+1, j]) and (M[i, j] > M[i-1, j]):
                    if M[i, j] >= lthresh:
                        if M[i, j] >= uthresh:
                            gnh[i, j] = 1
                        else:
                            gnl[i, j] = M[i, j]
            
            # 135 degrees
            if ((dirGradiente > 112.5) and (dirGradiente <= 157.5)) or \
               ((dirGradiente > 292.5) and (dirGradiente <= 337.5)):
                if (M[i, j] > M[i+1, j-1]) and (M[i, j] > M[i-1, j+1]):
                    if M[i, j] >= lthresh:
                        if M[i, j] >= uthresh:
                            gnh[i, j] = 1
                        else:
                            gnl[i, j] = M[i, j]
    
    return gnh, gnl