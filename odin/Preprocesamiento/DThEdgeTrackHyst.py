import numpy as np
import sys
from scipy.ndimage import label, generate_binary_structure, binary_dilation

def EdgeTrack_Hyst(strong, weaks):
    """
    Realiza el umbralizado doble y el seguimiento de bordes por histéresis 
    de forma vectorizada (sin recursión).
    
    Parameters:
    MG (numpy.ndarray): Matriz de magnitudes (generalmente resultado de NonMaxSup).
    threshold (float): Umbral superior base.
    
    Returns:
    numpy.ndarray: Imagen binaria con los bordes finales (0 o 1).
    """
    
    print("--- DIAGNÓSTICO DE HISTÉRESIS ---")
    print(f"Máximo en fuertes: {np.max(strong)}")
    print(f"Máximo en debiles: {np.max(weaks)}")
    print(f"Píxeles verdaderos en strong_mask: {np.sum(strong > 0)}")
    print(f"Píxeles verdaderos en weak_mask: {np.sum(weaks > 0)}")
    
    # 1. Crear máscaras lógicas globales para bordes fuertes y débiles
    # (Evitamos los bucles for para clasificar los píxeles)
    strong_mask = strong > 0
    weak_mask = weaks > 0
    
    #strong_mask = MG > uthresh
    #weak_mask = (MG >= lthresh) & (MG <= uthresh)
    
    
    
    #uthresh = threshold
    #lthresh = threshold * threshold
    
    

    # Inicializar la imagen de salida vacía (bordes en 0 por defecto)
    weaks_labeled = np.zeros_like(weaks, dtype=np.uint8)
    output = np.zeros_like(strong, dtype=np.uint8)

    # En tu MATLAB ignoras el borde exterior de 1px en el primer bucle,
    # replicamos eso limpiando los extremos de las máscaras.
    #strong_mask[0, :] = strong_mask[-1, :] = strong_mask[:, 0] = strong_mask[:, -1] = False
    #weak_mask[0, :] = weak_mask[-1, :] = weak_mask[:, 0] = weak_mask[:, -1] = False
    
    # 2. Análisis de componentes conexas para la histéresis
    # Tu función buscaba en un vecindario de 7x7 (-3 a 3).
    # Definimos una estructura de conectividad (kernel) de 7x7 llena de 1s.
    # 2. El Truco del Vecindario 7x7:
    # Como SciPy exige que la conectividad para 'label' sea de 3x3, lo que hacemos
    # es "crecer" (dilatar) los bordes fuertes con un kernel de 7x7. 
    # Esto simula exactamente que el borde fuerte "alcanza" a los débiles a 3px de distancia.
    # 1. Dilatación de bordes fuertes
        
    dilation_kernel = np.ones((7,7), dtype=bool)
    strong_dilated = binary_dilation(strong_mask, structure=dilation_kernel)
    
    kernel = generate_binary_structure(2,2)
    #kernel = np.ones((3,3), dtype=bool)
    num_features = label(weak_mask, kernel, weaks_labeled)
    
    if num_features == 0:
        output[strong_mask] = True
        return output
    
    # 3. Identificar qué islas débiles tocan a los bordes fuertes dilatados
   # Evitamos el 0 (que representa el fondo) directamente en el filtro
    #touches_strong = weaks_labeled[strong_dilated.astype(bool)]
    #valores_interseccion = weaks_labeled[strong_dilated == True]
    
    connected_ids = np.unique(weaks_labeled[strong_dilated == True])
    connected_ids = connected_ids[connected_ids != 0]
    #connected_ids = np.unique(touches_strong[touches_strong != 0])
    
    # 4. Construir la imagen final
    output[strong_mask] = 255
    
    # 5. Activar bordes débiles conectados a fuertes
    if connected_ids.size > 0:
        connected_weak_mask = np.isin(weaks_labeled, connected_ids)
        output[connected_weak_mask] = 255
        
        
    print(f"Bordes fuertes recuperados: {np.sum(strong_mask)}")
    print(f"Islas débiles conectadas encontradas: {connected_ids.size} de {num_features}")
    print(f"Total de píxeles blancos en la salida: {np.sum(output == 255)}")
        
    return output


