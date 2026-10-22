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
- Etapa ② `MagFase` completada: spec de caracterización en `.kiro/specs/mag-fase/` (R1-R5) — la matemática estaba correcta; el spec fija el contrato (magnitud `hypot` normalizada a [0,1], ángulo en grados `(-180,180]` con `mod360` aguas abajo). Limpieza aplicada: sin `import cv2` muerto y guarda de arrays vacíos → tupla vacía.
- Etapa ③ `NonMaxSup` completada: spec en `.kiro/specs/non-max-sup/` (R1-R5) y fixes D1+D2 (núcleo reescrito: comparación sobre el eje mod 180° con interpolación angular — simetría por cuadrante exacta y tie-breaking `>=` uniforme), D3 (`DobleThreshold(M, thresh)` sin el parámetro muerto `angle`; `main.py` actualizado), D4 (descartados `NMS_Parabolic`/`NMS_Gaussian`/`Interpolation_old`/`NMS_Migrado.py`, cero referencias verificadas). Verificado: batería completa + referencia escalar independiente igualada en 100 casos + integración etapas 1→2→3.

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

- Continuar el spec-driven con la etapa ④ (`Otsu`/`Rosin` en `MtoOtsu.py` — ya refactorizado, spec rápido de caracterización) o la ⑤/⑥ (`DobleThreshold` ya spec-ificado; `EdgeTrack_Hyst` tiene recursión conocida como deuda).
- Orden acordado: quick wins ✅ → `kernelSeparable` ✅ → `MagFase` ✅ → `NonMaxSup` ✅ → siguiente: etapas 4-6 o slice de arranque → refactor `src/odin/` al final.
- Deuda anotada: ① D4 sigma flotante, D5 convolución Python puro, D6 duplicados muertos de `Convolucion/`; ③ `LinearInterpolation` conserva `Gx`/`Gy` sin usar en la firma (compatibilidad).
