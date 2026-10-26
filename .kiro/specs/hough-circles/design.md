# Design Document — hough-circles (etapa ⑦)

## 1. Estado del módulo

`houghCircles.py` (283 líneas):

| Símbolo | Rol | Llamadores | Estado |
|---|---|---|---|
| `hough_circles_vectorizado(im_binary, r, thres, dist)` | Hough vectorizado | `main.py:448` | **en producción** |
| `houghCircles(Imbinary, r, thres, dist)` | traducción MATLAB, bucles por punto y ángulo | **0** | código muerto (R8) |
| `houghpeaks(H, numpeaks)` | pico máximo del acumulador | solo `houghCircles` | código muerto (R8) |
| `imregionalmax(image)` | máximos regionales con bucles Python | solo `houghCircles` | código muerto (R8) |

El orquestador (`main.py:447-453`) hace hoy:

```python
diametro = 253                                        # <-- constante
xRecortada, yRecortada, n, accumulador = aproxHough.hough_circles_vectorizado(DetectedEdges, diametro/2, 0.8)
aproxCenter = (xRecortada, yRecortada)
puntosFiltrados = circleFilter.find_circle(DetectedEdges, diametro/2, aproxCenter)
x, y, r, pv = LSC.Circulo_simple(puntosFiltrados)
x = self.xRecorte + x
y = self.yRecorte + y
```

Verificado: `self.current_image = handle.recortar_imagen(self)` (main.py:399),
así que los bordes están en coordenadas del recorte y sumar `xRecorte` /
`yRecorte` es correcto — **no** hay doble desplazamiento.

## 2. Evidencia ejecutada sobre `img100.bmp`

Imagen: 3288 × 4608, 8 bits, valores 6-173, mediana 39.

### 2.1 El objeto real

| Dato | Valor |
|---|---|
| Disco claro (componente mayor) | área 576 314 px → **r_eq = 428.3 px** |
| Centro | (2660.6, 1611.2) |
| Diámetro real | **857 px** |
| Interior del disco | media 169.0, desv 0.9, variación entre bandas **0.5** → **plano**, sin círculo pequeño dentro |

El texto "100μ" produce dos componentes de radio equivalente **128.5** y
**125.9** px. La constante `diametro / 2 = 126.5` del orquestador coincide con
ellas: por eso el `253` "funciona" en algunas imágenes por accidente.

### 2.2 La dilatación de la etapa ⑥ no influye

| kernel | bordes | rescatados | diferencia vs 3×3 |
|---|---|---|---|
| 3×3 | 10 028 | 1 | — |
| 5×5 | 10 028 | 1 | 0 px |
| 7×7 | 10 028 | 1 | 0 px |

Fuertes 10 027, débiles 3 522, rescatado 1. La histéresis casi no actúa en esta
imagen y el radio de dilatación es indiferente. Conclusión: el 7×7 se conserva
(es el radio original y no cambia nada en la práctica).

### 2.3 El defecto: radio constante

Recorte simulado con 15% de margen: 1114 × 1112, disco en coords del recorte
centro (555.6, 556.2) r=428.3. Bordes en el recorte: 3 182.

| Configuración | centros Hough | anillo | ajuste | error vs r real | pv |
|---|---|---|---|---|---|
| **hoy** (`r=126.5`) | **54** | 129 pts | centro (557.6, 532.8) **r=403.95** | **24.4 px** | **0.995** |
| radio real (`r=428.3`) | 1 | 3 153 pts | centro (2661, 1611) **r=427.85** | **0.46 px** | 2.034 |

El caso de hoy ajusta un arco de 129 puntos (el borde superior del disco) y
extrapola un círculo 6% más chico, corrido 24 px. **El `pv` baja a 0.995, es
decir la métrica de error no delata la falla.** Ese es el síntoma "pequeño
círculo dentro del grande" reportado por el usuario.

### 2.4 Barrido de radios

Recorte 1114 × 1112 (r0 = 556.0), bordes 3 182, 112 radios en **5.1 s**:

