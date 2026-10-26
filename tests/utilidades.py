"""Referencias independientes para la suite de ODIN.

Ninguna función de este módulo importa el código de `odin`: son
implementaciones escritas desde la definición matemática (o apoyadas en una
biblioteca externa, como NumPy/OpenCV) para contrastar los resultados del
pipeline. Si una referencia y ODIN discrepan, el spec es el árbitro.
"""

import numpy as np

# Vecinos en el sentido de MagFase: 0=E, 1=SE, 2=S, 3=SW,
# 4=W, 5=NW, 6=N, 7=NE (filas crecen hacia abajo).
_DESPLAZAMIENTOS = [
    (0, 1), (1, 1), (1, 0), (1, -1),
    (0, -1), (-1, -1), (-1, 0), (-1, 1),
]


def kernels_gaussianos(sigma):
    """Kernel gaussiano normalizado y su derivada analítica.

    n = 3*sigma muestras a cada lado, igual que la etapa 1.
    """
    n = 3 * sigma
    x = np.arange(-n, n + 1, dtype=float)
    gk = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
    gk = gk / gk.sum()
    dgk = -(1.0 / sigma ** 2) * x * gk
    return gk, dgk


def convolucion_1d(arreglo, kernel, eje):
    """Convolución 1D con relleno de ceros a lo largo de `eje`.

    `np.convolve(..., mode="same")` con kernel de longitud impar devuelve la
    parte central de la convolución completa, equivalente a convolucionar con
    el kernel centrado y ceros fuera del arreglo.
    """
    return np.apply_along_axis(
        lambda v: np.convolve(v, kernel, mode="same"), eje, arreglo
    )


def derivada_gaussiana_referencia(imagen, sigma):
    """DGX/DGY por convolución separable de referencia (sin usar ODIN)."""
    gk, dgk = kernels_gaussianos(sigma)
    dgx = convolucion_1d(convolucion_1d(imagen, dgk, eje=1), gk, eje=0)
    dgy = convolucion_1d(convolucion_1d(imagen, gk, eje=1), dgk, eje=0)
    return dgx, dgy


def nms_referencia_escalar(mg, angulo):
    """NMS escalar: interpola el EJE del gradiente (ángulo mod 180°).

    Para cada píxel interior toma la dirección d1 = 45·sector y su vecina
    d2 = d1 + 45°, interpola linealmente el valor en ambos extremos del eje y
    conserva el píxel si es mayor o igual que ambos (empate conservador).
    """
    nr, nc = mg.shape
    salida = np.zeros_like(mg)

    for i in range(1, nr - 1):
        for j in range(1, nc - 1):
            phi = float(angulo[i, j]) % 180.0
            sector = int(phi // 45.0)
            f = (phi - 45.0 * sector) / 45.0
            i1, i2 = sector, sector + 1

            def vecino(indice):
                dfila, dcol = _DESPLAZAMIENTOS[indice]
                return mg[i + dfila, j + dcol]

            extremo_1 = vecino(i2) * f + vecino(i1) * (1.0 - f)
            extremo_2 = vecino((i2 + 4) % 8) * f + vecino((i1 + 4) % 8) * (1.0 - f)

            centro = mg[i, j]
            if centro >= extremo_1 and centro >= extremo_2:
                salida[i, j] = centro

    return salida


def varianza_interclase(datos, umbral):
    """Criterio de Otsu evaluado en un umbral concreto: w0·w1·(u1−u0)²."""
    datos = np.asarray(datos, dtype=float).ravel()
    clase0 = datos[datos <= umbral]
    clase1 = datos[datos > umbral]
    w0 = clase0.size / datos.size
    w1 = 1.0 - w0
    if w0 <= 0.0 or w1 <= 0.0:
        return 0.0
    return w0 * w1 * (clase1.mean() - clase0.mean()) ** 2


def otsu_referencia(datos):
    """Umbral de Otsu por barrido exhaustivo sobre los valores reales.

    No usa bins: evalúa el criterio en el punto medio de cada par de valores
    distintos consecutivos. Es una referencia independiente de la
    discretización de 256 bins de ODIN.
    """
    valores = np.sort(np.asarray(datos, dtype=float).ravel())
    unicos = np.unique(valores)
    mejor_umbral, mejor_varianza = None, -1.0

    for i in range(len(unicos) - 1):
        umbral = 0.5 * (unicos[i] + unicos[i + 1])
        varianza = varianza_interclase(valores, umbral)
        if varianza > mejor_varianza:
            mejor_varianza, mejor_umbral = varianza, umbral

    return mejor_umbral
