# Design Document — find-circle (etapa ⑧)

## 1. Estado del módulo

`findCircle.py` (95 líneas), exportado como `circleFilter`:

| Símbolo | Rol | Llamadores | Estado |
|---|---|---|---|
| `find_circle(detected_edges, re, centro)` | filtra los bordes del anillo | `main.py:586` | **en producción** |
| rama `re > 0` | anillo `[re - 10, re + 10]` | el llamador único | en producción |
| `segmento_mas_largo(puntos)` | agrupamiento por saltos de 6 px | **0** | extraído de la rama `re == 0`, probado aislado (R6) |

`main.py` pasa `re = radio` (siempre > 0, estimado en ⑦ o declarado en el campo
de diámetro) y el centro elegido por `mejor_centro`. La salida va directo a
`LSC.Circulo_simple`.

## 2. Evidencia ejecutada

### 2.1 El anillo es frágil lejos del radio real

Sintéticos con manchas tipo texto y radio de búsqueda `re` desviado:

| `r` real | `re` | Puntos | Cobertura | Hueco | r ajustado | Error |
|---|---|---|---|---|---|---|
| 12 | 12 | 156 | 100 % | 0° | 11.99 | 0.01 px |
| 12 | 24 | 89 | 9.7 % | 325° | 5.48 | 6.52 px |
| 20 | 32 | 70 | 8.3 % | 330° | 6.24 | 13.76 px |
| 45 | 57 | 25 | 2.8 % | 350° | 2.10 | 42.90 px |
| 60 | 72 | 14 | 2.8 % | 350° | 1.92 | 58.08 px |
| 100 | 112 | 0 | — | — | anillo vacío | — |
| 428 | 440 | 0 | — | — | anillo vacío | — |

Con `re` acierta (±6 px) el ajuste es exacto a ≤ 0.1 px. Con `re` desviado más
que la tolerancia, el anillo queda vacío (círculos grandes) o contiene solo
manchas (círculos chicos) y **el ajuste devuelve un círculo que no existe**.

### 2.2 La tolerancia fija degenera cuando `re <= 10`

Sintético `r = 8` con un círculo interno en `r = 20`, `re = 10`:

| Tolerancia | Puntos | Contaminación | r ajustado | Error de radio |
|---|---|---|---|---|
| fija 10 px (`[0, 20]`) | 240 | **55.0 %** | 15.40 | **7.40 px** |
| `min(10, 0.25·re)` = 2 px | 60 | 0.0 % | 8.43 | 0.43 px |

El límite inferior `re - 10 = 0` convierte el anillo en un disco: incluye el
círculo interno completo. Con la tolerancia acotada se captura solo la mitad
exterior del anillo, que basta para el ajuste (0.43 px).

Sin círculo interno (`r = 8`, `re = 10`): fija → 108 pts / 0.03 px; acotada →
60 pts / 0.43 px. Ambas correctas; la acotada es más exigente con la precisión
del radio recibido, y la etapa ⑦ entrega ±0.3–1 px.

### 2.3 El síntoma del usuario, reproducido sobre `img100`

Recorte holgado 2288 × 2000 (bordes cacheados, disco real r = 428.31 en
(760.6, 611.2)):

| Radio de búsqueda | Picos de Hough | Centro elegido | Anillo | Cobertura | Hueco | Ajuste final | Error |
|---|---|---|---|---|---|---|---|
| `126.5` (constante vieja) | 4 | (982, 2045) — **el texto** | 506 pts | **54.2 %** | **115°** | r = 128.01 | centro **1452.81 px** |
| `300.0` | — | — | 502 pts | 27.8 % | 155° | rechazado | — |
| `550.0` | — | — | 454 pts | 15.3 % | 185° | rechazado | — |
| `428.3` (el real) | 1 | (761, 611) | 3153 pts | **100 %** | **0°** | r = 427.85 | 0.46 px radio / 0.32 px centro |

