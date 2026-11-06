# Tasks Document — hough-circles (etapa ⑦)

## Tarea 1: Especificación — hecha

- [x] `requirements.md` R1-R9.
- [x] `design.md` con el estado del módulo, la evidencia sobre `img100.bmp`
      (r real 428.3, defecto del radio constante, barrido en 5.6 s, contraste
      invertido DICLECI) y el diseño.
- [x] Batería previa: kernels idénticos en la imagen real, barrido de 112
      radios, comparación del ajuste con radio correcto vs constante.

## Tarea 2: Tests (TDD) — hecha

- [x] `tests/test_etapa7_hough_circles.py`, 37 casos.
- [x] Caracterización de `hough_circles_vectorizado` (R1).
- [x] Barrido `estimar_radio` sobre círculos sintéticos de radio conocido (R3).
- [x] Test en rojo del defecto: el orquestador no debe usar un radio constante
      (R2); falló hasta que `main.py` dejó de tener el `253`.
- [x] Ambigüedad y banda inválida (R3.4, R5).
- [x] Selección de un solo centro (R9), con la regresión del broadcasting.
- [x] Contraste invertido (R7).
- [x] Recorte holgado y manchas tipo texto (R10); validado contra el enfoque
      anterior, que falla en los mismos casos con 12-35 px de error.
- [x] Estado del campo de diámetro y precedencia manual/automática (R6),
      headless: `EstadoDiametro` y `resolver_radio` no dependen de GTK.

## Tarea 3: Implementación — hecha

- [x] `estimar_radio` y `mejor_centro` en `src/odin/Procesamiento/models/hough_circles.py`
      (capa modelo, sin UI).
- [x] Guarda de imagen vacía en `hough_circles_vectorizado` (R1.4).
- [x] Limpieza: imports duplicados (`numpy` y `maximum_filter` dos veces,
      `math` sin uso) y `np.arange(r_min, r_max + 1, ...)` corregido a
      `+ paso/2` para no pasarse del límite.
- [x] `main.py`: fuera `diametro = 253`; flujo de banda + barrido + un centro
      (§3.2 del design).
- [x] **R6 — hecho**: campo `Adw.SpinRow` "Diámetro (px)" en el grupo
      "Parámetros del Algoritmo" (junto a σ), con botón "Auto" como sufijo y
      estado separado en la clase `EstadoDiametro` (`detectado` / `usuario`).
      El subtítulo informa origen y aviso de ambigüedad. `resolver_radio`
      (función pura) decide la precedencia.
- [x] **R10 — hecho**: `estimar_radio_dominante` con barrido grueso
      `[0.08·r0, r0]` + refinamiento de los candidatos mejor separados; la banda
      fija `[0.6·r0, r0]` se descarta en `main.py`.

## Tarea 4: Verificación con datos reales — hecha

- [x] `img100.bmp` recortado: diámetro detectado **855.70** frente a 856.61
      real (error **0.91 px**), centro a **0.29 px**. Antes daba 807.9 con
      24.4 px de error.
- [x] Ambigüedad 0.35 → confiable; barrido en 5.6 s.
- [x] Recorte holgado (2288 × 2000, incluye el texto, `r/r0 = 0.428`): radio
      **428.0** (error 0.31 px), ambigüedad 0.38, **10.9 s**; cadena completa
      855.70 frente a 856.61 real y centro a 0.29 px.
- [x] Contraste invertido cubierto con tests sintéticos (R7); las DICLECI
      reales no se commitean.
- [x] Humo de ventana real sobre Wayland: campo creado junto a σ, escritura
      manual gana, el detectado no la pisa, "Auto" vuelve a automático.
- [x] Suite completa verde: **99 passed**, sin regresiones en las etapas 1-6.

## Tarea 5: Cierre

- [x] Decisión sobre el código muerto: `houghCircles`, `houghpeaks` e
      `imregionalmax` siguen **sin llamadores** (verificado por grep). No se
      borran en esta tarea: la regla del proyecto exige autorización explícita.
- [ ] `MEMORY.md` y commit.

## Pendientes anotados

1. **Círculos concéntricos**: top-k de radios. Sin eso, un círculo grande tapa
   a uno mucho más chico sin reportar ambigüedad (§2.5 / R5.4).
2. **Círculos muy chicos en recortes grandes**: por debajo del 8% del lado menor
   quedan fuera de la banda (R10.5). Se resuelven declarando el diámetro a mano.
3. **Costo del barrido holgado**: 10.9 s sobre 10 028 bordes, dominado por la
   convolución de las etapas ①-⑥ (50.7 s en el mismo recorte).
