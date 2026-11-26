# Tarea: multi-trazo en ODIN (2+ trazos en una imagen completa)

Repo: `/home/jolopez/proyectos/ODIN`. Trabajás en `main` (`61396f2`, árbol `87cd329`).
Antes de escribir nada, leé `AGENTS.md` (reglas del proyecto) y `MEMORY.md` (ledger de estado actual).

## Objetivo

Hoy el controlador mide **un trazo por recorte**. En una imagen completa (p. ej.
`src/data/images/Lineas Servicio Micrometrologia/600mm_Imag0000.bmp`) hay dos o más trazos y
solo se mide el que cae dentro del rectángulo arrastrado. Extender a multi-trazo: detectar
todos los trazos presentes y medir ancho y centro de cada uno.

## Estado actual que necesitás conocer

- `src/odin/Ajustes/models/trazo_linea.py` ya resuelve **un** trazo: `separar_orillas` separa
  las dos orillas de un trazo por `signo(gradiente · normal)` y `medir_trazo(puntos, gx, gy, theta)`
  devuelve un `MedicionTrazo` (linea_a, linea_b, ancho, centro). Port de `CodigoMatlab/separaPuntos.m`.
- `src/odin/controllers/main_controller.py`, rama recta (`_rama_recta`), es el punto de integración.
- `src/odin/Procesamiento/models/hough_lineas.py` produce las rectas candidatas.
- El clasificador círculo/recta vive en `src/odin/Procesamiento/models/geometria.py`.

## Cómo encararlo (ODD, obligatorio)

1. **Documento de tarea primero:** creá `odd/tasks/multi-trazo.md` con la estructura que ya usan
   los demás (`odd/tasks/linea-gruesa.md` es el modelo a copiar): encabezado de 2-3 líneas,
   `## Specs` con requisitos numerados `S#` que citen textualmente lo pedido, `## Tasks` con una
   línea por tarea (ID, `S#` que cubre, ruta, commit), y `## Log` al final donde `L1` es este
   pedido textual. Avisá en una línea cuántas tareas quedaron.
2. **TDD:** un test en RED por cada regla pedida, después GREEN. Nada de tests escritos después.
3. **Modelos puros:** `models/` no importa `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`; sin bucles
   anidados por píxel (broadcasting, máscaras, `scipy.ndimage`). Entrá por los alias públicos de
   `Ajustes/__init__.py` / `Procesamiento/__init__.py`, nunca por el archivo de algoritmo.
4. **Idioma:** identificadores, comentarios, docstrings y mensajes en **español** (AGENTS.md §6.4).
5. Commits por unidad revisable (~400 líneas), en rama propia creada desde `main`; mensaje
   `<tipo>(<scope>): <descripción en español>`.

## Entrega

- Push dual: `git push github <rama>` **y** `git push azure <rama>` (no existe `origin` útil: apunta a Azure).
- PR contra `main` en ambos: `gh pr create --repo JoseloCelis/ODIN --base main ...` y
  `az repos pr create --organization https://dev.azure.com/JoseloCelis --project ODIN --repository ODIN`.
- **Nunca** `--delete-branch` ni `--delete-source-branch true`: borrar la base cierra el PR hijo.
- Esperá los checks `test` y `security`; mergeá y verificá que `github/main^{tree}` == `azure/main^{tree}`
  **y** que el contenido esté en `main` (`git show github/main:<ruta>`). El estado MERGED no lo prueba.
- Cerrá con `Risk: item N (motivo)` o `Risk: none` según la lista de riesgos.

## Verificación funcional

Además de `python3 -m pytest tests -q`, probá con la imagen real y reportá los anchos y centros
obtenidos por trazo. Baseline actual: **397 passed, 1 skipped, 1 falla preexistente** en
`test_geometria_prop.py::test_prop_invariancia_rotacion_y_reflexion` (residuales empatados, ajena
a esta tarea: no la "arregles" cambiando el clasificador).

## Trampas conocidas

- El hook de pre-commit corre GGA (`.gga` ya tiene `OPENCODE_AGENT="gga-reviewer"`, que fija la
  regla de idioma y el contrato `STATUS:`). Debe dar PASSED. Sus citas de línea son imprecisas:
  verificalas antes de obedecer.
- `CodigoMatlab/` **no se versiona** (decisión del usuario): es solo referencia de lectura.
- `src/odin/views/interactive_viewer.py` es una copia **sin uso** de `VisualizadorInteractivo`;
  la clase viva es la de `handleImage.py`.

## Si GGA vuelve a pedir inglés

El perfil que lo evita es `~/.config/opencode/agent/gga-reviewer.md`: fija la regla de idioma del
proyecto (AGENTS.md §6.4, español) y el contrato `STATUS: PASSED|FAILED`. Hace falta porque
`~/.config/opencode/AGENTS.md` (global, líneas 30 y 33) impone «Default to English» para artefactos
técnicos, y el modelo aplicaba esa regla en lugar de la del proyecto — llegó a pedir lo contrario
en dos intentos seguidos. Respaldo y pasos de vuelta atrás:
`~/.config/opencode/backups/gga-20261124/` (`RESTAURAR.md`, el `AGENTS.md` global intacto,
`opencode.json.orig` y `gga.actual`). Si GGA pide traducir identificadores al inglés, **no
obedezcas**: verificá que `.gga` tenga `OPENCODE_AGENT="gga-reviewer"` y que ese archivo exista.