Con la constante vieja el anillo **no** selecciona el disco: selecciona los
glifos del texto y ajusta un círculo de r = 128 ahí. El `pv` de ese ajuste es
12.2 frente a 2.03 del correcto, pero en la etapa ⑦ ya se midió que el `pv`
puede ser *mejor* en un ajuste malo (0.995 vs 2.034), así que no sirve como
validador.

### 2.4 Una selección insuficiente rompe el ajuste en silencio

| Entrada a `Circulo_simple` | Resultado |
|---|---|
| 0 puntos | `ValueError: zero-size array to reduction operation maximum which has no identity` |
| 1 punto `(10,10)` | centro (4.99, 4.99), r = 7.08, **pv = 0.0** |
| 2 puntos colineales | centro (15, 15), r = 7.07, **pv = 0.0** |
| 3 puntos colineales | centro (10, 10), r = 11.55, pv = 8.95 |
| 3 puntos **casi** colineales | centro (**-200010, 200020**), r = **282864**, **pv = 0.0** |

El `pv` no distingue estos casos: devuelve 0 exacto tanto en un ajuste
subdeterminado como en uno catastrófico. Por eso la etapa ⑧ frena antes, con
el mínimo de puntos y la cobertura angular.

## 3. Diseño

### 3.1 API (capa modelo)

```python
TOLERANCIA_MAX_PX = 10.0
FRACCION_TOLERANCIA_RADIO = 0.25
UMBRAL_COBERTURA = 0.75
HUECO_MAX_DEG = 60.0
MINIMO_PUNTOS = 3

def tolerancia_anillo(re):                    # -> float
def find_circle(detected_edges, re=None, centro=(0, 0), tolerancia=None)
                                              # -> ndarray (N, 2)
def cobertura_angular(puntos, centro, bins=72)  # -> (cobertura, hueco_max_deg)
def validar_anillo(puntos, centro, minimo_puntos=MINIMO_PUNTOS,
                   cobertura_min=UMBRAL_COBERTURA, hueco_max=HUECO_MAX_DEG)
                                              # -> (bool, motivo)
def segmento_mas_largo(puntos)                # -> ndarray (M, 2)
```

- `tolerancia_anillo(re) = min(TOLERANCIA_MAX_PX, FRACCION_TOLERANCIA_RADIO * re)`
  y nunca deja el límite inferior en negativo.
- `find_circle` **exige** el radio (R6): `re=None` y `re <= 0` lanzan
  `ValueError`. `tolerancia=None` pide el valor automático de R2 y un valor
  explícito permite pruebas y escenarios con ruido de radio conocido.
- `segmento_mas_largo` es el antiguo modo "sin radio", extraído para que no se
  active por omisión; conserva el resultado de la rama original (R6.4).

- `cobertura_angular` reparte los ángulos en `bins` sectores y devuelve la
  fracción ocupada y el mayor hueco circular. Costo O(N) sobre los puntos
  seleccionados (3153 en el caso real: despreciable).
- `validar_anillo` devuelve `(False, motivo)` con un texto que el orquestador
  usa en el error; no lanza excepción, para que el llamador decida.
- Sin dependencias de UI: cumple la regla del modelo.

### 3.2 Elección de los umbrales

La cobertura es el primer filtro y el hueco el segundo. Medido:

| Criterio | Valor | Acepta | Rechaza |
|---|---|---|---|
| Cobertura | **0.75** | 100 % (círculo completo) | 54.2 % (glifo real), 27.8 %, 15.3 %, 9.7 % y menos |
| Hueco máximo | **60°** | 0° | 70° (arco de 290°), 115° (glifo), 325–350° (basura) |

El umbral de cobertura queda a 0.21 del rechazado más cercano (54.2 %) y a 0.25
del caso válido, o sea casi equidistante. Como la cobertura ya rechaza todo lo
que está por debajo de 0.75, el hueco solo puede actuar en la banda 0.75–0.83:
es una segunda defensa para un anillo que cubre bastante pero deja una porción
grande sin puntos (medido con un arco de 290°: 80.5 % de cobertura, 70° de
hueco). Los dos umbrales tienen test propio.

