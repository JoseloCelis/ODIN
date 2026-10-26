import numpy as np
import cv2

#from scipy.ndimage import label, generate_binary_structure, binary_dilation

def EdgeTrack_Hyst(strong, weaks):
    """
    Realiza el umbralizado doble y el seguimiento de bordes por histéresis 
    de forma vectorizada (sin recursión).
    
    """
    strong = np.asarray(strong)
    weaks = np.asarray(weaks)

    # Entrada sin píxeles: OpenCV rechaza imágenes vacías y np.max no tiene
    # identidad para tamaño cero. Se devuelve la salida vacía con la forma de
    # `strong` (spec edge-track-hyst, R6/D1).
    if strong.size == 0:
        return np.zeros(strong.shape, dtype=np.uint8)

    # Sin débiles no hay nada que propagar: sobreviven solo los fuertes.
    if weaks.size == 0:
        salida = np.zeros(strong.shape, dtype=np.uint8)
        salida[strong > 0] = 255
        return salida
    
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
