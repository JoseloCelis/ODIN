# Documentación ODIN

Estructura canónica:

```
docs/
├── README.md                    # Este archivo
├── architecture/                # Decisiones de arquitectura (ADR)
├── api/                         # Referencia de API pública (aliases de dominio)
├── design/
│   └── system.md               # Sistema de diseño (tokens, tipografía, componentes)
├── development/                 # Guías de desarrollo, setup, convenciones
├── odd/                         # Documentación ODD
│   ├── README.md               # Índice ODD
│   ├── tasks/                  # Features ODD (tasks/*.md)
│   └── prompts/                # Prompts de trabajo ODD
├── project-state/               # Estado actual del proyecto
│   ├── README.md               # Visión general
│   ├── AGENTS.md               # Instrucciones para agentes
│   ├── CHANGELOG.md            # Historial de cambios
│   └── MEMORY.md               # Ledger de estado (local, gitignored)
├── releases/                    # Notas de release por versión
├── specs/                       # Specs absorbidos de Kiro (referencia canónica)
│   └── README.md               # Índice de specs
├── specs-source/                # Specs originales de .kiro/specs/ (inmutables)
│   └── README.md               # Índice de fuentes
└── templates/                   # Plantillas para reports
```

## Navegación rápida

| Qué buscas | Dónde está |
|------------|------------|
| Empezar a desarrollar | `docs/development/` |
| Entender la arquitectura | `docs/architecture/` |
| Referencia de la API pública | `docs/api/` |
| Specs del pipeline (9 etapas) | `docs/specs/` |
| Features ODD con tareas y commits | `docs/odd/tasks/` |
| Estado actual (qué está hecho, qué no) | `docs/project-state/` |
| Sistema de diseño (UI) | `docs/design/system.md` |
| Historial de releases | `docs/releases/` y `CHANGELOG.md` |
| Specs originales Kiro (auditoría) | `docs/specs-source/` |

---

> **Nota:** Los archivos en `docs/` son **copias canónicas** para navegación y lectura. Los originales que consumen tests y código siguen en sus ubicaciones (`odd/specs/`, `odd/tasks/`, `.kiro/specs/`, raíz del repo). No edites en `docs/` esperando que afecte al runtime; edita el original y vuelve a copiar, o usa un script de sincronización.
