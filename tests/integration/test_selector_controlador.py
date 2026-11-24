"""Integración del selector de geometría en el controlador (spec S4, T5).

Ejecuta `_tarea_pesada_computacional` con los módulos de pipeline
sustituidos por dobles que registran llamadas, para verificar sin UI:

1. La geometría fijada por el operador se obedece sin consultar al
   clasificador.
2. En automático se consulta `clasificar_geometria` sobre los puntos de borde
   y la propuesta se usa solo si el clasificador decidió.
3. Sin decisión el pipeline se detiene mostrando ambos candidatos, con la
   confianza y la evidencia, y sin lanzar una excepción críptica.
4. La rama de círculo usa ⑦→⑧→⑨ y la de recta ⑩→⑪.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import gi

gi.require_version('GdkPixbuf', '2.0')
import numpy as np
import pytest
from gi.repository import GdkPixbuf

from src.odin.Procesamiento import EvidenciaGeometria, Geometria
from src.odin.controllers import main_controller


INF = float("inf")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _evidencia(
    geometria: Geometria | None,
    *,
    confianza: float = 0.9,
    candidatos: tuple[Geometria, ...] | None = None,
    residual_recta: float = 1.0,
    residual_circulo: float = 2.0,
    cobertura: float = 0.5,
    radio: float | None = 10.0,
) -> EvidenciaGeometria:
    if candidatos is None:
        candidatos = (geometria,) if geometria is not None else (
            Geometria.CIRCULO,
            Geometria.RECTA,
        )
    return EvidenciaGeometria(
        geometria=geometria,
        confianza=confianza,
        candidatos=candidatos,
        residual_recta=residual_recta,
        residual_circulo=residual_circulo,
        cobertura_angular=cobertura,
        radio=radio,
        detalle="evidencia de prueba",
    )


def _pixbuf() -> GdkPixbuf.Pixbuf:
    return GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 2, 2)


class _FakePicture:
    def __init__(self) -> None:
        self.paintable = None

    def set_paintable(self, paintable) -> None:
        self.paintable = paintable


class _FakeRow:
    def __init__(self) -> None:
        self.subtitle: str | None = None

    def set_subtitle(self, texto: str) -> None:
        self.subtitle = texto


class _FakeBoton:
    def __init__(self) -> None:
        self.sensitive = True

    def set_sensitive(self, valor: bool) -> None:
        self.sensitive = bool(valor)


class _FakeAdjustment:
    def __init__(self) -> None:
        self.value = 0.0

    def set_value(self, valor: float) -> None:
        self.value = float(valor)


class _FakeSpinRow:
    """SpinRow mínimo: ajuste y subtítulo, como usa el controlador."""

    def __init__(self) -> None:
        self.ajuste = _FakeAdjustment()
        self.subtitle: str | None = None

    def get_adjustment(self) -> _FakeAdjustment:
        return self.ajuste

    def set_subtitle(self, texto: str) -> None:
        self.subtitle = texto


class _FakeVentana:
    """Ventana mínima: registra alertas y expone el resumen de geometría."""

    def __init__(self) -> None:
        self.sigma = 3
        self.xRecorte = 0
        self.yRecorte = 0
        self.vistas_procesadas = {
            nombre: _FakePicture()
            for nombre in (
                "original", "gradiente x", "gradiente y", "magnitud",
                "maximos", "bordes debiles", "bordes fuertes", "bordes",
            )
        }
        self.btn_procesar = _FakeBoton()
        self.row_geometria = _FakeRow()
        self.row_diametro = _FakeSpinRow()
        self.alertas: list[tuple[str, str, bool]] = []
        self.exitos = 0

    def mostrar_alerta(self, titulo: str, mensaje: str, es_error: bool = True) -> None:
        self.alertas.append((titulo, mensaje, es_error))

    def finalizar_proceso_exitoso(self) -> None:
        self.exitos += 1


def _modulos_falsos() -> tuple[dict[str, Mock], Mock, np.ndarray]:
    """Dobles de la suite con llamadas registradas y una máscara de bordes fija."""
    bordes = np.zeros((12, 12), dtype=float)
    bordes[2, 3] = 1.0
    bordes[5, 7] = 1.0
    bordes[9, 2] = 1.0

    handle = Mock()
    handle.matriz_a_pixbuf = Mock(return_value=_pixbuf())

    modulos: dict[str, Mock] = {
        "kernelSeparable": Mock(
            DerivGauss=Mock(return_value=(np.zeros((12, 12)), np.zeros((12, 12))))
        ),
        "MagnitudGradiente": Mock(
            MagFase=Mock(return_value=(np.zeros((12, 12)), np.zeros((12, 12))))
        ),
        "NonMaxSup": Mock(
            LinearInterpolation=Mock(return_value=np.zeros((12, 12))),
            DobleThreshold=Mock(return_value=(np.zeros((12, 12)), np.zeros((12, 12)))),
        ),
        "Otsu": Mock(umbralRosinYOtsu=Mock(return_value=(0.5, 0.6))),
        "DoubleTh": Mock(EdgeTrack_Hyst=Mock(return_value=bordes)),
        "aproxHough": Mock(
            estimar_radio_dominante=Mock(return_value=(10.0, 5, 0.0)),
            hough_circles_vectorizado=Mock(
                return_value=(np.array([1.0]), np.array([2.0]), 1, np.zeros((1, 1)))
            ),
            mejor_centro=Mock(return_value=(5.0, 5.0)),
            UMBRAL_AMBIGUEDAD=0.5,
        ),
        "circleFilter": Mock(
            find_circle=Mock(return_value=np.array([[1.0, 2.0]])),
            validar_anillo=Mock(return_value=(True, "")),
        ),
        "LSC": Mock(Circulo_simple=Mock(return_value=(1.0, 2.0, 10.0, 0.0))),
        "HoughLineas": Mock(
            hough_lineas=Mock(return_value=(5.0, 0.1, 3, 10, 0.5))
        ),
        "LineaRobusta": Mock(
            euc_space=Mock(return_value=np.array([0.0, 0.0, 1.0, 0.0])),
            linea_robusta=Mock(
                return_value=(np.array([0.0, 0.0, 1.0, 0.0]), 0.5, np.array([[1.0, 2.0]]))
            ),
        ),
    }
    return modulos, handle, bordes


def _controlador(ventana: _FakeVentana):
    modulos, handle, bordes = _modulos_falsos()
    bootstrap = SimpleNamespace(
        modules=SimpleNamespace(preprocesamiento=modulos, handle=handle)
    )
    logger = SimpleNamespace(set_application_name=lambda nombre: None)
    controlador = main_controller.OdinController(bootstrap, logger, ventana)
    controlador.current_image = np.zeros((12, 12))
    return controlador, modulos, bordes


def _instalar_idle_sincrono(monkeypatch: pytest.MonkeyPatch) -> None:
    """`GLib.idle_add` ejecuta el callback en el acto, para no necesitar un loop."""

    def _idle(funcion, *args):
        funcion(*args)
        return 0

    monkeypatch.setattr(
        main_controller,
        "GLib",
        SimpleNamespace(idle_add=_idle, Error=main_controller.GLib.Error),
    )


# ---------------------------------------------------------------------------
# Criterio 1 — la geometría es una entrada explícita
# ---------------------------------------------------------------------------

def test_criterio_1_el_operador_fija_circulo_y_el_pipeline_obede(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)

    controlador.establecer_geometria(0)  # Círculo
    assert controlador.geometria_seleccionada is Geometria.CIRCULO

    def _no_se_consulta(*_args, **_kwargs):
        raise AssertionError("el clasificador no se consulta con geometría fijada")

    monkeypatch.setattr(main_controller, "clasificar_geometria", _no_se_consulta)

    controlador._tarea_pesada_computacional()

    modulos["aproxHough"].hough_circles_vectorizado.assert_called_once()
    modulos["HoughLineas"].hough_lineas.assert_not_called()
    assert ventana.exitos == 1


def test_criterio_1_el_operador_fija_recta_y_el_pipeline_obede(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)

    controlador.establecer_geometria(1)  # Recta
    assert controlador.geometria_seleccionada is Geometria.RECTA

    def _no_se_consulta(*_args, **_kwargs):
        raise AssertionError("el clasificador no se consulta con geometría fijada")

    monkeypatch.setattr(main_controller, "clasificar_geometria", _no_se_consulta)

    controlador._tarea_pesada_computacional()

    modulos["HoughLineas"].hough_lineas.assert_called_once()
    modulos["aproxHough"].hough_circles_vectorizado.assert_not_called()
    assert ventana.exitos == 1


# ---------------------------------------------------------------------------
# Criterio 2 — automático consulta, no adivina
# ---------------------------------------------------------------------------

def test_criterio_2_automatico_consulta_y_usa_la_propuesta(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)

    controlador.establecer_geometria(2)  # Automático
    assert controlador.geometria_seleccionada is None

    llamadas: list[np.ndarray] = []

    def _clasificar(puntos):
        llamadas.append(np.asarray(puntos))
        return _evidencia(Geometria.CIRCULO, confianza=0.9)

    monkeypatch.setattr(main_controller, "clasificar_geometria", _clasificar)

    controlador._tarea_pesada_computacional()

    assert len(llamadas) == 1
    modulos["aproxHough"].hough_circles_vectorizado.assert_called_once()
    modulos["HoughLineas"].hough_lineas.assert_not_called()
    assert "0.900" in (ventana.row_geometria.subtitle or "")


def test_criterio_2_el_clasificador_recibe_los_puntos_de_borde(monkeypatch):
    ventana = _FakeVentana()
    controlador, _modulos, bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)
    controlador.establecer_geometria(2)

    capturado: dict[str, np.ndarray] = {}

    def _clasificar(puntos):
        capturado["puntos"] = np.asarray(puntos)
        return _evidencia(Geometria.CIRCULO)

    monkeypatch.setattr(main_controller, "clasificar_geometria", _clasificar)

    controlador._tarea_pesada_computacional()

    esperado = np.argwhere(bordes > 0)[:, ::-1].astype(float)
    np.testing.assert_array_equal(capturado["puntos"], esperado)


def test_criterio_2_automatico_no_adivina_cuando_falla_cerrado(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)
    controlador.establecer_geometria(2)

    monkeypatch.setattr(
        main_controller,
        "clasificar_geometria",
        lambda puntos: _evidencia(
            None,
            confianza=0.2,
            candidatos=(Geometria.CIRCULO, Geometria.RECTA),
        ),
    )

    controlador._tarea_pesada_computacional()

    modulos["aproxHough"].hough_circles_vectorizado.assert_not_called()
    modulos["HoughLineas"].hough_lineas.assert_not_called()
    assert ventana.exitos == 0


# ---------------------------------------------------------------------------
# Criterio 3 — sin decisión no hay excepción críptica
# ---------------------------------------------------------------------------

def test_criterio_3_sin_decision_reporta_candidatos_confianza_y_evidencia(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)
    controlador.establecer_geometria(2)

    evidencia = _evidencia(
        None,
        confianza=0.2,
        candidatos=(Geometria.CIRCULO, Geometria.RECTA),
        residual_recta=1.25,
        residual_circulo=INF,
        cobertura=0.3,
        radio=None,
    )
    monkeypatch.setattr(
        main_controller, "clasificar_geometria", lambda puntos: evidencia
    )

    controlador._tarea_pesada_computacional()

    modulos["aproxHough"].hough_circles_vectorizado.assert_not_called()
    modulos["HoughLineas"].hough_lineas.assert_not_called()
    assert ventana.exitos == 0
    assert ventana.alertas == []  # no hay excepción críptica
    assert ventana.btn_procesar.sensitive is True

    subtitulo = (ventana.row_geometria.subtitle or "").lower()
    assert "círculo" in subtitulo
    assert "recta" in subtitulo
    assert "0.200" in subtitulo
    assert "1.250" in subtitulo
    assert "inf" in subtitulo
    assert "30.0%" in subtitulo


# ---------------------------------------------------------------------------
# Criterio 4 — las dos geometrías son ramas del mismo selector
# ---------------------------------------------------------------------------

def test_criterio_4_recta_ejecuta_las_etapas_10_y_11(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)

    controlador.establecer_geometria(1)  # Recta
    monkeypatch.setattr(
        main_controller,
        "clasificar_geometria",
        lambda puntos: (_ for _ in ()).throw(AssertionError("no se consulta")),
    )

    controlador._tarea_pesada_computacional()

    modulos["HoughLineas"].hough_lineas.assert_called_once()
    modulos["LineaRobusta"].linea_robusta.assert_called_once()
    modulos["aproxHough"].hough_circles_vectorizado.assert_not_called()
    modulos["circleFilter"].find_circle.assert_not_called()
    assert ventana.exitos == 1


def test_criterio_3_el_fallo_de_circulo_se_reporta_sin_excepcion(monkeypatch):
    """El antiguo `ValueError` de círculo ausente ahora es un reporte con evidencia."""
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)

    controlador.establecer_geometria(0)  # Círculo
    modulos["aproxHough"].estimar_radio_dominante = Mock(return_value=(0.0, 0, 0.0))

    controlador._tarea_pesada_computacional()

    assert ventana.exitos == 0
    assert len(ventana.alertas) == 1
    titulo, mensaje, es_error = ventana.alertas[0]
    assert es_error is True
    assert "No se pudo estimar el radio del círculo" in mensaje
    assert "geometría fijada por el operador" in mensaje
    assert ventana.btn_procesar.sensitive is True


def test_criterio_4_circulo_ejecuta_las_etapas_7_8_9(monkeypatch):
    ventana = _FakeVentana()
    controlador, modulos, _bordes = _controlador(ventana)
    _instalar_idle_sincrono(monkeypatch)

    controlador.establecer_geometria(0)  # Círculo
    monkeypatch.setattr(
        main_controller,
        "clasificar_geometria",
        lambda puntos: (_ for _ in ()).throw(AssertionError("no se consulta")),
    )

    controlador._tarea_pesada_computacional()

    modulos["aproxHough"].hough_circles_vectorizado.assert_called_once()
    modulos["circleFilter"].find_circle.assert_called_once()
    modulos["LSC"].Circulo_simple.assert_called_once()
    modulos["HoughLineas"].hough_lineas.assert_not_called()
    assert ventana.exitos == 1
