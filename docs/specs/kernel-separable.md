# kernel-separable — Etapa ①: kernel derivada-gaussiana separable

> Absorbido de `.kiro/specs/kernel-separable/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Kernel gaussiano normalizado

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/deri_gauss.py:34-42`

> ### Requirement 1: Kernel gaussiano normalizado
>
> **User Story:** Como usuario de ODIN, quiero que el kernel de suavizado sea una
> gaussiana correctamente normalizada, para que el filtro no altere la escala de
> intensidades de la imagen.
>
> #### Acceptance Criteria
>
> 1. WHEN `sigma` es un entero positivo, THE `DerivGauss` SHALL construir `gk` con
>    `gk[k] = exp(-i²/(2σ²))` para `i` en `[-3σ, 3σ]` (longitud `6σ+1`).
> 2. THE `sum(gk)` SHALL ser igual a 1 con tolerancia `1e-12`.
> 3. THE `gk` SHALL ser simétrica respecto a su tap central (`gk[k] == gk[2·nk−k]`
>    dentro de tolerancia de punto flotante).

El código construye `gk` con `np.exp(-(i ** 2) / s2)` para `i ∈ [-n, n]` y lo
normaliza por su suma (`gk[k] = gk[k] / s`). Verificado en esta ejecución:
`sum(gk) = 1.0` y simetría exacta (`gk == gk[::-1]`).

### R2 — Kernel derivada de la gaussiana

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/deri_gauss.py:40-43`

> ### Requirement 2: Kernel derivada de la gaussiana
>
> **User Story:** Como usuario de ODIN, quiero derivar con la derivada analítica
> de la gaussiana, para que suavizado y derivada sean un solo filtro óptimo
> (minimizador del ruido-derivada).
>
> #### Acceptance Criteria
>
> 1. THE `dgk[k]` SHALL calcularse como `-(i/σ²)·gk[k]` con `i` la posición del tap.
> 2. THE `sum(dgk)` SHALL ser aproximadamente 0 (antisimétrica) con tolerancia
>    `1e-12`.

El código calcula `dgk[k] = -s2 * i * gk[k]` con `s2 = 1.0/σ²`. Verificado:
`sum(dgk) ≈ -7.4e-18`, dentro de la tolerancia `1e-12`.

### R3 — Separabilidad de la convolución

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/deri_gauss.py:51-52`

> ### Requirement 3: Separabilidad de la convolución
>
> **User Story:** Como desarrollador de ODIN, quiero explotar la separabilidad de
> la gaussiana (filas luego columnas), para obtener el mismo resultado que una
> convolución 2D con costo O(n·σ) en lugar de O(n²·σ²).
>
> #### Acceptance Criteria
>
> 1. THE `DGX` SHALL obtenerse aplicando `dgk` a lo largo de las filas (eje X) y
>    `gk` a lo largo de las columnas (eje Y), en ese orden.
> 2. THE `DGY` SHALL obtenerse aplicando `gk` a lo largo de las filas y `dgk` a lo
>    largo de las columnas, en ese orden.
> 3. (Convención de signo, verificada con evidencia) ODIN calcula la **convolución
>    discreta estándar** `Σ f[j]·k[i−j]` — la misma convención del `conv2` de
>    MATLAB del que proviene el código. OpenCV (`sepFilter2D`/`filter2D`) calcula
>    **correlación** (sin voltear el kernel); como `dgk` es antisimétrica, ambos
>    difieren exactamente por el signo en DGX/DGY. La comparación válida contra
>    OpenCV es `sepFilter2D` con correlación sobre `−dgk` y `BORDER_CONSTANT`
>    (zero-padding, idéntico al de ODIN): SHALL coincidir en la **imagen completa**
>    (bordes incluidos) con tolerancia `1e-12`.

`DGX = Conv2D(E, dgk, gk, nk, nr, nc)` y `DGY = Conv2D(E, gk, dgk, nk, nr, nc)`.
Re-verificado en esta ejecución contra `cv2.sepFilter2D` con correlación sobre
`−dgk` y `BORDER_CONSTANT`: discrepancia máxima observada `2.3e-16` para
σ = 1.0–4.0, dentro de la tolerancia `1e-12`. El bloque de estado del original
consigna `≤ 7e-17`; la substancia (concordancia a precisión de máquina) se
verifica, aunque la cota exacta observada es ligeramente mayor.

