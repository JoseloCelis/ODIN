<!-- ESTADO:INICIO -->
> **Estado del documento** — veredicto: `ABSORBIDO` · versión ODD: `odd/specs/hough-circles.md` · fecha: 2026-11-21
>
> | Requisito | Estado | Evidencia |
> |---|---|---|
> | R1 | IMPLEMENTADO | `hough_circles.py:34-108`; rechazos `:50-58`, entrada vacía `:65-68`; tests `tests/unit/Procesamiento/test_etapa7_hough_circles.py:83,90,97,107,117` |
> | R2 | IMPLEMENTADO | `main_controller.py:79-96`: radio por barrido o del usuario; sin constante de diámetro; test `:236` |
> | R3 | IMPLEMENTADO | `estimar_radio` `hough_circles.py:131-184`; `ValueError` de banda `:157-160`; tests `:175,184,191,198` |
> | R4 | IMPLEMENTADO | `main_controller.py:276` (`r0 = min(alto, ancho)/2`); la banda efectiva es `[0.08·r0, r0]` de R10 (`hough_circles.py:188-268`) |
> | R5 | IMPLEMENTADO | `hough_circles.py:23-28` (`UMBRAL_AMBIGUEDAD=0.8`, `SEPARACION_AMBIGUEDAD_PX=6.0`); tests `:213,221` |
> | R6 | IMPLEMENTADO | `main_window.py:186-205` (SpinRow «Diámetro (px)» + botón Auto) y `main_controller.py:35-72`; tests `:353,362,372,383,395,404,415,430` |
> | R7 | IMPLEMENTADO | test `:251` (cadena con y sin contraste invertido) |
> | R8 | IMPLEMENTADO | utilidad verificada y funciones eliminadas: 0 definiciones de `houghCircles`/`houghpeaks`/`imregionalmax` en `src/`; registro `.kiro/specs/hough-circles/tasks.md:63-64,80` |
> | R9 | IMPLEMENTADO | `mejor_centro` `hough_circles.py:111-127` (por votos; `None` sin picos); tests `:139,151,157` |
> | R10 | IMPLEMENTADO | `estimar_radio_dominante` `hough_circles.py:188-268` (dos escalas, ≥2 candidatos); tests `:288,299,313,319,326` |
>
> **Pendientes:** ninguna obligación pendiente. Limitaciones declaradas: top-k de radios para círculos concéntricos (R5.4) y diámetro < 8 % del lado menor del recorte (R10.5).
> **Divergencias verificadas:** R4 — el docstring `hough_circles.py:144-145` todavía documenta la banda descartada `[0.6*r0, r0]` como la de R4; el barrido real es `[0.08*r0, r0]` (R10.1). R8 — `requirements.md:160-170`, `design.md:26-33` y el docstring `hough_circles.py:16-17` describen `houghCircles`/`houghpeaks`/`imregionalmax` como código muerto presente; en `src/` no quedan definiciones (eliminadas; registro en `tasks.md:63-64,80`).
> **Inciertos:** las cifras de evidencia medida (R3.3: 427.6 px; R10.4: 428.0 px, 10.9 s) no se re-ejecutaron en esta reverificación; se conservan como evidencia histórica del spec.
<!-- ESTADO:FIN -->

# Requirements Document — hough-circles (etapa ⑦)

## Introduction

Etapa ⑦ localiza el **centro aproximado** del círculo con la transformada de
Hough y alimenta la etapa ⑧ (`find_circle`), que filtra los puntos del anillo.

**Contexto que motiva la etapa**: el orquestador busca hoy círculos de un radio
fijo (`main.py:447`, `diametro = 253`). Con una imagen real de 857 px de
diámetro eso produce un círculo fantasma de r=403.95 corrido 24 px, con un
`pv` engañosamente bueno. La medición está en `design.md` §2.

---

## Glossary

- **Banda de radios**: intervalo `[r_min, r_max]` donde se busca el radio.
- **Pico**: máximo del acumulador de Hough para un radio dado.
- **r0**: `min(alto, ancho) / 2` del recorte; cota superior grosera del radio.
- **Ambigüedad**: cuánto se acerca el segundo mejor pico al mejor.

---

## Requirements

### Requirement 1: Contrato de `hough_circles_vectorizado`

**User Story:** Como etapa ⑧, quiero centros en las mismas coordenadas que la
imagen de bordes que recibo.

#### Acceptance Criteria

1. THE función SHALL recibir una imagen binaria de bordes y un radio `r > 0`.
2. THE función SHALL rechazar `dist < 10` y `thres < 0.5` con `ValueError`
   (comportamiento actual, se conserva).
