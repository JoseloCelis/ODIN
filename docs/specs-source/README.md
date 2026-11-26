# Specs Originales de Kiro (Inmutables)

Copia fiel de `.kiro/specs/` al momento de la absorción. **No se editan**.

Cada spec vive en su directorio con:
- `requirements.md` — requisitos originales
- `design.md` — diseño original (si existe)
- `tasks.md` — tareas originales (si existe)

## Integridad

`tests/unit/test_kiro_inmutabilidad.py` verifica que el contenido no ha cambiado comparando con los hashes en `.originales.sha256` (hash de cuerpo y hash de archivo completo).

## Estructura

```
specs-source/
├── circulo-simple/
├── edge-track-hyst/
├── find-circle/
├── hough-circles/
├── kernel-separable/
├── mag-fase/
├── non-max-sup/
├── odin-startup-structure/
└── otsu-rosin/
```
