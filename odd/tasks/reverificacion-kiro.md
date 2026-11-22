# Reverificación de `.kiro/specs/` contra el código

- **Fecha:** 2026-11-21
- **Rama:** `docs/absorcion-kiro`
- **Alcance:** 9 specs × `requirements.md`, `design.md`, `tasks.md` (27 archivos).
- **Objetivo:** respaldar con evidencia `archivo:línea` los bloques de estado
  (`<!-- ESTADO:INICIO -->` … `<!-- ESTADO:FIN -->`) agregados al inicio de cada
  archivo. Esta tabla es la prueba de lo que declaran los bloques.
- **Método:** lectura del código y de los tests; verificación de ausencias con
  `grep` acotado; un contraste numérico puntual (kernel-separable R3/R4). No se
  modificó ningún cuerpo de spec: el diff es 100 % inserción (27 archivos,
  462 líneas añadidas, 0 borradas).

## Hallazgos previos: resultado de la re-verificación

| Hallazgo previo | Resultado |
|---|---|
| `non-max-sup` R1.1/R2.1 CONTRADICHOS (`mod 180` y fracción angular) | **Confirmado** — `non_max_sup.py:64-66,72-78,85`; Gx/Gy sin uso `:36-38` |
| `circulo-simple` R1.6 CONTRADICHO (`TypeError` vs `ValueError`) | **Confirmado** — `circulo_simple.py:55-57` |
| `odin-startup-structure` R1.3 (`type(display).__name__`) | **Confirmado** — `bootstrap.py:291` |
| `odin-startup-structure` R2.5 (cadena `"Preprocesamiento_Suite: OK"` inexistente) | **Confirmado** — 0 hits; `bootstrap.py:243,255-258` |
| `odin-startup-structure` R3.1 (`os.uname()` sin try/except) | **Confirmado** — `bootstrap.py:165` |
| `odin-startup-structure` R4.1/R4.2/R4.6 PENDIENTES | **Confirmado** — no hay límites de tiempo; solo duración logueada (`main_window.py:521-524`) |
| `kernel-separable` R3/R4 INCIERTO | **Corregido** — el contraste ejecutado coincide (≤ 7e-17); no existe cross-check automático versionado (nota en el bloque) |
| `mag-fase` R4/R5, `edge-track-hyst` R6, `otsu-rosin` R6: criterios desactualizados | **Confirmado** — los cuatro describen defectos ya corregidos |
| `hough-circles` R4: docstring con `[0.6·r0, r0]` | **Confirmado** — `hough_circles.py:144-145` |
| Pipeline cubre etapas ①-⑤ y no ①-⑨ | **Confirmado** — `tests/integration/test_pipeline.py:1,22-29` |
| Banda `[0.6·r0, r0]` en `find-circle` | **Descartada** (falsa): no pertenece a `find-circle`; no se escribió en ningún bloque |

Nuevo hallazgo (no listado como previo): **el código muerto de `hough-circles`
ya no existe**. `hough_circles.py:16-17` y los docs dicen que
`houghCircles`/`houghpeaks`/`imregionalmax` están "sin mover"; en `src/` hay 0
definiciones. La eliminación está registrada en
`.kiro/specs/hough-circles/tasks.md:63-64,80`.

---

## kernel-separable

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | IMPLEMENTADO | `deri_gauss.py:34-42`: `gk` normalizado por su suma; simetría por construcción (`i` en `[-n, n]`) |
| R2 | IMPLEMENTADO | `deri_gauss.py:40-43`: `dgk = -(1/σ²)·i·gk`, antisimétrico |
| R3 | IMPLEMENTADO | `deri_gauss.py:51-52`; contraste ejecutado en esta reverificación: `sepFilter2D` con correlación sobre `−dgk` y `BORDER_CONSTANT`, y referencia NumPy, discrepancia ≤ 7e-17 (5 casos, σ=1.0–4.0). Sin cross-check automático versionado |
| R4 | IMPLEMENTADO | `convolucion.py:25-34`: soporte inclusivo `j ∈ [i−nk, i+nk]` con `j0/j1` recortados (zero-padding); equivalencia con `np.convolve(mode='same')` ≤ 6e-17 en tamaños habituales |
| R5 | IMPLEMENTADO | `deri_gauss.py:21-23`: retorno temprano antes de `n = round(3σ)` (`:30`); tests `tests/unit/Preprocesamiento/test_etapa1_kernel_separable.py:17,25` |
| R6 | PENDIENTE | no implementado: el módulo es modelo puro sin visualización (`deri_gauss.py:1-8`); no existen `wc = min(640, nc−1)` ni `wr` |

