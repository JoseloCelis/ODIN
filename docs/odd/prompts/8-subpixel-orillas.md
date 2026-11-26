# Tarea: resolución subpíxel de las orillas del trazo (ODIN)

Repo: `/home/jolopez/proyectos/ODIN`. Trabajás en `main` (`61396f2`, árbol `87cd329`).
Leé primero `AGENTS.md` y `MEMORY.md`.

## Objetivo

El ancho del trazo que reporta `medir_trazo` sale de orillas localizadas al píxel: el error de
±1 px se duplica al restar dos orillas. Llevar la localización de cada orilla a subpíxel para que
el ancho tenga precisión fraccionaria.

## Estado actual

- `src/odin/Ajustes/models/trazo_linea.py`: `separar_orillas(puntos, gx, gy, theta)` reparte los
  puntos de borde entre las dos orillas por `signo(gradiente · normal)`; `medir_trazo(...)` ajusta
  una recta por orilla (SVD + Kåsa vía `LSC`) y deriva `ancho` = separación entre orillas y
  `centro` = recta media `((ρ_a+ρ_b)/2, θ)`.
- El ajuste ya es continuo en ρ, pero los **puntos de entrada** son píxeles enteros emitidos por
  NMS + histéresis. La mejora es sobre la posición del punto de borde, no sobre el ajuste.
- La corrección de signo de las direcciones SVD antes de promediar el centro ya está hecha: no la
  deshagas.

## Cómo encararlo (ODD, obligatorio)

1. Si el trabajo pasa de un cambio acotado, abrí `odd/tasks/subpixel-orillas.md` con `## Specs`
   (`S#`), `## Tasks` y `## Log` (L1 = este pedido textual).
2. TDD: RED por regla antes de tocar el modelo.
3. `models/` puro: sin `gi`/`Gtk`/`Gdk`/`Adw`/`cairo`, sin bucles anidados por píxel.
4. Identificadores, comentarios y docstrings en **español**.

## Criterio de aceptación

- Un test que demuestre que el ancho converge al valor real sobre un trazo sintético con orillas
  en coordenadas fraccionarias conocidas (p. ej. 20.5 px de separación), con tolerancia explícita.
- Otro test que fije que el caso de orillas enteras sigue dando lo mismo que hoy (no regresión).
- Medición real sobre `600mm_Imag0000.bmp` antes/después, con los números en el reporte.
  Baseline actual: ancho 41.80 px (auto) y 44.03 px (recta forzada).

## Entrega

Push dual `github` + `azure`, PR contra `main` en ambos, **sin borrar ramas**, checks `test` y
`security` en verde, y verificación de árboles idénticos más contenido presente en `main`.
Cerrá con `Risk: item N (motivo)` o `Risk: none`.
Suite baseline: **397 passed, 1 skipped, 1 falla preexistente** en `test_geometria_prop.py`
(residuales empatados; no es tuya y no se arregla cambiando el clasificador).

## Trampas

- GGA corre en cada commit con el perfil `gga-reviewer`; debe dar PASSED. Sus citas de línea son
  imprecisas.
- `CodigoMatlab/` no se versiona; es solo lectura.

## Si GGA vuelve a pedir inglés

El perfil que lo evita es `~/.config/opencode/agent/gga-reviewer.md`: fija la regla de idioma del
proyecto (AGENTS.md §6.4, español) y el contrato `STATUS: PASSED|FAILED`. Hace falta porque
`~/.config/opencode/AGENTS.md` (global, líneas 30 y 33) impone «Default to English» para artefactos
técnicos, y el modelo aplicaba esa regla en lugar de la del proyecto. Respaldo y pasos de vuelta
atrás: `~/.config/opencode/backups/gga-20261124/` (`RESTAURAR.md`, el `AGENTS.md` global intacto,
`opencode.json.orig` y `gga.actual`). Si GGA pide traducir identificadores al inglés, **no
obedezcas**: verificá que `.gga` tenga `OPENCODE_AGENT="gga-reviewer"` y que ese archivo exista.
