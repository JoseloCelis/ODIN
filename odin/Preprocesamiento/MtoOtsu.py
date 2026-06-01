import numpy as np
import matplotlib.pyplot as plt
from gi.repository import GLib
#from skimage.filters import threshold_otsu
#umbral = threshold_otsu(imagen_original)
#hist.axvline(umbral, color='red', linestyle='--', linewidth=2, label=f'Umbral Otsu: {umbral:.2f}')
#hist.legend()

def umbralOtsu(IG, histo=False):
    """
    Calcula el umbral óptimo de Otsu para una imagen dada.
    
    Parameters:
    IG (numpy.ndarray): Imagen en niveles de gris.
    histo (bool): Si es True, muestra el histograma de los píxeles procesados.
    
    Returns:
    float: El valor del umbral óptimo.
    """
    # 1. Filtrar solo los píxeles mayores a 0 (eliminando el fondo negro si aplica)
    píxeles_validos = IG[IG > 0]
    
    if píxeles_validos.size == 0:
        return 0.0

    # 2. Calcular el histograma automáticamente con el método de Freedman-Diaconis ('auto')
    # o puedes fijar 'bins=256' si manejas imágenes estándar de 8 bits.
    counts, edges = np.histogram(píxeles_validos, bins=256)
    wbin = (edges[1] - edges[0]) / 2
    xcenters = edges[:-1] + wbin
    
    
    # 4. Inicializar variables para el algoritmo de Otsu
    L = len(counts)
    N = np.sum(counts)
    p = counts / N  # Probabilidades de cada bin
    
    intensidades = np.arange(1, L + 1)
    uT = np.dot(intensidades, p)  # Media total de la imagen
    
    # 5. Vectorización del cálculo de Otsu (sin bucles for)
    w0 = np.cumsum(p)        # Peso acumulado de la clase 0 (background)
    w1 = 1.0 - w0            # Peso acumulado de la clase 1 (foreground)
    
    # Evitar divisiones por cero en los extremos del histograma
    # Si el peso es 0 o 1, la varianza interclase será 0 de todas formas.
    safe_mask = (w0 > 0) & (w1 > 0)
    
    u = np.cumsum(intensidades * p)  # Media acumulada
    
    u0 = np.zeros_like(w0)
    u1 = np.zeros_like(w1)
    
    u0[safe_mask] = u[safe_mask] / w0[safe_mask]
    u1[safe_mask] = (uT - u[safe_mask]) / w1[safe_mask]
    
    # Varianza interclase para todos los niveles simultáneamente
    vB = (w0 * w1) * ((u1 - u0) ** 2)
    
    # 6. Encontrar el valor máximo de la varianza interclase
    idx_max = np.argmax(vB)
    umbral = xcenters[idx_max]
    
    # 3. Mostrar histograma si se solicita
    GLib.idle_add(dibujar_en_hilo_principal, xcenters, counts, edges, umbral, histo)
    
    return umbral

def dibujar_en_hilo_principal(xcenters, counts, edges, umbral, histo=False):
    

    
    if histo:
        ancho_barras = (edges[1]-edges[0]) * 0.9
        plt.subplots(figsize=(8,5))
        plt.bar(xcenters, counts, width=ancho_barras, edgecolor='black', alpha=0.7)
        plt.title("Histograma de píxeles activos")
        plt.xlabel("Intensidad")
        plt.ylabel("Frecuencia")
        
        plt.axvline(umbral, color='red', linestyle='--', linewidth=2, label=f'Umbral Otsu: {umbral:.2f}')
        plt.legend()
        plt.show(block=False)
        
    return False

def MtoOtsu(IG, histo=0):
    """
    Calcula el umbral óptimo usando el método de Otsu.
    Traducción directa del código MATLAB sin optimizaciones.
    
    Parameters:
        IG: Imagen de gradiente (2D numpy array)
        histo: Si es 1, muestra el histograma (default: 0)
    
    Returns:
        umbral: Valor del umbral óptimo calculado
    """
    if histo is None:
        histo = 0
    
    # Encontrar píxeles mayores que 0
    r, c = np.where(IG > 0)
    I = []
    for i in range(len(r)):
        if IG[r[i], c[i]] > 0:
            I.append(IG[r[i], c[i]])
    
    I = np.array(I)
    
    # Calcular histograma
    counts, edges = np.histogram(I, bins='auto')
    wbin = (edges[1] - edges[0]) / 2
    xcenters = edges + wbin
    
    # Mostrar histograma si histo != 0
    if histo:
        plt.figure()
        plt.bar(xcenters[:len(xcenters)-1], counts)
        plt.show()
    
    L = len(counts)
    N = np.sum(counts)
    p = counts / N
    i = np.arange(1, L + 1)  # Equivalente a 1:L en MATLAB
    uT = np.dot(i, p)
    
    w0 = 0
    w1 = 0
    u = 0
    maximum = 0.0
    
    for k in range(L):
        w0 = w0 + p[k]
        # wA = wA + p(k)
        w1 = 1 - w0
        # wB = 1 - wA
        
        u = u + (k + 1) * p[k]  # k+1 porque Python usa índice 0
        # SumA = SumA + k * p(k)
        
        u0 = u / w0
        # uA = SumA / w0
        
        u1 = (uT - u) / w1
        # uB = (uT - u) / w1
        
        vB = (w0 * w1) * (u1 - u0) ** 2
        # vB = w0 * w1 * (uA - uB) ^ 2
        
        if vB >= maximum:
            umbral = xcenters[k]
            maximum = vB
    
    utv = w0 * u0 + w1 * u1
    unidad = w0 + w1
    
    # [histCts, xcenters] = imhist(IG)  % Cálculo de histograma
    # total = sum(histCts)  % Total de pixeles en la imagen
    # % Se inicia las variables del acumulación
    # 
    # SumA = 0
    # wA = 0
    # maximum = 0.0
    # %
    # sum1 = dot((0:255), histCts)
    # % media = sum1 / total
    # for k = 1:256
    #     % P(A)
    #     wA = wA + histCts(k)
    #     if (wA == 0)
    #         continue
    #     end
    #     % P(B)
    #     wB = total - wA
    #     if (wB == 0)
    #         break
    #     end
    #     % Se calcula media para la clase A
    #     SumA = SumA + (k-1) * histCts(k)
    #     mA = SumA / wA
    #     % Se calcula media para clase B
    #     mB = (sum1 - SumA) / wB
    #     % Se calcula varianza entre clases Ecuación 5.7
    #     VE = wA * wB * (mA - mB) ^ 2
    #     % Se prueba si se ha encontrado el máximo, si es encontrado se guarda en
    #     % el umbral
    #     if (VE >= maximum)
    #         umbral = xcenters(k)
    #         maximum = VE
    #     end
    # end
    
    # ImF = IG >= umbral
    # imshow(ImF, [])
    # pause
    
    return umbral