# Deuda 4 — el registro va por logging, no por stdout

Cierra la deuda de registro: `print` fuera de `src/odin/` y trazas de interacción que hoy se
pierden o inundan la salida estándar. Doc: `MEMORY.md`; deuda original registrada el 2026-11-21.

## Specs

S1. **Ningún módulo de `src/odin/` escribe por stdout.** El registro va por
`logging.getLogger(__name__)`, que es la convención ya establecida en
`src/odin/utils/handleImage.py:11` (`registro = logging.getLogger(__name__)`) y respaldada por la
configuración de `bootstrap.py`.

S2. **El contenido del registro se conserva.** Cada mensaje mantiene los mismos datos que el
`print` que reemplaza, y los etiqueta. Se elimina solo lo que no aporta diagnóstico: valores
desnudos sin etiqueta.

S3. **`draw_callback` no registra por fotograma.** Se invoca en cada repintado, y durante un
arrastre eso es un mensaje por movimiento del ratón. Un registro por fotograma es una inundación,
no una traza.

S4. **Niveles.** `debug` para trazas de interacción (recorte, ajuste, inicio de convoluciones),
`info` para resultados del pipeline (ruta, bordes, geometría, recta, trazo, radio), `error` para
fallos.

S5. **Español y tipado.** Identificadores, comentarios y mensajes en español (AGENTS.md §6.4).
Las firmas nuevas o modificadas llevan anotaciones de tipo.

## Tasks

| # | Specs | Qué | Ruta | Commit |
|---|-------|-----|------|--------|
| T1 | S1-S5 | Vistas: quitar el `print` por fotograma del visor, registrar el recorte y el valor del ajuste | `src/odin/views/interactive_viewer.py`, `src/odin/views/main_window.py` | `037db96` |
| T2 | S1-S5 | Controlador: los `print` operativos al logger con su nivel | `src/odin/controllers/main_controller.py` | `037db96` |

Verificación: `tests/unit/test_registro_sin_stdout.py`, ya escrito en RED (3 fallas).

## Log

L1. Pedido del usuario, verbatim: «Me referia que siguieras con el punto 4 para despues cerrar la
sesion» y «No olvides delegar, usar skills y RDD».

L2. Inventario al abrir la tarea (2026-11-25): el `print` de `handleImage.py:196` que pedía la
deuda **ya no existe** (lo retiró `fix/registro-y-recorte-handleimage`, PR #36). Quedan 13 en
`src/`: 9 en `main_controller.py`, 2 en `main_window.py` (`:336` valor desnudo del ajuste, `:554`
banner `ODIN 1.0`) y 2 en `interactive_viewer.py` (`:74` recorte, `:89` **cuatro valores desnudos
dentro de `draw_callback`**, invocado en cada repintado). El defecto que el usuario describía como
«dimensiones que no son las procesadas» es ese: imprime `width, height` de la asignación del widget
junto a `alto, ancho` de la selección, sin etiquetas.
