# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual (2026-10-26)

- `AGENTS.md` unificado como versión canónica: original recuperado + visión de Kiro + correcciones.
- Specs de arranque en `.kiro/specs/odin-startup-structure/` (requirements/design/tasks) — NO implementados aún.
- CodeGraph indexado (19 archivos). Spec implícito S1-S6 extraído para la etapa ① `kernelSeparable`.
- Cambios de Kiro revisados, corregidos (regresión `umbralOtsu`/dibujado y división por cero de Rosin) y commiteados.
- Deuda de Otsu duplicado saldada: helpers privados `_preparar_histograma` y `_umbral_otsu`; verificada por equivalencia numérica contra HEAD (33 casos, idénticos).
- Quick wins hechos: `.gitignore` (fusión con el previo: Python + env + VS Code) y eliminación de la función legada `MtoOtsu()` (307 → 194 líneas, cero llamadores verificados).
- Etapa ① `kernelSeparable` completada spec-first: spec en `.kiro/specs/kernel-separable/` (R1-R6 estilo ODD) y fixes D1 (off-by-one de `ConvR`/`ConvC`: se perdía el tap extremo del kernel), D2 (guard de sigma tras dimensionar arrays) y D3 (`DGY[:,640]` hardcodeado). Verificado: 200 casos vs referencia NumPy (1e-12) y vs `cv2.sepFilter2D` (6.9e-17 imagen completa).
- Etapa ② `MagFase` completada: spec de caracterización en `.kiro/specs/mag-fase/` (R1-R5) — la matemática estaba correcta; el spec fija el contrato (magnitud `hypot` normalizada a [0,1], ángulo en grados `(-180,180]` con `mod360` aguas abajo). Limpieza aplicada: sin `import cv2` muerto y guarda de arrays vacíos → tupla vacía.
- Etapa ③ `NonMaxSup` completada: spec en `.kiro/specs/non-max-sup/` (R1-R5) y fixes D1+D2 (núcleo reescrito: comparación sobre el eje mod 180° con interpolación angular — simetría por cuadrante exacta y tie-breaking `>=` uniforme), D3 (`DobleThreshold(M, thresh)` sin el parámetro muerto `angle`; `main.py` actualizado), D4 (tras revisión con verificación de utilidad: **recuperados** `NMS_Parabolic`/`NMS_Gaussian` por su estimación subpíxel — error 0.000000/0.0011 vs 0.0081 del discreto, útil para etapas 7-9; descartados `Interpolation_old` y `NMS_Migrado.py` tras comprobar que fallan simetría 20/20). Verificado: batería completa + referencia escalar independiente igualada en 100 casos + integración etapas 1→2→3.
- Etapa ④ `Otsu`/`Rosin` completada: spec en `.kiro/specs/otsu-rosin/` (R1-R6). Hallazgo principal: la diferencia contra la referencia independiente (0.44 vs 0.52) **no era bug** sino la **meseta de Otsu** — `vB` idéntica a 12 decimales en ambos puntos; con varianza amplia ODIN coincide dentro de 0.4-0.6 anchos de bin. Defecto real corregido (D1): histograma de un solo bin (imagen de valor constante) devolvía `valor−0.5` (negativo para 0.05); la guarda vive en `_preparar_histograma`, que devuelve un bin centrado en el valor exacto. `umbralOtsu` se conserva (API pública sin llamadores); `GLib.idle_add` queda como deuda para `src/odin/`.

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

- Continuar el spec-driven con la etapa ⑥ `EdgeTrack_Hyst` (`DThEdgeTrackHyst.py`, la recursión es deuda conocida) — la ⑤ ya quedó spec-ificada junto con la ③.
- Orden acordado: quick wins ✅ → `kernelSeparable` ✅ → `MagFase` ✅ → `NonMaxSup` ✅ → `Otsu`/`Rosin` ✅ → siguiente: ⑥ y etapas 7-9 o slice de arranque → refactor `src/odin/` al final.
- Deuda anotada: ① D4 sigma flotante, D5 convolución Python puro, D6 duplicados muertos de `Convolucion/`; ③ `LinearInterpolation` conserva `Gx`/`Gy` sin usar en la firma (compatibilidad); `NMS_Parabolic`/`NMS_Gaussian` restaurados como herramientas de subpíxel **sin consumidor en el pipeline aún** (candidatos a etapas 7-9, pueden exceder max(MG)); ④ `GLib.idle_add` incondicional en el umbralizado (acoplamiento a GTK, se resuelve con callback inyectado).