### 3.3 Flujo del orquestador (implementado)

```
⑦ -> radio (usuario o barrido)
   centro = mejor_centro(...)                     # un solo centro (R5)
   puntos = find_circle(bordes, radio, (cx, cy))  # anillo con tolerancia acotada
   (ok, motivo) = validar_anillo(puntos, (cx, cy))
   si not ok -> ValueError(motivo)                # mensaje explicativo
   (x, y, r, pv) = Circulo_simple(puntos)
```

La validación ocurre **antes** del ajuste y con el centro de ⑦ (R3.4), así que
la etapa ⑧ no depende de la etapa ⑨.

### 3.4 Fuera de alcance

- Ajuste robusto en ⑨ (rechazo de puntos atípicos, RANSAC, mínimos cuadrados
  totales): el `pv` actual no distingue un ajuste bueno de uno malo, y eso
  pertenece a la etapa ⑨.
- Eliminación de `segmento_mas_largo` (R6): sin llamadores, pero se conserva
  como capacidad y por trazabilidad con el MATLAB original. Si tras la
  refactorización nadie la usa, ahí sí se puede borrar.
- Recuperación automática tras un rechazo (reintentar con otro radio): hoy el
  usuario corrige el diámetro en el campo de la etapa ⑦.

## 4. Verificación ejecutada

`tests/test_etapa8_find_circle.py` — **33 casos**:

| Requisito | Test |
|---|---|
| R1 | selección por distancia, forma `(N,2)`, vacío sin excepción, orden irrelevante para el ajuste |
| R2 | `tolerancia_anillo` con re = 8 / 20 / 40 / 428, radios no positivos, círculo interno sin contaminación, equivalencia con la tolerancia fija para re ≥ 40, tolerancia explícita |
| R3 | cobertura 100 % / hueco 0° en un anillo completo; anillo de basura por debajo del umbral; sin puntos → (0.0, 360.0); arco rechazado por cobertura; arco de 290° rechazado por hueco |
| R4 | 0, 1 y 2 puntos rechazados con motivo; ajuste subdeterminado con `pv = 0`; tres puntos casi colineales (r = 282864) rechazados por cobertura |
| R5 | centro con arreglos → `ValueError` explícito |
| R6 | `find_circle` sin radio / con radio 0 / con radio negativo → `ValueError`; `segmento_mas_largo` elige el grupo más numeroso, no corta con un hueco de 6 px, conserva (x, y) y devuelve (0,2) con entrada vacía |


Escrito en rojo primero: **19 fallos / 5 pasados**; los 5 que pasaron son la
caracterización del comportamiento actual (forma del arreglo vacío, selección
vacía, orden, rama `re == 0` y el `ValueError` de numpy con arreglos), y los 19
restantes describen el comportamiento nuevo.

Después se corrigió R6: la caracterización de la rama `re == 0` se reemplazó por
siete casos del modo explícito, y la equivalencia de `segmento_mas_largo` con la
rama original se comprobó contra el archivo commiteado en `b350deb` (300
conjuntos aleatorios, 0 diferencias).

Verificación sobre el recorte holgado real de `img100` (bordes cacheados):

| Radio de búsqueda | Cobertura | Hueco | Validación | Ajuste |
|---|---|---|---|---|
| 428.0 (el real) | 100 % | 0° | **aceptado** | r = 427.85 → 0.46 px de radio, 0.32 px de centro |
| 126.5 (constante vieja) | 54.2 % | 115° | rechazado | — |
| 300.0 | 27.8 % | 155° | rechazado | — |
| 550.0 | 15.3 % | 185° | rechazado | — |

Sin regresión en la medición de la etapa ⑦: el caso correcto da exactamente los
mismos números que antes (diámetro 855.70, centro a 0.29–0.32 px). Suite
completa: **126 passed**.
