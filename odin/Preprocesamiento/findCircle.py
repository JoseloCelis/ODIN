import numpy as np

# Tolerancia del anillo (spec find-circle, R2). Nunca más de 10 px ni más de un
# cuarto del radio: con re = 8 una tolerancia fija de 10 px convierte el anillo
# en un disco que incluye el círculo interno (medido: 55% de contaminación).
TOLERANCIA_MAX_PX = 10.0
FRACCION_TOLERANCIA_RADIO = 0.25

# Umbrales de la validación del anillo (R3). Margen medido: los círculos
# completos dan 100% de cobertura con 0° de hueco; el glifo del texto en img100
# da 54.2% con 115°, y la basura sintética 2.8-9.7% con 325-350°.
UMBRAL_COBERTURA = 0.75
HUECO_MAX_DEG = 60.0
MINIMO_PUNTOS = 3


def tolerancia_anillo(re):
    """Tolerancia radial del anillo para un radio de búsqueda `re` (R2).

    Es `min(10 px, 0.25 · re)`: el tope absoluto conserva el comportamiento
    histórico con círculos grandes (para re >= 40 el resultado es idéntico), y
    la fracción evita que con radios chicos el anillo incluya el interior del
    círculo o a sus vecinos.
    """
    re = float(re)
    if not np.isfinite(re) or re <= 0:
        raise ValueError("tolerancia_anillo:: re debe ser un número positivo")

    return float(min(TOLERANCIA_MAX_PX, FRACCION_TOLERANCIA_RADIO * re))


def find_circle(detected_edges, re=0.0, centro=(0, 0), tolerancia=None):
    """
    Filtra los puntos de la matriz DetectedEdges para aislar las coordenadas de un círculo.
    
    Casos de uso:
    - re > 0 : Filtra los puntos en un anillo de tolerancia [re-tol, re+tol],
      con `tol = tolerancia_anillo(re)` salvo que se pase `tolerancia`.
    - re == 0: Aísla el segmento continuo más largo detectando saltos mayores a 6 píxeles.
    """
    
    xd, yd = centro

    # El centro debe ser UN par de escalares: recibir los arreglos de picos de
    # la etapa ⑦ rompía el broadcasting (spec find-circle, R5).
    if np.ndim(xd) != 0 or np.ndim(yd) != 0:
        raise ValueError(
            "find_circle:: centro debe ser un par de escalares (xd, yd); "
            "se recibieron arreglos (¿todos los picos de Hough?)"
        )

    # Extraer los índices mayores a 0 de la matriz de bordes
    # np.argwhere nos da [fila, columna] -> [Y, X]. Invertimos a [X, Y].
    puntos = np.argwhere(detected_edges > 0)[:, ::-1]
    
    if puntos.size == 0:
        return np.empty((0, 2))
        
        # -----------------------------------------------------------------
    # CASO 1: Búsqueda con parámetros de Hough (Un solo círculo o concéntricos juntos)
    # -----------------------------------------------------------------
    if re:
        # Calculamos la distancia euclidiana de todos los puntos al centro a la vez
        distancias = np.sqrt((puntos[:, 0] - xd)**2 + (puntos[:, 1] - yd)**2)
        
        # Filtramos los puntos que caen dentro del anillo de tolerancia (R2)
        tol = tolerancia_anillo(re) if tolerancia is None else float(tolerancia)
        if tol < 0:
            raise ValueError("find_circle:: la tolerancia no puede ser negativa")

        mascara = (distancias >= re - tol) & (distancias <= re + tol)
        puntos0 = puntos[mascara]
        
    # -----------------------------------------------------------------
    # CASO 2: re == 0 (Aislamiento automático del segmento continuo más largo)
    # -----------------------------------------------------------------
    else:
        puntos0 = puntos.copy()
        
        # --- ETAPA 1: Análisis en el eje X ---
        k = np.argsort(puntos0[:, 0])
        puntos_sorted = np.column_stack((puntos0[k, 0], puntos0[k, 1]))
        
        x = puntos_sorted[:, 0]
        y = puntos_sorted[:, 1]
        
        l = np.ones_like(x)
        if len(x) > 1:
            l[1:] = np.diff(x)
        l[l < 6] = 1
        
        k_indices = np.where(l > 6)[0]
        k_indices = np.concatenate(([0], k_indices, [len(x)]))
        
        diff_k = np.diff(k_indices)
        if diff_k.size > 0:
            max_idx = np.argmax(diff_k)
            l_final = np.zeros_like(x, dtype=bool)
            l_final[k_indices[max_idx]:k_indices[max_idx + 1]] = True
        else:
            l_final = np.ones_like(x, dtype=bool)
            
        puntosX = x[l_final]
        puntosY = y[l_final]
        puntos0 = np.column_stack((puntosY, puntosX))
        
        # --- ETAPA 2: Análisis en el eje Y ---
        k = np.argsort(puntos0[:, 0])
        puntos_sorted = np.column_stack((puntos0[k, 0], puntos0[k, 1]))
        
        x = puntos_sorted[:, 1]
        y = puntos_sorted[:, 0]
        
        l = np.ones_like(y)
        if len(y) > 1:
            l[1:] = np.diff(y)
        l[l <= 6] = 1
        
        k_indices = np.where(l > 6)[0]
        k_indices = np.concatenate(([0], k_indices, [len(y)]))
        
        diff_k = np.diff(k_indices)
        if diff_k.size > 0:
            max_idx = np.argmax(diff_k)
            l_final = np.zeros_like(y, dtype=bool)
            l_final[k_indices[max_idx]:k_indices[max_idx + 1]] = True
        else:
            l_final = np.ones_like(y, dtype=bool)
            
        puntosY = y[l_final]
        puntosX = x[l_final]
        puntos_res = np.column_stack((puntosY, puntosX))
        
        # Ordenamiento final idéntico a MATLAB
        k = np.argsort(puntos_res[:, 1])
        puntos0 = np.column_stack((puntos_res[k, 1], puntos_res[k, 0]))

    return puntos0


