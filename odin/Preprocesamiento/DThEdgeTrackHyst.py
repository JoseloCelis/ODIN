import numpy as np
import sys
from scipy.ndimage import label

def EdgeTrack_Hyst(MG, threshold):
    """
    Realiza el umbralizado doble y el seguimiento de bordes por histéresis 
    de forma vectorizada (sin recursión).
    
    Parameters:
    MG (numpy.ndarray): Matriz de magnitudes (generalmente resultado de NonMaxSup).
    threshold (float): Umbral superior base.
    
    Returns:
    numpy.ndarray: Imagen binaria con los bordes finales (0 o 1).
    """
    uthresh = threshold
    lthresh = threshold * threshold
    
    # 1. Crear máscaras lógicas globales para bordes fuertes y débiles
    # (Evitamos los bucles for para clasificar los píxeles)
    strong_mask = MG > uthresh
    weak_mask = (MG >= lthresh) & (MG <= uthresh)
    
    # Inicializar la imagen de salida vacía (bordes en 0 por defecto)
    output = np.zeros_like(MG, dtype=np.uint8)
    
    # En tu MATLAB ignoras el borde exterior de 1px en el primer bucle,
    # replicamos eso limpiando los extremos de las máscaras.
    strong_mask[0, :] = strong_mask[-1, :] = strong_mask[:, 0] = strong_mask[:, -1] = False
    weak_mask[0, :] = weak_mask[-1, :] = weak_mask[:, 0] = weak_mask[:, -1] = False
    
    # 2. Análisis de componentes conexas para la histéresis
    # Tu función buscaba en un vecindario de 7x7 (-3 a 3).
    # Definimos una estructura de conectividad (kernel) de 7x7 llena de 1s.
    estructura_conectividad = np.ones((7, 7), dtype=bool)
    
    # 'label' agrupa todos los píxeles débiles contiguos y les asigna un ID único (1, 2, 3...)
    g_weak_labeled, num_features = label(weak_mask, structure=estructura_conectividad)
    
    # 3. Encontrar qué grupos "débiles" tocan a al menos un píxel "fuerte"
    # Extraemos los IDs de los grupos débiles que coinciden con la máscara fuerte
    connected_ids = np.unique(g_weak_labeled[strong_mask])
    
    # El ID 0 representa el fondo, lo eliminamos si aparece
    connected_ids = connected_ids[connected_ids != 0]
    
    # 4. Construir la imagen final
    # Activamos los bordes que originalmente eran fuertes
    output[strong_mask] = 1
    
    # Activamos los bordes débiles cuyos IDs están conectados a un borde fuerte
    # (Equivale a np.isin, pero más rápido si usamos indexación booleana)
    if connected_ids.size > 0:
        connected_weak_mask = np.isin(g_weak_labeled, connected_ids)
        output[connected_weak_mask] = 1
        
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