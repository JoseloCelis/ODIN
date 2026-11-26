# Barrido del pipeline (ODIN)

Verificación de que las etapas encadenadas producen resultados coherentes de punta a punta. No migra código: falsa el pipeline que ya existe.

## Specs

**S1 — Recorrido completo sin recortar.**
El pipeline debe procesar la imagen completa, sin recortar, a través de todas las etapas registradas en `PREPROCESAMIENTO_SUITE_ORDER` sin errores.

**S2 — Consistencia en las transiciones.**
Los datos deben seguir siendo coherentes al cruzar cada frontera entre etapas (por ejemplo, la magnitud tras la supresión de no máximos, o los bordes tras la histéresis).

**S3 — Determinismo.**
La misma entrada debe producir el mismo resultado.

**S4 — Sin divisiones por cero ni NaN.**
El procesado estándar no debe generar divisiones por cero ni valores `NaN`.

## Tasks

| ID | Specs | Ruta | Estado | Evidencia |
|----|-------|------|--------|-----------|
| T1 | S1, S2 | `tests/integration/test_pipeline.py` | parcial — cubre etapas 1→5 | `1 passed in 2.32s` (2026-11-21) |
| T2 | S3, S4 | Barrido sobre dataset de calibración | pendiente | — |
| T3 | S2 | Análisis de discrepancias de borde y umbrales | pendiente | — |

**Lo que falta de T1.** El test existente cubre las etapas ①→⑤ y fija un snapshot de caracterización (`268` en el umbral alto, `0` en el bajo). No ejerce ⑥ histéresis, ⑦ `aproxHough`, ⑧ `circleFilter` ni ⑨ `LSC`, que son justamente donde el pipeline completo se corta hoy: el controlador asume geometría de círculo y lanza `ValueError` cuando no la encuentra. Tampoco cubre las etapas ⑩ `HoughLineas` ni ⑪ `LineaRobusta`, que ya están registradas en el arranque.

## Log

**L1**: orquestación del pipeline completo para detectar inconsistencias de borde, iniciada por el usuario.

**L2** (2026-10-30): barrido de falsación **por etapa** ejecutado con 7 subagentes (pistas e1..e8). Evidencia en `/tmp/opencode/barrido-e{1,2,3e5,4,6,7,8}/`, ya inexistente. Divergencias: bug real en e7 (`resolver_radio` con `NameError`, corregido) y en e4 (`Otsu` revienta con imagen casi constante); el resto fue desactualización documental. Las pistas e2, e4, e6 y e8 dejaron solo scripts, sin salida citable.

**L3**: S1-S4 (recorrido completo sin recortar) quedaron pendientes: lo hecho falsificaba etapa por etapa, no el recorrido completo.

**L4** (2026-11-21): el documento se reescribió contra el estado verificado del repositorio, no contra su propio texto. Medido hoy: `tests/integration/test_pipeline.py` existe, pasa (`1 passed in 2.32s`) y cubre **solo las etapas ①→⑤** según su propio docstring; `PREPROCESAMIENTO_SUITE_ORDER` registra **10** etapas (`kernelSeparable`, `MagnitudGradiente`, `NonMaxSup`, `Otsu`, `DoubleTh`, `aproxHough`, `circleFilter`, `LSC`, `HoughLineas`, `LineaRobusta`). Por eso T1 pasa a *parcial* en vez de *hecho*: el recorrido completo de S1 sigue sin ejercerse, y ahora abarca dos etapas más que cuando se escribió L1. La evidencia de L2 se perdió con `/tmp`, así que no se cita como respaldo de nada.
