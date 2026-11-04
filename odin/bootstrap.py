"""
Infraestructura de arranque estructurado para ODIN.
Proporciona logging homogéneo, detección de entorno, carga de módulos,
validación de display y orquestación completa del bootstrap.
"""

import sys
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Literal, Optional
import importlib


# Constantes de fases y niveles de log
FASES = ("ENV_PROBE", "MODULE_LOAD", "DISPLAY_VALID", "WINDOW_INIT")
NIVELES = ("INFO", "WARNING", "ERROR")
LOG_FORMAT = "[ODIN] {fase} | {nivel} | {mensaje}\n"
MAX_MSG_LEN = 500
MAX_WARN_LEN = 200

# Orden canónico de importación de la suite de preprocesamiento
# Tuplas: (alias público, nombre del archivo/módulo)
PREPROCESAMIENTO_SUITE_ORDER = (
    ("kernelSeparable", "DeriGauss"),
    ("MagnitudGradiente", "MagFase"),
    ("NonMaxSup", "NonMaxSuppressionVectorizado"),
    ("Otsu", "MtoOtsu"),
    ("DoubleTh", "DThEdgeTrackHyst"),
    ("aproxHough", "houghCircles"),
    ("circleFilter", "findCircle"),
    ("LSC", "circuloSimple"),
)


@dataclass
class EnvironmentResult:
    """Resultado de la detección de entorno."""
    env_type: str  # "WSL2" | "NATIVE_LINUX" | "DOCKER"
    base_path: Path
    detection_ms: float


@dataclass
class ModuleResult:
    """Resultado de la carga de módulos."""
    preprocesamiento: Dict[str, Any]
    handle: Any
    mode: Literal["SCRIPT", "PACKAGE"]


@dataclass
class DisplayResult:
    """Resultado de la validación de display."""
    display: Any
    backend_name: str


@dataclass
class BootstrapResult:
    """Resultado completo del bootstrap."""
    env: EnvironmentResult
    modules: ModuleResult
    logger: "StartupLogger"


class StartupLogger:
    """Logger de arranque con formato canónico y fallback a stderr."""

    def __init__(self, stream=None):
        self.stream = stream or sys.stdout

    def log(self, fase: str, nivel: str, mensaje: str) -> None:
        """
        Emite una entrada de log con formato canónico.
        
        Formato: [ODIN] <fase> | <nivel> | <mensaje>\n
        - fase: una de ENV_PROBE, MODULE_LOAD, DISPLAY_VALID, WINDOW_INIT
        - nivel: INFO, WARNING, ERROR
        - mensaje: truncado a 500 caracteres
        - UTF-8, exactamente un \n por línea
        """
        if fase not in FASES:
            raise ValueError(f"Fase inválida: {fase}. Debe ser una de {FASES}")
        if nivel not in NIVELES:
            raise ValueError(f"Nivel inválido: {nivel}. Debe ser uno de {NIVELES}")

        # Truncar mensaje a 500 caracteres
        mensaje = mensaje[:MAX_MSG_LEN]

        linea = LOG_FORMAT.format(fase=fase, nivel=nivel, mensaje=mensaje)

        try:
            self.stream.write(linea)
            self.stream.flush()
        except OSError:
            # Fallback a stderr
            try:
                sys.stderr.write(linea)
                sys.stderr.flush()
            except OSError:
                pass
            sys.exit(1)

    def log_phase_complete(self, fase: str, duracion_ms: float) -> None:
        """
        Emite una entrada INFO con la fase y su duración en milisegundos
        con exactamente un decimal.
        """
        if fase not in FASES:
            raise ValueError(f"Fase inválida: {fase}. Debe ser una de {FASES}")
        
        mensaje = f"{fase} completado en {duracion_ms:.1f} ms"
        self.log(fase, "INFO", mensaje)


class EnvironmentProbe:
    """Detecta el entorno de ejecución y resuelve la ruta base de archivos."""

    def __init__(self, logger: StartupLogger):
        self.logger = logger

    def _classify(self, release: str, dockerenv_path: Path) -> str:
        """Clasifica el entorno: DOCKER > WSL2 > NATIVE_LINUX."""
        if dockerenv_path.exists():
            return "DOCKER"
        if "microsoft" in release.lower():
            return "WSL2"
        return "NATIVE_LINUX"

    @staticmethod
    def _resolve_base_path(env_type: str, username: str) -> Path:
        """Resuelve la ruta base con cascada de prioridades."""
        # Todas las rutas usan /home/ (Linux nativo) por rendimiento en WSL2
        candidatos = [
            Path(f"/home/{username}/proyectos/ODIN"),
            Path(f"/home/{username}"),
            Path.home(),
        ]
        for candidato in candidatos:
            if candidato.exists() and candidato.is_dir():
                return candidato
        # Fallback garantizado (Path.home() siempre existe)
        return Path.home()

    def detect(self) -> EnvironmentResult:
        """Ejecuta la detección completa del entorno."""
        t0 = time.monotonic()
        
        # Obtener username
        try:
            username = os.getlogin()
        except (OSError, AttributeError):
            username = Path.home().name
        
        # Clasificar entorno
        env_type = self._classify(os.uname().release, Path("/.dockerenv"))
        
        # Resolver ruta base
        base_path = self._resolve_base_path(env_type, username)
        
        detection_ms = (time.monotonic() - t0) * 1000
        
        # Log WARNING si detección > 200ms
        if detection_ms > 200:
            self.logger.log(
                "ENV_PROBE",
                "WARNING",
                f"Detección de entorno superó 200 ms: {detection_ms:.1f} ms"
            )
        
        # Log INFO con resultado
        self.logger.log(
            "ENV_PROBE",
            "INFO",
            f"Entorno: {env_type}, base_path: {base_path}"
        )
        
        return EnvironmentResult(
            env_type=env_type,
            base_path=base_path,
            detection_ms=detection_ms
        )


