"""La absorción cita los requisitos verbatim (S6).

Un spec absorbido que parafrasea el requisito original borra la evidencia de qué
se especificó: el lector ya no puede distinguir la cita de una interpretación.
Este test compara cada cita contra `.kiro/specs/<slug>/requirements.md`
ignorando solo diferencias de espaciado.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ORIGINALES = RAIZ / ".kiro" / "specs"
ABSORBIDOS = RAIZ / "odd" / "specs"

SLUGS = [
    "kernel-separable",
    "mag-fase",
    "otsu-rosin",
    "edge-track-hyst",
    "hough-circles",
    "find-circle",
    "non-max-sup",
    "circulo-simple",
    "odin-startup-structure",
]

ESTADO = re.compile(r"^\*\*Estado:\*\*")


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def _citas(absorbido: str) -> list[str]:
    """Devuelve el bloque de cita que sigue a cada línea `**Estado:**`."""
    lineas = absorbido.splitlines()
    citas: list[str] = []
    for indice, linea in enumerate(lineas):
        if not ESTADO.match(linea):
            continue
        bloque: list[str] = []
        for siguiente in lineas[indice + 1 :]:
            if siguiente.startswith(">"):
                bloque.append(siguiente.lstrip(">").strip())
                continue
            if bloque or siguiente.strip():
                break
        citas.append(" ".join(bloque).strip())
    return citas


def test_los_nueve_specs_estan_absorbidos():
    faltantes = [slug for slug in SLUGS if not (ABSORBIDOS / f"{slug}.md").exists()]

    assert not faltantes, f"sin absorber: {faltantes}"


def test_cada_requisito_se_cita_verbatim():
    for slug in SLUGS:
        absorbido = (ABSORBIDOS / f"{slug}.md").read_text(encoding="utf-8")
        original = _normalizar(
            (ORIGINALES / slug / "requirements.md").read_text(encoding="utf-8")
        )
        citas = _citas(absorbido)

        assert citas, f"{slug}: ningún requisito citado"
        for cita in citas:
            assert cita, f"{slug}: cita vacía después de una línea de estado"
            assert _normalizar(cita) in original, (
                f"{slug}: la cita no aparece verbatim en requirements.md: "
                f"{cita[:120]!r}"
            )