def DThEdgeTrack(MG, threshold):
    """
    Double Threshold Edge Tracking con histéresis.
    Traducción directa del código MATLAB sin optimizaciones.
    
    Parameters:
        MG: Matriz de magnitudes después de supresión no máxima
        threshold: Umbral superior (entre 0 y 1)
    
    Returns:
        MG: Matriz binaria de bordes detectados
    """
    row, col = MG.shape
    uthresh = threshold
    lthresh = threshold * threshold
    
    # Inicializar arrays de seguimiento
    strongEdgesRow = np.zeros(row * col, dtype=int)
    strongEdgesCol = np.zeros(row * col, dtype=int)
    weakEdgesRow = np.zeros(row * col, dtype=int)
    weakEdgesCol = np.zeros(row * col, dtype=int)
    strongIndex = 0  # Python usa índice 0
    weakIndex = 0    # Python usa índice 0
    
    # Primera pasada: clasificar píxeles
    for i in range(1, row - 1):  # Equivalente a 2:row-1 en MATLAB
        for j in range(1, col - 1):  # Equivalente a 2:col-1 en MATLAB
            if MG[i, j] > uthresh:  # Borde fuerte
                MG[i, j] = 1
                strongEdgesRow[strongIndex] = i
                strongEdgesCol[strongIndex] = j
                strongIndex = strongIndex + 1
            elif MG[i, j] < lthresh:  # No es borde
                MG[i, j] = 0
            else:  # Borde débil
                weakEdgesRow[weakIndex] = i
                weakEdgesCol[weakIndex] = j
                weakIndex = weakIndex + 1
    
    # Crear arrays de bordes (solo la parte usada)
    sEdges = np.column_stack((strongEdgesRow[:strongIndex], 
                               strongEdgesCol[:strongIndex]))
    wEdges = np.column_stack((weakEdgesRow[:weakIndex], 
                               weakEdgesCol[:weakIndex]))
    
    # Aumentar límite de recursión (equivalente a set(0,'RecursionLimit',10000))
    sys.setrecursionlimit(10000)
    
    # Segunda pasada: seguimiento de bordes por histéresis
    for i in range(strongIndex):
        MG = FindConnectedWeakEdges(MG, strongEdgesRow[i], strongEdgesCol[i])
    
    # Tercera pasada: limpiar bordes débiles no conectados
    for i in range(weakIndex):
        if MG[weakEdgesRow[i], weakEdgesCol[i]] != 1:
            MG[weakEdgesRow[i], weakEdgesCol[i]] = 0
    
    return MG


def FindConnectedWeakEdges(Gmag, row, col):
    """
    Función recursiva que encuentra bordes débiles conectados a bordes fuertes.
    
    Parameters:
        Gmag: Matriz de magnitudes
        row: Fila del píxel actual
        col: Columna del píxel actual
    
    Returns:
        Gmag: Matriz actualizada
    """
    for i in range(-3, 4):  # Equivalente a -3:1:3 en MATLAB
        for j in range(-3, 4):  # Equivalente a -3:1:3 en MATLAB
            # Verificar límites
            if (row + i > 0) and (col + j > 0) and \
               (row + i < Gmag.shape[0]) and (col + j < Gmag.shape[1]):
                # Si es borde débil (entre 0 y 1)
                if (Gmag[row + i, col + j] > 0) and (Gmag[row + i, col + j] < 1):
                    Gmag[row + i, col + j] = 1
                    # Llamada recursiva
                    Gmag = FindConnectedWeakEdges(Gmag, row + i, col + j)
    
    return Gmag