class ModuleLoader:
    """Carga y valida los módulos de preprocesamiento y utilidades."""

    def __init__(self, logger: StartupLogger, package_context: Optional[str]):
        self.logger = logger
        self.package_context = package_context

    def _detect_mode(self) -> Literal["SCRIPT", "PACKAGE"]:
        """Detecta el modo de ejecución basado en __package__."""
        if self.package_context is not None and self.package_context != "":
            return "PACKAGE"
        return "SCRIPT"

    def load(self) -> ModuleResult:
        """Carga todos los módulos requeridos en orden."""
        mode = self._detect_mode()
        
        # Log modo detectado
        self.logger.log(
            "MODULE_LOAD",
            "INFO",
            f"Modo de ejecución: {mode}"
        )
        
        preprocesamiento = {}
        
        # Importar Preprocesamiento_Suite en orden
        for alias, archivo in PREPROCESAMIENTO_SUITE_ORDER:
            try:
                if mode == "PACKAGE":
                    modulo = importlib.import_module(
                        f".Preprocesamiento.{archivo}", package="odin"
                    )
                else:
                    # SCRIPT: resolver relativo al directorio actual (sys.path[0])
                    # importlib.util no usado directamente, importlib ya cargado
                    # Buscar en sys.path (ya configurado por exec de script)
                    modulo = importlib.import_module(f"Preprocesamiento.{archivo}")
                
                preprocesamiento[alias] = modulo
                self.logger.log("MODULE_LOAD", "INFO", f"{alias}: OK")
            
            except ImportError as e:
                self.logger.log(
                    "MODULE_LOAD",
                    "ERROR",
                    f"Fallo al importar {archivo}: {e}"
                )
                raise RuntimeError(
                    f"No se pudo cargar el módulo {alias} ({archivo}) "
                    f"en modo {mode}: {e}"
                )
        
        # Importar Handle_Module
        try:
            if mode == "PACKAGE":
                handle = importlib.import_module(".utils.handleImage", package="odin")
            else:
                handle = importlib.import_module("utils.handleImage")
            
            self.logger.log("MODULE_LOAD", "INFO", "Handle_Module: OK")
        
        except ImportError as e:
            self.logger.log(
                "MODULE_LOAD",
                "ERROR",
                f"Fallo al importar Handle_Module: {e}"
            )
            raise RuntimeError(f"Handle_Module no disponible en modo {mode}: {e}")
        
        # Log módulos resueltos
        self.logger.log(
            "MODULE_LOAD",
            "INFO",
            f"Módulos resueltos: {', '.join(preprocesamiento.keys())}, handle"
        )
        
        return ModuleResult(
            preprocesamiento=preprocesamiento,
            handle=handle,
            mode=mode
        )


class DisplayValidator:
    """Valida la disponibilidad de un display GDK."""

    def __init__(self, logger: StartupLogger):
        self.logger = logger

    def validate(self) -> DisplayResult:
        """Valida que exista un display GDK disponible."""
        import gi
        gi.require_version('Gtk', '4.0')
        gi.require_version('Gdk', '4.0')
        from gi.repository import Gdk
        
        display = Gdk.Display.get_default()
        
        if display is None:
            error_msg = (
                "Display_Validator: no se encontró un display GDK disponible.\n"
                "Acción recomendada: Verifique que DISPLAY o WAYLAND_DISPLAY estén configurados.\n"
            )
            sys.stderr.write(f"[ODIN] DISPLAY_VALID | ERROR | {error_msg}")
            sys.stderr.flush()
            sys.exit(1)
        
        backend_name = type(display).__name__
        self.logger.log("DISPLAY_VALID", "INFO", f"Backend GDK: {backend_name}")
        
        return DisplayResult(display=display, backend_name=backend_name)


def run_bootstrap(package_context: Optional[str] = None) -> BootstrapResult:
    """Orquesta el bootstrap completo de ODIN."""
    logger = StartupLogger()
    # Componente en curso para el ERROR de R5.4. Solo cubre las fases que
    # corren dentro de este try (ENV_PROBE y MODULE_LOAD); DisplayValidator
    # se ejecuta en on_activate, fuera, con su propio sys.exit(1). Si se
    # añade una fase aquí, DEBE asignar esta variable antes de ejecutarse.
    componente = "EnvironmentProbe"

    try:
        # Fase 1: ENV_PROBE
        t0 = time.monotonic()
        env_probe = EnvironmentProbe(logger)
        env = env_probe.detect()
        logger.log_phase_complete("ENV_PROBE", (time.monotonic() - t0) * 1000)
        
        # Fase 2: MODULE_LOAD
        componente = "ModuleLoader"
        t0 = time.monotonic()
        module_loader = ModuleLoader(logger, package_context)
        modules = module_loader.load()
        logger.log_phase_complete("MODULE_LOAD", (time.monotonic() - t0) * 1000)
        
        # Fase 3 y 4 se ejecutan más tarde (en on_activate y MainWindow)
        
        return BootstrapResult(env=env, modules=modules, logger=logger)
    
    except Exception as e:
        logger.log(
            "WINDOW_INIT",
            "ERROR",
            f"{componente}: {type(e).__name__}: {e}"
        )
        sys.exit(1)