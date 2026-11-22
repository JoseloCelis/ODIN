# Absorción de `.kiro/specs` en ODD

Documentación únicamente: no se toca código de producción.

## Specs

- **S1 — Nada se borra.** Los 9 directorios de `.kiro/specs/` y sus tres archivos
  (`requirements.md`, `design.md`, `tasks.md`) se conservan, versionados. La
  absorción no elimina ni mueve el original.

- **S2 — El texto de un requisito no se reescribe.** Las citas se preservan
  verbatim. Corregir el texto de un requisito para que coincida con el código
  borra la evidencia de qué se especificó y cuándo: eso es falsificar el
  registro, no corregirlo. **Alcance:** aplica a los requisitos de
  `requirements.md` y a los enunciados de `design.md`. Una casilla `[x]`/`[ ]`
  de `tasks.md` no es un requisito: es el **estado** de una tarea, y un estado
  falso se corrige en el lugar donde está, no se deja mintiendo.

- **S3 — Todo spec declara su estado en sus tres archivos.** Al inicio de
  `requirements.md`, `design.md` y `tasks.md` de cada uno de los 9 specs va un
  bloque con: veredicto (`ABSORBIDO` / `ARCHIVADO`), ruta de la versión ODD
  cuando exista, requisitos implementados con evidencia `archivo:línea`,
  requisitos **PENDIENTES**, divergencias conocidas, y la fecha del veredicto.
  Un spec sin este bloque miente por omisión, y un `tasks.md` que declara
  pendiente lo que el código ya tiene miente igual que un `requirements.md`
  desactualizado. El bloque va delimitado por `<!-- ESTADO:INICIO -->` y
  `<!-- ESTADO:FIN -->` para que sea separable del cuerpo de forma mecánica.
  Un requisito que no se pudo verificar se declara `INCIERTO`: nunca se completa
  por inferencia.

- **S4 — Un requisito no implementado se declara PENDIENTE**, nunca se presenta
  como cumplido. Aplica a R4.1/R4.2/R4.6 (límites de 2s/3s) y a
  `kernel-separable` R6 (`wc=640`), que nunca se implementaron.

- **S5 — Toda divergencia entre lo que un spec afirma y lo que el código hace**
  se registra en el bloque de estado del spec que la posee, con evidencia
  `archivo:línea`. Solo se registran divergencias **verificadas contra el código
  en esta ejecución**: una divergencia recordada de memoria no se escribe, porque
  el bloque de estado no puede mentir en nombre de la honestidad. Candidatas a
  verificar: el pipeline cubre etapas 1→5 en los tests y no 1→9; la banda
  `[0.6·r0, r0]` de `find-circle` es una contradicción spec-vs-código, no un
  docstring mentiroso.

- **S6 — Los ABSORB se escriben en `odd/specs/<slug>.md`** citando verbatim
  los requisitos absorbidos. Tras la re-verificación (L7) son **9 de 9**:
  `kernel-separable`, `mag-fase`, `otsu-rosin`, `edge-track-hyst`,
  `hough-circles`, `find-circle`, `non-max-sup`, `circulo-simple`,
  `odin-startup-structure`.

- **S7 — No hay specs ARCHIVADOS.** Los dos que la auditoría previa marcó como
  ARCHIVE (`non-max-sup`, `circulo-simple`) tienen módulo vivo y requisitos
  accionables: el primero contradice al código en R1.1/R2.1
  (`non_max_sup.py:64-67,78-80`), el segundo contradice en R1.6
  (`circulo_simple.py:55` lanza `TypeError` donde el spec exige `ValueError`).
  El veredicto previo se emitió antes de re-verificar y no se sostiene.

- **S8 — `odd/specs/` se versiona.** Hoy `.gitignore` excluye `odd/` entero, así
  que un spec escrito ahí se pierde en silencio. Hay que extender la regla
  (mismo patrón de negación que usan las tareas) antes de escribir nada.

- **S9 — Un índice único** en `odd/specs/README.md` con la tabla de los 9 specs,
  su veredicto y el enlace a la versión ODD. Es el punto de entrada para saber
  qué está vigente sin abrir nueve documentos.

