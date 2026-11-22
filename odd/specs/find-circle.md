# find-circle (etapa ⑧)

> Absorbido de `.kiro/specs/find-circle/` el 2026-11-21. Original conservado sin
> modificar (S1). Estado verificado contra el código en esa fecha.

## Requisitos absorbidos

### R1 — Contrato de `find_circle`

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/find_circle.py:46-104`

> ### Requirement 1: Contrato de `find_circle`
>
> **User Story:** Como etapa ⑨, quiero puntos en las mismas coordenadas que la
> imagen de bordes y con un orden irrelevante.
>
> #### Acceptance Criteria
>
> 1. THE función SHALL recibir una imagen binaria de bordes, un radio `re` y un
>    centro `(xd, yd)`.
> 2. WHEN `re > 0`, THEN SHALL devolver las coordenadas `(x, y)` de los píxeles
>    con borde cuya distancia euclidiana al centro cae en `[re - tol, re + tol]`,
>    con `tol` según R2.
> 3. THE arreglo devuelto SHALL tener forma `(N, 2)` en coordenadas de la imagen
>    recibida.
> 4. WHEN no hay bordes o ninguno cae en el anillo, THEN SHALL devolver un
>    arreglo de forma `(0, 2)` sin lanzar excepción.
> 5. THE orden de los puntos SHALL NOT ser parte del contrato: la etapa ⑨ ajusta
>    por mínimos cuadrados y el orden no influye en el resultado.

`np.argwhere(...)[:, ::-1]` devuelve `(N, 2)` en `(x, y)` y el anillo `[re - tol, re + tol]` es inclusive (`:89-102`); sin bordes devuelve `(0, 2)` (`:91-92`); tests `tests/unit/Ajustes/test_etapa8_find_circle.py:64,74,82`.

### R2 — La tolerancia del anillo no puede superar al radio

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/find_circle.py:31-43,97-99`

> ### Requirement 2: La tolerancia del anillo no puede superar al radio
>
> **User Story:** Como usuario que mide círculos chicos, quiero que el anillo no
> se trague el interior del círculo ni a sus vecinos.
>
> #### Acceptance Criteria
>
> 1. THE tolerancia SHALL calcularse como `min(10 px, 0.25 · re)`.
> 2. Justificación medida (sintético `r = 8` con un círculo interno en `r = 20`,
>    radio de búsqueda `re = 10`):
>
>    | Tolerancia | Puntos | Contaminación | Radio ajustado | Error |
>    |---|---|---|---|---|
>    | fija 10 px | 240 | **55.0 %** | 15.40 | **7.40 px** |
>    | `min(10, 0.25·re)` = 2 px | 60 | 0.0 % | 8.43 | 0.43 px |
>
>    La tolerancia fija hace que el anillo `[0, 20]` incluya el círculo interno
>    completo.
> 3. WHEN `re ≤ 10`, THEN el límite inferior del anillo SHALL ser no negativo,
>    porque una distancia negativa no es un intervalo con sentido.
> 4. WHEN `re ≥ 40`, THEN el resultado SHALL ser idéntico al de la tolerancia
>    fija de 10 px, para no alterar la medición de los círculos grandes ya
>    verificados: en `img100` (r = 428.31) el ajuste es `427.85` en ambos casos.
> 5. THE tolerancia SHALL poder pasarse explícitamente para pruebas y para
>    escenarios con ruido de radio conocido.

`tolerancia_anillo` devuelve `min(10, 0.25 · re)` (`:43`), el parámetro `tolerancia` es opcional (`:46,97`) y un valor negativo lanza `ValueError` (`:98-99`); tests `:105,116,129,138`.