### R4 — Soporte completo del kernel en cada píxel de salida

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/convolucion.py:25-34`

> ### Requirement 4: Soporte completo del kernel en cada píxel de salida
>
> **User Story:** Como usuario de ODIN, quiero que cada píxel de salida sume
> **todos** los taps del kernel que caen dentro de la imagen, para que el filtro
> sea simétrico y el gradiente quede correctamente centrado.
>
> #### Acceptance Criteria
>
> 1. WHEN `i − nk ≥ 0` y `i + nk ≤ n−1`, THE `ConvR`/`ConvC` SHALL incluir en la
>    suma **ambos** extremos `j = i−nk` y `j = i+nk` (rango inclusivo).
> 2. THE salida de `ConvR`/`ConvC` SHALL coincidir, con tolerancia relativa
>    `1e-12`, con la correlación de referencia de NumPy (`np.convolve` con
>    zero-padding y modo `'same'`) en al menos: 100 kernels/sizes aleatorios y los
>    casos de borde `i < nk`, `i > n−1−nk` y `n ≤ 2·nk`.
> 3. (Defecto registrado) la implementación previa cumplía
>    `salida_actual == referencia_con_gk[0]_anulado`: descartaba el tap de
>    distancia máxima positiva, produciendo un filtro asimétrico con error de
>    hasta ~12% frente a la referencia en señales pequeñas.

`ConvR`/`ConvC` usan `j0 = max(i−nk, 0)` y `j1 = min(i+nk+1, n)`, es decir el
rango inclusivo con zero-padding. En tamaños habituales coincide con
`np.convolve(..., mode='same')`; el caso literal `n ≤ 2·nk` queda registrado en
Divergencias.

### R5 — Validación del parámetro sigma

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/deri_gauss.py:21-23`

> ### Requirement 5: Validación del parámetro sigma
>
> **User Story:** Como usuario de ODIN, quiero que `sigma ≤ 0` devuelva imágenes
> nulas sin excepción, para que un parámetro inválido no tumbe la aplicación.
>
> #### Acceptance Criteria
>
> 1. WHEN `sigma ≤ 0`, THE `DerivGauss` SHALL retornar `(zeros_like(E),
>    zeros_like(E))` sin lanzar excepción.
> 2. WHEN `sigma ≤ 0`, THE validación SHALL ejecutarse **antes** de dimensionar
>    cualquier array con `n = 3σ` (que sería de longitud ≤ 0 o negativa).

El guard `if sigma <= 0: return np.zeros_like(E), np.zeros_like(E)` está en `:21`,
antes de `n = round(3 * sigma)` (`:30`). Tests:
`tests/unit/Preprocesamiento/test_etapa1_kernel_separable.py:17,25`.

### R6 — Visualización con cortes válidos

**Estado:** PENDIENTE · **Evidencia:** `src/odin/Preprocesamiento/models/deri_gauss.py:1-8`

> ### Requirement 6: Visualización con cortes válidos
>
> **User Story:** Como usuario de ODIN, quiero ver los cortes de gradiente sin
> que la ventana de visualización truene, sin importar el tamaño de la imagen.
>
> #### Acceptance Criteria
>
> 1. WHEN `wConv` es verdadero, THE visualización SHALL graficar el corte vertical
>    en una columna `wc = min(640, nc−1)` (hoy hardcodeada a 640) y el corte
>    horizontal en una fila `wr` acotada a `[0, nr−1]`.
> 2. WHEN la imagen tiene menos de 641 columnas, THE visualización SHALL graficar
>    sin `IndexError`.

El módulo es modelo puro: su cuerpo es docstring, `import numpy` y `DerivGauss`,
sin código de visualización. No existe `wc = min(640, nc−1)`; `wr` solo está
presente como parámetro sin usar en la firma de `DerivGauss`
(`deri_gauss.py:12`). El requisito no está implementado.

## Divergencias

- **R4.2** — el AC literal `n ≤ 2·nk` toma `np.convolve(..., mode='same')` como
  referencia, pero NumPy devuelve `max(n, 2nk+1)` muestras: con `n=5` y `nk=9` la
  referencia tiene forma `(19,)` y `ConvR` devuelve `(5,)`. El código calcula la
  convolución centrada completa con zero-padding y longitud `n`. · `src/odin/Preprocesamiento/models/convolucion.py:21-37`
- **R3/R4** — no hay cross-check automático versionado: `tests/utilidades.py:44-49`
  define `derivada_gaussiana_referencia` y ningún test la invoca (0 usos). · `tests/utilidades.py:44-49`
- **R6** — el bloque de estado del original afirma que no existen
  `wc = min(640, nc−1)` ni `wr`; `wc` efectivamente no existe, pero `wr` está
  presente como parámetro sin usar en la firma de `DerivGauss`. · `src/odin/Preprocesamiento/models/deri_gauss.py:12`

## Pendientes

- **R6** — implementar la visualización de cortes con `wc = min(640, nc−1)` y `wr`
  acotada a `[0, nr−1]`; hoy el módulo es modelo puro y no grafica.
