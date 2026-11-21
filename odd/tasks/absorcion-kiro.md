# Absorción de `.kiro/specs` en ODD

Documentación únicamente: no se toca código de producción.

## Specs

- **S1 — Nada se borra.** Los 9 directorios de `.kiro/specs/` y sus tres archivos
  (`requirements.md`, `design.md`, `tasks.md`) se conservan, versionados. La
  absorción no elimina ni mueve el original.

- **S2 — El cuerpo de un requisito no se reescribe.** Las citas se preservan
  verbatim. Corregir el texto de un requisito para que coincida con el código
  borra la evidencia de qué se especificó y cuándo: eso es falsificar el
  registro, no corregirlo.

- **S3 — Todo spec declara su estado.** Al inicio de `requirements.md` de cada
  uno de los 9 specs va un bloque con: veredicto (`ABSORBIDO` / `ARCHIVADO`),
  ruta de la versión ODD cuando exista, requisitos implementados con evidencia
  `archivo:línea`, requisitos **PENDIENTES**, divergencias conocidas, y la fecha
  del veredicto. Un spec sin este bloque miente por omisión.

- **S4 — Un requisito no implementado se declara PENDIENTE**, nunca se presenta
  como cumplido. Aplica a R4.1/R4.2/R4.6 (límites de 2s/3s) y a
  `kernel-separable` R6 (`wc=640`), que nunca se implementaron.

- **S5 — Toda divergencia entre lo que un spec afirma y lo que el código hace**
  se registra en el bloque de estado del spec que la posee, con evidencia
  `archivo:línea`. Divergencias ya confirmadas: el pipeline cubre etapas 1→5 en
  los tests y no 1→9; la banda `[0.6·r0, r0]` de `find-circle` es una
  contradicción spec-vs-código, no un docstring mentiroso.

- **S6 — Los 7 ABSORB se escriben en `odd/specs/<slug>.md`** citando verbatim
  los requisitos absorbidos: `kernel-separable`, `mag-fase`, `otsu-rosin`,
  `edge-track-hyst`, `hough-circles`, `find-circle`, `odin-startup-structure`.

- **S7 — Los 2 ARCHIVE se marcan superados** con el motivo, sin absorber su
  contenido: `non-max-sup`, `circulo-simple`.

- **S8 — `odd/specs/` se versiona.** Hoy `.gitignore` excluye `odd/` entero, así
  que un spec escrito ahí se pierde en silencio. Hay que extender la regla
  (mismo patrón de negación que usan las tareas) antes de escribir nada.

- **S9 — Un índice único** en `odd/specs/README.md` con la tabla de los 9 specs,
  su veredicto y el enlace a la versión ODD. Es el punto de entrada para saber
  qué está vigente sin abrir nueve documentos.

## Tasks

| ID | Specs | Alcance | Commit |
|----|-------|---------|--------|
| T1 | S8 | Extender `.gitignore` para versionar `odd/specs/*.md` | pendiente |
| T2 | S9 | Escribir `odd/specs/README.md` con la tabla de los 9 specs | pendiente |
| T3 | S3, S4, S5 | Bloque de estado en los 9 `requirements.md`, con evidencia y PENDIENTES | pendiente |
| T4 | S6 | Absorber los 7 ABSORB en `odd/specs/<slug>.md` con citas verbatim | pendiente |
| T5 | S7 | Marcar los 2 ARCHIVE como superados con su motivo | pendiente |
| T6 | S1, S2 | Verificar que ningún requisito fue reescrito y que nada se borró | pendiente |

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