**Pendientes:** R6 — visualización de cortes (`wc = min(640, nc−1)`, `wr`
acotada a `[0, nr−1]`): nunca implementada; el módulo no contiene código de
visualización.

**Divergencias verificadas:**
- R4.2 — el caso literal `n ≤ 2·nk` es inconsistente con la referencia
  `np.convolve(mode='same')` (p.ej. imagen 5×5 con σ=3: referencia (5,19) vs
  salida (5,5)); el código calcula la convolución completa centrada con
  zero-padding.
- R3/R4 — no hay cross-check automático versionado:
  `tests/utilidades.py:44-49` define `derivada_gaussiana_referencia` y ningún
  test la invoca (0 usos).

**Contraste ejecutado (resumen):** `DerivGauss` vs OpenCV
(`sepFilter2D`, `-dgk`/`gk`, `BORDER_CONSTANT`) y vs `np.convolve` de referencia:
discrepancias máximas entre 1.4e-17 y 6.9e-17 para imágenes 17×23 (σ=1.0, 2.0,
2.5), 40×50 (σ=3.0) y 80×90 (σ=4.0).

**Inciertos:** ninguno.

---

## mag-fase

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | IMPLEMENTADO | `mag_fase.py:23`: `np.hypot(GrX, GrY)`; tests `tests/unit/Preprocesamiento/test_etapa2_mag_fase.py:17,37` |
| R2 | IMPLEMENTADO | `mag_fase.py:24-26`: división por el máximo solo si > 0; imagen plana queda en ceros; tests `test_etapa2_mag_fase.py:27,37` |
| R3 | IMPLEMENTADO | `mag_fase.py:29-30`: `atan2*180/π`, `-180` se mapea a `180`; test `test_etapa2_mag_fase.py:61` |
| R4 | IMPLEMENTADO | `mag_fase.py:7`: único import (`numpy`); sin `cv2` ni UI |
| R5 | IMPLEMENTADO | `mag_fase.py:19-20`: entrada vacía devuelve tuplas vacías sin excepción de NumPy; test `test_etapa2_mag_fase.py:54` |

**Pendientes:** ninguno.

**Divergencias verificadas:** R4.1 y R5.1 están desactualizados: describen
`import cv2` y el `ValueError` interno de NumPy como defectos vigentes; ambos
están corregidos. `design.md:34,48` repite la deuda D1.

**Inciertos:** ninguno.

---

## otsu-rosin

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | IMPLEMENTADO | `otsu_rosin.py:19-21,43`: `IG > 0`, 256 bins; vacío → `0.0`; tests `tests/unit/Procesamiento/test_etapa4_otsu_rosin.py:91,105` |
| R2 | IMPLEMENTADO | `otsu_rosin.py:57-100`: argmax de `vB`; tests `test_etapa4_otsu_rosin.py:33,57` |
| R3 | IMPLEMENTADO | `otsu_rosin.py:98`: argmax determinista dentro de la meseta; test `test_etapa4_otsu_rosin.py:43` (meseta plana) |
| R4 | IMPLEMENTADO | `otsu_rosin.py:102-161`: Rosin pico→cola, respaldo a Otsu (`:159`); test `test_etapa4_otsu_rosin.py:114` |
| R5 | IMPLEMENTADO | `otsu_rosin.py:29-40,45-52`: un solo bin centrado en el valor real y rescate del caso casi-constante; tests `test_etapa4_otsu_rosin.py:68,76` |
| R6 | IMPLEMENTADO | `otsu_rosin.py:9`: solo `numpy`; sin `gi`/`GLib`/matplotlib |

**Pendientes:** ninguno.

**Divergencias verificadas:** R6.1 está desactualizado: describe la deuda D3
(`GLib.idle_add(dibujar_en_hilo_principal, ...)`) como vigente; el módulo ya no
invoca UI (`design.md:14,63` lo repite).

