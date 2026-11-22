<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/kernel-separable.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | IMPLEMENTADO | `deri_gauss.py:34-42`: `gk` normalizado por su suma; simetría por construcción (`i` en `[-n, n]`) |
> | R2 | IMPLEMENTADO | `deri_gauss.py:40-43`: `dgk = -(1/σ²)·i·gk`, antisimétrico |
> | R3 | IMPLEMENTADO | `deri_gauss.py:51-52`; contraste ejecutado en esta reverificación: `sepFilter2D` con correlación sobre `−dgk` y `BORDER_CONSTANT`, y referencia NumPy, discrepancia ≤ 7e-17 (5 casos, σ=1.0–4.0). Sin cross-check automático versionado |
> | R4 | IMPLEMENTADO | `convolucion.py:25-34`: soporte inclusivo `j ∈ [i−nk, i+nk]` con `j0/j1` recortados (zero-padding); equivalencia con `np.convolve(mode='same')` ≤ 6e-17 en tamaños habituales |
> | R5 | IMPLEMENTADO | `deri_gauss.py:21-23`: retorno temprano antes de `n = round(3σ)` (`:30`); tests `tests/unit/Preprocesamiento/test_etapa1_kernel_separable.py:17,25` |
> | R6 | PENDIENTE | no implementado: el módulo es modelo puro sin visualización (`deri_gauss.py:1-8`); no existen `wc = min(640, nc−1)` ni `wr` |
>
> **Pendientes:** R6 — visualización de cortes (`wc = min(640, nc−1)`, `wr` acotada a `[0, nr−1]`): nunca implementada; el módulo no contiene código de visualización.
> **Divergencias verificadas:** R4.2 — el caso literal `n ≤ 2·nk` es inconsistente con la referencia `np.convolve(mode='same')` (p.ej. imagen 5×5 con σ=3: referencia (5,19) vs salida (5,5)); el código calcula la convolución completa centrada con zero-padding. R3/R4 — no hay cross-check automático versionado: `tests/utilidades.py:44-49` define `derivada_gaussiana_referencia` y ningún test la invoca (0 usos).
> **Inciertos:** ninguno.
<!-- ESTADO:FIN -->

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
  <!-- estado superado: la funcion y el archivo ya no existen -->
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

## Correcciones de estado

- Tarea 4 — anterior `[x]`, nota, sin invertir (superada: la función y el archivo ya no existen); evidencia `.kiro/specs/kernel-separable/tasks.md:23` y 0 hits de `dibujar_en_hilo_principal` / sin `DeriGauss.py` en `src/`; 2026-11-21.
