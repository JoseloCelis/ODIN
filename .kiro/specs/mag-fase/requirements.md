# Requirements Document

## Introduction

Este documento captura los requerimientos de la **etapa ② del pipeline de ODIN**
(`mag-fase`): el cálculo de la magnitud y la dirección del gradiente a partir de
las derivadas producidas por la etapa ①.

Corresponde a `MagFase(GrX, GrY)` en `odin/Preprocesamiento/MagFase.py`. Es un
**spec de caracterización**: la implementación actual resultó correcta en todos
los requerimientos revisados (ver `design.md`); el objetivo del documento es
fijar el contrato numérico que las etapas ③ (`LinearInterpolation`,
`DobleThreshold`) y ⑥ (`EdgeTrack_Hyst`) asumen, para que refactorizaciones
futuras (src layout, sustitución de implementación) no lo rompan en silencio.

Contrato aguas abajo verificado en el código real:
`main.py` llama `MG, Tetha = MagFase(Gx, Gy)`, y `Tetha` alimenta
`NonMaxSup.LinearInterpolation` (que aplica `np.mod(angle, 360)`) y
`NonMaxSup.DobleThreshold` (que hoy ignora el ángulo); `MG` alimenta
`umbralRosinYOtsu` y `DobleThreshold` (que asume magnitudes en `[0, 1]`).

---

## Glossary

- **Magnitud** (`MGr`): `hypot(GrX, GrY)` elemento a elemento; ≥ 0.
- **Normalización global**: división de `MGr` entre su máximo, produciendo
  `MGr ∈ [0, 1]`.
- **Ángulo** (`angle`): dirección del gradiente en **grados**, vía
  `atan2(GrY, GrX)`, rango `(-180, 180]`.
- **Imagen plana**: matriz cuya magnitud de gradiente es idénticamente cero en
  todos los píxeles.

---

## Requirements

### Requirement 1: Magnitud del gradiente

**User Story:** Como usuario de ODIN, quiero la magnitud del gradiente con la
función `hypot`, para evitar desbordes/underflow de `sqrt(x²+y²)` en valores
extremos.

#### Acceptance Criteria

1. THE `MGr[i,j]` SHALL calcularse como `np.hypot(GrX, GrY)` elemento a
   elemento, con la misma forma (shape) que las entradas.
2. WHEN `GrX=3, GrY=4`, THEN `MGr` cruda SHALL ser `5` (verificado: con la
   normalización de R2 el resultado es `1.0`).
3. THE magnitud cruda (`MGr * max`) SHALL coincidir con `sqrt(GrX²+GrY²)` con
   tolerancia relativa `1e-12`.

### Requirement 2: Normalización global a [0, 1]

**User Story:** Como etapas posteriores del pipeline, quiero la magnitud
normalizada a su máximo, para que el umbral de Otsu y el doble umbral operen
en una escala fija `[0, 1]`.

#### Acceptance Criteria

1. WHEN `max(MGr) > 0`, THEN `MGr` SHALL dividirse entre su máximo; el
   resultado SHALL estar en `[0, 1]` con máximo exactamente `1.0`.
2. WHEN `max(MGr) == 0` (imagen plana), THEN `MGr` SHALL permanecer en ceros
   **sin lanzar** división por cero.
3. La normalización SHALL conservar razones: `MGr_normalizada × max ==
   MGr_cruda` con tolerancia relativa `1e-12`.
4. (Contrato documentado, intencional) La normalización depende del contenido
   de la imagen completa: `MGr` **no** es comparable entre imágenes distintas.

### Requirement 3: Dirección del gradiente en grados

**User Story:** Como la etapa de NMS, quiero el ángulo en grados vía `atan2`,
para clasificarlo en sectores angulares de 45°.

#### Acceptance Criteria

1. THE `angle` SHALL calcularse como `np.atan2(GrY, GrX) * 180/π`, en grados,
   con la misma forma que las entradas.
2. THE `angle` SHALL estar en el rango `(-180, 180]`.
3. WHEN `GrX=3, GrY=4`, THEN `angle` SHALL ser `53.1301°` con tolerancia
   `1e-4`.
4. WHEN el consumidor aplica `np.mod(angle, 360)`, THEN el resultado SHALL
   caer en `[0, 360)` (contrato de `LinearInterpolation`, verificado en
   código).

### Requirement 4: Función pura sin dependencias de UI

**User Story:** Como el resto del pipeline, quiero que `MagFase` sea matemática
pura (NumPy), para que sea testeable sin GTK y reusable fuera de la app.

#### Acceptance Criteria

1. THE módulo `MagFase.py` SHALL importar únicamente `numpy` (hoy declara un
   `import cv2 as cv` sin uso — divergencia D1, ver `design.md`).
2. THE `MagFase` SHALL ser una función pura: mismas entradas → mismas salidas,
   sin efectos secundarios ni estado global.

### Requirement 5: Casos degenerados

**User Story:** Como llamador futuro (tests, librería), quiero un comportamiento
definido en casos degenerados, para que no dependa de mensajes de error de
NumPy.

#### Acceptance Criteria

1. WHEN las entradas están vacías (`size == 0`), THEN `MagFase` SHALL retornar
   tuplas vacías (o lanzar un `ValueError` propio con mensaje claro) — hoy
   truena con el mensaje interno de NumPy
   `zero-size array to reduction...` (divergencia D3).
