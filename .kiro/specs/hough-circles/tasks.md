# Tasks Document — hough-circles (etapa ⑦)

## Tarea 1: Especificación (hecha)

- [x] `requirements.md` R1-R8.
- [x] `design.md` con el estado del módulo, la evidencia sobre `img100.bmp`
      (r real 428.3, defecto del radio constante, barrido en 5.1 s, contraste
      invertido DICLECI) y el diseño propuesto.
- [x] Batería previa: kernels idénticos en la imagen real, barrido de 112
      radios, comparación del ajuste con radio correcto vs constante.

## Tarea 2: Tests (TDD) — pendiente

- [ ] `tests/test_etapa7_hough_circles.py` con la caracterización de
      `hough_circles_vectorizado` (R1).
- [ ] Tests del barrido `estimar_radio` sobre círculos sintéticos de radio
      conocido (R3).
- [ ] Test en rojo del defecto: el orquestador no debe usar un radio constante
      (R2).
- [ ] Caso de ambigüedad y de banda inválida (R3.4, R5).

## Tarea 3: Implementación — pendiente

- [ ] `estimar_radio` en `odin/Preprocesamiento/houghCircles.py` (capa modelo,
      sin UI).
- [ ] `main.py`: sustituir `diametro = 253` por el flujo de §3.2 del design.
- [ ] Campo de diámetro en la vista con estado separado
      `valor_detectado` / `valor_usuario` (R6).
- [ ] Aviso de ambigüedad (R5) y caso de círculo mayor que el recorte (R7.3).

## Tarea 4: Verificación con datos reales — pendiente

- [ ] `img100.bmp` recortado: diámetro detectado ≈ 854.7 px, ajuste con error
      ≤ 1 px respecto de r=428.3 (hoy da 403.95, error 24.4 px).
- [ ] Una imagen DICLECI (contraste invertido) sin cambios de configuración.
- [ ] Suite completa verde y sin regresiones en las etapas 1-6.

## Tarea 5: Cierre — pendiente

- [ ] Decisión sobre el código muerto `houghCircles`/`houghpeaks`/
      `imregionalmax` (R8) previa verificación de utilidad.
- [ ] `MEMORY.md` y commit.