- **S10 — Los tres archivos quedan pinneados con dos hashes, y eso se prueba.**
  Un manifiesto `odd/specs/.originales.sha256` guarda **dos** hashes por archivo
  (`requirements.md`, `design.md` y `tasks.md` de cada spec):

  - `cuerpo` — todo lo que queda **fuera** del bloque delimitado. Protege el
    texto del requisito: si alguien lo reescribe, el test falla nombrando el
    archivo y la causa. Es lo que le da dientes automáticos a S2.
  - `archivo` — el archivo **completo**, bloque de estado incluido. Protege la
    cabecera: si cambia, hay que actualizar el hash en el mismo commit.

  Un solo hash no alcanza: con el bloque adentro no se distingue "actualicé el
  estado" de "reescribí un requisito", y S2 quedaría sin verificación
  automática. Con los dos, toda modificación no declarada rompe al menos uno.

  **Cómo convive con S2 y S12:** el manifiesto no prohíbe corregir, exige que la
  corrección sea visible. Una casilla o un bloque corregido mueve `archivo`; un
  requisito reescrito mueve también `cuerpo`. El hash se actualiza **en el mismo
  commit** que la corrección, S12 registra por qué, y el diff muestra qué cambió.
  El manifiesto no es "estos archivos nunca cambian": es "ningún cambio pasa sin
  que alguien lo declare, y un requisito reescrito no se puede disfrazar de
  actualización de estado".

  El test no lee historia de git ni un commit fijo; compara contra el manifiesto
  versionado. **Orden:** el manifiesto se genera después de T3, porque los
  bloques de estado cambian `archivo`; generarlo antes haría fallar el test al
  insertarlos. El hash `cuerpo` de ese momento pasa a ser la referencia de S2.

- **S12 — Toda casilla corregida queda registrada.** Cada corrección de
  `tasks.md` se anota en el bloque de estado de ese archivo con el valor
  anterior, el nuevo, la evidencia `archivo:línea` y la fecha. Corregir sin
  registrar borraría el hecho de que el documento estuvo mal, que es información
  tan valiosa como la corrección.

- **S11 — Los veredictos se re-verifican contra el código actual.** ABSORBIDO
  exige al menos un requisito accionable hoy, verificable contra un módulo vivo
  (que lo cumpla o que lo contradiga de forma accionable). ARCHIVADO aplica
  cuando ningún requisito es accionable: el módulo no existe o el requisito ya
  quedó cubierto por otra spec. Un veredicto emitido antes de que el código
  cambiara no vale por sí solo.

## Tasks

| ID | Specs | Alcance |
|----|-------|---------|
| T1 | S8 | Extender `.gitignore` para versionar `odd/specs/*.md` — **hecho** |
| T2 | S11 | Re-verificar los 9 veredictos contra el código actual — **hecho**, ver L7 |
| T3 | S3, S4, S5 | Bloque de estado en los **tres** archivos de cada spec, con evidencia y PENDIENTES — **hecho** |
| T4 | S9 | Escribir `odd/specs/README.md` con la tabla de los 9 specs |
| T5 | S6 | Absorber los 7 ABSORB en `odd/specs/<slug>.md` con citas verbatim |
| T6 | S7 | Marcar los 2 ARCHIVE como superados con su motivo |
| T7 | S10 | Manifiesto con **dos** hashes por archivo (`cuerpo` y `archivo`) y test que distinga un requisito reescrito de una actualización de estado (después de T3) |
| T8 | S2, S12 | Corregir las casillas falsas de los `tasks.md` y registrar cada corrección |

## Log

- **L1 (pedido original, verbatim):** «Entiendo que la todo #14 no borrara .kiro/ ?
  se absorbera dentro de ODD pero SDD quedara como historio, obvio corregido hasta
  donde le toca. ¡Estoy en lo cierto?»

- **L2 (corrección del usuario, verbatim):** «Estoy de acuerdo con todo lo que
  mencionasa con respecto "hasta donde le toca". no me refiero a tocar codigo.
  pero que las .kiro/specs sean congruentes con lo que les toca y no mientan.»

- **L3 (decisión derivada de L2):** la congruencia se logra declarando el estado
  del documento, no reescribiendo el requisito. Un spec histórico sin bloque de
  estado miente por omisión porque nada advierte que un requisito no está
  implementado. Esto reemplaza la postura anterior de «el .kiro no se edita»: el
  cuerpo no se edita, la cabecera sí se agrega.

- **L4 (operativo):** `odd/` no existe en `main`; los `odd/tasks/*.md` viven en
  `feat/migracion-lineas-geometria`. Por eso esta rama sale de `main` y
  re-crea la excepción de `.gitignore` en vez de depender de la rama de fase 1,
  que arrastraría 4385 líneas a un PR de documentación.

- **L5 (revisión del usuario, cuatro respuestas verbatim):** «1. en todos.
  2. que nada mienta. 3. test automatizado. 4. reverificalo».