**Inciertos:** ninguno.

---

## edge-track-hyst

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | IMPLEMENTADO | `edge_track_hyst.py:22-34,45,55,76-89`: `uint8` en `{0,255}`, misma forma, no muta los argumentos; tests `tests/unit/Procesamiento/test_etapa6_edge_track_hyst.py:122,134` |
| R2 | IMPLEMENTADO | `edge_track_hyst.py:76,84`: los fuertes se conservan; sin fuertes la salida es cero; tests `:94,104,112` |
| R3 | IMPLEMENTADO | `edge_track_hyst.py:60`: kernel 5×5 → Chebyshev ≤ 2; tests `:39,50` |
| R4 | IMPLEMENTADO | `edge_track_hyst.py:66-89`: componentes 8-conexas, isla entera; tests `:60,70` |
| R5 | IMPLEMENTADO | `edge_track_hyst.py:66-89`: solo propaga dentro de la isla; los huecos no unen; test `:82` |
| R6 | IMPLEMENTADO | `edge_track_hyst.py:40-48`: entrada vacía → vacía `uint8` sin excepción; test `:147` |
| R7 | IMPLEMENTADO | `edge_track_hyst.py:22-89` iterativo; 0 hits de `setrecursionlimit` en `src/` |
| R8 | IMPLEMENTADO | sin prints en el módulo; el orquestador reporta una línea en `main_controller.py:227-232` |

**Pendientes:** ninguno.

**Divergencias verificadas:** R6.1 está desactualizado: afirma «NO CUMPLE hoy»
con el `ValueError` de NumPy; el caso vacío ya está resuelto
(`edge_track_hyst.py:40-48`, `requirements.md:100`).

**Inciertos:** ninguno.

---

## hough-circles

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | IMPLEMENTADO | `hough_circles.py:34-108`; rechazos `:50-58`, entrada vacía `:65-68`; tests `tests/unit/Procesamiento/test_etapa7_hough_circles.py:83,90,97,107,117` |
| R2 | IMPLEMENTADO | `main_controller.py:79-96`: radio por barrido o del usuario; sin constante de diámetro; test `:236` |
| R3 | IMPLEMENTADO | `estimar_radio` `hough_circles.py:131-184`; `ValueError` de banda `:157-160`; tests `:175,184,191,198` |
| R4 | IMPLEMENTADO | `main_controller.py:276` (`r0 = min(alto, ancho)/2`); la banda efectiva es `[0.08·r0, r0]` de R10 (`hough_circles.py:188-268`) |
| R5 | IMPLEMENTADO | `hough_circles.py:23-28` (`UMBRAL_AMBIGUEDAD=0.8`, `SEPARACION_AMBIGUEDAD_PX=6.0`); tests `:213,221` |
| R6 | IMPLEMENTADO | `main_window.py:186-205` (SpinRow «Diámetro (px)» + botón Auto) y `main_controller.py:35-72`; tests `:353,362,372,383,395,404,415,430` |
| R7 | IMPLEMENTADO | test `:251` (cadena con y sin contraste invertido) |
| R8 | IMPLEMENTADO | utilidad verificada y funciones eliminadas: 0 definiciones de `houghCircles`/`houghpeaks`/`imregionalmax` en `src/`; registro `.kiro/specs/hough-circles/tasks.md:63-64,80` |
| R9 | IMPLEMENTADO | `mejor_centro` `hough_circles.py:111-127` (por votos; `None` sin picos); tests `:139,151,157` |
| R10 | IMPLEMENTADO | `estimar_radio_dominante` `hough_circles.py:188-268` (dos escalas, ≥2 candidatos); tests `:288,299,313,319,326` |

**Pendientes:** ninguna obligación pendiente. Limitaciones declaradas: top-k de
radios para círculos concéntricos (R5.4) y diámetro < 8 % del lado menor del
recorte (R10.5).

**Divergencias verificadas:**
- R4 — el docstring `hough_circles.py:144-145` todavía documenta la banda
  descartada `[0.6*r0, r0]` como la de R4; el barrido real es `[0.08*r0, r0]`
  (R10.1).
