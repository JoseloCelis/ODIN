"""Arranque estructurado — odin/bootstrap.py (spec odin-startup-structure).

Cubre el contrato observable del bootstrap sin abrir ventanas:

- `StartupLogger`: validación de fase/nivel, formato canónico, truncado del
  mensaje y duración de fase con un decimal.
- `ModuleLoader`: orden canónico de los 8 alias de la suite y modo detectado,
  tanto en PACKAGE (`python3 -m odin.main`) como en SCRIPT
  (`python3 odin/main.py`, con `sys.path[0] = odin/`).
- `DisplayValidator`: sin display GDK termina con código 1 y mensaje
  estructurado en stderr.
- `run_bootstrap`: éxito con los tres componentes y aborto con log ERROR
  (propiedad 4 del spec).
"""

import io
import subprocess
import sys
from pathlib import Path

import pytest

from odin import bootstrap as B

RAIZ = Path(__file__).resolve().parents[1]
DIR_ODIN = RAIZ / "odin"

# Orden fijado por el spec odin-startup-structure (requirements, regla 1),
# escrito a mano a propósito: derivarlo de PREPROCESAMIENTO_SUITE_ORDER haría
# que el test comparara el código contra sí mismo y no pudiera fallar.
ALIASES_ESPERADOS = [
    "kernelSeparable",
    "MagnitudGradiente",
    "NonMaxSup",
    "Otsu",
    "DoubleTh",
    "aproxHough",
    "circleFilter",
    "LSC",
]


# ---------------------------------------------------------------------------
# StartupLogger — validación y formato
# ---------------------------------------------------------------------------

def test_logger_rechaza_fase_invalida():
    with pytest.raises(ValueError, match="Fase inválida"):
        B.StartupLogger(io.StringIO()).log("BAD", "INFO", "x")


def test_logger_rechaza_nivel_invalido():
    with pytest.raises(ValueError, match="Nivel inválido"):
        B.StartupLogger(io.StringIO()).log("ENV_PROBE", "BAD", "x")


def test_logger_emite_formato_canonico():
    stream = io.StringIO()
    B.StartupLogger(stream).log("ENV_PROBE", "INFO", "test")

    assert stream.getvalue() == "[ODIN] ENV_PROBE | INFO | test\n"


def test_logger_trunca_el_mensaje_a_500_caracteres():
    stream = io.StringIO()
    B.StartupLogger(stream).log("ENV_PROBE", "INFO", "x" * 600)

    lineas = stream.getvalue().splitlines()
    prefijo = "[ODIN] ENV_PROBE | INFO | "
    assert len(lineas) == 1
    assert len(lineas[0]) - len(prefijo) == 500


def test_logger_reporta_duracion_con_un_decimal():
    stream = io.StringIO()
    B.StartupLogger(stream).log_phase_complete("ENV_PROBE", 123.456)

    assert "[ODIN] ENV_PROBE | INFO | ENV_PROBE completado en 123.5 ms" in (
        stream.getvalue()
    )


def test_logger_log_phase_complete_valida_la_fase():
    with pytest.raises(ValueError, match="Fase inválida"):
        B.StartupLogger(io.StringIO()).log_phase_complete("NADA", 1.0)


# ---------------------------------------------------------------------------
# EnvironmentProbe — clasificación del entorno y cascada de rutas
# ---------------------------------------------------------------------------

def test_clasifica_docker_por_dockerenv(tmp_path):
    probe = B.EnvironmentProbe(B.StartupLogger(io.StringIO()))
    dockerenv = tmp_path / ".dockerenv"
    dockerenv.touch()

    assert probe._classify("6.1.0-microsoft-standard-WSL2", dockerenv) == "DOCKER"


def test_clasifica_wsl2_por_release_de_microsoft(tmp_path):
    probe = B.EnvironmentProbe(B.StartupLogger(io.StringIO()))
    sin_docker = tmp_path / "no_existe"

    assert probe._classify("5.15.167.4-microsoft-standard", sin_docker) == "WSL2"
    assert probe._classify("6.8.0-45-generic", sin_docker) == "NATIVE_LINUX"


def test_base_path_cae_a_home_si_el_usuario_no_existe():
    ruta = B.EnvironmentProbe._resolve_base_path(
        "NATIVE_LINUX", "usuario_que_no_existe_9f2"
    )

    assert ruta == Path.home()
    assert ruta.is_dir()


def test_detect_devuelve_entorno_y_ruta_validos(capsys):
    resultado = B.EnvironmentProbe(B.StartupLogger()).detect()

    assert isinstance(resultado, B.EnvironmentResult)
    assert resultado.env_type in ("WSL2", "NATIVE_LINUX", "DOCKER")
    assert resultado.base_path.is_dir()
    assert resultado.detection_ms >= 0
    assert "Entorno:" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# ModuleLoader — orden canónico y modo de ejecución
# ---------------------------------------------------------------------------

