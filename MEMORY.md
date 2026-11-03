# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Última modificación: 2026-11-03

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- Suite de tests: 168 casos en pytest (tests/), `python3 -m pytest tests` desde la raíz.
- Etapas implementadas y verificadas: ① kernelSeparable, ② MagFase, ③ NonMaxSup, ④ Otsu/Rosin, ⑥ EdgeTrack_Hyst, ⑦ houghCircles (R1-R10), ⑧ findCircle (R1-R6), ⑨ circuloSimple (cerrada, spec commiteado en `857f422`). Etapa ⑤ = DobleThreshold dentro de ④.
- Falsificación por etapa (barrido e1-e8) completada; bugs reales corregidos: (a) `hough_circles_vectorizado` rechaza `r <= 0` con `ValueError` (commit `11183bf`); (b) `_preparar_histograma` maneja rango mínimo (casi-constante) con fallback a un solo bin (commit `12bd93d`).
- Barrido completo S1-S4 (pipeline full, sin recortar): VERDE sobre img050.bmp — S1 sin errores, S2 consistencias OK, S3 determinismo, S4 sin NaN (salida en /tmp/opencode/barrido-e9/salida_s1_s4_final.json).
- `.gitignore`: `odin/data/` (3.0 GB) excluido.
- `.kiro/specs/`: specs de etapas ①-⑨ + arranque (parcial: tasks 12/15 completadas, 14 y 16 abiertas).

## Mediciones Task 14 / Task 16 (sin pantalla)
- ENV_PROBE (detección entorno): 0.2 ms (umbral < 200 ms) ✅ OK
- Bootstrap completo: 0.1 ms (umbral < 3000 ms) ✅ OK (en proceso existente)
- Suite pytest: 168 passed ✅ OK
- DISPLAY_VALID: requiere pantalla (Wayland/X11) ⏳ bloqueado
- WINDOW_INIT: requiere MainWindow + pantalla ⏳ bloqueado
- Task 14 (checkpoint integración GUI): ⏳ pendiente por falta de pantalla
- Task 16 (checkpoint final): tests y tiempos OK; faltan 11 propiedades de corrección y consulta final al usuario

## Doc-staleness pendiente (barrido ①-⑧)
- (ninguna pendiente; R3.2 resuelta, etapa ④ resuelta)

## Decisiones (y por qué)
- Acrónimo oficial: ODIN = *Otsu + Directional + Intensity + Non-Maximum Suppression* (usuario).
- `requirements.txt` en UTF-8 (fijado por el usuario; UTF-16LE fue error histórico corregido).
- Si Engram y MEMORY.md chocan: preguntar al usuario cuál manda.
- No renombrar `odin/` a `src`; futuro src layout será `src/odin/` preservando paquete Python.
- Kernel 5×5 (no 7×7) por decisión de usuario; medido inocuo y mejor bajo ruido.

## Aprendizajes y errores a evitar
- Kiro tiende a truncar/reescriturar AGENTS.md al generar documentación: revisar tras cada sesión de Kiro.
- Al cambiar firma de helper compartido, verificar TODOS los llamadores.
- Barrido con un solo paso grueso da márgenes frágiles: refinar candidatos gruesos convierte decisión en 2.6:1 por ~3 s.

## Próximos pasos
- Task 14: checkpoint de integración completa (requiere pantalla/Wayland).
- Task 16: checkpoint final de verificación completa (requiere pantalla/Wayland).
- Slice de arranque: tasks 12 y 15 completadas (flag --version, orden de widgets).
- Refactor `src/odin/` al final.
