"""Modelo del trazo grueso: dos orillas, no una recta de grosor cero.

Función pura: numpy puro (medición geométrica, no UI). Sin gi, Gtk, Gdk, Adw
ni cairo. Identificadores, comentarios y docstrings en español.

Port optimizado de `CodigoMatlab/separaPuntos.m` + medición de ancho/centro
de `circle_detector.m` (rama `geometria==1`), con la optimización de S5:
separación por proyección del gradiente sobre la normal del Hough.

Contrato:
  - `separar_orillas(puntos, gx, gy, normal)` recibe una nube de puntos (N,2)
    y sus gradientes (N,), y los divide por signo de la proyección sobre una
    normal dada (2,). Devuelve dos nubes (M,2), una por lado.
  - `medir_trazo(puntos, gx, gy, theta)` ajusta dos rectas a las orillas
    separadas por `separar_orillas` y devuelve el ancho y centro del trazo.
    Si alguna orilla tiene menos de `minimo_puntos`, devuelve `None`.
  - `MedicionTrazo` contiene las dos rectas ajustadas, ancho, centro y puntos
    de cada orilla.

Desviaciones deliberadas del MATLAB original (documentadas, ver `odd/tasks/
linea-gruesa.md`):
  - `separaPuntos.m` dividía por signo de Gx/Gy, asumiendo trazo casi
    horizontal/vertical. Aquí se separa por `signo(gradiente · normal)`,
    donde `normal` sale de la dirección θ del Hough.
  - El ancho se calcula como distancia perpendicular media entre las dos
    rectas, no por barrido 1D de filas/columnas.
  - El centro es la recta media derivada, no ajustada a puntos: promedio de
    centros y direcciones de ambas orillas, normalizado.

No se migra `dibuja` ni `anchos` (S5: código muerto).
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .linea_robusta import dist_p_recta, linea_mc


@dataclass(frozen=True, slots=True)
class MedicionTrazo:
    """Resultado de medir un trazo grueso.

    Attributes:
        linea_a (np.ndarray): Recta ajustada a la orilla A `[x0, y0, cos_x, cos_y]`.
        linea_b (np.ndarray): Recta ajustada a la orilla B `[x0, y0, cos_x, cos_y]`.
        ancho (float): Distancia perpendicular media entre las dos orillas.
        centro (np.ndarray): Recta media `[x0, y0, cos_x, cos_y]`.
        puntos_a (np.ndarray): Puntos de la orilla A (M, 2).
        puntos_b (np.ndarray): Puntos de la orilla B (N, 2).
    """
    linea_a: np.ndarray
    linea_b: np.ndarray
    ancho: float
    centro: np.ndarray
    puntos_a: np.ndarray
    puntos_b: np.ndarray


def _como_puntos(puntos: np.ndarray, nombre: str) -> np.ndarray:
    """Valida y convierte una nube de puntos (N, 2) a float.

    Compartida por todos los helpers para no repetir las guardas. No impone
    una cantidad mínima de puntos: la decide cada función.
    """
    if not isinstance(puntos, np.ndarray):
        raise TypeError(f"{nombre}:: se esperaba un numpy.ndarray de forma (N, 2)")

    if puntos.ndim != 2 or puntos.shape[1] != 2:
        raise ValueError(
            f"{nombre}:: el arreglo debe tener forma (N, 2) con coordenadas (x, y); "
            f"recibido {puntos.shape}"
        )

    puntos = np.asarray(puntos, dtype=float)
    if not np.all(np.isfinite(puntos)):
        raise ValueError(f"{nombre}:: los puntos deben ser finitos (sin NaN ni Inf)")

    return puntos


def _como_gradientes(g: np.ndarray, nombre: str) -> np.ndarray:
    """Valida y convierte gradientes (N,) a float."""
    g = np.asarray(g, dtype=float)
    if g.ndim != 1:
        raise ValueError(f"{nombre}:: se esperaba un arreglo 1D; recibido {g.ndim}D")
    if not np.all(np.isfinite(g)):
        raise ValueError(f"{nombre}:: los gradientes deben ser finitos")

    return g


def _como_normal(normal: np.ndarray, nombre: str) -> np.ndarray:
    """Valida y normaliza un vector 2D no nulo."""
    normal = np.asarray(normal, dtype=float)
    if normal.shape != (2,):
        raise ValueError(f"{nombre}:: se esperaba un vector (2,); recibido {normal.shape}")
    norma = float(np.hypot(normal[0], normal[1]))
    if norma == 0.0 or not np.isfinite(norma):
        raise ValueError(f"{nombre}:: la normal no puede ser el vector cero")

    return normal / norma


def separar_orillas(
    puntos: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    normal: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Separa una nube de puntos en dos orillas por proyección del gradiente.

    La proyección es `proyeccion = gx * normal[0] + gy * normal[1]`. Los puntos
    con proyección positiva van a la primera orilla, los negativos a la segunda.

    Args:
        puntos (np.ndarray): Nube (N, 2) de puntos (x, y).
        gx (np.ndarray): Componente X del gradiente en cada punto (N,).
        gy (np.ndarray): Componente Y del gradiente en cada punto (N,).
        normal (np.ndarray): Vector normal unitario (2,) de separación.

    Returns:
        tuple[np.ndarray, np.ndarray]: Dos nubes (M, 2) con los puntos de cada
            orilla, en el mismo orden de entrada.

    Raises:
        TypeError: si `puntos` no es un numpy.ndarray.
        ValueError: si la forma o los valores de los argumentos son inválidos.
    """
    puntos = _como_puntos(puntos, "separar_orillas")
    gx = _como_gradientes(gx, "separar_orillas")
    gy = _como_gradientes(gy, "separar_orillas")
    normal = _como_normal(normal, "separar_orillas")

    if not (gx.shape == gy.shape == (puntos.shape[0],)):
        raise ValueError(
            "separar_orillas:: gx y gy deben tener la misma longitud que puntos"
        )

    proyeccion = gx * normal[0] + gy * normal[1]
    # Umbral pequeño para evitar puntos exactamente en la separación (proyección=0).
    epsilon = 1e-12
    mascara_a = proyeccion >= epsilon
    mascara_b = proyeccion <= -epsilon

    return puntos[mascara_a], puntos[mascara_b]