def test_orden_de_los_8_modulos_en_el_log(capsys):
    """R2.1/R2.5: los 8 alias aparecen en el orden de la suite, y handle al final."""
    B.run_bootstrap("odin")

    ok = [
        linea.strip() for linea in capsys.readouterr().out.splitlines()
        if linea.startswith("[ODIN] MODULE_LOAD | INFO | ")
        and linea.strip().endswith(": OK")
    ]
    cargados = [linea.rsplit("|", 1)[1].strip()[: -len(": OK")] for linea in ok]

    assert cargados == ALIASES_ESPERADOS + ["Handle_Module"]


def test_run_bootstrap_paquete_carga_los_tres_componentes(capsys):
    resultado = B.run_bootstrap("odin")

    assert isinstance(resultado, B.BootstrapResult)
    assert resultado.env.env_type in ("WSL2", "NATIVE_LINUX", "DOCKER")
    assert isinstance(resultado.modules, B.ModuleResult)
    assert resultado.modules.mode == "PACKAGE"
    assert sorted(resultado.modules.preprocesamiento) == sorted(ALIASES_ESPERADOS)
    assert resultado.logger is not None


def test_run_bootstrap_registra_las_fases_en_orden(capsys):
    B.run_bootstrap("odin")

    fases = [
        linea.split("|")[0].removeprefix("[ODIN] ").strip()
        for linea in capsys.readouterr().out.splitlines()
        if linea.startswith("[ODIN] ")
    ]

    # ENV_PROBE y MODULE_LOAD completan en ese orden (DISPLAY_VALID y
    # WINDOW_INIT pertenecen a fases posteriores del orquestador).
    assert fases.index("ENV_PROBE") < fases.index("MODULE_LOAD")


def test_modo_script_carga_la_misma_suite(capsys, monkeypatch):
    """SCRIPT: sys.path[0] es odin/, así que se importa `Preprocesamiento.*`."""
    monkeypatch.syspath_prepend(str(DIR_ODIN))

    logger = B.StartupLogger(io.StringIO())
    resultado = B.ModuleLoader(logger, None).load()

    assert resultado.mode == "SCRIPT"
    assert sorted(resultado.preprocesamiento) == sorted(ALIASES_ESPERADOS)
    assert resultado.handle is not None


def test_mal_import_de_un_modulo_lanza_runtime_error_con_el_alias(capsys, monkeypatch):
    """R2.3: ImportError re-lanzado como RuntimeError nombrando alias y archivo."""
    real = B.importlib.import_module

    def _falso(nombre, *args, **kwargs):
        if nombre.endswith("houghCircles"):
            raise ImportError("simulado")
        return real(nombre, *args, **kwargs)

    monkeypatch.setattr(B.importlib, "import_module", _falso)

    logger = B.StartupLogger(io.StringIO())
    with pytest.raises(RuntimeError, match="aproxHough"):
        B.ModuleLoader(logger, "odin").load()

    assert "ERROR" in logger.stream.getvalue()
    assert "houghCircles" in logger.stream.getvalue()


# ---------------------------------------------------------------------------
# DisplayValidator — sin display
# ---------------------------------------------------------------------------

def _gdk_sin_display():
    """Doble de `gi.repository.Gdk` cuyo `get_default()` devuelve None."""

    class _Display:
        @staticmethod
        def get_default():
            return None

    class _Gdk:
        Display = _Display

    return _Gdk


def test_sin_display_termina_con_codigo_1_y_mensaje_estructurado(
        capsys, monkeypatch):
    import gi

    gi.require_version("Gtk", "4.0")
    monkeypatch.setattr(gi.repository, "Gdk", _gdk_sin_display())

    with pytest.raises(SystemExit) as exc:
        B.DisplayValidator(B.StartupLogger()).validate()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "[ODIN] DISPLAY_VALID | ERROR | Display_Validator:" in err
    assert "DISPLAY o WAYLAND_DISPLAY" in err


# ---------------------------------------------------------------------------
# run_bootstrap — aborto ante fallo (propiedad 4)
# ---------------------------------------------------------------------------

def test_run_bootstrap_aborta_con_log_error_si_una_fase_falla(capsys, monkeypatch):
    def _fallo_simulado(_self):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(B.EnvironmentProbe, "detect", _fallo_simulado)

    with pytest.raises(SystemExit) as exc:
        B.run_bootstrap("odin")

    assert exc.value.code == 1
    assert "[ODIN] WINDOW_INIT | ERROR | RuntimeError: fallo simulado" in (
        capsys.readouterr().out
    )


# ---------------------------------------------------------------------------
# main.py -- flag --version (Task 15.1 / 15.2)
# ---------------------------------------------------------------------------

def test_version_flag_verifica_arranque_y_sale_con_codigo_0():
    """--version ejecuta el bootstrap (fases 1-3), imprime la versión y sale
    con código 0 sin abrir la GUI. Cubre el arranque en modo SCRIPT."""
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "odin" / "main.py"), "--version"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert resultado.returncode == 0, f"stderr: {resultado.stderr}"
    salida = resultado.stdout
    assert "[ODIN] ENV_PROBE | INFO |" in salida
    assert "[ODIN] MODULE_LOAD | INFO |" in salida
    assert "[ODIN] DISPLAY_VALID | INFO |" in salida
    assert "ODIN 1.0" in salida
