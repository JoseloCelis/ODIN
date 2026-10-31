import numpy as np
import matplotlib.pyplot as plt
from gi.repository import GLib
#from skimage.filters import threshold_otsu
#umbral = threshold_otsu(imagen_original)
#hist.axvline(umbral, color='red', linestyle='--', linewidth=2, label=f'Umbral Otsu: {umbral:.2f}')
#hist.legend()


def _preparar_histograma(IG):
    """Filtra los píxeles > 0 y calcula el histograma con 256 bins fijos.

    Devuelve (counts, edges, xcenters), o (None, None, None) si no hay píxeles válidos.
    """
    # Filtrar solo los píxeles mayores a 0 (eliminando el fondo negro si aplica)
    píxeles_validos = IG[IG > 0]
    
    if píxeles_validos.size == 0:
        return None, None, None

    # Caso degenerado: todos los valores activos son iguales. np.histogram
    # expandiria el rango a +/-0.5 alrededor del valor y el centro del bin
    # dejaria de ser el valor real (para valores chicos el resultado podia
    # ser negativo). Devolvemos un histograma de un solo bin centrado
    # exactamente en ese valor (spec otsu-rosin, R5/D1).
    vmin, vmax = píxeles_validos.min(), píxeles_validos.max()
    if vmin == vmax:
        valor = float(vmin)
        ancho = max(abs(valor) * 1e-6, 1e-9)  # ancho arbitrario: solo importa el centro
        return (np.array([píxeles_validos.size]),
                np.array([valor - ancho, valor + ancho]),
                np.array([valor]))

    # Bins fijos para asegurar consistencia indexada. R5/D1: si el rango
    # activo no admite 256 bins finitos (casi-constante con rango minimo),
    # se usa un solo bin centrado en el valor en vez de dejar que np.histogram
    # lance "Too many bins for data range".
    try:
        counts, edges = np.histogram(píxeles_validos, bins=256)
    except ValueError:
        valor = float(vmin)
        ancho = max(abs(valor) * 1e-6, 1e-9)
        return (np.array([píxeles_validos.size]),
                np.array([valor - ancho, valor + ancho]),
                np.array([valor]))
    wbin = (edges[1] - edges[0]) / 2
    xcenters = edges[:-1] + wbin
    return counts, edges, xcenters


def _umbral_otsu(counts, xcenters):
    """Otsu vectorizado: devuelve el umbral que maximiza la varianza interclase.

    Parameters:
    counts (numpy.ndarray): Conteos del histograma.
    xcenters (numpy.ndarray): Centros de bin del histograma.

    Returns:
    float: El valor del umbral óptimo.
    """
    L = len(counts)
    N = np.sum(counts)
    p = counts / N  # Probabilidades de cada bin

    # Caso degenerado: un solo bin no vacio (todos los pixeles activos iguales).
    # np.histogram expande un rango cero a +/-0.5, deja un unico bin ocupado y
    # vB queda en cero en todo el arreglo: np.argmax devolveria el indice 0,
    # es decir xcenters[0] = valor - 0.5 (potencialmente negativo). Devolvemos
    # el centro del bin ocupado, que es el valor real (spec otsu-rosin, R5/D1).
    bins_ocupados = np.flatnonzero(counts > 0)
    if bins_ocupados.size <= 1:
        return float(xcenters[bins_ocupados[0]]) if bins_ocupados.size == 1 else 0.0

    intensidades = np.arange(1, L + 1)
    uT = np.dot(intensidades, p)  # Media total de la imagen
    
    # Vectorización del cálculo de Otsu (sin bucles for)
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
    
    # Encontrar el valor máximo de la varianza interclase
    idx_max = np.argmax(vB)
    return xcenters[idx_max]