def medir_trazo(
    puntos: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    theta: float,
    *,
    minimo_puntos: int = 3,
) -> Optional[MedicionTrazo]:
    """Mide el ancho y centro de un trazo grueso.

    Args:
        puntos (np.ndarray): Nube (N, 2) de puntos de borde.
        gx (np.ndarray): Componente X del gradiente en cada punto (N,).
        gy (np.ndarray): Componente Y del gradiente en cada punto (N,).
        theta (float): Dirección del trazo en radianes (del Hough).
        minimo_puntos (int): Mínimo de puntos por orilla para considerarla válida.

    Returns:
        MedicionTrazo | None: Medición del trazo si ambas orillas tienen suficientes
            puntos; `None` en caso contrario.

    Raises:
        TypeError: si `puntos` no es un numpy.ndarray.
        ValueError: si la forma o los valores de los argumentos son inválidos.
    """
    puntos = _como_puntos(puntos, "medir_trazo")
    gx = _como_gradientes(gx, "medir_trazo")
    gy = _como_gradientes(gy, "medir_trazo")
    theta = float(theta)
    if not np.isfinite(theta):
        raise ValueError("medir_trazo:: theta debe ser finito")

    if not (gx.shape == gy.shape == (puntos.shape[0],)):
        raise ValueError(
            "medir_trazo:: gx y gy deben tener la misma longitud que puntos"
        )

    normal = np.array([np.cos(theta), np.sin(theta)])
    puntos_a, puntos_b = separar_orillas(puntos, gx, gy, normal)

    if len(puntos_a) < minimo_puntos or len(puntos_b) < minimo_puntos:
        return None

    linea_a = linea_mc(puntos_a)
    linea_b = linea_mc(puntos_b)

    # Ancho: distancia perpendicular media entre las dos rectas.
    dist_a_a_b = dist_p_recta(puntos_a, linea_b)
    dist_b_a_b = dist_p_recta(puntos_b, linea_a)
    ancho = float(np.mean(np.concatenate([dist_a_a_b, dist_b_a_b])))

    # Centro: recta media derivada (promedio de centros y direcciones). Las
    # direcciones de SVD son unitarias pero su signo es arbitrario: se alinean
    # antes de promediar para que no se cancelen si salen opuestas.
    centro_x = (linea_a[0] + linea_b[0]) / 2
    centro_y = (linea_a[1] + linea_b[1]) / 2
    direccion_a = linea_a[2:4]
    direccion_b = linea_b[2:4]
    if float(np.dot(direccion_a, direccion_b)) < 0.0:
        direccion_b = -direccion_b
    centro_dir = direccion_a + direccion_b
    norma = float(np.hypot(centro_dir[0], centro_dir[1]))
    if norma > 0.0:
        centro_dir = centro_dir / norma
    centro = np.array([centro_x, centro_y, centro_dir[0], centro_dir[1]])

    return MedicionTrazo(linea_a, linea_b, ancho, centro, puntos_a, puntos_b)