- **L6 (decisiones derivadas de L5):** (1) el bloque de estado va en
  `requirements.md`, `design.md` y `tasks.md`, porque los tres afirman cosas que
  pueden estar desactualizadas; (2) no se escribe ninguna divergencia que no se
  haya verificado contra el código en esta ejecución — la lista de S5 baja a
  "candidatas"; (3) la verificación de S1/S2 deja de ser una intención y pasa a
  ser un test con manifiesto de hashes (S10, T7), sin leer historia de git;
  (4) los 9 veredictos se re-verifican contra el código actual antes de absorber
  nada (S11, T2).

- **L7 (resultado de T2, 9 specs re-verificados contra el código):**
  **los 9 son ABSORBIDO**, no 7. La auditoría previa falló en dos:
  `non-max-sup` (R1.1/R2.1 contradichos en `non_max_sup.py:64-67,78-80`) y
  `circulo-simple` (R1.6 contradicho en `circulo_simple.py:55`). Ambos tienen
  módulo vivo y requisito accionable, que es lo que S11 exige.

- **L8 (divergencias candidatas, resueltas):** **A es CIERTA** —
  `tests/integration/test_pipeline.py:24-31` encadena etapas ①-⑤ y no incluye
  ⑥-⑨. **B es FALSA** — la banda `[0.6·r0, r0]` no pertenece a `find-circle`:
  aparece en `hough-circles/requirements.md:80,190`, donde ya está declarada
  descartada, y el código barre `[0.08·r0, r0]` (`hough_circles.py:188`).
  `find_circle.py` no trabaja con `r0`. Queda descartada: no entra a ningún
  bloque de estado.

- **L9 (engaños en `tasks.md`, para T4):** hay casillas marcadas hechas sobre
  código que no existe o no hace lo que dice. Los más graves están en
  `odin-startup-structure/tasks.md`: 10.1/10.2 piden aliases en
  `src/odin/__init__.py`, que es solo un docstring; 12.2 se autodesmiente en su
  propio Log; 14 y 16 están `[x]` con pendientes declarados; 15.1 está `[ ]`
  pero `--version` ya existe (`main_window.py:479-491`). También
  `hough-circles` T5 ("no se borran" cuando ya fueron eliminados) y
  `kernel-separable` T4 (`dibujar_en_hilo_principal` no existe).

- **L10 (límite de la evidencia):** el explorador no ejecutó la suite. Las filas
  marcadas `INCIERTO` (kernel R3/R4 sin cross-check contra OpenCV ni contra
  `tests/utilidades.py`; startup R5.5 codec de stdout) y las marcadas
  "test, no ejecutado" se escriben como tales en los bloques de estado. No se
  convierten en IMPLEMENTADO por inferencia.

- **L11 (decisión del usuario, verbatim):** «mejor corrígela». La casilla falsa
  se corrige en el lugar; no alcanza con declararla en el bloque de estado.

- **L12 (correcciones a S2/S10 y verificaciones propias):** como corregir una
  casilla edita `tasks.md`, S2 se acota a los requisitos y enunciados, y
  `tasks.md` sale del manifiesto de hashes de S10. Para no borrar el hecho de
  que el documento estaba mal, se agrega S12. Las cinco afirmaciones se
  verificaron de forma independiente antes de corregir: `src/odin/__init__.py`
  tiene 1 línea sin aliases; `--version` existe en `main_window.py:480`;
  `dibujar_en_hilo_principal` da 0 hits; `def houghCircles`/`houghpeaks`/
  `imregionalmax` dan 0 hits; y el Log del propio
  `odin-startup-structure/tasks.md` dice «Pendiente 12.2», «Pendiente 14» y
  «Pendiente 16» (`:403,406,409`), contradiciendo sus casillas `[x]`.

- **L13 (decisión del usuario, verbatim):** «prefiero que el manifiesto cubra
  task.md». Cambia S10: el manifiesto cubre los tres archivos, no dos.

- **L14 (por qué L13 mejora el diseño):** dejar `tasks.md` fuera del manifiesto
  dejaba las correcciones invisibles y la protección a medias. Cubriéndolo, toda
  corrección mueve el hash y el hash se actualiza en el mismo commit: el diff
  muestra qué cambió y S12 registra por qué. El manifiesto pasa de "no cambies"
  a "no cambies sin declararlo", que es una garantía más fuerte y compatible con
  S2 y S12. Consecuencia de orden: T7 se ejecuta **después** de T3.

- **L15 (decisión del usuario, verbatim):** «si dale con t3, para que los bloques
  de estado no queden fuera del hash».

- **L16 (por qué son dos hashes y no uno):** meter el bloque en el hash único
  cumple L15 pero deja el hash incapaz de distinguir una actualización de estado
  de un requisito reescrito, y S2 perdería su verificación automática. Se usa un
  hash del `cuerpo` (lo de fuera del bloque) y otro del `archivo` completo: L15
  queda cumplido y S2 conserva dientes.
