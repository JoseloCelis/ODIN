# Documentación ODD (Organic Driven Development)

Esta carpeta contiene la documentación de features desarrolladas bajo el proceso ODD.

## Índice

| Documento | Qué cubre |
|-----------|-----------|
| `tasks/4-deuda-registro.md` | Deuda 4: registro por logging, no stdout (S1-S5, T1-T2, commits `037db96` + `ea2260d`) |
| `tasks/8-trazo-por-picos.md` | Trazo entre orillas reales: región conexa, HWHM, selección por intensidad |
| `tasks/subpixel-orillas.md` | Refinamiento subpíxel (±0.5 px, parábola sobre magnitud del gradiente) |
| `tasks/absorcion-kiro.md` | Absorción de specs Kiro a ODD |
| `tasks/reverificacion-kiro.md` | Reverificación de specs absorbidos |
| `tasks/migracion-lineas-geometria.md` | Migración de geometría a líneas |
| `tasks/linea-gruesa.md` | Trabajo sobre línea gruesa |
| `tasks/pipeline-sweep.md` | Barrido del pipeline |
| `tasks/9-defectos-kiro.md` | Defectos encontrados en specs Kiro |
| `prompts/7-multi-trazo.md` | Prompt: multi-trazo |
| `prompts/8-subpixel-orillas.md` | Prompt: subpíxel de orillas |
| `prompts/9-defectos-kiro.md` | Prompt: defectos Kiro |

## Proceso ODD en este proyecto

1. **Authorize** → 2. **Explore** → 3. **Resolve uncertainty** → 4. **Classify** → 5. **Track** → 6. **Implement** → 7. **Close**

Cada feature ODD tiene su `odd/tasks/<feature>.md` con:
- **Specs** (`S#`): requisitos verbatim del usuario
- **Tasks** (`T#`): una línea por tarea (ID, specs vinculados, ruta, commit)
- **Log** (`L#`): pedido original verbatim + correcciones/evidencias/decisiones