def cobertura_angular(puntos, centro, bins=72):
    """Qué parte del círculo rodean los puntos (spec find-circle, R3).

    Devuelve `(cobertura, hueco_max_deg)`:

    - `cobertura`: fracción de sectores de `360/bins` grados con al menos un
      punto.
    - `hueco_max_deg`: mayor racha circular de sectores vacíos, en grados.

    Es el discriminador medido entre una selección correcta y una que no rodea
    el círculo: los círculos completos dan 100 % / 0°, mientras que un glifo
    real da 54.2 % / 115° y la basura sintética 2.8-9.7 % / 325-350°. Ni el `pv`
    ni la cobertura sobre el radio ajustado los separan.
    """
    puntos = np.asarray(puntos, dtype=float)

    if puntos.size == 0:
        return 0.0, 360.0
    if puntos.ndim != 2 or puntos.shape[1] != 2:
        raise ValueError("cobertura_angular:: se esperaba un arreglo (N, 2)")

    bins = int(bins)
    if bins < 4:
        raise ValueError("cobertura_angular:: bins debe ser 4 o más")

    xd, yd = centro
    angulos = np.degrees(np.arctan2(puntos[:, 1] - yd, puntos[:, 0] - xd)) % 360.0
    indice = np.minimum((angulos / (360.0 / bins)).astype(int), bins - 1)

    ocupados = np.zeros(bins, dtype=bool)
    ocupados[indice] = True

    # Racha circular: se duplica la máscara para que un hueco que cruza el
    # origen (359° -> 0°) se cuente entero.
    hueco = 0
    actual = 0
    for ocupado in np.concatenate([ocupados, ocupados]):
        actual = 0 if ocupado else actual + 1
        if actual > hueco:
            hueco = actual

    return float(ocupados.mean()), float(hueco * 360.0 / bins)


def validar_anillo(puntos, centro, minimo_puntos=MINIMO_PUNTOS,
                   cobertura_min=UMBRAL_COBERTURA, hueco_max=HUECO_MAX_DEG):
    """Decide si la selección de `find_circle` rodea un círculo (R3, R4).

    Devuelve `(True, "")` o `(False, motivo)`. No lanza excepción: el motivo es
    texto para que el orquestador lo muestre tal cual.

    Frena dos fallas medidas: una selección con menos de 3 puntos (el ajuste
    queda subdeterminado y devuelve un círculo con `pv = 0`, imposible de
    distinguir de uno perfecto) y una selección que no cubre el círculo (anillo
    con el radio equivocado).
    """
    puntos = np.asarray(puntos)
    n = 0 if puntos.size == 0 else int(puntos.shape[0])

    if n < int(minimo_puntos):
        return False, (f"el anillo tiene {n} punto(s) y se necesitan al menos "
                       f"{int(minimo_puntos)} para ajustar un círculo")

    cobertura, hueco = cobertura_angular(puntos, centro)

    if cobertura < cobertura_min:
        return False, (f"los {n} puntos del anillo cubren solo "
                       f"{cobertura * 100:.1f}% del círculo (mínimo "
                       f"{cobertura_min * 100:.0f}%): el radio o el centro no "
                       f"corresponden a este círculo")

    if hueco > hueco_max:
        return False, (f"el anillo deja un hueco de {hueco:.0f}° (máximo "
                       f"{hueco_max:.0f}°): los puntos no rodean el círculo")

    return True, ""