- R8 — `requirements.md:143-149`, `design.md:11-12` y el docstring
  `hough_circles.py:16-17` describen `houghCircles`/`houghpeaks`/`imregionalmax`
  como código muerto presente; en `src/` no quedan definiciones (eliminadas;
  registro en `tasks.md:63-64,80`).

**Inciertos:** las cifras de evidencia medida (R3.3: 427.6 px; R10.4: 428.0 px,
10.9 s) no se re-ejecutaron en esta reverificación; se conservan como evidencia
histórica del spec.

---

## find-circle

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | IMPLEMENTADO | `find_circle.py:46-105` (salida (N,2), vacío (0,2) en `:92`, orden irrelevante); tests `tests/unit/Ajustes/test_etapa8_find_circle.py:64,74,82` |
| R2 | IMPLEMENTADO | `tolerancia_anillo` `find_circle.py:31-43` (`min(10, 0.25·re)`), parámetro explícito `:46,98`; tests `:105,116,129,138` |
| R3 | IMPLEMENTADO | `cobertura_angular` `find_circle.py:187-229`, `validar_anillo:231-262`; umbrales `:26-28`; aborta con motivo en `main_controller.py:321-325`; tests `:151,161,178,188,203` |
| R4 | IMPLEMENTADO | `validar_anillo:237-260` (<3 puntos y cobertura insuficiente); tests `:237,259` |
| R5 | IMPLEMENTADO | centro escalar `find_circle.py:64-71`; el orquestador pasa `mejor_centro` (`main_controller.py:298-303,317`); tests `:157,278` |
| R6 | IMPLEMENTADO | `find_circle.py:75-86` (`re=None`/`re<=0` → `ValueError` con `segmento_mas_largo`), `segmento_mas_largo:107-183`; tests `:289,297,304,311,323` |

**Pendientes:** ninguno.

**Divergencias verificadas:** ninguna. La banda `[0.6·r0, r0]` no pertenece a
este spec (L8, candidata B falsa) y no se registra.

**Inciertos:** R6.4 (equivalencia contra `b350deb`) no se re-ejecutó en esta
reverificación; el comportamiento está cubierto por los tests `:311-343`.

---

## non-max-sup

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | CONTRADICHO | el requisito exige sectores con `np.mod(angle, 360)` y cortes en 22.5° (`requirements.md:46`); el código compara sobre el eje `mod 180` con fracción angular: `non_max_sup.py:64-66,72-78,85`. R1.2/R1.3 se cumplen (borde de 1 px en 0; adelgazamiento) |
| R2 | CONTRADICHO | el requisito exige pesos `w_x=|Gx|/max(|Gx|,|Gy|)`, `w_y=|Gy|/max(...)` (`requirements.md:64`); el código interpola con la fracción angular `f` y no usa Gx/Gy (`non_max_sup.py:36-38,66,81-82`) |
| R3 | IMPLEMENTADO | simetría por construcción sobre el eje mod 180 (`non_max_sup.py:61-66`); test `tests/unit/Procesamiento/test_etapa3_non_max_sup.py:50` |
| R4 | IMPLEMENTADO | `keep = (C >= v_este) & (C >= v_opuesto)` (`non_max_sup.py:85`); test `:40` |
| R5 | IMPLEMENTADO | `DobleThreshold` `non_max_sup.py:268-297` (gnh=1.0 si M≥thresh; gnl magnitud en [thresh², thresh); thresh>1→1.0; sin parámetro `angle`); tests `:77,88` |

**Pendientes:** ninguno.

**Divergencias verificadas:**
- R1.1 — `requirements.md:46` exige `np.mod(angle, 360)` con límites
  22.5°/67.5°/…; `non_max_sup.py:64-66` usa `np.mod(angle, 180.0)` y
  `sector = floor(phi/45)`.
- R2.1 — `requirements.md:64` exige los pesos `|Gx|/max`; `non_max_sup.py:36-38`
  declara Gx/Gy sin uso y `:66,81-82` interpola con
  `f=(phi−45·sector)/45`.
- La referencia `tests/utilidades.py:nms_referencia_escalar` implementa el mismo
  esquema mod-180: su test valida coherencia interna, no el spec.

**Inciertos:** ninguno.

---