| r | pico | pico / (2πr) |
|---|---|---|
| **427.6** | **206** | **0.0767** |
| 429.6 | 107 | 0.0396 |
| 425.6 | 88 | 0.0329 |
| 431.6 | 87 | 0.0321 |

El ganador coincide con el radio real (428.3) dentro de **0.7 px** y le saca 2:1
al segundo. Pico bruto y pico normalizado por circunferencia coinciden en el
mismo radio, así que se usa el pico bruto (más simple).

### 2.5 Contraste invertido (DICLECI)

| Imagen | Contenido |
|---|---|
| `0.050_1.bmp` | disco **oscuro** r=427.5 sobre fondo claro |
| `0.508_1.bmp` | región clara r_eq=1534 con disco oscuro dentro (553 897 px) |
| `1.575_1.bmp` | círculo **mayor que el campo de visión**: solo se ve un arco |

La cadena usa magnitud de gradiente, así que el signo del contraste no la
afecta en principio (R7), pero el caso del círculo que excede el recorte
necesita detección explícita (R5).

### 2.6 Costos medidos

| Operación | Costo |
|---|---|
| `DerivGauss` 900 × 900 | 10.6 s → imagen completa ≈ 200 s |
| `DerivGauss` ROI 3.85 Mpx | 56.3 s |
| Estaciones 2-6 sobre la misma ROI | < 1 s |
| Barrido de 112 radios (3 182 bordes) | 5.1 s |

La convolución domina el tiempo; el barrido es marginal.

## 3. Diseño propuesto

### 3.1 Función de barrido (capa modelo)

```python
def estimar_radio(im_binary, r_min, r_max, paso=2.0, thres=0.99, dist=20):
    """Devuelve (radio, pico, relacion_ambiguedad)."""
```

- Recorre `np.arange(r_min, r_max + 1, paso)`.
- Para cada radio obtiene `acc.max()` (no necesita los picos, solo el máximo).
- `relacion_ambiguedad = segundo_pico / primer_pico` con los dos mayores picos
  de radios **distintos**.
- Sin dependencias de UI: cumple la regla del modelo.

Umbral de ambigüedad propuesto: **0.8**. En img100 la relación es 107/206 = 0.52
(no ambigua); un empate técnico (≥ 0.8) se reporta.

### 3.2 Flujo del orquestador

```
recorte -> etapas 1-6 -> bordes
   r0 = min(alto, ancho)/2
   si el usuario declaró diámetro: r = diametro_usuario/2        (omite barrido)
   si no:                          (r, pico, amb) = estimar_radio(bordes, 0.6*r0, r0)
   Hough con r -> find_circle(radio=r) -> LSC
```

### 3.3 Campo de diámetro (capa vista)

- Un `Adw.EntryRow` (o `Gtk.SpinButton`) rotulado por el valor detectado.
- Estado separado: `valor_detectado` (lo pone el barrido) y
  `valor_usuario` (lo escribe el usuario). El campo muestra
  `valor_usuario` si existe; si no, `valor_detectado`.
- Un cambio de texto marca `valor_usuario`; así un precargado nunca se confunde
  con una decisión manual (R6.3).
- Si el barrido es ambiguo, se muestra un aviso junto al campo.

### 3.4 Fuera de alcance (etapas siguientes)

- Círculos concéntricos (top-2 de radios) — requiere decisión de producto.
- Estimación del radio sin recorte previo.
- Borrado del código muerto (R8): se decide tras verificar utilidad, como en la
  etapa ⑥.

## 4. Verificación prevista

`tests/test_etapa7_hough_circles.py`:

- Barrido sobre círculos sintéticos de radio conocido (r = 20, 45, 80): error
  ≤ 1 px.
- Radio fuera de la banda → `ValueError`.
- Sin bordes → `n = 0`, sin excepción.
- `imagen binaria` con dos círculos de radios distintos → el barrido devuelve
  el de mayor pico y lo reporta como ambiguo si corresponde.
- Integración ⑥→⑦→⑧→⑨ sobre un círculo sintético de radio conocido: error del
  radio final ≤ 0.5 px.
- Caso de regresión del defecto: recorte de `img100` no se commitea (15 MB); la
  evidencia queda en este documento.
