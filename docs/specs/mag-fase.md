# mag-fase — Etapa ②: magnitud y dirección del gradiente

> Absorbido de `.kiro/specs/mag-fase/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Magnitud del gradiente

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/mag_fase.py:23`

> ### Requirement 1: Magnitud del gradiente
>
> **User Story:** Como usuario de ODIN, quiero la magnitud del gradiente con la
> función `hypot`, para evitar desbordes/underflow de `sqrt(x²+y²)` en valores
> extremos.
>
> #### Acceptance Criteria
>
> 1. THE `MGr[i,j]` SHALL calcularse como `np.hypot(GrX, GrY)` elemento a
>    elemento, con la misma forma (shape) que las entradas.
> 2. WHEN `GrX=3, GrY=4`, THEN `MGr` cruda SHALL ser `5` (verificado: con la
>    normalización de R2 el resultado es `1.0`).
> 3. THE magnitud cruda (`MGr * max`) SHALL coincidir con `sqrt(GrX²+GrY²)` con
>    tolerancia relativa `1e-12`.

`MGr = np.hypot(GrX, GrY)`. Verificado en esta ejecución: `GrX=3, GrY=4` →
`MGr = 1.0` tras la normalización de R2. Tests:
`tests/unit/Preprocesamiento/test_etapa2_mag_fase.py:17,37`.

### R2 — Normalización global a [0, 1]

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/mag_fase.py:24-26`

> ### Requirement 2: Normalización global a [0, 1]
>
> **User Story:** Como etapas posteriores del pipeline, quiero la magnitud
> normalizada a su máximo, para que el umbral de Otsu y el doble umbral operen
> en una escala fija `[0, 1]`.
>
> #### Acceptance Criteria
>
> 1. WHEN `max(MGr) > 0`, THEN `MGr` SHALL dividirse entre su máximo; el
>    resultado SHALL estar en `[0, 1]` con máximo exactamente `1.0`.
> 2. WHEN `max(MGr) == 0` (imagen plana), THEN `MGr` SHALL permanecer en ceros
>    **sin lanzar** división por cero.
> 3. La normalización SHALL conservar razones: `MGr_normalizada × max ==
>    MGr_cruda` con tolerancia relativa `1e-12`.
> 4. (Contrato documentado, intencional) La normalización depende del contenido
>    de la imagen completa: `MGr` **no** es comparable entre imágenes distintas.

`MGr_max = np.max(MGr)` y división solo si `MGr_max > 0`; la imagen plana queda
en ceros. Tests: `tests/unit/Preprocesamiento/test_etapa2_mag_fase.py:27,37`.

### R3 — Dirección del gradiente en grados

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/mag_fase.py:29-30`

> ### Requirement 3: Dirección del gradiente en grados
>
> **User Story:** Como la etapa de NMS, quiero el ángulo en grados vía `atan2`,
> para clasificarlo en sectores angulares de 45°.
>
> #### Acceptance Criteria
>
> 1. THE `angle` SHALL calcularse como `np.atan2(GrY, GrX) * 180/π`, en grados,
>    con la misma forma que las entradas.
> 2. THE `angle` SHALL estar en el rango `(-180, 180]`.
> 3. WHEN `GrX=3, GrY=4`, THEN `angle` SHALL ser `53.1301°` con tolerancia
>    `1e-4`.
> 4. WHEN el consumidor aplica `np.mod(angle, 360)`, THEN el resultado SHALL
>    caer en `[0, 360)` (contrato de `LinearInterpolation`, verificado en
>    código).

`angle = np.atan2(GrY, GrX) * 180 / np.pi` y `np.where(angle == -180.0, 180.0, angle)`
para cerrar el rango `(-180, 180]`. Verificado: `GrX=3, GrY=4` → `53.1301°`;
`atan2(-0.0, negativo)` se mapea a `180`. Test:
`tests/unit/Preprocesamiento/test_etapa2_mag_fase.py:61`.

### R4 — Función pura sin dependencias de UI

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/mag_fase.py:7`

> ### Requirement 4: Función pura sin dependencias de UI
>
> **User Story:** Como el resto del pipeline, quiero que `MagFase` sea matemática
> pura (NumPy), para que sea testeable sin GTK y reusable fuera de la app.
>
> #### Acceptance Criteria
>
> 1. THE módulo `MagFase.py` SHALL importar únicamente `numpy` (hoy declara un
>    `import cv2 as cv` sin uso — divergencia D1, ver `design.md`).
> 2. THE `MagFase` SHALL ser una función pura: mismas entradas → mismas salidas,
>    sin efectos secundarios ni estado global.

El módulo tiene un único import: `import numpy as np` (`:7`); no importa `cv2`
ni ninguna dependencia de UI. La cita del AC 1 queda registrada como desactualizada
en Divergencias.

### R5 — Casos degenerados

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Preprocesamiento/models/mag_fase.py:19-20`

> ### Requirement 5: Casos degenerados
>
> **User Story:** Como llamador futuro (tests, librería), quiero un comportamiento
> definido en casos degenerados, para que no dependa de mensajes de error de
> NumPy.
>
> #### Acceptance Criteria
>
> 1. WHEN las entradas están vacías (`size == 0`), THEN `MagFase` SHALL retornar
>    tuplas vacías (o lanzar un `ValueError` propio con mensaje claro) — hoy
>    truena con el mensaje interno de NumPy
>    `zero-size array to reduction...` (divergencia D3).

`if GrX.size == 0 or GrY.size == 0: return np.empty(0), np.empty(0)`. Verificado:
entrada vacía devuelve dos arreglos de tamaño 0 sin excepción. Test:
`tests/unit/Preprocesamiento/test_etapa2_mag_fase.py:54`.

## Divergencias

- **R4.1** — el requisito describe `import cv2 as cv` sin uso como divergencia
  vigente; el módulo solo importa `numpy`. · `src/odin/Preprocesamiento/models/mag_fase.py:7`
- **R5.1** — el requisito describe el `ValueError` interno de NumPy
  (`zero-size array to reduction...`) como vigente; el código devuelve tuplas
  vacías sin excepción. · `src/odin/Preprocesamiento/models/mag_fase.py:19-20`
- **R4.1 (bloque de estado)** — el bloque de estado del original cita
  `design.md:34,48` como repetición de la deuda D1; esas líneas no contienen D1
  (la deuda D1 está en `design.md:50` y `design.md:64`). La divergencia de fondo
  (D1 está resuelta en el código) se verifica. · `.kiro/specs/mag-fase/design.md:50`

## Pendientes

- Ninguno.
