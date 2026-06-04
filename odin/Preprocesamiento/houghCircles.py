import numpy as np
from scipy.ndimage import maximum_filter
import math

import numpy as np
from scipy.ndimage import maximum_filter

def hough_circles_vectorizado(im_binary, r, thres=0.5, dist=20):
    """
    Detecta círculos en una imagen binaria de bordes usando la Transformada de Hough.
    
    Parámetros:
        im_binary (numpy.ndarray): Imagen binaria (mapa de bordes).
        r (int o float): Radio del círculo a detectar.
        thres (float): Umbral relativo al valor máximo del acumulador (0.5 a 1.0).
        dist (int): Distancia mínima entre centros de círculos detectados.
        
    Retorna:
        x0_detected (numpy.ndarray): Coordenadas X de los centros.
        y0_detected (numpy.ndarray): Coordenadas Y de los centros.
        n (int): Número de círculos detectados.
        accumulator (numpy.ndarray): Matriz de votación del espacio de Hough.
    """
    if dist < 10:
        raise ValueError("HOUGHCIRCLE:: Distance value must be bigger or equal to 10 px")
    
    if thres < 0.5:
        raise ValueError("HOUGHCIRCLE:: Treshold value must be bigger or equal to 0.5")

    # Asegurarnos de que sea una matriz booleana
    im_binary = np.asarray(im_binary, dtype=bool)
    num_row, num_col = im_binary.shape

    # 1. Encontrar los índices (y, x) de los píxeles que son bordes
    y_index, x_index = np.nonzero(im_binary)

    # 2. Vectorización: Precalcular el seno y coseno para ángulos de 0 a 359 grados
    theta = np.deg2rad(np.arange(0, 360))
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    # 3. Broadcasting: Calcular (a, b) para TODOS los puntos y TODOS los ángulos a la vez
    # x_index[:, None] crea una matriz columna para interactuar con la matriz fila de cos_t
    a = np.round(x_index[:, None] - (r * cos_t)).astype(int)
    b = np.round(y_index[:, None] - (r * sin_t)).astype(int)

    # 4. Filtrar las coordenadas que caen fuera de los límites de la imagen
    valid_mask = (a >= 0) & (a < num_col) & (b >= 0) & (b < num_row)
    a_valid = a[valid_mask]
    b_valid = b[valid_mask]

    # 5. Llenar el acumulador de forma vectorizada
    accumulator = np.zeros((num_row, num_col), dtype=int)
    # np.add.at suma 1 en las coordenadas especificadas, manejando duplicados correctamente
    np.add.at(accumulator, (b_valid, a_valid), 1)

    # 6. Encontrar los picos locales (Reemplaza el bucle while de agrupación de MATLAB)
    # El maximum_filter actúa como Supresión de No Máximos en una ventana de tamaño 'dist'
    local_max = maximum_filter(accumulator, size=dist) == accumulator

    # 7. Aplicar el umbral (Threshold)
    threshold_value = np.max(accumulator) * thres
    
    # Un pico válido es un máximo local que supera el umbral y tiene votos > 0
    peak_mask = local_max & (accumulator >= threshold_value) & (accumulator > 0)

    # Extraer las coordenadas finales
    y0_detected, x0_detected = np.nonzero(peak_mask)
    n = len(y0_detected)

    return x0_detected, y0_detected, n, accumulator

