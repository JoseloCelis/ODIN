# Tasks Document — hough-circles (etapa ⑦)

## Tarea 1: Especificación — hecha

- [x] `requirements.md` R1-R9.
- [x] `design.md` con el estado del módulo, la evidencia sobre `img100.bmp`
      (r real 428.3, defecto del radio constante, barrido en 5.6 s, contraste
      invertido DICLECI) y el diseño.
- [x] Batería previa: kernels idénticos en la imagen real, barrido de 112
      radios, comparación del ajuste con radio correcto vs constante.

## Tarea 2: Tests (TDD) — hecha

- [x] `tests/test_etapa7_hough_circles.py`, 22 casos.
- [x] Caracterización de `hough_circles_vectorizado` (R1).
- [x] Barrido `estimar_radio` sobre círculos sintéticos de radio conocido (R3).
- [x] Test en rojo del defecto: el orquestador no debe usar un radio constante
      (R2); falló hasta que `main.py` dejó de tener el `253`.
- [x] Ambigüedad y banda inválida (R3.4, R5).
- [x] Selección de un solo centro (R9), con la regresión del broadcasting.
- [x] Contraste invertido (R7).

## Tarea 3: Implementación — hecha

- [x] `estimar_radio` y `mejor_centro` en `odin/Preprocesamiento/houghCircles.py`
      (capa modelo, sin UI).
- [x] Guarda de imagen vacía en `hough_circles_vectorizado` (R1.4).
- [x] Limpieza: imports duplicados (`numpy` y `maximum_filter` dos veces,
      `math` sin uso) y `np.arange(r_min, r_max + 1, ...)` corregido a
      `+ paso/2` para no pasarse del límite.
- [x] `main.py`: fuera `diametro = 253`; flujo de banda + barrido + un centro
      (§3.2 del design).
- [ ] **R6 — DEUDA**: campo de diámetro en la vista con estado separado
      `valor_detectado` / `valor_usuario` y aviso de ambigüedad en la UI. Hoy
      el valor se informa por consola y no se puede sobrescribir.

## Tarea 4: Verificación con datos reales — hecha

- [x] `img100.bmp` recortado: diámetro detectado **855.70** frente a 856.61
      real (error **0.91 px**), centro a **0.29 px**. Antes daba 807.9 con
      24.4 px de error.
- [x] Ambigüedad 0.35 → confiable; barrido en 5.6 s.
- [x] Contraste invertido cubierto con tests sintéticos (R7); las DICLECI
      reales no se commitean.
- [x] Suite completa verde: **84 passed**, sin regresiones en las etapas 1-6.

## Tarea 5: Cierre

- [x] Decisión sobre el código muerto: `houghCircles`, `houghpeaks` e
      `imregionalmax` siguen **sin llamadores** (verificado por grep). No se
      borran en esta tarea: la regla del proyecto exige autorización explícita.
- [ ] `MEMORY.md` y commit.

## Pendientes anotados

1. **R6**: campo de diámetro con precarga automática (decisión del usuario:
   implementación 1, el campo muestra el detectado y permite corregirlo).
2. **Círculos concéntricos**: top-k de radios. Sin eso, un círculo grande tapa
   a uno mucho más chico sin reportar ambigüedad (§2.5 / R5.4).
3. **Bandas holgadas**: si el recorte no está ajustado al círculo, el radio
   verdadero cae fuera de `[0.6·r0, r0]`. Ampliar la banda encarece el barrido
   y multiplica los candidatos; requiere decisión de producto.
