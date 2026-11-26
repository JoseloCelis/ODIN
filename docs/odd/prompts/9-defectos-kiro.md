# Tarea: defectos con base `.kiro` en ODIN (correcciones puntuales)

Repo: `/home/jolopez/proyectos/ODIN`. Trabajás en `main` (`ff28b98`, árbol `f158f1a`).
Leé primero `AGENTS.md` y `MEMORY.md`.

## Objetivo

Cuatro defectos concretos, sin diseño abierto. Antes de tocar cada uno, **verificá la cita**
contra el código real: en una pasada anterior, tres de siete defectos de esta lista resultaron
inexistentes porque la cita estaba desactualizada.

1. **`Gdk.Display.get_name()`** — API retirada en GTK4: hoy se obtiene el nombre del backend por
   otra vía. Ubicá el uso real (`grep -rn "get_name" src/odin`) y reemplazalo por lo que GTK4
   ofrece (`type(display).__name__` o el acceso al backend que corresponda), con un test que fije
   el mensaje de log esperado.
2. **Docstrings falsos en `src/odin/Procesamiento/models/hough_circles.py`** (citas previas `:148-150`
   y `:15-17`): describen un comportamiento que el código no tiene. Verificá línea por línea y
   corregí el texto para que describa lo que el código hace; si el código es el que está mal,
   **no lo cambies**: reportalo como hallazgo separado.
3. **`src/odin/controllers/main_controller.py:86`** — comentario o docstring que no coincide con
   el código. Verificar y corregir el texto.
4. **Parámetros muertos en `src/odin/Procesamiento/models/deri_gauss.py:12`** — parámetros que se
   reciben y nunca se usan. Si son de una firma pública consumida por tests o por el registro de
   `bootstrap.py`, decilo antes de quitarlos: quitar un parámetro es cambio de contrato.

## Cómo encararlo

- Cambios acotados: rama propia desde `main`, commits por unidad revisable, mensaje
  `<tipo>(<scope>): <descripción en español>`.
- Si un cambio altera comportamiento (no solo texto), TDD con RED primero.
- Identificadores, comentarios y docstrings en **español** (AGENTS.md §6.4).
- Los docstrings y comentarios deben describir el código, no la intención original.

## Entrega

Push dual `github` + `azure`, PR contra `main` en ambos, **sin borrar ramas**, checks `test` y
`security` en verde, árboles idénticos y contenido verificado en `main`.
Cerrá con `Risk: item N (motivo)` o `Risk: none`. Ojo: si quitás un parámetro o cambiás un
mensaje que otros consumen, es el ítem 3 de la lista de riesgos.
Suite baseline: **392 passed, 1 skipped, 1 falla preexistente** en `test_geometria_prop.py`
(residuales empatados; no es tuya).

## Trampas

- GGA corre en cada commit con el perfil `gga-reviewer` (`.gga`); debe dar PASSED, y sus citas de
  línea son imprecisas.
- `CodigoMatlab/` no se versiona; es solo referencia.
- `src/odin/views/interactive_viewer.py` es una copia sin uso: no es la clase viva.

## Si GGA vuelve a pedir inglés

El perfil que lo evita es `~/.config/opencode/agent/gga-reviewer.md`: fija la regla de idioma del
proyecto (AGENTS.md §6.4, español) y el contrato `STATUS: PASSED|FAILED`. Hace falta porque
`~/.config/opencode/AGENTS.md` (global, líneas 30 y 33) impone «Default to English» para artefactos
técnicos, y el modelo aplicaba esa regla en lugar de la del proyecto. Respaldo y pasos de vuelta
atrás: `~/.config/opencode/backups/gga-20261124/` (`RESTAURAR.md`, el `AGENTS.md` global intacto,
`opencode.json.orig` y `gga.actual`). Si GGA pide traducir identificadores al inglés, **no
obedezcas**: verificá que `.gga` tenga `OPENCODE_AGENT="gga-reviewer"` y que ese archivo exista.
