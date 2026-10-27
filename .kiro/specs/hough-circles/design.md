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

### 2.7 Defecto R9: el llamador recibía todos los centros

`main.py` hacía `aproxCenter = (xRecortada, yRecortada)` y lo pasaba a
`find_circle`, que hace `xd, yd = centro`. Con `n = 1` los arreglos de un
elemento se transmiten por broadcasting y **funciona por casualidad**. Con
`n > 1` y un número distinto de puntos de borde, rompe:

```
ValueError: operands could not be broadcast together with shapes (968,) (2,)
```

Medido con dos círculos sintéticos: `n = 2`, 968 puntos → `ValueError`. En el
recorte real de `img100`, Hough devolvía **54 picos** con `r = 126.5`, así que
el caso que funcionaba era el improbable. `main.py` captura la excepción y
muestra "Error Matemático", de modo que el usuario ve un fallo genérico y no
la causa.

Además, el orden de `np.nonzero` es por filas, **no** por votos: quedarse con
`[0]` sería elegir el pico más arriba en la imagen. Por eso la selección es por
`argmax` del acumulador.

### 2.8 Verificación de punta a punta sobre `img100`

Recorte de 1114 × 1112 (r0 = 556.0), cadena exacta del orquestador:

| Dato | Valor |
|---|---|
| Disco real | centro (555.6, 556.2), r = 428.31 → diámetro 856.61 |
| Banda de búsqueda | [333.6, 556.0] |
| `estimar_radio` | **427.6** en 5.6 s, pico 206, ambigüedad **0.35** |
| Picos de Hough con ese radio | **1**, centro (556, 556), 206 votos |
| Anillo de `find_circle` | 3153 puntos |
| Ajuste final | centro (555.81, 556.43), **r = 427.85**, diámetro 855.70 |

Errores: radio **0.46 px**, diámetro **0.91 px**, centro **0.29 px**.
Antes, con `diametro = 253`: r = 403.95, 24.4 px de error de centro y 24.4 px
de radio. `pv` pasó de 0.995 (ajuste a un arco) a 2.034.

## 3. Diseño

### 3.1 API implementada (capa modelo)

```python
UMBRAL_AMBIGUEDAD = 0.8
SEPARACION_AMBIGUEDAD_PX = 6.0

def mejor_centro(x0, y0, acumulador):        # -> (x, y, votos) | None
def estimar_radio(im_binary, r_min, r_max, paso=2.0, thres=0.99, dist=20,
                  separacion_px=SEPARACION_AMBIGUEDAD_PX):
                                             # -> (radio, pico, ambiguedad)
```

- Recorre `np.arange(r_min, r_max + paso/2, paso)`.
- Para cada radio toma `acc.max()`.
- `ambiguedad = segundo / primero`, donde `segundo` ignora los radios a menos
  de `separacion_px` del ganador (si no, todo círculo perfecto sería ambiguo:
  medido 0.95 de relación con `r=35 + r=45` frente a 0.26-0.37 de un círculo
  único).
- Sin bordes o sin votos → `(0.0, 0, 0.0)`, sin excepción.
- Sin dependencias de UI: cumple la regla del modelo.

### 3.2 Flujo del orquestador (implementado, sin R6)

```
recorte -> etapas 1-6 -> bordes
   r0 = min(alto, ancho)/2
   (r, pico, amb) = estimar_radio(bordes, 0.6*r0, r0)
   si r == 0 -> ValueError (el recorte no contiene un círculo)
   Hough con r -> mejor_centro -> find_circle(radio=r, centro) -> LSC
   si amb >= UMBRAL_AMBIGUEDAD -> aviso en consola
```

El campo de diámetro con precarga (R6) sigue pendiente: hoy el valor detectado
se informa por consola, no se puede sobrescribir desde la interfaz.

### 3.3 Campo de diámetro (capa vista) — DEUDA (R6)

- Un `Adw.EntryRow` (o `Gtk.SpinButton`) rotulado por el valor detectado.
- Estado separado: `valor_detectado` (lo pone el barrido) y
  `valor_usuario` (lo escribe el usuario). El campo muestra
  `valor_usuario` si existe; si no, `valor_detectado`.
- Un cambio de texto marca `valor_usuario`; así un precargado nunca se confunde
  con una decisión manual (R6.3).
- Si el barrido es ambiguo, se muestra un aviso junto al campo.

### 3.4 Fuera de alcance (etapas siguientes)

- Círculos concéntricos (top-2 de radios) — requiere decisión de producto.
  Mientras no exista, un círculo grande tapa a uno mucho más chico sin que se
  reporte ambigüedad (§2.5 de R5).
- Estimación del radio sin recorte previo: la banda `[0.6·r0, r0]` asume que el
  recorte contiene el círculo completo y no mucho más. Medido: con un recorte
  holgado (r0 = 2.2·r) el radio verdadero queda **fuera** de la banda y el
  barrido devuelve basura.
- Borrado del código muerto (R8): verificado sin llamadores; se decide aparte.


## 4. Verificación ejecutada

`tests/test_etapa7_hough_circles.py` — **22 casos**:

| Requisito | Test |
|---|---|
| R1 | centro de un círculo sintético, forma del acumulador, `dist<10`, `thres<0.5`, sin bordes, imagen de tamaño cero |
| R9 | dos círculos → `n=2`; `mejor_centro` elige por votos; sin picos → `None`; flujo con un solo centro no rompe |
| R3 / R4 | radios conocidos 20/45/80 (error ≤ 1 px), banda invertida, radio no positivo, paso no positivo, sin bordes, ambigüedad alta y baja |
| R2 | `main.py` no contiene radio constante y llama a `estimar_radio` |
| R7 | cadena ①→⑥→⑦→⑧→⑨ con contraste normal e invertido (error ≤ 0.5 px) |

Escrito en rojo primero: **16 fallos / 6 pasados**; los 6 que pasaron son la
caracterización de R1, o sea que los tests describen el contrato real y no uno
inventado. Suite completa: **84 passed**.

El recorte de `img100` no se commitea (15 MB); la evidencia numérica de punta a
punta queda en §2.8.

