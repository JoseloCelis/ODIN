# Pipeline Sweep (ODIN)

## Specs
S1: El pipeline debe procesar imágenes completas (sin recortar) a través de las etapas ①-⑨ sin errores.
S2: Se debe verificar la consistencia de los datos en los puntos de transición (ej. magnitud tras NMS, bordes tras histéresis).
S3: El barrido debe ser determinista: misma entrada, mismo resultado.
S4: El pipeline no debe generar divisiones por cero ni valores NaN en el procesado estándar.

## Tasks
T1: Crear suite de integración para el pipeline completo.
T2: Ejecutar barrido sobre dataset de calibración.
T3: Analizar discrepancias de borde y valores de umbral.

## Log
L1: Orquestación del pipeline completo para detectar inconsistencias de borde iniciada por el usuario.
L2 (2026-10-30): Barrido de falsación **por etapa** ejecutado con 7 subagentes (pistas e1..e8). Evidencia en `/tmp/opencode/barrido-e{1,2,3e5,4,6,7,8}/`. Divergencias: bug real en e7 (`resolver_radio` con `NameError`, ya corregido) y en e4 (`Otsu` revienta con imagen casi-constante); el resto es desactualización documental (R5.2 tras el kernel 5×5, R3.2, contradicción requirements↔design en ③). Las pistas e2, e4, e6 y e8 dejaron solo scripts: falta re-correrlas guardando la salida para que sus números sean citables.
L3: S1-S4 (pipeline completo sin recortar) siguen **pendientes**: lo hecho hasta ahora falsifica etapa por etapa, no el recorrido completo.
