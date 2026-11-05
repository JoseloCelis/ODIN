# Requirements Document

## Introduction

Este documento captura los requerimientos de la **etapa ① del pipeline de ODIN**
(`kernel-separable`): el cálculo del gradiente de una imagen mediante convolución
separable con un kernel derivada-gaussiana.

La etapa corresponde a `DerivGauss(E, sigma, wk, wConv, wr)` en
`src/odin/Preprocesamiento/models/deri_gauss.py` (legacy `odin/Preprocesamiento/DeriGauss.py`), apoyada por `Conv2D`/`ConvR`/`ConvC` en
`src/odin/Preprocesamiento/models/convolucion.py` (legacy `odin/Preprocesamiento/Convolucion/Conv2D.py`). La especificación fue extraída del
código actual (spec implícito) y de la referencia matemática; las divergencias
entre ambas quedan documentadas en `design.md`.

El resultado de esta etapa alimenta directamente a la etapa ② (`MagFase`):
cualquier error aquí se propaga a la magnitud/dirección del gradiente, al
umbralizado de Otsu y, en última instancia, a la detección de bordes y círculos.

---

## Glossary

- **Kernel_Gaussiano** (`gk`): vector de longitud `6σ+1` con la gaussiana
  `exp(-i²/(2σ²))` normalizada a suma 1, indexado de `-3σ` a `3σ`.
- **Kernel_Derivada** (`dgk`): derivada analítica del Kernel_Gaussiano:
  `dgk[i] = -(i/σ²)·gk[i]`.
- **Tap**: una de las muestras del kernel; `nk = 3σ` es la distancia máxima
  entre el tap central y un extremo (el kernel tiene `2·nk+1` taps).
- **Soporte**: rango de píxeles de entrada que contribuyen a un píxel de salida:
  `j ∈ [i−nk, i+nk]`, **incluyendo ambos extremos**.
- **Zero-padding**: los píxeles fuera de la imagen se tratan como 0 al
  evaluar el Soporte en los bordes.
- **DGX / DGY**: imágenes de salida con la derivada en dirección X / Y.
- **Corte**: fila (`DGX[wr,:]`) o columna (`DGY[:,wc]`) mostrada en la
  visualización de gradientes.

---

## Requirements

### Requirement 1: Kernel gaussiano normalizado

**User Story:** Como usuario de ODIN, quiero que el kernel de suavizado sea una
gaussiana correctamente normalizada, para que el filtro no altere la escala de
intensidades de la imagen.

#### Acceptance Criteria

1. WHEN `sigma` es un entero positivo, THE `DerivGauss` SHALL construir `gk` con
   `gk[k] = exp(-i²/(2σ²))` para `i` en `[-3σ, 3σ]` (longitud `6σ+1`).
2. THE `sum(gk)` SHALL ser igual a 1 con tolerancia `1e-12`.
3. THE `gk` SHALL ser simétrica respecto a su tap central (`gk[k] == gk[2·nk−k]`
   dentro de tolerancia de punto flotante).

### Requirement 2: Kernel derivada de la gaussiana

**User Story:** Como usuario de ODIN, quiero derivar con la derivada analítica
de la gaussiana, para que suavizado y derivada sean un solo filtro óptimo
(minimizador del ruido-derivada).

#### Acceptance Criteria

1. THE `dgk[k]` SHALL calcularse como `-(i/σ²)·gk[k]` con `i` la posición del tap.
2. THE `sum(dgk)` SHALL ser aproximadamente 0 (antisimétrica) con tolerancia
   `1e-12`.

### Requirement 3: Separabilidad de la convolución

**User Story:** Como desarrollador de ODIN, quiero explotar la separabilidad de
la gaussiana (filas luego columnas), para obtener el mismo resultado que una
convolución 2D con costo O(n·σ) en lugar de O(n²·σ²).

#### Acceptance Criteria

1. THE `DGX` SHALL obtenerse aplicando `dgk` a lo largo de las filas (eje X) y
   `gk` a lo largo de las columnas (eje Y), en ese orden.
2. THE `DGY` SHALL obtenerse aplicando `gk` a lo largo de las filas y `dgk` a lo
   largo de las columnas, en ese orden.
3. (Convención de signo, verificada con evidencia) ODIN calcula la **convolución
   discreta estándar** `Σ f[j]·k[i−j]` — la misma convención del `conv2` de
   MATLAB del que proviene el código. OpenCV (`sepFilter2D`/`filter2D`) calcula
   **correlación** (sin voltear el kernel); como `dgk` es antisimétrica, ambos
   difieren exactamente por el signo en DGX/DGY. La comparación válida contra
   OpenCV es `sepFilter2D` con correlación sobre `−dgk` y `BORDER_CONSTANT`
   (zero-padding, idéntico al de ODIN): SHALL coincidir en la **imagen completa**
   (bordes incluidos) con tolerancia `1e-12`.

### Requirement 4: Soporte completo del kernel en cada píxel de salida

**User Story:** Como usuario de ODIN, quiero que cada píxel de salida sume
**todos** los taps del kernel que caen dentro de la imagen, para que el filtro
sea simétrico y el gradiente quede correctamente centrado.

#### Acceptance Criteria

1. WHEN `i − nk ≥ 0` y `i + nk ≤ n−1`, THE `ConvR`/`ConvC` SHALL incluir en la
   suma **ambos** extremos `j = i−nk` y `j = i+nk` (rango inclusivo).
2. THE salida de `ConvR`/`ConvC` SHALL coincidir, con tolerancia relativa
   `1e-12`, con la correlación de referencia de NumPy (`np.convolve` con
   zero-padding y modo `'same'`) en al menos: 100 kernels/sizes aleatorios y los
   casos de borde `i < nk`, `i > n−1−nk` y `n ≤ 2·nk`.
3. (Defecto registrado) la implementación previa cumplía
   `salida_actual == referencia_con_gk[0]_anulado`: descartaba el tap de
   distancia máxima positiva, produciendo un filtro asimétrico con error de
   hasta ~12% frente a la referencia en señales pequeñas.

### Requirement 5: Validación del parámetro sigma

**User Story:** Como usuario de ODIN, quiero que `sigma ≤ 0` devuelva imágenes
nulas sin excepción, para que un parámetro inválido no tumbe la aplicación.

#### Acceptance Criteria

1. WHEN `sigma ≤ 0`, THE `DerivGauss` SHALL retornar `(zeros_like(E),
   zeros_like(E))` sin lanzar excepción.
2. WHEN `sigma ≤ 0`, THE validación SHALL ejecutarse **antes** de dimensionar
   cualquier array con `n = 3σ` (que sería de longitud ≤ 0 o negativa).

### Requirement 6: Visualización con cortes válidos

**User Story:** Como usuario de ODIN, quiero ver los cortes de gradiente sin
que la ventana de visualización truene, sin importar el tamaño de la imagen.

#### Acceptance Criteria

1. WHEN `wConv` es verdadero, THE visualización SHALL graficar el corte vertical
   en una columna `wc = min(640, nc−1)` (hoy hardcodeada a 640) y el corte
   horizontal en una fila `wr` acotada a `[0, nr−1]`.
2. WHEN la imagen tiene menos de 641 columnas, THE visualización SHALL graficar
   sin `IndexError`.