3. THE función SHALL devolver `(x0, y0, n, acumulador)` con los centros en
   píxeles de la imagen recibida y `n = len(x0)`.
4. WHEN no hay bordes, THEN `n` SHALL ser 0 y la función SHALL NOT lanzar
   excepción.

### Requirement 2: El radio no puede ser una constante

**User Story:** Como usuario, quiero medir patrones de distinto diámetro sin
editar el código.

#### Acceptance Criteria

1. THE orquestador SHALL NOT contener una constante de diámetro o radio.
2. THE radio usado SHALL provenir del barrido automático (R3) o de un valor
   declarado por el usuario (R6).
3. WHEN el usuario declara un radio, THEN el barrido SHALL omitirse para esa
   ejecución.

### Requirement 3: Barrido de radios

#### Acceptance Criteria

1. THE barrido SHALL evaluar radios en una banda `[r_min, r_max]` con un paso
   configurable y devolver el radio cuyo pico del acumulador sea mayor.
2. THE barrido SHALL devolver además el valor del pico y la relación
   `segundo_pico / primer_pico`.
3. Evidencia vinculante (img100 con recorte de 15%): radio real 428.3 px;
   el barrido devuelve **427.6** (error 0.7 px) con pico 206 frente a 107 del
   segundo, en 5.1 s para 112 radios sobre 3182 bordes.
4. WHEN `r_min > r_max` o la banda está vacía, THEN SHALL lanzar `ValueError`.

### Requirement 4: Banda derivada del recorte

#### Acceptance Criteria

1. THE orquestador SHALL derivar `r0 = min(alto, ancho) / 2` del recorte y
   usar `r0` como **cota superior** del radio buscado; la banda efectiva es la
   de R10, no una fracción fija de `r0`.
2. Justificación medida: en el recorte con 15% de margen, `r0 = 556.0` y el
   radio real es 428.3 (r0 sobreestima un 30%); en un recorte holgado medido,
   `r0 = 1000.0` y el radio real es el mismo 428.3 (sobreestima un 133%).
3. WHEN el recorte no contiene el círculo completo, THEN el resultado SHALL
   poder marcarse como no confiable (R5) en lugar de devolver un valor
   silenciosamente erróneo.
4. La banda fija `[0.6·r0, r0]` queda **descartada**: con un recorte holgado
   (`r/r0 = 0.428`) el radio real cae fuera y el barrido devuelve basura. Se
   sustituye por el barrido de dos escalas de R10, y el porqué medido está en
   R10.2.

### Requirement 5: Reporte de ambigüedad

#### Acceptance Criteria

1. THE resultado del barrido SHALL indicar si la detección es ambigua, usando
   la relación `segundo_pico / primer_pico` con un umbral declarado en el
   diseño.
2. WHEN la detección es ambigua, THEN la interfaz SHALL mostrarlo antes de
   aceptar el valor, en lugar de presentar el diámetro como certero.
3. Los radios vecinos (a menos de `SEPARACION_AMBIGUEDAD_PX`) SHALL NOT contar
   como candidatos distintos: son el mismo pico repartido por la
   discretización. Sin esta exclusión, todo círculo perfecto se reportaría
   como ambiguo.
4. Limitación declarada: el pico bruto crece con el radio, así que un círculo
   grande domina a uno mucho más chico y la ambigüedad no se reporta. Medido:
   `r=35 + r=45` concéntricos → relación 0.951 (ambigua); `r=30 + r=60` →
   0.366 (no reportada). Resolverlo exige top-k de radios, fuera de alcance.

### Requirement 6: Campo de diámetro en la interfaz

#### Acceptance Criteria

1. THE vista SHALL ofrecer un campo de diámetro que muestre el valor detectado
   por el barrido.
2. THE usuario SHALL poder sobrescribir ese valor; si lo hace, ese valor SHALL
   usarse tal cual y el barrido SHALL omitirse.
3. THE aplicación SHALL distinguir entre un valor **precargado** por el barrido
   y uno **escrito por el usuario**: un precargado no debe convertir la
   siguiente ejecución en manual.
4. THE campo SHALL existir también cuando el barrido no se haya ejecutado
   todavía (por ejemplo, antes de cargar una imagen).
