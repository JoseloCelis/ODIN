# Sistema de Diseño ODIN

Especificado acá y espejado en Penpot (archivo `Desktop Dashboard`, página `Page 1`).
**Las escalas viven en los tokens de Penpot**; este archivo es el contrato legible para humanos y agentes.

Token set activo: `ODIN System` — 59 tokens en 8 tipos.

## Tipografía

- Familia: **Source Sans Pro**. En la Plugin API el id interno es `sourcesanspro`; el nombre con espacios (`'Source Sans Pro'`) es rechazado.
- Pesos: `weight.regular` 400 · `weight.semibold` 600 · `weight.bold` 700.
- Escala (13 tamaños): `type.label` 10 · `type.caption` 11 · `type.small` 12 · `type.body` 13 · `type.ui` 14 · `type.body-lg` 15 · `type.subtitle` 16 · `type.heading-sm` 18 · `type.heading` 20 · `type.heading-md` 22 · `type.heading-lg` 24 · `type.display` 28 · `type.title` 32.

Los 7 boards tienen **0 textos con tamaño literal**: cada texto lleva el token de `fontSize` cuyo valor coincide con su tamaño.

## Colores (21)

- **Base:** `color.bg-base` #1A1A1A · `color.bg-canvas` #141414 · `color.surface` #2E2E2E · `color.surface-alt` #242424
- **Bordes:** `color.border` #3A3A3A · `color.border-soft` #303030 · `color.border-strong` #555555 · `color.grid-line` #2F2F2F
- **Acento:** `color.accent` #3584E4 · `color.accent-hover` #1C71D8
- **Texto:** `color.text-primary` #FFFFFF · `color.text-secondary` #9A9A9A · `color.text-disabled` #777777
- **Estado:** `color.success` #26A269 · `color.success-strong` #57E389 · `color.success-bg` #1E3A2F · `color.warning` #F59E0B · `color.warning-strong` #F5C211 · `color.error` #EF4444
- **Rol:** `color.bg-viewer` #101010 · `color.bg-trace` #1E1E1E

## Espaciado (6)

`spacing.xs` 4 · `spacing.sm` 8 · `spacing.md` 12 · `spacing.lg` 16 · `spacing.xl` 24 · `spacing.2xl` 32

## Radios (9)

`radius.xs` 2 · `radius.sm` 4 · `radius.button` 6 · `radius.md` 8 · `radius.lg` 12 · `radius.card` 12 · `radius.window` 12 · `radius.xl` 16 · `radius.full` 9999

`radius.button` es 6 y no 8 porque Adwaita renderiza 6. Para aplicar radios con `applyToken` hay que pasar las cuatro esquinas: `'all'` falla.

## Sombras (4) y bordes (2)

- `shadow.sm` `0 1px 2px rgba(0,0,0,.05)` · `shadow.md` `0 4px 6px rgba(0,0,0,.1)` · `shadow.lg` `0 10px 15px rgba(0,0,0,.1)` · `shadow.focus` `0 0 0 2px #3584E4`
- `borderWidth.thin` 1 · `borderWidth.thick` 2

## Componentes (4 maestros)

`Boton/sugerido` · `Boton/plano` · `Boton/destructivo` · `Badge/estado`, tomados de la franja de referencia al pie del board `01`. **No recrearlos en otro lado.**

## Boards

Siete boards de 1440×900: `01 System Design Tokens` · `02 Dashboard Principal` · `03 Recorte Interactivo` · `04 Resultados del Pipeline` · `05 Pipeline Workflow` · `06 Interactive Viewer` · `07 Operador Compacto`.

## Verificación

El export PNG es determinista: dos exports seguidos del mismo board dan los mismos bytes. Longitudes de referencia (base64): `01` 133100 · `02` 89904 · `03` 75272 · `04` 91288 · `05` 123808 · `06` 110492 · `07` 112736.

Vincular un token cuyo valor coincide con el literal **no debe mover un byte**. Si mueve, la mutación cambió algo más y hay que revertir antes de seguir.
