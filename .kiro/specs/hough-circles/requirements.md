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
   buscar en `[0.6·r0, 1.0·r0]`.
2. Justificación medida: en el recorte con 15% de margen, `r0 = 556.0` y el
   radio real es 428.3 (r0 sobreestima 30%); el valor real cae dentro de la
   banda.
3. WHEN el recorte no contiene el círculo completo, THEN el resultado SHALL
   poder marcarse como no confiable (R5) en lugar de devolver un valor
   silenciosamente erróneo.

### Requirement 5: Reporte de ambigüedad

#### Acceptance Criteria

1. THE resultado del barrido SHALL indicar si la detección es ambigua, usando
   la relación `segundo_pico / primer_pico` con un umbral declarado en el
   diseño.
2. WHEN la detección es ambigua, THEN la interfaz SHALL mostrarlo antes de
   aceptar el valor, en lugar de presentar el diámetro como certero.

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
