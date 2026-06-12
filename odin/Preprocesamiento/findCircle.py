import numpy as np

def find_circle(detected_edges, re=0.0, centro=(0, 0)):
    """
    Filtra los puntos de la matriz DetectedEdges para aislar las coordenadas de un círculo.
    
    Casos de uso:
    - re > 0 : Filtra los puntos en un anillo de tolerancia [re-10, re+10] usando Hough.
    - re == 0: Aísla el segmento continuo más largo detectando saltos mayores a 6 píxeles.
    """
    
    xd, yd = centro
    # Extraer los índices mayores a 0 de la matriz de bordes
    # np.argwhere nos da [fila, columna] -> [Y, X]. Invertimos a [X, Y].
    puntos = np.argwhere(detected_edges > 0)[:, ::-1]
    
    if puntos.size == 0:
        return np.empty((0, 2))
        
        # -----------------------------------------------------------------
    # CASO 1: Búsqueda con parámetros de Hough (Un solo círculo o concéntricos juntos)
    # -----------------------------------------------------------------
    if re:
        # Calculamos la distancia euclidiana de todos los puntos al centro a la vez
        distancias = np.sqrt((puntos[:, 0] - xd)**2 + (puntos[:, 1] - yd)**2)
        
        # Filtramos los puntos que caen dentro del anillo de tolerancia de +/- 10 píxeles
        mascara = (distancias >= re - 10) & (distancias <= re + 10)
        puntos0 = puntos[mascara]
        
    # -----------------------------------------------------------------
    # CASO 2: re == 0 (Aislamiento automático del segmento continuo más largo)
    # -----------------------------------------------------------------
    else:
        puntos0 = puntos.copy()
        
        # --- ETAPA 1: Análisis en el eje X ---
        k = np.argsort(puntos0[:, 0])
        puntos_sorted = np.column_stack((puntos0[k, 0], puntos0[k, 1]))
        
        x = puntos_sorted[:, 0]
        y = puntos_sorted[:, 1]
        
        l = np.ones_like(x)
        if len(x) > 1:
            l[1:] = np.diff(x)
        l[l < 6] = 1
        
        k_indices = np.where(l > 6)[0]
        k_indices = np.concatenate(([0], k_indices, [len(x)]))
        
        diff_k = np.diff(k_indices)
        if diff_k.size > 0:
            max_idx = np.argmax(diff_k)
            l_final = np.zeros_like(x, dtype=bool)
            l_final[k_indices[max_idx]:k_indices[max_idx + 1]] = True
        else:
            l_final = np.ones_like(x, dtype=bool)
            
        puntosX = x[l_final]
        puntosY = y[l_final]
        puntos0 = np.column_stack((puntosY, puntosX))
        
        # --- ETAPA 2: Análisis en el eje Y ---
        k = np.argsort(puntos0[:, 0])
        puntos_sorted = np.column_stack((puntos0[k, 0], puntos0[k, 1]))
        
        x = puntos_sorted[:, 1]
        y = puntos_sorted[:, 0]
        
        l = np.ones_like(y)
        if len(y) > 1:
            l[1:] = np.diff(y)
        l[l <= 6] = 1
        
        k_indices = np.where(l > 6)[0]
        k_indices = np.concatenate(([0], k_indices, [len(y)]))
        
        diff_k = np.diff(k_indices)
        if diff_k.size > 0:
            max_idx = np.argmax(diff_k)
            l_final = np.zeros_like(y, dtype=bool)
            l_final[k_indices[max_idx]:k_indices[max_idx + 1]] = True
        else:
            l_final = np.ones_like(y, dtype=bool)
            
        puntosY = y[l_final]
        puntosX = x[l_final]
        puntos_res = np.column_stack((puntosY, puntosX))
        
        # Ordenamiento final idéntico a MATLAB
        k = np.argsort(puntos_res[:, 1])
        puntos0 = np.column_stack((puntos_res[k, 1], puntos_res[k, 0]))

    return puntos0