def refinar_bordes_subpixel(
    puntos: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    magnitud: np.ndarray,
) -> np.ndarray:
    """Refina la posición de los bordes mediante interpolación parabólica.

    Para cada punto (x, y) con gradiente (gx_i, gy_i), se calcula la normal
    n = (gx, gy)/|g| y se muestrea la magnitud en tres puntos a lo largo de
    esta dirección: p0 = p - n, p1 = p, p2 = p + n. Luego se ajusta una
    parábola y se encuentra el desplazamiento subpíxel óptimo.

    Args:
        puntos (np.ndarray): Coordenadas enteras (N, 2) de los puntos de borde.
        gx (np.ndarray): Componente X del gradiente en cada punto (N,).
        gy (np.ndarray): Componente Y del gradiente en cada punto (N,).
        magnitud (np.ndarray): Imagen 2D de magnitud del gradiente.

    Returns:
        np.ndarray: Puntos refinados (N, 2) con coordenadas subpíxel.
    """
    puntos = _como_puntos(puntos, "refinar_bordes_subpixel")
    gx = _como_gradientes(gx, "refinar_bordes_subpixel")
    gy = _como_gradientes(gy, "refinar_bordes_subpixel")

    if not (gx.shape == gy.shape == (puntos.shape[0],)):
        raise ValueError(
            "refinar_bordes_subpixel:: gx y gy deben tener la misma longitud que puntos"
        )

    if magnitud.ndim != 2:
        raise ValueError("refinar_bordes_subpixel:: magnitud debe ser una imagen 2D")

    # Calcular la norma del gradiente
    norma_g = np.hypot(gx, gy)
    
    # Inicializar puntos refinados como copia de los originales
    puntos_refinados = puntos.copy()
    
    # Crear máscara para gradientes válidos (no nulos)
    mascara_valida = norma_g > 1e-12
    
    # Procesar solo los puntos con gradiente significativo
    gx_validos = gx[mascara_valida]
    gy_validos = gy[mascara_valida]
    norma_validos = norma_g[mascara_valida]
    puntos_validos = puntos[mascara_valida]
    
    if len(puntos_validos) == 0:
        return puntos_refinados
    
    # Calcular dirección normal unitaria
    nx = gx_validos / norma_validos
    ny = gy_validos / norma_validos
    
    # Coordenadas de los puntos válidos
    x = puntos_validos[:, 0]
    y = puntos_validos[:, 1]
    
    # Muestrear magnitud en los tres puntos usando interpolación bilineal
    def interpolar(img, px, py):
        """Interpolación bilineal con recorte a los bordes de la imagen."""
        alto, ancho = img.shape
        px = np.clip(px, 0, ancho - 1)
        py = np.clip(py, 0, alto - 1)
        
        x0 = np.floor(px).astype(int)
        x1 = np.minimum(x0 + 1, ancho - 1)
        y0 = np.floor(py).astype(int)
        y1 = np.minimum(y0 + 1, alto - 1)
        
        wa = (x1 - px) * (y1 - py)
        wb = (px - x0) * (y1 - py)
        wc = (x1 - px) * (py - y0)
        wd = (px - x0) * (py - y0)
        
        return (wa * img[y0, x0] +
                wb * img[y0, x1] +
                wc * img[y1, x0] +
                wd * img[y1, x1])
    
    # Puntos para muestreo
    p0_x = x - nx
    p0_y = y - ny
    p1_x = x
    p1_y = y
    p2_x = x + nx
    p2_y = y + ny
    
    # Obtener valores de magnitud
    m0 = interpolar(magnitud, p0_x, p0_y)
    m1 = interpolar(magnitud, p1_x, p1_y)
    m2 = interpolar(magnitud, p2_x, p2_y)
    
    # Calcular desplazamiento parabólico
    denom = m0 - 2 * m1 + m2
    # Evitar división por cero o valores muy pequeños
    mascara_denom = np.abs(denom) > 1e-12
    # También evitar cuando todos los valores son iguales (picos planos)
    mascara_constante = (np.abs(m0 - m1) < 1e-12) & (np.abs(m1 - m2) < 1e-12)
    mascara_valida_offset = mascara_denom & ~mascara_constante
    with np.errstate(divide='ignore', invalid='ignore'):
        d = np.where(mascara_valida_offset, 0.5 * (m0 - m2) / denom, 0.0)

    # Cota: con muestras en -1, 0 y +1, la parábola m(x) = M - a(x - d)^2 tiene
    # a m1 = m(0) como máximo de las tres exactamente cuando |d| <= 0.5
    # (m(0) >= m(+1) <=> d <= 0.5 y m(0) >= m(-1) <=> d >= -0.5). Fuera de ese
    # rango la muestra central NO es el máximo, así que la vecindad no describe
    # un pico único —plateau, borde de imagen o una segunda orilla— y el vértice
    # se dispara: en `600mm_Imag0000.bmp` llega a 125 px y arrastra el ajuste
    # SVD de la orilla. ±0.5 px es entonces el dominio de validez del ajuste y,
    # a la vez, la mitad del espaciado de muestreo: lo máximo que el dato
    # sostiene cuando no hay pico que refinar.
    d = np.clip(d, -0.5, 0.5)
    
    # Aplicar desplazamiento solo donde es significativo
    dx = d * nx
    dy = d * ny
    
    # Actualizar coordenadas refinadas
    indices_validos = np.where(mascara_valida)[0]
    puntos_refinados[indices_validos, 0] += dx
    puntos_refinados[indices_validos, 1] += dy
    
    return puntos_refinados
