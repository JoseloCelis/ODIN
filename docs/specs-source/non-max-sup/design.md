<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/non-max-sup.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | CONTRADICHO | el requisito exige sectores con `np.mod(angle, 360)` y cortes en 22.5° (`requirements.md:46`); el código compara sobre el eje `mod 180` con fracción angular: `non_max_sup.py:64-66,72-78,85`. R1.2/R1.3 se cumplen (borde de 1 px en 0; adelgazamiento) |
> | R2 | CONTRADICHO | el requisito exige pesos `w_x=|Gx|/max(|Gx|,|Gy|)`, `w_y=|Gy|/max(...)` (`requirements.md:64`); el código interpola con la fracción angular `f` y no usa Gx/Gy (`non_max_sup.py:36-38,66,81-82`) |
> | R3 | IMPLEMENTADO | simetría por construcción sobre el eje mod 180 (`non_max_sup.py:61-66`); test `tests/unit/Procesamiento/test_etapa3_non_max_sup.py:50` |
> | R4 | IMPLEMENTADO | `keep = (C >= v_este) & (C >= v_opuesto)` (`non_max_sup.py:85`); test `:40` |
> | R5 | IMPLEMENTADO | `DobleThreshold` `non_max_sup.py:268-297` (gnh=1.0 si M≥thresh; gnl magnitud en [thresh², thresh); thresh>1→1.0; sin parámetro `angle`); tests `:77,88` |
>
> **Pendientes:** ninguno.
> **Divergencias verificadas:** R1.1 — `requirements.md:46` exige `np.mod(angle, 360)` con límites 22.5°/67.5°/…; `non_max_sup.py:64-66` usa `np.mod(angle, 180.0)` y `sector = floor(phi/45)`. R2.1 — `requirements.md:64` exige los pesos `|Gx|/max`; `non_max_sup.py:36-38` declara Gx/Gy sin uso y `:66,81-82` interpola con `f=(phi−45·sector)/45`. La referencia `tests/utilidades.py:nms_referencia_escalar` implementa el mismo esquema mod-180: su test valida coherencia interna, no el spec.
> **Inciertos:** ninguno.
<!-- ESTADO:FIN -->

# Design Document — non-max-sup

## 1. Revisión de la implementación

El módulo `NonMaxSuppressionVectorizado.py` contiene 5 funciones; el pipeline
(`main.py`) usa **solo 2**:

| Función | Uso | Estado |
|---|---|---|
| `LinearInterpolation(MG, Gx, Gy, angle)` | etapa ③, activa | divergencias D1, D2 |
| `DobleThreshold(M, angle, thresh)` | etapa ⑤, activa | D3 (parámetro muerto) |
| `NMS_Parabolic(MG, angle)` | sin uso | experimental |
| `NMS_Gaussian(MG, angle)` | sin uso | experimental |
| `Interpolation_old(MG, Gx, Gy, angle)` | sin uso | código muerto (D4) |

Existe además `NMS_Migrado.py` (variante alternativa, sin importar).

### Divergencias probadas con ejecución

- **D1 (cuadrante perdido)**: `w_x`/`w_y` usan `np.abs`, por lo que el signo de
  `Gx`/`Gy` se descarta y los vecinos de interpolación son siempre los del
  primer cuadrante (p.ej. `S→SE` y `N→NW`). Verificado: un perfil asimétrico y
  su espejo (ángulos 80°/100°) producen máscaras que **no son espejo** — la
  celda extra sobrevive en el lado equivocado (2 celdas de 81). Sesgo sistemático
  en bordes diagonales fuera del primer cuadrante.
- **D2 (tie-breaking asimétrico)**: sector 0 usa `>=` y los sectores 45/90/135
  usan `>`. Verificado con meseta 3×3: 9/9 celdas sobreviven con gradiente 0;
  0/9 con gradiente 90. Las mesetas se tratan distinto según su orientación.
- **D3 (firma que miente)**: `DobleThreshold(M, angle, thresh)` ignora `angle`
  por completo (el NMS se separó a `LinearInterpolation` y el parámetro quedó).
- **D4 (código muerto)**: `Interpolation_old` + bloques comentados grandes en
  `DobleThreshold` y en las variantes experimentales. `NMS_Parabolic` y
  `NMS_Gaussian` son material de experimentación sin uso — se conservan hasta
  decisión de limpieza dedicada (no tocar en el fix).

