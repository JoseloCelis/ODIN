"""Umbrales de Otsu y Rosin (etapa ④).

Lógica matemática pura en NumPy/SciPy. Sin dependencias de UI:
sin gi, sin Gtk, sin Gdk, sin Adw, sin cairo, sin matplotlib.
El dibujo de histogramas queda en la capa de vista/controlador;
el modelo solo devuelve los umbrales numéricos.
"""

import numpy as np


def _preparar_histograma(IG):
    """Filtra píxeles > 0 y calcula el histograma con 256 bins fijos.

    Devuelve (counts, edges, xcenters), o (None, None, None) si no hay
    píxeles válidos.
    """
    # Filtrar solo píxeles mayores a 0 (eliminando fondo negro si aplica)
    pixeles_validos = IG[IG > 0]

    if pixeles_validos.size == 0:
        return None, None, None

    # Caso degenerado: todos los valores activos son iguales.
    # np.histogram expandiría el rango a +/-0.5 alrededor del valor y el
    # centro del bin dejaría de ser el valor real. Devolvemos un histograma
    # de un solo bin centrado exactamente en ese valor (spec otsu-rosin, R5/D1).
    vmin, vmax = pixeles_validos.min(), pixeles_validos.max()
    if vmin == vmax:
        valor = float(vmin)
        ancho = max(abs(valor) * 1e-6, 1e-9)  # ancho arbitrario: solo importa el centro
        return (
            np.array([pixeles_validos.size]),
            np.array([valor - ancho, valor + ancho]),
            np.array([valor]),
        )

    # Bins fijos para asegurar consistencia indexada. Si el rango activo
    # no admite 256 bins finitos (casi-constante con rango mínimo), se usa
    # un solo bin centrado en el valor en vez de dejar que np.histogram
    # lance "Too many bins for data range" (spec otsu-rosin, R5/D1).
    try:
        counts, edges = np.histogram(pixeles_validos, bins=256)
    except ValueError:
        valor = float(vmin)
        ancho = max(abs(valor) * 1e-6, 1e-9)
        return (
            np.array([pixeles_validos.size]),
            np.array([valor - ancho, valor + ancho]),
            np.array([valor]),
        )
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

    # Caso degenerado: un solo bin no vacío (todos los píxeles activos iguales).
    bins_ocupados = np.flatnonzero(counts > 0)
    if bins_ocupados.size <= 1:
        return float(xcenters[bins_ocupados[0]]) if bins_ocupados.size == 1 else 0.0

    intensidades = np.arange(1, L + 1)
    uT = np.dot(intensidades, p)  # Media total de la imagen

    # Vectorización del cálculo de Otsu (sin bucles for)
    w0 = np.cumsum(p)  # Peso acumulado de la clase 0 (background)
    w1 = 1.0 - w0  # Peso acumulado de la clase 1 (foreground)

    # Evitar divisiones por cero en los extremos del histograma
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
    """Calcula el umbral utilizando Otsu y Rosin.

    Devuelve (umbral_otsu, umbral_rosin). El parámetro `histo` se conserva
    por compatibilidad de firma pero no dibuja nada desde el modelo: el
    dibujo de histogramas pertenece a la capa de vista (callback inyectado
    por el controlador, no acoplado al modelo).

    Parameters:
    IG (numpy.ndarray): Imagen en niveles de gris (magnitud del gradiente).
    histo (bool): Por compatibilidad; el modelo no dibuja.

    Returns:
    tuple[float, float]: (umbral_otsu, umbral_rosin)
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
    indices_con_datos = np.where(counts > 0)[0]
    idx_cola = indices_con_datos[-1] if len(indices_con_datos) > 0 else (L - 1)
    x2, y2 = xcenters[idx_cola], counts[idx_cola]

    # Calcular distancias desde cada punto del histograma a la recta P1->P2
    A = y2 - y1
    B = x1 - x2
    C = x2 * y1 - x1 * y2

    # Solo evaluamos la región de la cola (desde el pico hasta el final)
    zona_busqueda = np.arange(idx_pico, idx_cola + 1)

    # Si el histograma tiene un solo bin, P1 == P2 y el denominador es 0
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
        umbral_rosin = umbral_otsu  # Respaldo si falla la geometría

    return umbral_otsu, umbral_rosin


def umbralOtsu(IG, histo=False):
    """Calcula el umbral óptimo de Otsu para una imagen dada.

    API pública conservada (sin llamadores internos en el pipeline, pero
    reutilizable como librería).

    Parameters:
    IG (numpy.ndarray): Imagen en niveles de gris.
    histo (bool): Por compatibilidad; el modelo no dibuja.

    Returns:
    float: El valor del umbral óptimo.
    """
    # 1. Histograma de píxeles activos
    counts, edges, xcenters = _preparar_histograma(IG)

    if counts is None:
        return 0.0

    # 2. Otsu vectorizado
    umbral = _umbral_otsu(counts, xcenters)

    return umbral
