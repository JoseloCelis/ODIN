# Specs absorbidos de Kiro

Cada documento absorbe un spec de `.kiro/specs/` conservando el original sin
modificar (S1) y citando sus requisitos verbatim (S6). El estado de cada
requisito esta verificado contra el codigo, con evidencia `archivo:linea`.

| Spec | Titulo | Veredicto | Version ODD |
|---|---|---|---|
| `circulo-simple` | circulo-simple | `ABSORBIDO` | [circulo-simple.md](circulo-simple.md) |
| `edge-track-hyst` | edge-track-hyst (etapa ⑥) | `ABSORBIDO` | [edge-track-hyst.md](edge-track-hyst.md) |
| `find-circle` | find-circle (etapa ⑧) | `ABSORBIDO` | [find-circle.md](find-circle.md) |
| `hough-circles` | hough-circles (etapa ⑦) | `ABSORBIDO` | [hough-circles.md](hough-circles.md) |
| `kernel-separable` | kernel-separable — Etapa ①: kernel derivada-gaussiana separable | `ABSORBIDO` | [kernel-separable.md](kernel-separable.md) |
| `mag-fase` | mag-fase — Etapa ②: magnitud y dirección del gradiente | `ABSORBIDO` | [mag-fase.md](mag-fase.md) |
| `non-max-sup` | non-max-sup | `ABSORBIDO` | [non-max-sup.md](non-max-sup.md) |
| `odin-startup-structure` | odin-startup-structure | `ABSORBIDO` | [odin-startup-structure.md](odin-startup-structure.md) |
| `otsu-rosin` | otsu-rosin — Etapa ④: umbrales de Otsu y Rosin | `ABSORBIDO` | [otsu-rosin.md](otsu-rosin.md) |

Los originales estan pinneados con dos hashes en `.originales.sha256`
(`cuerpo` y `archivo`); `tests/unit/test_kiro_inmutabilidad.py` lo verifica y
`tests/unit/test_absorcion_kiro.py` verifica que cada cita sea verbatim.

Regenerar el manifiesto solo junto con una correccion registrada (S10):
`python3 odd/specs/generar_manifiesto.py`