## 2. Comportamientos correctos verificados (caracterización)

- Adelgazamiento: cuchilla ancha de 3 px → sobrevive solo el máximo (1 px).
- Pico aislado (delta) sobrevive como único píxel.
- `DobleThreshold`: partición exacta `M >= thresh` → fuertes 1.0; `[thresh²,
  thresh)` → débiles con magnitud original. Corte superior a 1 → 1.0.
- Pesos sin división por cero en píxeles planos (`max_G_safe`).

## 3. Decisiones

- **Alcance del fix (pendiente de usuario)**:
  1. D2 (tie-breaking): alineación trivial de un operador; recomiendo `>=` en
     los 4 sectores (nunca pierde máximos reales; las mesetas sobreviven
     completas y el umbralizado doble las maneja).
  2. D1 (cuadrante): cambio algorítmico real — seleccionar los vecinos de
     interpolación según el signo de `Gx`/`Gy` (cuadrantes 2-4). Requiere su
     propia batería de verificación; es el fix con más riesgo de la serie.
  3. D3: quitar el parámetro `angle` de `DobleThreshold` **cambia la firma**
     pública y su único llamador (`main.py`). Alternativa conservadora:
     documentar y dejar para el refactor `src/odin/`.
  4. D4: limpieza de código muerto en su propio commit, aparte.
- **No sustituir por `cv2.Canny`**: el pipeline usa NMS + Otsu + Rosin +
  histéresis propia; reemplazar por Canny cambiaría el algoritmo completo.

## 4. Verificación

Batería ejecutada (referencia en la sesión): A1/A4 (picos y adelgazamiento),
B' (meseta 3×3 por sector), C' (simetría de espejo 80°/100°), D (partición de
umbrales). Tras cualquier fix, reejecutarla; los cambios de D1 deben conservar
A1/A4 y lograr la simetría exacta de C'.

## 5. Resolución (commits de fix)

- **D1 + D2 resueltos con una sola reescritura del núcleo**: la comparación se
  hace sobre el **eje del gradiente (mod 180°)** interpolando entre los dos
  vecinos discretos que lo estrangulan en cada extremo (fracción angular
  `(φ mod 45)/45`). Los vecinos se eligen por sector, no por cuadrante →
  simetría exacta; `>=` en todos los sectores → tie-breaking consistente.
  Nota: `Gx`/`Gy` quedan en la firma de `LinearInterpolation` reservados por
  compatibilidad; el cálculo usa solo `angle`.
- **D3 resuelto**: firma `DobleThreshold(M, thresh)`; llamador actualizado en
  `main.py`.
- **D4 resuelto con revisión de utilidad (corregido tras decisión del usuario)**:
  "sin referencias" no es lo mismo que "sin utilidad" — verificar la ausencia
  de llamadores solo respondía "¿se usa?", no "¿sirve?". Veredicto final tras
  batería de utilidad:
  - **Recuperados** `NMS_Parabolic` y `NMS_Gaussian`: variantes de NMS con
    estimación **subpíxel del valor del pico** (ajuste parabólico). En el
    perfil cuadrático de prueba (vertex en x0=2.3): error `0.000000` y
    `0.001138` vs `0.008100` del discreto. Simetría 20/20 y adelgazamiento
    correctos. Caveat documentado en sus docstrings: el valor del pico puede
    exceder `max(MG)` — aptos para medición geométrica (etapas 7-9), no como
    entrada de Otsu/DobleThreshold.
  - **Se mantienen eliminados** `Interpolation_old` (falla simetría 20/20: es
    la misma ceguera de cuadrante D1, superada por el `LinearInterpolation`
    reescrito) y `NMS_Migrado.py` (falla simetría 20/20, aviso `0/0` al
    dividir entre `MG[i,j]=0`, bucles por píxel lentos). Verificados ambos
    antes de confirmar el descarte; git retiene el historial.
- **Verificación del fix**: batería completa en verde + **referencia escalar
  independiente** (loops escritos desde la fórmula del spec) igualada de forma
  exacta en 100 casos aleatorios + integración etapas 1→2→3 con 268 bordes
  fuertes detectados en un rectángulo sintético.
- **Impacto numérico**: el output del pipeline cambia para ángulos no
  alineados a ejes (pesos angulares en vez de tan; vecinos corregidos en
  cuadrantes 2-4). Es un cambio buscado — era el defecto D1.
