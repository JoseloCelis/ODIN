# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Última modificación: 2026-11-04

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- Suite de tests: 183 casos en pytest (tests/), `python3 -m pytest tests` desde la raíz (~7-10 s).
  Etapa ⑨ suma `tests/test_etapa9_imagen_real.py`: 4 tests con bordes Gabor reales (rápidos) y
  1 e2e con `img100.bmp` (opt-in `ODIN_TEST_LENTO=1`, ~21 s) que reproduce r=428.1769, pv=1.8856.
- Refactor `src/odin/` en curso: etapa ① kernelSeparable movida a `src/odin/Preprocesamiento/models/deri_gauss.py` (puro NumPy, sin UI) + `models/convolucion.py` + `tests/test_etapa1_kernel_separable.py` (4 tests, verde). Legacy `odin/` aún coexiste.
- Etapas implementadas y verificadas: ① kernelSeparable, ② MagFase, ③ NonMaxSup, ④ Otsu/Rosin, ⑥ EdgeTrack_Hyst, ⑦ houghCircles (R1-R10), ⑧ findCircle (R1-R6), ⑨ circuloSimple (cerrada, spec commiteado en `857f422`). Etapa ⑤ = DobleThreshold dentro de ④.
- Falsificación por etapa (barrido e1-e8) completada; bugs reales corregidos: (a) `hough_circles_vectorizado` rechaza `r <= 0` con `ValueError` (commit `11183bf`); (b) `_preparar_histograma` maneja rango mínimo (casi-constante) con fallback a un solo bin (commit `12bd93d`).
- Barrido completo S1-S4 (pipeline full, sin recortar): VERDE sobre img050.bmp — S1 sin errores, S2 consistencias OK, S3 determinismo, S4 sin NaN (salida en /tmp/opencode/barrido-e9/salida_s1_s4_final.json).
- `.gitignore`: `odin/data/` (3.0 GB) y `.hypothesis/` excluidos.
- `.kiro/specs/`: specs de etapas ①-⑨ + arranque (tasks 12-16 marcadas como cerradas).

## Mediciones Task 14 / Task 16 (con pantalla virtual Xvfb :99)
- ENV_PROBE (detección entorno): 0.2 ms (umbral < 200 ms) ✅ OK
- Bootstrap completo: 0.1 ms (umbral < 3000 ms) ✅ OK (en proceso existente)
- Suite pytest: 181 passed ✅ OK
- DISPLAY_VALID: verificada con X11Display (DISPLAY=:99 + GDK_BACKEND=x11) ✅ OK
- WINDOW_INIT: verificada con Xvfb :99 (15.8 ms) ✅ OK
- Task 14 (checkpoint integración GUI): COMPLETA — verificada en ambos modos (PACKAGE y SCRIPT) con Xvfb :99: las 4 fases en orden y sin errores.
- Task 16 (checkpoint final): COMPLETA — 11 propiedades de corrección GREEN (`tests/test_bootstrap_arranque.py`, Hypothesis), 181 passed, 3 reviews de gentle-ai approved. Commits `d4e15f8`, `22333f4`, `f62042c`.

## Doc-staleness pendiente (barrido ①-⑧)
- (ninguna pendiente; R3.2 resuelta, etapa ④ resuelta)

## Decisiones (y por qué)
- Acrónimo oficial: ODIN = *Otsu + Directional + Intensity + Non-Maximum Suppression* (usuario).
- `requirements.txt` en UTF-8 (fijado por el usuario; UTF-16LE fue error histórico corregido).
- Si Engram y MEMORY.md chocan: preguntar al usuario cuál manda.
- No renombrar `odin/` a `src`; futuro src layout será `src/odin/` preservando paquete Python.
- Kernel 5×5 (no 7×7) por decisión de usuario; medido inocuo y mejor bajo ruido.

## Aprendizajes y errores a evitar
- `hypothesis` figura en `requirements.txt` (dev/test). En el host vive solo en `~/.local/lib/python3.14/site-packages` (sin pip/venv/sudo); sin él, la clase de propiedades se omite con un único mecanismo stub (18 passed + 11 skipped).
- Deuda documentada (`.kiro/specs/kernel-separable/design.md`, D4): `sigma` flotante truena en `DerivGauss` (`range(3*sigma)` → TypeError). En `src/odin/.../models/deri_gauss.py` ya se castea `int(3*sigma)` antes de dimensionar arrays. No borrar esta deuda de MEMORY.md ni de Engram.
- Kiro tiende a truncar/reescriturar AGENTS.md al generar documentación: revisar tras cada sesión de Kiro.
- Al cambiar firma de helper compartido, verificar TODOS los llamadores.
- Barrido con un solo paso grueso da márgenes frágiles: refinar candidatos gruesos convierte decisión en 2.6:1 por ~3 s.

## Próximos pasos
- Refactor `src/odin/` (MVC + Strategy) al final.
