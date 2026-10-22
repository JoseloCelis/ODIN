# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual (2026-10-22)

- `AGENTS.md` unificado como versión canónica: original recuperado + visión de Kiro + correcciones.
- Specs de arranque en `.kiro/specs/odin-startup-structure/` (requirements/design/tasks) — NO implementados aún.
- CodeGraph indexado (19 archivos). Spec implícito S1-S6 extraído para la etapa ① `kernelSeparable`.
- Cambios de Kiro revisados, corregidos (regresión `umbralOtsu`/dibujado y división por cero de Rosin) y commiteados.
- Deuda de Otsu duplicado saldada: helpers privados `_preparar_histograma` y `_umbral_otsu`; verificada por equivalencia numérica contra HEAD (33 casos, idénticos).

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

- Formalizar el spec de `kernelSeparable` (etapa ①) o continuar la fase 2 con `MagFase` (etapa ②).
- Eliminar la función legada `MtoOtsu(IG, histo=0)` del final del archivo: Otsu con bucle `for`, nadie la usa, y calcula los centros de bin con `edges + wbin` (diferente al resto del archivo).
- Agregar `.gitignore` para `__pycache__/` y core dumps.
