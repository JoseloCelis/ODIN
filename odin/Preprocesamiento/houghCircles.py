import numpy as np
from scipy.ndimage import maximum_filter

# Umbral de ambigüedad del barrido de radios (spec hough-circles, R5): si el
# segundo candidato supera esta fracción del primero, la detección se reporta
# como ambigua en lugar de presentarse como certera.
UMBRAL_AMBIGUEDAD = 0.8

# Separación mínima, en píxeles, para considerar que dos radios son candidatos
# distintos y no el mismo pico repartido entre radios vecinos.
SEPARACION_AMBIGUEDAD_PX = 6.0


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

    # Entrada vacía: np.max no tiene identidad para tamaño cero (spec
    # hough-circles, R1.4). Se devuelve la salida vacía, como en la etapa 6.
    if im_binary.size == 0:
        vacio = np.empty(0, dtype=int)
        return vacio, vacio, 0, np.zeros(im_binary.shape, dtype=int)

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


def mejor_centro(x0, y0, acumulador):
    """Devuelve `(x, y, votos)` del pico con más votos, o `None` sin picos.

    `hough_circles_vectorizado` devuelve TODOS los picos, en orden de barrido
    de la imagen (no de votos). El llamador debe quedarse con uno solo: pasar
    el arreglo completo a `find_circle` rompe el broadcasting (spec
    hough-circles, R9).
    """
    x0 = np.asarray(x0)
    y0 = np.asarray(y0)

    if x0.size == 0 or y0.size == 0:
        return None

    votos = np.asarray(acumulador)[y0, x0]
    mejor = int(np.argmax(votos))

    return int(x0[mejor]), int(y0[mejor]), int(votos[mejor])


def estimar_radio(im_binary, r_min, r_max, paso=2.0, thres=0.99, dist=20,
                  separacion_px=SEPARACION_AMBIGUEDAD_PX):
    """Estima el radio dominante barriendo la banda `[r_min, r_max]`.

    Devuelve `(radio, pico, ambiguedad)`:

    - `radio`: el radio cuyo pico del acumulador es mayor (0.0 si no hay bordes).
    - `pico`: votos de ese radio.
    - `ambiguedad`: relación entre el segundo candidato y el primero. Los
      radios vecinos (a menos de `separacion_px`) no cuentan como candidatos
      distintos: son el mismo pico repartido por la discretización.

    La banda la deriva el llamador del recorte: `r0 = min(alto, ancho) / 2`
    y `[0.6 * r0, r0]` (spec hough-circles, R4).

    Limitación conocida: el pico bruto crece con el radio (más puntos de
    borde), así que un círculo grande domina a uno mucho más chico y la
    ambigüedad no se reporta. Ver `design.md` §3.4.
    """
    r_min = float(r_min)
    r_max = float(r_max)
    paso = float(paso)

    if not np.isfinite([r_min, r_max, paso]).all():
        raise ValueError("estimar_radio:: los límites y el paso deben ser finitos")
    if r_min <= 0:
        raise ValueError("estimar_radio:: r_min debe ser mayor que 0")
    if r_min > r_max:
        raise ValueError("estimar_radio:: r_min no puede superar a r_max")
    if paso <= 0:
        raise ValueError("estimar_radio:: el paso debe ser mayor que 0")

    im_binary = np.asarray(im_binary)
    if im_binary.size == 0 or not np.any(im_binary > 0):
        return 0.0, 0, 0.0

    radios = np.arange(r_min, r_max + paso * 0.5, paso)
    picos = np.array([
        int(hough_circles_vectorizado(im_binary, float(radio), thres, dist)[3].max())
        for radio in radios
    ])

    mejor = int(np.argmax(picos))
    if picos[mejor] <= 0:
        return 0.0, 0, 0.0

    pasos_separacion = max(1, int(round(separacion_px / paso)))
    otros = [p for j, p in enumerate(picos) if abs(j - mejor) >= pasos_separacion]
    segundo = max(otros) if otros else 0

    return float(radios[mejor]), int(picos[mejor]), float(segundo / picos[mejor])


def estimar_radio_dominante(im_binary, r0, fraccion_min=0.08, paso_grueso_rel=0.02,
                            candidatos=2, paso_fino=None, thres=0.99, dist=20):
    """Estima el radio dominante de un recorte, holgado o ajustado.

    Barrido en dos escalas (spec hough-circles, R10):

    1. **Grueso**: recorre `[fraccion_min * r0, r0]` con un paso proporcional a
       `r0`, así el costo no crece con el tamaño de la imagen.
    2. **Fino**: refina los `candidatos` máximos gruesos mejor separados, con
       un paso absoluto pequeño.

    Refinar varios candidatos es lo que hace robusta la decisión: en el
    recorte holgado de `img100`, el barrido grueso daba 68 votos al disco y 58
    al texto (1.17:1), mientras que al refinar quedan 211 contra 80 (2.6:1).

    Devuelve `(radio, pico, ambiguedad)` con el mismo contrato que
    `estimar_radio`. La ambigüedad se calcula entre estructuras ya refinadas y
    separadas, no entre radios vecinos.
    """
    r0 = float(r0)
    if not np.isfinite(r0) or r0 <= 0:
        raise ValueError("estimar_radio_dominante:: r0 debe ser mayor que 0")

    r_max = r0
    r_min = max(4.0, fraccion_min * r0)
    if r_min >= r_max:
        r_min = max(1.0, r_max / 2.0)

    paso_grueso = max(4.0, paso_grueso_rel * r0)
    if paso_fino is None:
        paso_fino = max(1.0, min(4.0, paso_grueso / 5.0))

    radios = np.arange(r_min, r_max + paso_grueso * 0.5, paso_grueso)
    picos = np.array([
        int(hough_circles_vectorizado(im_binary, float(radio), thres, dist)[3].max())
        for radio in radios
    ])

    if picos.size == 0 or picos.max() <= 0:
        return 0.0, 0, 0.0

    # Candidatos gruesos: los picos más altos, separados al menos dos pasos
    # para no refinar tres veces la misma estructura.
    candidatos_idx = []
    for j in np.argsort(-picos):
        if all(abs(radios[j] - radios[e]) >= 2 * paso_grueso for e in candidatos_idx):
            candidatos_idx.append(int(j))
        if len(candidatos_idx) >= max(1, int(candidatos)):
            break

    refinados = []
    for j in candidatos_idx:
        bajo = max(r_min, radios[j] - paso_grueso)
        alto = min(r_max, radios[j] + paso_grueso)
        refinados.append(estimar_radio(im_binary, bajo, alto, paso_fino, thres, dist))

    refinados.sort(key=lambda salida: -salida[1])

    # Dos candidatos pueden converger al mismo radio: cuentan como uno solo.
    unicos = []
    for radio, pico, _ in refinados:
        if all(abs(radio - otro) >= 2 * paso_fino for otro, _ in unicos):
            unicos.append((radio, pico))

    radio, pico = unicos[0]
    segundo = unicos[1][1] if len(unicos) > 1 else 0

    return float(radio), int(pico), float(segundo / pico)

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