# Tasks Document — kernel-separable

## Tarea 1: Escribir la especificación

- [x] `requirements.md` con Requirements 1–6 y sus ACs (estilo ODD).
- [x] `design.md` con causa raíz (D1–D3), decisiones y estrategia de verificación.

## Tarea 2: Fix D1 — soporte completo del kernel

- [x] En `src/odin/Preprocesamiento/models/convolucion.py`, `ConvR` y `ConvC`:
  `j1 = i + nk + 1` con clamp superior a `n` (y `j0` como `max(i−nk, 0)`).
- [x] Verificar AC 4.2: 100 casos aleatorios + bordes vs referencia NumPy
  (`1e-12`) — **200 casos OK** (filas y columnas).

## Tarea 3: Fix D2 — guard de sigma antes de dimensionar

- [x] En `src/odin/Preprocesamiento/models/deri_gauss.py`, mover `if sigma <= 0` al inicio
  de `DerivGauss`, antes de calcular `n = 3*sigma` y crear `gk`/`dgk`.
- [x] Verificar AC 5.1/5.2: `sigma ∈ {0, −1}` → ceros, sin excepción — OK.

## Tarea 4: Fix D3 — cortes de visualización acotados

- [x] En `dibujar_en_hilo_principal` (DeriGauss.py): columna
  `wc = min(640, nc−1)`; fila `wr` acotada a `[0, nr−1]`.
- [x] Verificar AC 6.1/6.2: imagen angosta (100×80) sin `IndexError` — OK.

## Tarea 5: Cross-check de la etapa completa

- [x] AC 3.3: `DerivGauss` vs `cv2.sepFilter2D` — **corregido tras la primera
  ejecución**: OpenCV hace correlación y ODIN convolución (convención del
  `conv2` de MATLAB); comparar con correlación sobre `−dgk` → `6.9e-17 / 5.6e-17`
  en imagen completa. Ver `design.md` §3.1.
- [x] Humo de importación: `from odin.Preprocesamiento import kernelSeparable`.

## Tarea 6: Commit y memoria

- [x] Commit `fix:` con los tres arreglos + resultado de las baterías.
- [ ] Actualizar `MEMORY.md`.