## circulo-simple

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | CONTRADICHO | R1.6: el spec exige `ValueError` para entrada `None`/no array (`requirements.md:52`); el código lanza `TypeError` (`circulo_simple.py:55-57`). Resto verificado: forma/N<3/colinealidad/radicando → `ValueError` (`:61-103,132-135`); orden irrelevante (lstsq) |
| R2 | IMPLEMENTADO | `pv = max(|d−r|) − min(|d−r|)` (`circulo_simple.py:138-145`); test `tests/unit/Ajustes/test_etapa9_circulo_simple.py:132` |
| R3 | IMPLEMENTADO | `main_controller.py:321-338`: `Circulo_simple` se llama tras `validar_anillo` y el motivo del rechazo se muestra en el diálogo |

**Pendientes:** ninguno.

**Divergencias verificadas:** R1.6 — `requirements.md:52` exige `ValueError`;
`circulo_simple.py:55` lanza `TypeError` para `None`/no ndarray (el propio
docstring `:48-51` lo declara así).

**Inciertos:** ninguno.

---

## odin-startup-structure

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 | CONTRADICHO | R1.3 (`requirements.md:56`) exige `Gdk.Display.get_name()`; el código usa `type(display).__name__` (`bootstrap.py:291`). R1.1/R1.2/R1.4 sí: validación `:273-289`, mensaje con componente/causa/acción `:283-286`, `sys.exit(1)` `:289`, antes de construir MainWindow (`main_window.py:510-515`) |
| R2 | CONTRADICHO | R2.5 (`requirements.md:71`): la cadena `"Preprocesamiento_Suite: OK"` no existe; el loader registra `"Handle_Module: OK"` (`bootstrap.py:243`) y `"Módulos resueltos: ..."` (`:255-258`). R2.1-R2.4 sí (`:221-251`) |
| R3 | CONTRADICHO | R3.1 (`requirements.md:81`): `os.uname().release` sin try/except (`bootstrap.py:165`); el criterio exige NATIVE_LINUX si `os.uname()` falla. Resto sí: `_classify:127-133` (dockerenv prioritario), `_resolve_base_path:136-158`, log `:180-184`, warning >200 ms `:173-178` |
| R4 | PENDIENTE | `requirements.md:106-107,111` exigen límites de 2 s/3 s con aborto; no existen (solo se loguea la duración en `main_window.py:521-524`). R4.3-R4.5 sí: orden `main_window.py:73-107,238-313`, respaldo `Gtk.Picture` `:238-257`, `present()` `:526` |
| R5 | INCIERTO | R5.1-R5.4 y R5.6 verificables (`bootstrap.py:23-24,93-107,109-119`; fallback a stderr + `sys.exit(1)` `:100-107`); R5.5 no: `StartupLogger` usa `sys.stdout` sin codec declarado (`:74-75`), el encoding depende del locale |
| R6 | IMPLEMENTADO | `_detect_mode:201-206` (desde `__package__`), logs de modo y módulos `:213-216,255-258`, errores con alias/modo `:234-251`; `main_window.py:487,493`; tests `tests/integration/test_bootstrap_arranque.py:174,186,209` |

**Pendientes:** R4.1, R4.2 y R4.6 — límites de 2 s por componente y 3 s de
construcción, con aborto y `sys.exit(1)`: nunca implementados; hoy solo se
registra la duración (`main_window.py:521-524`).

**Divergencias verificadas:** R1.3 (`requirements.md:56` vs `bootstrap.py:291`);
R2.5 (`requirements.md:71`; `bootstrap.py:243,255-258`); R3.1
(`requirements.md:81` vs `bootstrap.py:165`).

**Inciertos:** R5.5 (`requirements.md:125`): el logger no fija UTF-8
(`bootstrap.py:74-75`).

---

## Verificación ejecutada

- `python3 -m pytest tests -q` → **187 passed, 1 skipped, 1 warning in 7.15s**,
  exit code `0`. No se nombró ningún fallo ambiental conocido; no hubo ninguno.
- Inserción verificada con `git diff --numstat -- .kiro/specs/`: 27 archivos,
  462 adiciones, 0 borrados.
- `grep -rl "ESTADO:INICIO" .kiro/specs/ | wc -l` → 27; idem `ESTADO:FIN` → 27.
