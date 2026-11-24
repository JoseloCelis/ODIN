# Defectos con base `.kiro` en ODIN — cuatro correcciones puntuales

Rama: `fix/defectos-kiro-docstrings` (desde `main` ff28b98). Cuatro defectos sin diseño abierto; cada cita de línea fue re-verificada contra el código real porque `main` avanzó cuatro merges desde que se anotaron.

## Specs

- **S1** — «**`Gdk.Display.get_name()`** — API retirada en GTK4: hoy se obtiene el nombre del backend por otra vía. Ubicá el uso real (`grep -rn "get_name" src/odin`) y reemplazalo por lo que GTK4 ofrece (`type(display).__name__` o el acceso al backend que corresponda), con un test que fije el mensaje de log esperado.»
- **S2** — «**Docstrings falsos en `src/odin/Procesamiento/models/hough_circles.py`** (citas previas `:148-150` y `:15-17`): describen un comportamiento que el código no tiene. Verificá línea por línea y corregí el texto para que describa lo que el código hace; si el código es el que está mal, **no lo cambies**: reportalo como hallazgo separado.»
- **S3** — «**`src/odin/controllers/main_controller.py:86`** — comentario o docstring que no coincide con el código. Verificar y corregir el texto.»
- **S4** — «**Parámetros muertos en `src/odin/Procesamiento/models/deri_gauss.py:12`** — parámetros que se reciben y nunca se usan. Si son de una firma pública consumida por tests o por el registro de `bootstrap.py`, decilo antes de quitarlos: quitar un parámetro es cambio de contrato.»

## Tasks

- **T1** [S1] — Verificar `Gdk.Display.get_name()`. Route: inline (padre). RESULTADO: inexistente; `bootstrap.py:307` ya usa `type(display).__name__`. Sin cambio de código.
- **T2** [S2] — Corregir docstrings falsos en `hough_circles.py` (quitar bloque "código muerto" R8 ya eliminado; banda `[0.6·r0, r0]` → `[0.08·r0, r0]`, R10.1). Route: writer.
- **T3** [S3] — Corregir docstring de `resolver_radio` en `main_controller.py` (módulo `hough_circles`, no `houghCircles`; inyección vía `ModuleLoader`). Route: writer.
- **T4** [S4] — Quitar parámetros muertos `wk`/`wConv`/`wr` de `DerivGauss` y actualizar llamadores (`main_controller.py` + 6 archivos de tests). Cambio de contrato → Risk item 3. Route: writer.

## Log

- **L1** — «Leé el archivo odd/prompts/9-defectos-kiro.md y ejecutá esa tarea.»
- **L2** — Commits: `0c637f0` (T2+T3: docstrings falsos + traducción de mensajes de error y `"My App ODIN"` → `"ODIN"`, §6.4) y `da93de9` (T4: quitar parámetros muertos `wk`/`wConv`/`wr` de `DerivGauss`). Suite: 397 passed, 1 skipped, 1 falla preexistente (`test_geometria_prop.py::test_prop_invariancia_rotacion_y_reflexion`, residuales empatados). GGA PASSED en ambos commits.
