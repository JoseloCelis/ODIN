"""Robustez del arranque: R3.1 y R5.3 de `odin-startup-structure`.

R3.1: `os.uname()` puede no existir o lanzar; el entorno se clasifica como
`NATIVE_LINUX` en vez de tumbar el arranque.
R5.3: la descripción de una advertencia tiene máximo 200 caracteres, mientras
R5.1 y R5.4 dejan 500 para INFO y ERROR.
"""

import io
import os
from pathlib import Path

from src.odin.bootstrap import MAX_WARN_LEN, EnvironmentProbe, StartupLogger


def _mensaje_de(salida: io.StringIO) -> str:
    return salida.getvalue().rstrip("\n").split(" | ")[-1]


def test_la_clasificacion_sin_release_es_native_linux():
    """R3.1: sin release no hay WSL2; el entorno es NATIVE_LINUX."""
    probe = EnvironmentProbe(StartupLogger(io.StringIO()))

    assert probe._classify("", Path("/no-existe-dockerenv")) == "NATIVE_LINUX"


def test_el_probe_sobrevive_a_la_ausencia_de_os_uname(monkeypatch):
    """R3.1: si `os.uname()` no existe, el arranque no se cae."""
    def sin_uname():
        raise AttributeError("module 'os' has no attribute 'uname'")

    monkeypatch.setattr(os, "uname", sin_uname, raising=False)

    resultado = EnvironmentProbe(StartupLogger(io.StringIO())).detect()

    assert resultado.env_type in {"NATIVE_LINUX", "DOCKER"}
    assert isinstance(resultado.base_path, Path)


def test_el_probe_sobrevive_a_un_os_uname_que_lanza(monkeypatch):
    """R3.1: una excepción de `os.uname()` tampoco debe propagarse."""
    def uname_roto():
        raise OSError("uname no disponible")

    monkeypatch.setattr(os, "uname", uname_roto, raising=False)

    assert EnvironmentProbe(StartupLogger(io.StringIO())).detect().env_type in {
        "NATIVE_LINUX",
        "DOCKER",
    }


def test_la_advertencia_se_recorta_a_200_caracteres():
    """R5.3: máximo 200 caracteres en la descripción de una advertencia."""
    salida = io.StringIO()

    StartupLogger(salida).log("ENV_PROBE", "WARNING", "x" * 300)

    assert len(_mensaje_de(salida)) == MAX_WARN_LEN == 200


def test_el_info_conserva_el_limite_de_500_caracteres():
    """R5.1: INFO mantiene los 500 caracteres, no hereda el recorte de 200."""
    salida = io.StringIO()

    StartupLogger(salida).log("ENV_PROBE", "INFO", "y" * 600)

    assert len(_mensaje_de(salida)) == 500
