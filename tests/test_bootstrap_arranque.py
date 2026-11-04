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

import contextlib
import io
import re
import subprocess
import sys
import tempfile
import types
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
    assert (
        "[ODIN] WINDOW_INIT | ERROR | EnvironmentProbe: RuntimeError: fallo simulado"
        in capsys.readouterr().out
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


# ---------------------------------------------------------------------------
# Tests de propiedades con Hypothesis (11 propiedades de corrección)
# ---------------------------------------------------------------------------
# Verifican las 11 propiedades de corrección de
# .kiro/specs/odin-startup-structure/design.md (sección "Correctness
# Properties", líneas 523-643). El design.md exige "al menos 100
# iteraciones" por prueba, así que todas usan max_examples >= 100.
#
# Sin hypothesis (pip install hypothesis / python3-hypothesis) el módulo no
# debe romper: _EstrategiasStub es el ÚNICO mecanismo de omisión. Evita el
# NameError al evaluar los decoradores de la clase y, de paso, marca cada
# test con skip. Por eso la clase NO lleva también @pytest.mark.skipif:
# dos mecanismos de omisión harían fácil eliminar uno por error.

try:
    from hypothesis import example, given, settings, strategies as st
    HYPOTHESIS_DISPONIBLE = True
except ImportError:
    HYPOTHESIS_DISPONIBLE = False

if not HYPOTHESIS_DISPONIBLE:
    class _EstrategiasStub:
        """Stub de strategies/given/settings: omisión única sin Hypothesis."""

        def __getattr__(self, _nombre):
            # Cualquier estrategia (st.text, st.sampled_from, ...) devuelve un
            # decorador identidad: given/settings la ignoran igualmente.
            return lambda *args, **kwargs: (lambda funcion: funcion)

    st = _EstrategiasStub()

    def example(*_args, **_kwargs):
        """Identidad: sin Hypothesis no hay ejemplos explícitos que ejecutar."""
        return lambda funcion: funcion

    def given(*_args, **_kwargs):
        def _decorar(funcion):
            return pytest.mark.skip(reason="Hypothesis no instalado")(funcion)
        return _decorar

    def settings(*_args, **_kwargs):
        def _decorar(funcion):
            return funcion
        return _decorar


def _normalizar(texto: str) -> str:
    """Minúsculas sin guiones bajos, para comparar nombres de componente.

    El spec es inconsistente con la grafía: requirements.md usa
    `Display_Validator` / `Module_Loader` / `Environment_Probe` y design.md
    usa `DisplayValidator` / `ModuleLoader` / `EnvironmentProbe`. La
    propiedad pide "el nombre del componente" sin fijar la forma exacta.
    """
    return texto.replace("_", "").lower()


def _importlib_con_fallo(archivo: str) -> types.SimpleNamespace:
    """Doble de `B.importlib` que falla solo al importar `archivo`.

    Compartido por P3 y P10 (un solo fixture en lugar de dos copias):
    delega cualquier otro módulo al importlib real capturado antes del
    parche, para que el resto de la carga siga intacto.
    """
    importar_real = B.importlib.import_module  # capturado antes del parche

    def _import_fallido(nombre, package=None, *args, **kwargs):
        if nombre.endswith(f".{archivo}"):
            raise ImportError(f"error simulado en {archivo}")
        return importar_real(nombre, package=package, *args, **kwargs)

    return types.SimpleNamespace(import_module=_import_fallido)


class TestPropiedadesCorreccion:
    """11 propiedades de corrección — design.md (Correctness Properties)."""

    # -----------------------------------------------------------------------
    # Propiedad 1: formato canónico de toda entrada de log
    # "[ODIN] <fase> | <nivel> | <mensaje>\n", decodificable UTF-8
    # Requisitos: 5.1, 5.5
    # -----------------------------------------------------------------------

    @given(
        fase=st.sampled_from(list(B.FASES)),
        nivel=st.sampled_from(list(B.NIVELES)),
        # Sin caracteres de control: la propiedad exige exactamente un "\n"
        # por línea (R5.5), y un "\n" dentro del mensaje lo rompería.
        mensaje=st.text(
            max_size=500,
            alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
        ),
    )
    @settings(max_examples=200, deadline=None)
    def test_propiedad_1_formato_canonico_log(self, fase, nivel, mensaje):
        """P1: toda entrada tiene la forma exacta [ODIN] fase | nivel | mensaje\\n."""
        stream = io.StringIO()
        B.StartupLogger(stream).log(fase, nivel, mensaje)
        salida = stream.getvalue()

        assert salida == f"[ODIN] {fase} | {nivel} | {mensaje}\n"
        salida.encode("utf-8")  # decodificable como UTF-8 (no lanza)

    # -----------------------------------------------------------------------
    # Propiedad 2: duración de fase con exactamente un decimal ("123.4 ms")
    # Requisitos: 5.2
    # -----------------------------------------------------------------------

    @given(
        fase=st.sampled_from(list(B.FASES)),
        duracion=st.floats(
            min_value=0.0, max_value=60_000.0,
            allow_nan=False, allow_infinity=False,
        ),
    )
    @settings(max_examples=200, deadline=None)
    def test_propiedad_2_duracion_un_decimal(self, fase, duracion):
        """P2: la duración se registra como número con un decimal seguido de ' ms'."""
        stream = io.StringIO()
        B.StartupLogger(stream).log_phase_complete(fase, duracion)
        salida = stream.getvalue()

        assert salida.startswith(f"[ODIN] {fase} | INFO | {fase} completado en ")
        assert re.search(r"\d+\.\d ms", salida), salida
        # Exactamente un decimal: ni dos ni más antes de " ms"
        assert not re.search(r"\d+\.\d{2,} ms", salida), salida
        assert salida.endswith("\n")

    # -----------------------------------------------------------------------
    # Propiedad 3: RuntimeError contiene el nombre del módulo fallido
    # Requisitos: 2.3
    # -----------------------------------------------------------------------

    @given(
        nombre_alias=st.sampled_from(
            [alias for alias, _ in B.PREPROCESAMIENTO_SUITE_ORDER]
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_propiedad_3_runtime_error_contiene_nombre_modulo(self, nombre_alias):
        """P3: un ImportError simulado se relanza como RuntimeError nombrando el módulo."""
        archivo = dict(B.PREPROCESAMIENTO_SUITE_ORDER)[nombre_alias]

        logger = B.StartupLogger(io.StringIO())
        loader = B.ModuleLoader(logger, package_context="odin")

        with pytest.MonkeyPatch.context() as mp:
            # Parchar solo la referencia de bootstrap: no se toca el
            # importlib global que usan pytest e Hypothesis.
            mp.setattr(B, "importlib", _importlib_con_fallo(archivo))
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()

        assert nombre_alias in str(exc_info.value)
        assert archivo in str(exc_info.value)
        assert "ERROR" in logger.stream.getvalue()

    # -----------------------------------------------------------------------
    # Propiedad 4: aborto con log ERROR ante fallo de cualquier componente
    # Requisitos: 4.2
    # -----------------------------------------------------------------------

    @given(
        componente=st.sampled_from(
            ["EnvironmentProbe", "ModuleLoader", "DisplayValidator"]
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_propiedad_4_aborto_con_log_error(self, componente):
        """P4: fallo de un componente → ERROR + sys.exit(1) sin instanciar MainWindow.

        MainWindow solo se construye en `on_activate`, después de que
        `run_bootstrap` devuelve; abortar con SystemExit antes de devolver
        resultado prueba que la construcción nunca llegó a comenzar.
        """
        buf = io.StringIO()

        with pytest.MonkeyPatch.context() as mp:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                if componente == "EnvironmentProbe":
                    def _detect_falla(_self):
                        raise RuntimeError("fallo simulado de entorno")

                    mp.setattr(B.EnvironmentProbe, "detect", _detect_falla)
                    with pytest.raises(SystemExit) as exc_info:
                        B.run_bootstrap("odin")

                elif componente == "ModuleLoader":
                    def _import_fallido(*_args, **_kwargs):
                        raise ImportError("fallo simulado de módulo")

                    mp.setattr(
                        B, "importlib",
                        types.SimpleNamespace(import_module=_import_fallido),
                    )
                    with pytest.raises(SystemExit) as exc_info:
                        B.run_bootstrap("odin")

                else:  # DisplayValidator — el mismo doble que el test de ejemplo
                    import gi

                    gi.require_version("Gtk", "4.0")
                    mp.setattr(gi.repository, "Gdk", _gdk_sin_display())
                    with pytest.raises(SystemExit) as exc_info:
                        B.DisplayValidator(B.StartupLogger()).validate()

        assert exc_info.value.code == 1

        lineas_error = [
            linea for linea in buf.getvalue().splitlines()
            if "| ERROR |" in linea
        ]
        assert lineas_error, buf.getvalue()
        assert _normalizar(componente) in _normalizar("\n".join(lineas_error))

    # -----------------------------------------------------------------------
    # Propiedad 5: ERROR contiene componente, tipo de excepción y mensaje
    # Requisitos: 5.4
    # -----------------------------------------------------------------------

    # Borde de truncado fijado de forma determinista (no delegado al azar):
    # el total cae exactamente en MAX_MSG_LEN y un byte por encima.
    @example(
        tipo="ErrorPrueba",
        mensaje="x" * (B.MAX_MSG_LEN - len("EnvironmentProbe: ErrorPrueba: ")),
    )
    @example(
        tipo="ErrorPrueba",
        mensaje="x" * (B.MAX_MSG_LEN - len("EnvironmentProbe: ErrorPrueba: ") + 1),
    )
    @given(
        tipo=st.text(
            min_size=1, max_size=15,
            alphabet=st.characters(whitelist_categories=("Ll",)),
        ),
        mensaje=st.text(
            max_size=600,
            alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_propiedad_5_error_contiene_componente_tipo_y_mensaje(self, tipo, mensaje):
        """P5: la entrada ERROR lleva componente + tipo + mensaje (hasta MAX_MSG_LEN)."""
        excepcion = type(tipo, (Exception,), {})

        def _detect_falla(_self):
            raise excepcion(mensaje)

        buf = io.StringIO()
        with pytest.MonkeyPatch.context() as mp:
            with contextlib.redirect_stdout(buf):
                mp.setattr(B.EnvironmentProbe, "detect", _detect_falla)
                with pytest.raises(SystemExit) as exc_info:
                    B.run_bootstrap("odin")

        assert exc_info.value.code == 1

        lineas_error = [
            linea for linea in buf.getvalue().splitlines()
            if "| ERROR |" in linea
        ]
        assert len(lineas_error) == 1, lineas_error
        linea = lineas_error[0]

        # Mensaje emitido = "componente: tipo: mensaje" truncado a
        # B.MAX_MSG_LEN (R5.4: el ERROR lleva componente + tipo + mensaje,
        # con el tope del propio log).
        mensaje_log = linea.split(" | ", 2)[2]
        assert mensaje_log == f"EnvironmentProbe: {tipo}: {mensaje}"[:B.MAX_MSG_LEN]
        assert len(mensaje_log) <= B.MAX_MSG_LEN
        assert _normalizar("EnvironmentProbe") in _normalizar(linea)

    # -----------------------------------------------------------------------
    # Propiedad 6: clasificación WSL2 robusta a capitalización de "microsoft"
    # Requisitos: 3.1
    # -----------------------------------------------------------------------

    @given(
        prefijo=st.text(
            max_size=20, alphabet=st.characters(blacklist_categories=("Cs",))
        ),
        sufijo=st.text(
            max_size=20, alphabet=st.characters(blacklist_categories=("Cs",))
        ),
        # Las 2^9 capitalizaciones posibles de "microsoft" (una booleana por
        # letra), no cuatro literales fijas.
        altas=st.lists(st.booleans(), min_size=9, max_size=9),
    )
    @settings(max_examples=200, deadline=None)
    def test_propiedad_6_wsl2_case_insensitive(self, prefijo, sufijo, altas):
        """P6: 'microsoft' en cualquier capitalización clasifica WSL2 sin /.dockerenv."""
        variante = "".join(
            letra.upper() if alta else letra
            for letra, alta in zip("microsoft", altas)
        )
        release = f"{prefijo}{variante}{sufijo}"
        probe = B.EnvironmentProbe(B.StartupLogger(io.StringIO()))

        with tempfile.TemporaryDirectory() as tmp:
            dockerenv = Path(tmp) / ".dockerenv"  # existe el dir, no el archivo
            assert probe._classify(release, dockerenv) == "WSL2"

    # -----------------------------------------------------------------------
    # Propiedad 7: DOCKER tiene prioridad sobre WSL2 en cualquier combinación
    # Requisitos: 3.2
    # -----------------------------------------------------------------------

    @given(release=st.text(max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_propiedad_7_docker_prioridad_sobre_wsl2(self, release):
        """P7: con /.dockerenv existente el entorno es DOCKER con cualquier release."""
        probe = B.EnvironmentProbe(B.StartupLogger(io.StringIO()))

        with tempfile.TemporaryDirectory() as tmp:
            dockerenv = Path(tmp) / ".dockerenv"
            dockerenv.touch()
            assert probe._classify(release, dockerenv) == "DOCKER"

    # -----------------------------------------------------------------------
    # Propiedad 8: base_path siempre apunta a una ruta existente
    # Requisitos: 3.3, 3.4
    # -----------------------------------------------------------------------

    @given(
        env_type=st.sampled_from(["WSL2", "NATIVE_LINUX", "DOCKER"]),
        usuario=st.text(
            min_size=1, max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll",)),
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_propiedad_8_base_path_siempre_existe(self, env_type, usuario):
        """P8: para cualquier entorno y usuario, base_path existe y es directorio.

        Determinista en cualquier host: los dos primeros candidatos pueden no
        existir para el usuario generado, pero la cascada termina en
        Path.home(), que siempre existe (R3.3/R3.4).
        """
        base_path = B.EnvironmentProbe._resolve_base_path(env_type, usuario)

        candidatos = [
            Path(f"/home/{usuario}/proyectos/ODIN"),
            Path(f"/home/{usuario}"),
            Path.home(),
        ]
        assert base_path in candidatos
        assert base_path.exists()
        assert base_path.is_dir()

    # -----------------------------------------------------------------------
    # Propiedad 9: log ENV_PROBE INFO contiene entorno y ruta base
    # Requisitos: 3.5
    # -----------------------------------------------------------------------

    @given(
        env_type=st.sampled_from(["WSL2", "NATIVE_LINUX", "DOCKER"]),
        usuario=st.text(
            min_size=1, max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll",)),
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_propiedad_9_env_probe_log_contiene_entorno_y_ruta(self, env_type, usuario):
        """P9: la entrada ENV_PROBE INFO registra los valores que detect() devuelve."""
        stream = io.StringIO()
        probe = B.EnvironmentProbe(B.StartupLogger(stream))

        with pytest.MonkeyPatch.context() as mp:
            # Doble completo de os: copia del namespace real con solo
            # getlogin sustituido. Si el código llegara a tocar cualquier
            # otro miembro (os.environ, os.path, ...) sigue resolviendo, en
            # lugar de acoplarse a los dos atributos que hoy se usan.
            doble_os = types.SimpleNamespace(**dict(vars(B.os)))
            doble_os.getlogin = lambda: usuario
            mp.setattr(B, "os", doble_os)
            mp.setattr(
                B.EnvironmentProbe, "_classify",
                lambda self, release, dockerenv: env_type,
            )
            resultado = probe.detect()

        # base_path lo resuelve la propia detect() con su cascada (acaba en
        # Path.home(), garantizado en cualquier host), y el log debe traer
        # exactamente ese valor.
        salida = stream.getvalue()
        assert "[ODIN] ENV_PROBE | INFO |" in salida
        assert resultado.env_type in salida
        assert str(resultado.base_path) in salida

    # -----------------------------------------------------------------------
    # Propiedad 10: mensaje de error terminal contiene módulo y modo
    # Requisitos: 6.3
    # -----------------------------------------------------------------------

    @given(
        nombre_alias=st.sampled_from(
            [alias for alias, _ in B.PREPROCESAMIENTO_SUITE_ORDER]
        ),
        modo=st.sampled_from(["SCRIPT", "PACKAGE"]),
    )
    @settings(max_examples=100, deadline=None)
    def test_propiedad_10_mensaje_error_contiene_modulo_y_modo(self, nombre_alias, modo):
        """P10: al no cargar un módulo, el ERROR terminal nombra módulo y modo."""
        archivo = dict(B.PREPROCESAMIENTO_SUITE_ORDER)[nombre_alias]
        package_context = "odin" if modo == "PACKAGE" else None

        buf = io.StringIO()
        with pytest.MonkeyPatch.context() as mp:
            with contextlib.redirect_stdout(buf):
                mp.setattr(B, "importlib", _importlib_con_fallo(archivo))
                if modo == "SCRIPT":
                    mp.syspath_prepend(str(DIR_ODIN))
                with pytest.raises(SystemExit) as exc_info:
                    B.run_bootstrap(package_context)

        assert exc_info.value.code == 1

        lineas_error = [
            linea for linea in buf.getvalue().splitlines()
            if "| ERROR |" in linea
        ]
        assert lineas_error, buf.getvalue()
        texto_error = "\n".join(lineas_error)
        assert nombre_alias in texto_error
        assert modo in texto_error

    # -----------------------------------------------------------------------
    # Propiedad 11: MODULE_LOAD INFO contiene modo y módulos resueltos
    # Requisitos: 6.5
    # -----------------------------------------------------------------------

    @given(modo=st.sampled_from(["SCRIPT", "PACKAGE"]))
    @settings(max_examples=100, deadline=None)
    def test_propiedad_11_module_load_info_contiene_modo_y_modulos(self, modo):
        """P11: las entradas INFO de MODULE_LOAD registran el modo y cada módulo."""
        stream = io.StringIO()
        package_context = "odin" if modo == "PACKAGE" else None
        loader = B.ModuleLoader(B.StartupLogger(stream), package_context)

        with pytest.MonkeyPatch.context() as mp:
            if modo == "SCRIPT":
                mp.syspath_prepend(str(DIR_ODIN))
            resultado = loader.load()

        assert resultado.mode == modo

        lineas_info = [
            linea for linea in stream.getvalue().splitlines()
            if "MODULE_LOAD" in linea and "INFO" in linea
        ]
        assert any(modo in linea for linea in lineas_info), lineas_info
        for alias in ALIASES_ESPERADOS:
            assert any(alias in linea for linea in lineas_info), (
                f"alias {alias} no aparece en MODULE_LOAD INFO: {lineas_info}"
            )
