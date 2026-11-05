# Requirements Document

## Introduction

Este documento captura los requerimientos de la **etapa ③ del pipeline de ODIN**
(`non-max-sup`): la Supresión de No Máximos (NMS) con interpolación lineal
subpíxel y el posterior umbralizado doble.

Corresponde a `LinearInterpolation(MG, Gx, Gy, angle)` y
`DobleThreshold(M, angle, thresh)` en
`src/odin/Procesamiento/models/non_max_sup.py` (legacy `odin/Preprocesamiento/NonMaxSuppressionVectorizado.py`). El módulo contiene
además tres variantes experimentales no usadas por el pipeline
(`NMS_Parabolic`, `NMS_Gaussian`, `Interpolation_old`) — ver `design.md`.

Entradas del contrato: `MG ∈ [0,1]` y `angle` en grados (etapa ②). Aguas
abajo: `umbralRosinYOtsu` recibe `GNMaxS` (etapa ④) y `DobleThreshold` produce
los bordes fuertes/débiles que consume `EdgeTrack_Hyst` (etapa ⑥).

---

## Glossary

- **Sector angular**: uno de los 4 tramos de 45° (0/45/90/135 con sus opuestos
  a 180°) a los que se clasifica el ángulo del gradiente.
- **Vecinos de interpolación**: las dos magnitudes vecinas que **estrangulan**
  la dirección del gradiente; su interpolación lineal da el umbral local
  subpíxel contra el que se compara el píxel central.
- **Pesos** (`w_x`, `w_y`): `|Gx|/max(|Gx|,|Gy|)` y `|Gy|/max(|Gx|,|Gy|)`;
  miden cuán cerca está la dirección del gradiente del eje horizontal/vertical.
- **Cuchilla**: cresta de magnitud localmente máxima en una dirección.
- **Tie-breaking**: criterio de desempate cuando el píxel empata con su vecino
  (`>=` conserva; `>` elimina).

---

## Requirements

### Requirement 1: Supresión de no máximos por sectores angulares

**User Story:** Como usuario de ODIN, quiero que el NMS compare cada píxel con
los vecinos de su dirección de gradiente (Canny clásico), para conservar solo
los picos reales del borde.

#### Acceptance Criteria

1. THE `LinearInterpolation` SHALL clasificar `np.mod(angle, 360)` en 4 sectores
   (límites 22.5°/67.5°/112.5°/135.5°…: 0±22.5, 45±22.5, 90±22.5, 135±22.5 con
   sus opuestos) y comparar contra los vecinos que estrangulan ese sector.
2. THE salida SHALL ser cero en el borde de 1 píxel de la imagen.
3. WHEN existe una cuchilla ancha (3 píxeles) perpendicular al gradiente,
   THEN el NMS SHALL conservar únicamente la fila/columna del máximo
   (adelgazamiento a 1 píxel) — verificado: columna del máximo única
   sobreviviente.

### Requirement 2: Interpolación lineal subpíxel

**User Story:** Como usuario de ODIN, quiero interpolar linealmente entre los
vecinos que estrangulan la dirección del gradiente, para decidir picos con
precisión subpíxel en vez de comparar contra ejes fijos.

#### Acceptance Criteria

1. THE valores de comparación SHALL calcularse como interpolación lineal entre
   el vecino del eje y el vecino diagonal del sector, con peso `w_x`/`w_y`.
2. WHEN `max(|Gx|,|Gy|) == 0` (píxel plano), THEN los pesos SHALL ser 0 sin
   división por cero.

### Requirement 3: Simetría por cuadrante del gradiente

**User Story:** Como usuario de ODIN, quiero que un borde y su reflejo
geométrico produzcan resultados reflejados, para que el detector no tenga
sesgo diagonal.

#### Acceptance Criteria

1. WHEN dos campos de gradiente son espejos geométricos entre sí (p.ej.
   perfiles simétricos con ángulos θ y 180−θ), THEN las máscaras de salida
   SHALL ser espejo entre sí. **(Resuelto: el esquema de comparación sobre el
   eje mod 180° con selección de vecinos por sector es simétrico por
   construcción — verificado: espejo 80°/100° exacto.)**

### Requirement 4: Tie-breaking consistente entre sectores

**User Story:** Como usuario de ODIN, quiero el mismo criterio de desempate en
los 4 sectores, para que las mesetas no se traten distinto según su
orientación.

#### Acceptance Criteria

1. WHEN un píxel empata con el valor interpolado de sus vecinos, THEN el
   criterio (`>=` o `>`) SHALL ser idéntico en los 4 sectores.
   **(Resuelto: `>=` en los 4 sectores — meseta 3×3 → 9/9 en gradiente 0 y
   en gradiente 90.)**

### Requirement 5: Umbralizado doble

**User Story:** Como la etapa de histéresis, quiero una partición limpia en
bordes fuertes y débiles, para que el seguimiento conecte solo débiles
adyacentes a fuertes.

#### Acceptance Criteria

1. WHEN `thresh ∈ (0,1]`, THEN `gnh` SHALL contener `1.0` en todo píxel con
   `M >= thresh`, y `gnl` SHALL contener la magnitud original en todo píxel con
   `thresh² <= M < thresh`; el resto 0.
2. WHEN `thresh > 1`, THEN SHALL tratarse como `1.0` (corte superior).
3. THE umbral inferior SHALL ser `thresh²` (decisión de diseño vigente; el
   código original usaba `0.4·thresh`, comentado en el fuente).
4. (Deuda de firma, resuelta) El parámetro `angle` de `DobleThreshold` era
   obsoleto: la función no lo utiliza desde que el NMS se separó en
   `LinearInterpolation`. **(Resuelto: parámetro eliminado de la firma y
   llamador `main.py` actualizado.)**
