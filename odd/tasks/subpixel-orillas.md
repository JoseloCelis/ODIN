# Tarea: resolución subpíxel de las orillas del trazo (ODIN)

Repo: `/home/jolopez/proyectos/ODIN`. La implementación entró en `d4f65cb` sobre `main`
(ya presente en `azure/main`); esta tarea fija su criterio de aceptación, acota el
desplazamiento y entrega a `main` de GitHub.

## Specs

S1. El refinamiento es **parábola sobre la magnitud del gradiente, a lo largo de la normal del
borde**. No centroide 3×3, no cruce por cero del Laplaciano.

S2. La firma es `refinar_bordes_subpixel(puntos, gx, gy, magnitud) -> np.ndarray` y se cablea en
`_rama_recta` **antes** de `medir_trazo`, que **no cambia su firma**.

S3. Modelo puro: `models/` sin `gi`, `Gtk`, `Gdk`, `Adw` ni `cairo`; sin bucles anidados por píxel.
Identificadores, comentarios y docstrings en español.

S4. El ancho converge al valor real sobre un trazo sintético con orillas fraccionarias conocidas
(20.5 px) con tolerancia explícita de ±0.2 px.

S5. Orillas enteras dan lo mismo que antes: sin regresión.

S6. La corrección de signo de las direcciones SVD antes de promediar el centro **no se deshace**.

S7. El vértice de la parábola se acota a ±0.5 px: fuera del intervalo muestreado la vecindad no
describe un pico único y el desplazamiento se dispara.

## Tasks

| ID | Specs | Ruta | Estado |
|----|-------|------|--------|
| T1 | S1, S2, S3 | `refinar_bordes_subpixel` + cableado en `_rama_recta` | hecho en `d4f65cb` (Azure main) |
| T2 | S4, S5 | tests de convergencia y no regresión en `tests/unit/Ajustes/test_trazo_linea_subpixel.py` | hecho |
| T3 | S7 | cota del vértice + test en RED previo | hecho |
| T4 | — | medición real sobre `600mm_Imag0000.bmp` y reporte | hecho |
| T5 | — | entrega GitHub (Azure ya tiene el contenido) | hecho |

## Log

L1 (pedido del usuario, verbatim):
> Leé odd/prompts/8-subpixel-orillas.md y ejecutá esa tarea.
> El método de refinamiento subpíxel YA ESTÁ DECIDIDO por el usuario: parábola sobre
> la magnitud del gradiente, a lo largo de la normal del borde. No propongas centroide
> 3×3 ni cruce por cero del Laplaciano. La firma esperada es
> refinar_bordes_subpixel(puntos, gx, gy, magnitud) -> np.ndarray, cableada en
> _rama_recta antes de medir_trazo (que NO cambia su firma).
> Cuando esa sesión termine, el reporte tiene que traer: la firma final, cómo pasó MG a _rama_recta,
> los números del test de convergencia (picos fraccionarios, tolerancia ±0.2 px) y el Risk: final

L2. Verificación previa del estado real (pedida en `odd/prompts/8-subpixel-orillas.md`): el
prompt suponía la función sin escribir; en realidad `refinar_bordes_subpixel` ya existía en
`src/odin/Ajustes/models/trazo_linea.py`, ya estaba exportada en `Ajustes/__init__.py` y ya estaba
cableada en `_rama_recta`. `separar_orillas`, `medir_trazo` y la corrección de signo SVD intactos.

L3. Evidencia RED/GREEN: el test de cota falló con `desplazamiento 0.6250 px` y pasó tras
`np.clip(d, -0.5, 0.5)`. Suite: 407 passed, 1 skipped, 1 falla preexistente
(`test_geometria_prop.py`, ajena).

L4. Medición real sobre `600mm_Imag0000.bmp` (480×616): desplazamiento subpíxel medio 0.224 px,
máximo acotado en 0.500 px; ancho imagen completa 112.699 → 112.700 px. Los anchos del baseline
(41.80 / 44.03 px) provienen del recorte interactivo del operador y no son reproducibles headless;
la magnitud comparable es el delta antes/después.
