import numpy as np
import cv2 
import sys

#from scipy.ndimage import label, generate_binary_structure, binary_dilation

def EdgeTrack_Hyst(strong, weaks):
    """
    Realiza el umbralizado doble y el seguimiento de bordes por histéresis 
    de forma vectorizada (sin recursión).
    
    """
    
    print("--- DIAGNÓSTICO DE HISTÉRESIS (OPENCV) ---")
    print(f"Máximo en fuertes: {np.max(strong)}")
    print(f"Máximo en debiles: {np.max(weaks)}")
    print(f"Píxeles verdaderos en strong_mask: {np.sum(strong > 0)}")
    print(f"Píxeles verdaderos en weak_mask: {np.sum(weaks > 0)}")
    
    # 1. Crear máscaras lógicas globales y asegurar formato uint8 para OpenCV
    strong_mask = strong > 0
    weak_mask = weaks > 0
    
    weak_mask_cv = weak_mask.astype(np.uint8) * 255

    # Inicializar la imagen de salida vacía
    output = np.zeros_like(strong, dtype=np.uint8)
    
    # 2. Dilatación de bordes fuertes (Simula el vecindario)
    # Nota: cv2.dilate requiere uint8. El kernel de 3x3 simula conectividad de 8 vecinos.
    dilation_kernel = np.ones((7, 7), dtype=np.uint8)
    strong_dilated = cv2.dilate(strong_mask.astype(np.uint8), dilation_kernel).astype(bool)
    
    # 3. Análisis de componentes conexas con OpenCV en 32 BITS (Evita el crash de bits)
    # connectivity=8 equivale a tu kernel de SciPy (incluye diagonales)
    # ltype=cv2.CV_32S permite manejar millones de etiquetas sin desbordamiento
    num_labels, weaks_labeled = cv2.connectedComponents(
        weak_mask_cv, 
        connectivity=8, 
        ltype=cv2.CV_32S
    )
    
    # En OpenCV, num_labels incluye el fondo (0), restamos 1 para saber las características reales
    num_features = num_labels - 1
    
    if num_features <= 0:
        output[strong_mask] = 255
        return output
    
    # 4. Identificar qué islas débiles tocan a los bordes fuertes dilatados
    connected_ids = np.unique(weaks_labeled[strong_dilated])
    connected_ids = connected_ids[connected_ids != 0] # Excluir el fondo
    
    # 5. Construir la imagen final y activar bordes válidos
    output[strong_mask] = 255
    
    if connected_ids.size > 0:
        # np.isin funciona perfectamente con la matriz de 32 bits generada por OpenCV
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