def houghCircles(Imbinary, r, thres=None, dist=None):
    """
    Detecta círculos usando la transformada de Hough.
    Traducción directa del código MATLAB sin optimizaciones.
    
    Parameters:
        Imbinary: Imagen binaria de bordes (2D numpy array)
        r: Radio del círculo a detectar
        thres: Umbral para detección de picos (default: 0.5)
        dist: Distancia mínima entre círculos (default: 20)
    
    Returns:
        x0detected: Coordenadas x de los círculos detectados
        y0detected: Coordenadas y de los círculos detectados
        n: Número de círculos detectados
        Accumulator: Matriz acumuladora de la transformada de Hough
    """
    # Valores por defecto
    if dist is None:
        dist = 20
    
    if dist < 10:
        raise ValueError('HOUGHCIRCLE:: Distance value must be bigger or equal to 10 px')
    
    if thres is None:
        thres = 0.5
    
    if thres < 0.5:
        raise ValueError('HOUGHCIRCLE:: Treshold value must be bigger or equal to .5')
    
    # Votación
    Accumulator = np.zeros(Imbinary.shape)  # Inicializar acumulador
    AccumulatorbinaryMax = np.zeros(Imbinary.shape)  # Inicializar acumulador binario
    
    # Encontrar píxeles de borde
    yIndex, xIndex = np.where(Imbinary)  # Encontrar x,y de píxeles de borde
    numRow = Imbinary.shape[0]  # Número de filas
    numCol = Imbinary.shape[1]  # Número de columnas
    r2 = r ** 2  # Cuadrado del radio
    
    k = 0
    suma = 0
    l = 1
    
    # Bucle principal de votación
    for cnt in range(len(xIndex)):
        angle = 0
        while angle <= 2 * math.pi:
            a = round(xIndex[cnt] - (r * math.cos(angle)))
            b = round(yIndex[cnt] - (r * math.sin(angle)))
            
            if a < numCol and a >= 0 and b < numRow and b >= 0:
                # plot(a,b,'r.','LineWidth',1,'MarkerSize',1)
                # hold on
                # if sqrt((xIndex(cnt)-a)^2+(yIndex(cnt)-b)^2)==r
                Accumulator[b, a] = Accumulator[b, a] + 1
                k = k + 1
                # end
            
            angle = angle + math.pi / 180
    
    # figure; imshow(Accumulator,[])
    # pause
    
    # Encontrar picos en el acumulador
    peaks = houghpeaks(Accumulator, 1)
    
    # Encontrar máximos locales en el acumulador
    y0detect = []
    x0detect = []
    AccumulatorbinaryMax = imregionalmax(Accumulator)
    
    Potential_y0, Potential_x0 = np.where(AccumulatorbinaryMax == 1)
    Accumulatortemp = Accumulator - np.max(Accumulator) * thres
    
    for cnt in range(len(Potential_y0)):
        if Accumulatortemp[Potential_y0[cnt], Potential_x0[cnt]] >= 0:
            y0detect.append(Potential_y0[cnt])
            x0detect.append(Potential_x0[cnt])
    
    # Convertir a arrays numpy
    if len(y0detect) > 0:
        y0detect = np.array(y0detect)
        x0detect = np.array(x0detect)
    else:
        y0detect = np.array([])
        x0detect = np.array([])
    
    n = 0
    done = False
    
    while not done:
        k = 1
        n = 1
        
        if len(x0detect) == 0:
            break
            
        x0detected = x0detect[0]
        y0detected = y0detect[0]
        
        # Limpiar variables
        xdetected = []
        ydetected = []
        
        for i in range(1, len(x0detect)):
            if abs(x0detect[i] - x0detect[i-1]) > dist or abs(y0detect[i] - y0detect[i-1]) > dist:
                xdetected.append(round(x0detected / k))
                ydetected.append(round(y0detected / k))
                k = 1
                n = n + 1
                x0detected = x0detect[i]
                y0detected = y0detect[i]
            else:
                x0detected = x0detected + x0detect[i]
                y0detected = y0detected + y0detect[i]
                k = k + 1
        
        if n == len(x0detect):
            xdetected.append(round(x0detected / k))
            ydetected.append(round(y0detected / k))
            done = True
        else:
            xdetected.append(x0detect[i])
            ydetected.append(y0detect[i])
            
            # Crear matriz de picos
            picos = np.column_stack((ydetected, xdetected))
            picos0 = picos.copy()
            
            # Ordenar por la primera columna (y)
            idx = np.argsort(picos0[:, 0])
            picos = picos0[idx]
            
            x0detect = picos[:, 1]
            y0detect = picos[:, 0]
            done = False
    
    # Convertir a arrays numpy
    if len(xdetected) > 0:
        xdetected = np.array(xdetected)
        ydetected = np.array(ydetected)
    
    if k == len(x0detect):
        x0detected = np.array([xdetected[n-1]]) if n > 0 else np.array([])
        y0detected = np.array([ydetected[n-1]]) if n > 0 else np.array([])
    else:
        x0detected = picos[:, 1] if len(x0detect) > 0 else np.array([])
        y0detected = picos[:, 0] if len(x0detect) > 0 else np.array([])
    
    return x0detected, y0detected, n, Accumulator


def houghpeaks(H, numpeaks):
    """
    Encuentra picos en la matriz acumuladora de Hough.
    Versión simplificada para compatibilidad.
    
    Parameters:
        H: Matriz acumuladora
        numpeaks: Número máximo de picos a encontrar
    
    Returns:
        peaks: Matriz de coordenadas de picos [fila, columna]
    """
    # Encontrar el valor máximo y su ubicación
    max_val = np.max(H)
    rows, cols = np.where(H == max_val)
    peaks = np.column_stack((rows[:numpeaks], cols[:numpeaks]))
    return peaks


def imregionalmax(image):
    """
    Encuentra máximos regionales en una imagen.
    Equivalente a imregionalmax de MATLAB.
    
    Parameters:
        image: Imagen de entrada (2D numpy array)
    
    Returns:
        binary_mask: Máscara binaria con 1 en los máximos regionales
    """
    # Usar filtro de máximo local 3x3
    footprint = np.ones((3, 3))
    local_max = maximum_filter(image, footprint=footprint) == image
    
    # También debe ser estrictamente mayor que los vecinos (no meseta)
    binary_mask = np.zeros_like(image, dtype=bool)
    rows, cols = np.where(local_max)
    
    for i in range(len(rows)):
        r, c = rows[i], cols[i]
        if image[r, c] > 0:  # Solo considerar valores positivos
            # Verificar que es estrictamente mayor que los vecinos
            is_max = True
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < image.shape[0] and 0 <= nc < image.shape[1]:
                        if image[nr, nc] >= image[r, c]:
                            is_max = False
                            break
                if not is_max:
                    break
            if is_max:
                binary_mask[r, c] = True
    
    return binary_mask.astype(int)