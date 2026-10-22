# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual (2026-10-22)

- `AGENTS.md` unificado como versión canónica: original recuperado + visión de Kiro + correcciones.
- Specs de arranque en `.kiro/specs/odin-startup-structure/` (requirements/design/tasks) — NO implementados aún.
- CodeGraph indexado (19 archivos). Spec implícito S1-S6 extraído para la etapa ① `kernelSeparable`.
- Cambios de Kiro revisados, corregidos (regresión `umbralOtsu`/dibujado y división por cero de Rosin) y commiteados.
- Deuda de Otsu duplicado saldada: helpers privados `_preparar_histograma` y `_umbral_otsu`; verificada por equivalencia numérica contra HEAD (33 casos, idénticos).
- Quick wins hechos: `.gitignore` (fusión con el previo: Python + env + VS Code) y eliminación de la función legada `MtoOtsu()` (307 → 194 líneas, cero llamadores verificados).
- Etapa ① `kernelSeparable` completada spec-first: spec en `.kiro/specs/kernel-separable/` (R1-R6 estilo ODD) y fixes D1 (off-by-one de `ConvR`/`ConvC`: se perdía el tap extremo del kernel), D2 (guard de sigma tras dimensionar arrays) y D3 (`DGY[:,640]` hardcodeado). Verificado: 200 casos vs referencia NumPy (1e-12) y vs `cv2.sepFilter2D` (6.9e-17 imagen completa).

## Decisiones (y por qué)

- Acrónimo oficial: ODIN = *Otsu + Directional + Intensity + Non-Maximum Suppression* (decisión del usuario).
- `requirements.txt` se mantiene en **UTF-8** (fijado por el usuario; el UTF-16LE era un error histórico ya corregido).
- Si Engram (memoria interna del agente OpenCode) y este archivo chocan: **preguntar al usuario cuál manda**; no decidir solo.
- No renombrar `odin/` a `src`; si algún día hay src layout, será `src/odin/` preservando el nombre del paquete Python.
- `LD_LIBRARY_PATH=/usr/lib/wsl/lib` quedó comentado en `devcontainer.json` a propósito: el usuario ya no trabaja en una máquina con GPU NVIDIA.

## Aprendizajes y errores a evitar

- Kiro tiende a truncar/reescriturar `AGENTS.md` al generar documentación: revisar el archivo tras cada sesión de Kiro. Git retiene el historial (commit `3c41148` y posteriores).
- Al cambiar la firma de un helper compartido (ej. `dibujar_en_hilo_principal`), verificar TODOS los llamadores: `umbralOtsu` quedó roto en silencio tras el cambio de Kiro (histo caía en el parámetro equivocado).
- Gotchas de entorno documentados en `AGENTS.md` (WSLg+Wayland rompe popovers, host sin pip/venv, doble rama de imports por `__package__`, prints al importar son intencionales).

## Próximos pasos

- Spec-driven de la etapa ② `MagFase` (magnitud y dirección del gradiente) — usando el patrón ya probado: spec → fix → batería numérica.
- Orden acordado: quick wins ✅ → `kernelSeparable` ✅ → `MagFase` → slice de arranque de `.kiro` → refactor `src/odin/` al final (con specs/tests como red de seguridad).
- Deuda anotada de la etapa ① (fuera de alcance del fix): D4 sigma flotante truena, D5 convolución en Python puro (~57M iteraciones para 1280×720), D6 `ConvR.py`/`ConvC.py` sueltos son duplicados muertos.
