"""`.kiro/specs` no cambia sin declararlo (S2 y S10).

Dos hashes por archivo: `cuerpo` detecta un requisito reescrito; `archivo`
detecta cualquier cambio, bloque de estado incluido. Un solo hash no alcanza,
porque no distinguiría "actualicé el estado" de "reescribí el requisito".

El test no lee historia de git: compara contra el manifiesto versionado.
"""

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GENERADOR = RAIZ / "odd" / "specs" / "generar_manifiesto.py"
MANIFIESTO = RAIZ / "odd" / "specs" / ".originales.sha256"


def _generador():
    """Carga el generador para compartir una sola implementación del hash."""
    especificacion = importlib.util.spec_from_file_location(
        "generar_manifiesto", GENERADOR
    )
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _manifiesto() -> dict[str, tuple[str, str]]:
    entradas: dict[str, tuple[str, str]] = {}
    for linea in MANIFIESTO.read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.startswith("#"):
            continue
        sha_cuerpo, sha_archivo, ruta = linea.split(maxsplit=2)
        entradas[ruta] = (sha_cuerpo, sha_archivo)
    return entradas


def test_el_manifiesto_cubre_todos_los_archivos():
    """Un archivo sin entrada sería un documento sin protección."""
    generador = _generador()

    assert set(generador.entradas()) == set(_manifiesto())


def test_ningun_cuerpo_fue_reescrito():
    """S2: el texto del documento es evidencia y no se reescribe."""
    generador = _generador()
    for ruta, (sha_cuerpo, _) in _manifiesto().items():
        actual = generador.sha(generador.cuerpo(generador.leer(RAIZ / ruta)))

        assert actual == sha_cuerpo, (
            f"{ruta}: el cuerpo cambió. Si fue una corrección deliberada, "
            f"regenerá el manifiesto en el mismo commit."
        )


def test_ningun_archivo_cambio_sin_declararlo():
    """S10: el bloque de estado también está pinneado."""
    generador = _generador()
    for ruta, (_, sha_archivo) in _manifiesto().items():
        actual = generador.sha(generador.leer(RAIZ / ruta))

        assert actual == sha_archivo, (
            f"{ruta}: el archivo cambió. Regenerá el manifiesto en el mismo commit."
        )