### R3 — Reporte de cobertura del anillo

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/find_circle.py:187-262`, `src/odin/controllers/main_controller.py:321-325`

> ### Requirement 3: Reporte de cobertura del anillo
>
> **User Story:** Como usuario, quiero que la aplicación me avise cuando los
> puntos seleccionados no rodean un círculo, en lugar de mostrarme un diámetro
> inventado.
>
> #### Acceptance Criteria
>
> 1. THE modelo SHALL ofrecer `cobertura_angular(puntos, centro, bins=72)` que
>    devuelva `(cobertura, hueco_max_deg)`.
> 2. THE modelo SHALL ofrecer `validar_anillo(...)` que decida si la selección
>    rodea al círculo, con umbrales declarados en el diseño.
> 3. Evidencia — la métrica separa los casos sin ambigüedad:
>
>    | Escenario | Cobertura | Hueco máx. | Ajuste |
>    |---|---|---|---|
>    | círculo completo sintético (r = 12 … 428) | **100 %** | **0°** | error ≤ 0.1 px |
>    | basura sintética (radio de búsqueda desviado) | **2.8 – 9.7 %** | 325 – 350° | error 6 – 57 px |
>    | glifo del texto en `img100` (recorte holgado, `re = 126.5`) | **54.2 %** | **115°** | centro a **1452.81 px**, r = 128.01 |
>    | disco real en `img100` (`re = 428.3`) | **100 %** | **0°** | 0.46 px de radio, 0.32 px de centro |
>
> 4. THE validación SHALL usar el centro recibido de la etapa ⑦, **no** el centro
>    ajustado por ⑨, para que la etapa ⑧ no dependa de la etapa siguiente.
>    Medido: en el caso del glifo la cobertura es 54.2 % con el centro de Hough y
>    55.6 % con el centro ajustado; en el caso correcto es 100 % en ambos.
> 5. WHEN la cobertura es menor que el umbral o el hueco supera el máximo, THEN
>    el orquestador SHALL abortar con un mensaje que explique la causa, en lugar
>    de continuar hacia ⑨.
> 6. Limitación declarada: un círculo real con una oclusión mayor que el hueco
>    admitido se rechaza aunque exista. Es preferible a devolver un número
>    silenciosamente equivocado (misma política que R5 de la etapa ⑦).

`cobertura_angular` (`:187-228`) y `validar_anillo` (`:231-262`) con umbrales `UMBRAL_COBERTURA = 0.75` y `HUECO_MAX_DEG = 60.0` (`:26-28`); el orquestador aborta con el motivo antes de `Circulo_simple` (`main_controller.py:321-325`); tests `:151,161,178,188,203`.

### R4 — Una selección insuficiente no llega al ajuste

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/find_circle.py:246-260`

> ### Requirement 4: Una selección insuficiente no llega al ajuste
>
> #### Acceptance Criteria
>
> 1. THE orquestador SHALL rechazar la selección antes de ajustar cuando tenga
>    menos de 3 puntos.
> 2. Justificación medida (`Circulo_simple` con pocos puntos):
>
>    | Entrada | Resultado |
>    |---|---|
>    | 0 puntos | `ValueError: zero-size array to reduction operation maximum which has no identity` |
>    | 1 punto `(10,10)` | centro (4.99, 4.99), **r = 7.08**, **pv = 0.0** |
>    | 2 puntos colineales | centro (15, 15), **r = 7.07**, **pv = 0.0** |
>    | 3 puntos colineales | centro (10, 10), r = 11.55, pv = 8.95 |
>    | 3 puntos **casi** colineales | centro (**-200010, 200020**), r = **282864**, **pv = 0.0** |
>
>    El ajuste con menos de 3 puntos está subdeterminado y devuelve un círculo
>    con `pv = 0`, indistinguible de uno perfecto; y con 3 puntos casi colineales
>    devuelve un círculo absurdo también con `pv = 0`. El `pv` no sirve como
>    validador en ninguno de los dos casos.
> 3. THE cobertura angular SHALL rechazar también el caso casi colineal, sin
>    depender de la etapa ⑨: medido, tres puntos casi colineales cubren 4.2 %.
> 4. El mensaje de error SHALL indicar la causa probable (anillo vacío, cobertura
>    insuficiente, pocos puntos) y no un error matemático genérico.

`validar_anillo` rechaza `n < 3` (`:246-248`) y cobertura/hueco insuficientes (`:252-260`) con un motivo explicativo; tests `:237,259`.

