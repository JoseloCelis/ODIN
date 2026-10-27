# Tasks Document — find-circle (etapa ⑧)

## Tarea 1: Especificación — hecha

- [x] `requirements.md` R1-R6.
- [x] `design.md` con el estado del módulo, la evidencia ejecutada (anillo
      frágil lejos del radio, degeneración con `re <= 10`, síntoma del usuario
      reproducido sobre `img100`) y los umbrales con su margen.

## Tarea 2: Tests (TDD) — hecha

- [x] `tests/test_etapa8_find_circle.py`, 27 casos (rojo: 19 fallos / 5 pasados).
- [x] Caracterización de `find_circle` (R1): selección, forma, coordenadas,
      vacío sin excepción, orden irrelevante.
- [x] `tolerancia_anillo` (R2): valores por radio, círculo interno sin
      contaminación, equivalencia con la tolerancia fija para `re >= 40`.
- [x] `cobertura_angular` y `validar_anillo` (R3): anillo completo vs basura,
      umbrales, motivo del rechazo; arco rechazado por cobertura y arco de 290°
      rechazado por hueco.
- [x] Selección insuficiente (R4): 0, 1 y 2 puntos; ajuste subdeterminado con
      `pv = 0`; tres puntos casi colineales.
- [x] Regresión de un solo centro (R5).
- [x] El modo sin radio quedó explícito (R6): `find_circle` exige el radio y
      `segmento_mas_largo` conserva el agrupamiento, probado aislado.

## Tarea 3: Implementación — hecha

- [x] `odin/Preprocesamiento/findCircle.py`: `tolerancia_anillo`,
      `cobertura_angular`, `validar_anillo`, y `tolerancia` opcional en
      `find_circle`; centro con arreglos rechazado con mensaje explícito.
- [x] `odin/main.py`: validar el anillo antes de `Circulo_simple` y abortar con
      el motivo; el diálogo pasó de "Error Matemático" a "No se pudo procesar
      la imagen" con la causa en el mensaje.

## Tarea 4: Verificación con datos reales — hecha

- [x] Recorte holgado de `img100`: el disco se acepta con 100 % de cobertura y
      el ajuste da 427.85 (0.46 px); los radios 126.5, 300 y 550 se rechazan
      con 54.2 % / 27.8 % / 15.3 % de cobertura.
- [x] Sin regresión en la medición de la etapa ⑦: diámetro 855.70, centro a
      0.29–0.32 px.
- [x] Suite completa verde: **126 passed**.

## Tarea 5: Cierre

- [x] `MEMORY.md` y commit.
- [x] R6: el modo sin radio es explícito. Se descartó eliminarlo por ahora
      (capacidad y trazabilidad con el MATLAB original); queda pendiente de
      borrado si tras la refactorización sigue sin llamadores.
- [x] Corrección: la afirmación de que `< 6` y `<= 6` eran umbrales distintos
      era falsa; ambos ejes usan `np.where(l > 6)`, así que son equivalentes.
