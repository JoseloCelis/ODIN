"""Genera el manifiesto de inmutabilidad de `.kiro/specs`.

Uso:

    python3 odd/specs/generar_manifiesto.py

El manifiesto guarda dos hashes por archivo (S10):

- `cuerpo` — el texto fuera del bloque de estado delimitado. Detecta un
  requisito reescrito (S2).
- `archivo` — el archivo completo, bloque incluido. Detecta cualquier cambio
  que nadie declaró.

Regenerar es un acto deliberado: si el diff muestra hashes movidos sin una
corrección registrada, algo cambió sin declararse.
"""

import hashlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESPECIFICACIONES = RAIZ / ".kiro" / "specs"
MANIFIESTO = RAIZ / "odd" / "specs" / ".originales.sha256"

INICIO = "<!-- ESTADO:INICIO -->"
FIN = "<!-- ESTADO:FIN -->"


def leer(ruta: Path) -> str:
    """Lee normalizando saltos de línea para que el hash no dependa del sistema."""
    return ruta.read_text(encoding="utf-8").replace("\r\n", "\n")


def cuerpo(texto: str) -> str:
    """Devuelve el texto sin el bloque de estado delimitado."""
    inicio = texto.find(INICIO)
    fin = texto.find(FIN)
    if inicio == -1 or fin == -1:
        return texto
    return texto[:inicio] + texto[fin + len(FIN) :]


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def entradas() -> dict[str, tuple[str, str]]:
    """Hash de cuerpo y de archivo completo, por ruta relativa al repo."""
    resultado: dict[str, tuple[str, str]] = {}
    for ruta in sorted(ESPECIFICACIONES.rglob("*.md")):
        texto = leer(ruta)
        relativa = str(ruta.relative_to(RAIZ)).replace("\\", "/")
        resultado[relativa] = (sha(cuerpo(texto)), sha(texto))
    return resultado


def main() -> int:
    lineas = [
        "# Manifiesto de inmutabilidad de .kiro/specs (S10).",
        "# cuerpo = texto fuera del bloque de estado; archivo = archivo completo.",
        "# Regenerar solo junto con una correccion registrada (S12):",
        "#   python3 odd/specs/generar_manifiesto.py",
    ]
    datos = entradas()
    for relativa, (sha_cuerpo, sha_archivo) in datos.items():
        lineas.append(f"{sha_cuerpo} {sha_archivo} {relativa}")
    MANIFIESTO.parent.mkdir(parents=True, exist_ok=True)
    MANIFIESTO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{len(datos)} archivos pinneados en {MANIFIESTO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
