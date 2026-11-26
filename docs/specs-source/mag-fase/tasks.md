<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/mag-fase.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | IMPLEMENTADO | `mag_fase.py:23`: `np.hypot(GrX, GrY)`; tests `tests/unit/Preprocesamiento/test_etapa2_mag_fase.py:17,37` |
> | R2 | IMPLEMENTADO | `mag_fase.py:24-26`: división por el máximo solo si > 0; imagen plana queda en ceros; tests `test_etapa2_mag_fase.py:27,37` |
> | R3 | IMPLEMENTADO | `mag_fase.py:29-30`: `atan2*180/π`, `-180` se mapea a `180`; test `test_etapa2_mag_fase.py:61` |
> | R4 | IMPLEMENTADO | `mag_fase.py:7`: único import (`numpy`); sin `cv2` ni UI |
> | R5 | IMPLEMENTADO | `mag_fase.py:19-20`: entrada vacía devuelve tuplas vacías sin excepción de NumPy; test `test_etapa2_mag_fase.py:54` |
>
> **Pendientes:** ninguno.
> **Divergencias verificadas:** R4.1 y R5.1 están desactualizados: describen `import cv2` y el `ValueError` interno de NumPy como defectos vigentes; ambos están corregidos. `design.md:50,64` repite la deuda D1.
> **Inciertos:** ninguno.
<!-- ESTADO:FIN -->

# Tasks Document — mag-fase

## Tarea 1: Escribir la especificación

- [x] `requirements.md` R1-R5 estilo ODD (spec de caracterización).
- [x] `design.md` con revisión de las 13 líneas, evidencia de ejecución y
  divergencias D1-D4.
- [x] Batería numérica previa: 3-4-5, imagen plana, rangos, contrato de
  normalización, arrays vacíos.

## Tarea 2: Decisión de limpieza (pendiente de usuario)

- [x] D1: quitar `import cv2 as cv` sin uso de `MagFase.py` (R4.1).
- [x] D3: guarda de arrays vacíos → tupla vacía sin excepción (decisión del
      usuario: aplicar D1 + D3).

## Tarea 3: Commit y memoria

- [x] Commit del spec.
- [ ] Commit de la limpieza D1 + D3.
- [x] Actualizar `MEMORY.md`.