5. Evidencia de implementación (humo de ventana real, backend Wayland):
   - el campo es un `Adw.SpinRow` "Diámetro (px)" en el grupo "Parámetros del
     Algoritmo", junto a σ, con un botón "Auto" como sufijo;
   - escribir 500 deja el estado en **manual** y el valor detectado (855.7) no
     lo pisa;
   - pulsar "Auto" devuelve el campo a 855.7 y el estado a **automático** (no
     manual), que es justo lo protegido por R6.3.

### Requirement 7: Contraste invertido

**User Story:** Como metrólogo, quiero medir tanto círculos claros sobre fondo
oscuro como agujeros oscuros sobre fondo claro.

#### Acceptance Criteria

1. THE cadena ⑦→⑧→⑨ SHALL funcionar con círculo oscuro sobre fondo claro,
   sin cambios de configuración.
2. Evidencia: `Imagenes_círculo_DICLECI/0.050_1.bmp` es un disco **oscuro** de
   r=427.5 sobre fondo claro; `1.575_1.bmp` tiene el círculo **más grande que
   el campo de visión** (solo se ve un arco).
3. WHEN el círculo excede el recorte, THEN la aplicación SHALL NOT devolver un
   ajuste como si fuera válido (ver R5).

### Requirement 8: Código muerto del módulo

#### Acceptance Criteria

1. THE proyecto SHALL verificar utilidad de `houghCircles`, `houghpeaks` e
   `imregionalmax` antes de decidir su destino (regla del proyecto: no se borra
   nada sin verificar).
2. Evidencia actual: `hough_circles_vectorizado` es la única función llamada
   (`main.py:448`); `houghCircles` es una traducción de MATLAB con bucles
   Python por punto y por ángulo, sin llamadores; `houghpeaks` e
   `imregionalmax` solo son usadas por ella.

### Requirement 9: El llamador elige UN centro

**User Story:** Como etapa ⑧ (`find_circle`), quiero recibir **un** centro, no
la lista completa de picos.

#### Acceptance Criteria

1. THE orquestador SHALL elegir un único centro entre los picos de R1, usando
   el **mayor número de votos** del acumulador.
2. THE función de selección SHALL devolver `None` cuando no hay picos, para que
   el orquestador pueda abortar con un mensaje en vez de seguir con basura.
3. THE elección SHALL NOT depender del orden de `np.nonzero`, que recorre la
   imagen por filas y no está ordenado por votos.
4. Evidencia del defecto (medido): `main.py` pasaba el tuple de **arreglos**
   completo a `find_circle`. Con `n = 1` funcionaba solo por broadcasting; con
   `n > 1` lanzaba `ValueError: operands could not be broadcast together with
   shapes (968,) (2,)`. En el recorte real de `img100` Hough devolvía 54 picos,
   así que el caso `n = 1` era una casualidad.

### Requirement 10: Barrido de dos escalas para recortes holgados

**User Story:** Como usuario, quiero recortar con margen alrededor del círculo
y que el radio se siga encontrando, sin tener que ajustar el recorte al borde.

#### Acceptance Criteria

1. THE barrido automático SHALL recorrer `[0.08·r0, r0]` con un paso
   proporcional a `r0` (grueso) y refinar después los candidatos gruesos mejor
   separados con un paso absoluto pequeño (fino).
2. THE refinamiento SHALL evaluar al menos **dos** candidatos gruesos
   separados, porque decidir a resolución gruesa es frágil: en el recorte
   holgado de `img100` el margen grueso era **1.17:1** (68 votos al disco
   frente a 58 al texto) y al refinar queda **2.6:1** (211 frente a 80).
3. THE ambigüedad SHALL calcularse entre estructuras ya refinadas y distintas,
   no entre radios vecinos de la rejilla gruesa.
4. Evidencia (recorte de 2288 × 2000 que incluye el disco **y** el texto,
   `r/r0 = 0.428`, 10 028 bordes): radio **428.0** frente a 428.31 real (error
   **0.31 px**), ambigüedad 0.38, **10.9 s**. Cadena completa: diámetro 855.70
   frente a 856.61 real, centro a 0.29 px. Con la banda anterior
   `[0.6·r0, r0]` el círculo quedaba fuera y el barrido no lo encontraba.
5. Limitación declarada: el diámetro del círculo SHALL ser al menos el **8%**
   del lado menor del recorte para caer dentro de la banda. Por debajo, no se
   encuentra; el campo de diámetro (R6) permite declararlo a mano.
6. WHEN `r0` no es finito o no es positivo, THEN SHALL lanzar `ValueError`.
7. WHEN no hay bordes o ningún radio obtiene votos, THEN SHALL devolver
   `(0.0, 0, 0.0)` sin excepción, igual que R3.