def umbralRosinYOtsu(IG, histo=False):
    """
    Calcula el umbral utilizando Otsu y Rosin, y muestra el histograma
    con escala logarítmica si histo=True.
    """
    # 1. Histograma de píxeles activos
    counts, edges, xcenters = _preparar_histograma(IG)
    
    if counts is None:
        return 0.0, 0.0

    # 2. Algoritmo 1: Otsu
    umbral_otsu = _umbral_otsu(counts, xcenters)
    
    # 3. Algoritmo 2: criterio de Rosin
    L = len(counts)
    # Encontrar el pico más alto (P1)
    idx_pico = np.argmax(counts)
    x1, y1 = xcenters[idx_pico], counts[idx_pico]
    
    # Encontrar el final de la cola a la derecha (P2)
    # Buscamos el último bin que tenga píxeles antes de quedar vacío
    indices_con_datos = np.where(counts > 0)[0]
    idx_cola = indices_con_datos[-1] if len(indices_con_datos) > 0 else (L - 1)
    x2, y2 = xcenters[idx_cola], counts[idx_cola]
    
    # Calcular distancias desde cada punto del histograma a la recta P1->P2
    # Ecuación de distancia perpendicular de un punto (x0,y0) a una recta Ax + By + C = 0
    # Donde la recta pasa por (x1,y1) y (x2,y2)
    A = y2 - y1
    B = x1 - x2
    C = x2 * y1 - x1 * y2
    
    # Solo evaluamos la región de la cola (desde el pico hasta el final)
    zona_busqueda = np.arange(idx_pico, idx_cola + 1)
    
    # Si el histograma tiene un solo bin, P1 == P2 y el denominador es 0 (recta indefinida)
    denominador = np.sqrt(A**2 + B**2)
    
    if len(zona_busqueda) > 0 and denominador != 0:
        x_zona = xcenters[zona_busqueda]
        y_zona = counts[zona_busqueda]
        
        # Distancias perpendiculares absolutas
        distancias = np.abs(A * x_zona + B * y_zona + C) / denominador
        
        # El umbral Rosin es el punto de máxima distancia
        idx_max_rosin = zona_busqueda[np.argmax(distancias)]
        umbral_rosin = xcenters[idx_max_rosin]
    else:
        umbral_rosin = umbral_otsu # Respaldo si falla la geometría
    
    # Enviar al hilo principal para renderizado gráfico
    GLib.idle_add(dibujar_en_hilo_principal, xcenters, counts, edges, umbral_otsu, umbral_rosin, histo)
    
    return umbral_otsu, umbral_rosin

def umbralOtsu(IG, histo=False):
    """
    Calcula el umbral óptimo de Otsu para una imagen dada.
    
    Parameters:
    IG (numpy.ndarray): Imagen en niveles de gris.
    histo (bool): Si es True, muestra el histograma de los píxeles procesados.
    
    Returns:
    float: El valor del umbral óptimo.
    """
    # 1. Histograma de píxeles activos
    counts, edges, xcenters = _preparar_histograma(IG)
    
    if counts is None:
        return 0.0

    # 2. Otsu vectorizado
    umbral = _umbral_otsu(counts, xcenters)
    
    # 3. Mostrar histograma si se solicita (sin umbral Rosin: None)
    GLib.idle_add(dibujar_en_hilo_principal, xcenters, counts, edges, umbral, None, histo)
    
    return umbral

def dibujar_en_hilo_principal(xcenters, counts, edges, umbral_otsu, umbral_rosin, histo=False):
    if histo:
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # 1. Graficar el histograma usando los bordes (edges)
        ax.stairs(counts, edges, fill=True, color='blue', edgecolor='black', alpha=0.4, label='Magnitud Gradiente')
        
        # 2. Configurar la Escala Logarítmica en el eje Y
        ax.set_yscale('log')
        ax.set_title("Histograma de Gradiente (Escala Logarítmica)")
        ax.set_xlabel("Magnitud del Gradiente")
        ax.set_ylabel("Frecuencia (Log)")
        
        # =========================================================================
        # USO DE XCENTERS: Graficar la recta base del criterio de Rosin
        # (solo aplica cuando hay umbral Rosin; umbralOtsu pasa None)
        # =========================================================================
        if umbral_rosin is not None:
            idx_pico = np.argmax(counts)
            indices_con_datos = np.where(counts > 0)[0]
            idx_cola = indices_con_datos[-1] if len(indices_con_datos) > 0 else (len(counts) - 1)
            
            # Coordenadas del inicio y fin de la cola
            x_recta = [xcenters[idx_pico], xcenters[idx_cola]]
            y_recta = [counts[idx_pico], counts[idx_cola]]
            
            # Dibujamos la recta geométrica de referencia en color naranja
            ax.plot(x_recta, y_recta, color='orange', linestyle=':', linewidth=2.5, 
                    label='Recta de Referencia Rosin')
            
            # Línea del umbral Rosin
            ax.axvline(umbral_rosin, color='green', linestyle='-', linewidth=2, 
                       label=f'Umbral Rosin: {umbral_rosin:.4f}')
        # =========================================================================
        
        # 3. Línea del umbral Otsu (siempre presente)
        ax.axvline(umbral_otsu, color='red', linestyle='--', linewidth=2, 
                   label=f'Umbral Otsu: {umbral_otsu:.4f}')
        
        ax.legend(loc='upper right')
        ax.grid(True, which="both", ls="--", alpha=0.4)
        plt.show(block=False)
        
    return False
