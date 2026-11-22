# non-max-sup

> Absorbido de `.kiro/specs/non-max-sup/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Supresión de no máximos por sectores angulares

**Estado:** CONTRADICHO · **Evidencia:** `src/odin/Procesamiento/models/non_max_sup.py:64-66,72-78,85`

> **User Story:** Como usuario de ODIN, quiero que el NMS compare cada píxel con
> los vecinos de su dirección de gradiente (Canny clásico), para conservar solo
> los picos reales del borde.
>
> #### Acceptance Criteria
>
> 1. THE `LinearInterpolation` SHALL clasificar `np.mod(angle, 360)` en 4 sectores
>    (límites 22.5°/67.5°/112.5°/135.5°…: 0±22.5, 45±22.5, 90±22.5, 135±22.5 con
>    sus opuestos) y comparar contra los vecinos que estrangulan ese sector.
> 2. THE salida SHALL ser cero en el borde de 1 píxel de la imagen.
> 3. WHEN existe una cuchilla ancha (3 píxeles) perpendicular al gradiente,
>    THEN el NMS SHALL conservar únicamente la fila/columna del máximo
>    (adelgazamiento a 1 píxel) — verificado: columna del máximo única
>    sobreviviente.

El código clasifica sobre el eje del gradiente con `phi = np.mod(angle, 180.0)` y `sector = np.floor(phi / 45.0)` (`non_max_sup.py:64-65`), no con `np.mod(angle, 360)` ni límites de 22.5°; R1.2 (borde de 1 px en 0) y R1.3 (adelgazamiento) sí se cumplen.

### R2 — Interpolación lineal subpíxel

**Estado:** CONTRADICHO · **Evidencia:** `src/odin/Procesamiento/models/non_max_sup.py:36-38,66,81-82`

> **User Story:** Como usuario de ODIN, quiero interpolar linealmente entre los
> vecinos que estrangulan la dirección del gradiente, para decidir picos con
> precisión subpíxel en vez de comparar contra ejes fijos.
>
> #### Acceptance Criteria
>
> 1. THE valores de comparación SHALL calcularse como interpolación lineal entre
>    el vecino del eje y el vecino diagonal del sector, con peso `w_x`/`w_y`.
> 2. WHEN `max(|Gx|,|Gy|) == 0` (píxel plano), THEN los pesos SHALL ser 0 sin
>    división por cero.

El código interpola con la fracción angular `f = (phi - 45.0 * sector) / 45.0` y los pesos `Gx`/`Gy` quedan declarados sin uso (`non_max_sup.py:36-38,66,81-82`); R2.1 es el contraste verificado y R2.2 no aplica al no existir ponderación que divida por cero.

### R3 — Simetría por cuadrante del gradiente

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/non_max_sup.py:61-66`; test `tests/unit/Procesamiento/test_etapa3_non_max_sup.py:50`

> **User Story:** Como usuario de ODIN, quiero que un borde y su reflejo
> geométrico produzcan resultados reflejados, para que el detector no tenga
> sesgo diagonal.
>
> #### Acceptance Criteria
>
> 1. WHEN dos campos de gradiente son espejos geométricos entre sí (p.ej.
>    perfiles simétricos con ángulos θ y 180−θ), THEN las máscaras de salida
>    SHALL ser espejo entre sí. **(Resuelto: el esquema de comparación sobre el
>    eje mod 180° con selección de vecinos por sector es simétrico por
>    construcción — verificado: espejo 80°/100° exacto.)**

La comparación sobre el eje `mod 180°` con selección de vecinos por sector hace la simetría estructural; el test de espejo 80°/100° lo verifica.

### R4 — Tie-breaking consistente entre sectores

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/non_max_sup.py:85`; test `tests/unit/Procesamiento/test_etapa3_non_max_sup.py:40`

> **User Story:** Como usuario de ODIN, quiero el mismo criterio de desempate en
> los 4 sectores, para que las mesetas no se traten distinto según su
> orientación.
>
> #### Acceptance Criteria
>
> 1. WHEN un píxel empata con el valor interpolado de sus vecinos, THEN el
>    criterio (`>=` o `>`) SHALL ser idéntico en los 4 sectores.
>    **(Resuelto: `>=` en los 4 sectores — meseta 3×3 → 9/9 en gradiente 0 y
>    en gradiente 90.)**

`keep = (C >= v_este) & (C >= v_opuesto)` aplica `>=` en los 4 sectores; el test de meseta 3×3 lo verifica.

### R5 — Umbralizado doble

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Procesamiento/models/non_max_sup.py:268-297`; tests `tests/unit/Procesamiento/test_etapa3_non_max_sup.py:77,88`

> **User Story:** Como la etapa de histéresis, quiero una partición limpia en
> bordes fuertes y débiles, para que el seguimiento conecte solo débiles
> adyacentes a fuertes.
>
> #### Acceptance Criteria
>
> 1. WHEN `thresh ∈ (0,1]`, THEN `gnh` SHALL contener `1.0` en todo píxel con
>    `M >= thresh`, y `gnl` SHALL contener la magnitud original en todo píxel con
>    `thresh² <= M < thresh`; el resto 0.
> 2. WHEN `thresh > 1`, THEN SHALL tratarse como `1.0` (corte superior).
> 3. THE umbral inferior SHALL ser `thresh²` (decisión de diseño vigente; el
>    código original usaba `0.4·thresh`, comentado en el fuente).
> 4. (Deuda de firma, resuelta) El parámetro `angle` de `DobleThreshold` era
>    obsoleto: la función no lo utiliza desde que el NMS se separó en
>    `LinearInterpolation`. **(Resuelto: parámetro eliminado de la firma y
>    llamador `main.py` actualizado.)**

`DobleThreshold(M, thresh)` limita `thresh > 1.0` a `1.0`, usa `lthresh = thresh * thresh`, asigna `gnh[M >= uthresh] = 1.0` y `gnl` con la magnitud en `[lthresh, uthresh)`; la firma ya no recibe `angle`.

## Divergencias

- **R1.1** — el spec exige clasificar `np.mod(angle, 360)` en 4 sectores con límites 22.5°/67.5°/112.5°/135.5°…; el código usa `np.mod(angle, 180.0)` y `sector = np.floor(phi / 45.0)` sobre el eje del gradiente · `src/odin/Procesamiento/models/non_max_sup.py:64-66`
- **R2.1** — el spec exige los pesos `w_x=|Gx|/max(|Gx|,|Gy|)` y `w_y=|Gy|/max(|Gx|,|Gy|)`; el código interpola con la fracción angular `f` y `Gx`/`Gy` quedan sin uso · `src/odin/Procesamiento/models/non_max_sup.py:36-38,66,81-82`

## Pendientes

- Ninguno.
