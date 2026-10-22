# Design Document — kernel-separable

## 1. Contexto y causa raíz de las divergencias

La etapa ① fue traducida de MATLAB a Python. En MATLAB los rangos
`j0:j1` son **inclusivos**; en Python `range(j0, j1)` es **exclusivo** del
extremo superior. Esa diferencia de convención, no la matemática, originó el
defecto crítico (D1).

### D1 (CRÍTICA) — Tap extremo perdido en `ConvR`/`ConvC`

```python
j1 = i + nk          # MATLAB: j1 era el último índice INCLUIDO
for j in range(j0, j1):   # Python: excluye j1 → nunca evalúa j = i+nk
```

Consecuencia: el tap `gk[0]` (distancia `+nk`) jamás se usa. El filtro resulta
**asimétrico** y su respuesta efectiva está **desplazada medio píxel**, con
error medido de hasta ~12% frente a la referencia en un ejemplo mínimo
(evidencia en `tasks.md`).

Corrección: `j1 = i + nk + 1` con clamps `j0 = max(i−nk, 0)` y
`j1 = min(i+nk+1, n)`. La semántica de borde se mantiene: zero-padding
(los `j` fuera de `[0, n−1]` simplemente no aportan, equivalente a sumar 0).

### D2 — Guard de `sigma` después de dimensionar arrays

`if sigma <= 0: return zeros` está **debajo** de
`gk = np.zeros((n*2)+1)` con `n = 3*sigma`. Con `sigma = −1`,
`np.zeros(−1)` lanza `ValueError` antes de llegar al guard.
Corrección: mover el guard al inicio, antes de calcular `n`.

### D3 — Columna hardcodeada en la visualización

`dibujar_en_hilo_principal` grafica `DGY[:,640]`. Cualquier imagen con menos de
641 columnas produce `IndexError`. Corrección: `wc = min(640, nc−1)` y acotar
también `wr` a `[0, nr−1]`.

### Divergencias registradas, fuera de alcance de este fix

- **D4**: `sigma` flotante truena (`range(3*1.4)` → `TypeError`); MATLAB lo
  permitía. Requiere decisión de producto: `n = round(3σ)` o exigir entero.
- **D5**: convolución en Python puro (~57M de iteraciones para 1280×720).
  Candidata futura a `scipy.ndimage`/`cv2.sepFilter2D` o NumPy vectorizado.
- **D6**: `Convolucion/ConvR.py` y `Convolucion/ConvC.py` son duplicados exactos
  — muertos: nada los importa (`Convolucion/__init__.py` está comentado y
  `DeriGauss` importa el módulo `Conv2D`, que define sus propias copias).
- Código muerto: bloques comentados, variables `ds`/`l` sin uso.

## 2. Decisiones

- **Arreglar en su sitio, no reemplazar por `cv2.sepFilter2D`** (D5): cambiar de
  implementación alteraría el manejo de bordes y el perfil de rendimiento a la
  vez que la corrección; hacerlo en un solo paso impide aislar la causa de
  cualquier regresión. La sustitución queda como tarea futura con su propia
  verificación.
- **Mantener el zero-padding** como semántica de borde: es la que el código
  actual ya simula y la que esperan las etapas siguientes; cambiarla es un
  requerimiento nuevo, no un fix.
- **Los duplicados muertos (D6) no se tocan en este fix**: se documentan para
  una limpieza dedicada.

## 3. Verificación (estrategia)

Sin suite de tests en el proyecto, la verificación es por **ejecución de baterías
numéricas** contra referencias independientes:

1. **AC 4.2** — 100 casos aleatorios (tamaños y kernels variados) + casos de
   borde, comparando `ConvR`/`ConvC` contra correlación de NumPy de referencia
   (zero-padding, rango inclusivo), tolerancia relativa `1e-12`.
2. **AC 3.3** — cross-check de `DerivGauss` completo contra
   `cv2.sepFilter2D` con `BORDER_CONSTANT` en el interior, tolerancia `1e-9`.
3. **AC 5.1/5.2** — `sigma ∈ {0, −1}` retorna ceros sin excepción.
4. **AC 6.1/6.2** — visualización con imagen angosta (p.ej. 100×80) sin
   `IndexError`.
5. Humo de importación del paquete `odin.Preprocesamiento`.