### R5 — Un solo centro, y de tipo escalar

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/find_circle.py:60-68`, `src/odin/controllers/main_controller.py:298-303,316`

> ### Requirement 5: Un solo centro, y de tipo escalar
>
> **User Story:** Como etapa ⑧, quiero recibir un centro, no una lista de picos.
>
> #### Acceptance Criteria
>
> 1. THE función SHALL esperar `centro = (xd, yd)` con dos escalares; `xd, yd =
>    centro` es el punto de desembalaje donde se manifiesta el defecto R9 de la
>    etapa ⑦.
> 2. THE orquestador SHALL pasar un único centro, elegido por votos
>    (`mejor_centro`), y esto SHALL cubrirse con un test de regresión.
> 3. Evidencia del defecto original: con `n > 1` picos, pasar los arreglos
>    completos lanzaba `ValueError: operands could not be broadcast together with
>    shapes (968,) (2,)`.

El desembalaje `xd, yd = centro` (`:60`) y el guard `np.ndim(...) != 0` (`:64-68`) rechazan arreglos; el orquestador pasa `mejor_centro` (`main_controller.py:298-303`) a `find_circle` (`:316`); tests `:157,278`.

### R6 — El modo sin radio es explícito

**Estado:** IMPLEMENTADO · **Evidencia:** `src/odin/Ajustes/models/find_circle.py:75-85,107-184`

> ### Requirement 6: El modo sin radio es explícito
>
> **User Story:** Como mantenedor, quiero que un llamador que olvide el radio
> reciba un error, no otro algoritmo.
>
> #### Acceptance Criteria
>
> 1. THE `find_circle` SHALL exigir un radio de búsqueda positivo: `re=None` y
>    `re <= 0` SHALL lanzar `ValueError` con un mensaje que indique el uso de
>    `segmento_mas_largo`.
> 2. THE agrupamiento por saltos SHALL vivir en `segmento_mas_largo(puntos)`,
>    separado de `find_circle`, para poder probarlo sin pasar por la firma de
>    búsqueda.
> 3. Evidencia del riesgo que se elimina: `main.py:586` es el único llamador de
>    producción y siempre pasa `radio > 0`, así que la rama solo se alcanzaba con
>    el **valor por defecto** (`re=0.0` + `if re:`). Un llamador que olvidara el
>    radio habría recibido, sin aviso, puntos agrupados por saltos en vez del
>    anillo.
> 4. THE `segmento_mas_largo` SHALL preservar exactamente el resultado de la rama
>    original: verificado contra la versión commiteada en `b350deb` sobre 300
>    conjuntos aleatorios con el mismo orden de entrada — **0 diferencias**.
> 5. Deuda corregida: la afirmación anterior de que `< 6` (X) y `<= 6` (Y) eran
>    umbrales distintos era **falsa**. Como en ambos ejes el test es
>    `np.where(l > 6)`, las dos normalizaciones son equivalentes y un hueco de
>    exactamente 6 px **no** corta en ninguno: fuzz sobre 300 conjuntos, 0
>    diferencias, y el caso de huecos de 6 px conserva los 4 puntos.
> 6. Limitación declarada de `segmento_mas_largo`: no usa ningún centro y agrupa
>    por saltos en la coordenada ordenada, no por conectividad espacial; con
>    círculos concéntricos se queda con la banda que los contiene a los dos. El
>    umbral de 6 px tampoco escala con la resolución de la imagen.

`find_circle` lanza `ValueError` mencionando `segmento_mas_largo` para `re=None` y `re <= 0` (`:75-85`); `segmento_mas_largo` está separado (`:107-184`); tests `:289,297,304,311,323`. R6.4 (equivalencia contra `b350deb`) no se re-ejecutó en esta verificación: INCIERTO. El llamador de producción hoy es `main_controller.py:316`, no `main.py:586`.

## Divergencias

- Ninguna divergencia behavioral verificada. La banda `[0.6·r0, r0]` no pertenece a este spec (aparece en `hough-circles`, donde ya está declarada descartada) y no se registra.

## Pendientes

- Ninguna obligación pendiente.
