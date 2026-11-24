"""Vista: selector de geometría y resumen de la decisión (spec S4, T5).

Cubre el criterio 5 del bloque «T5 — criterios de diseño del selector»:
la vista expone el selector (círculo / recta / automático) y muestra la
geometría propuesta con su confianza y detalle, o ambos candidatos cuando el
clasificador falla cerrado.

Requiere un display GDK; sin display los tests se omiten.
"""

import io

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import pytest
from gi.repository import Gdk

from odin.Procesamiento import Geometria
from odin.bootstrap import StartupLogger, run_bootstrap
from odin.views.main_window import OdinMainWindow

pytestmark = pytest.mark.skipif(
    Gdk.Display.get_default() is None,
    reason="requiere un display GDK para construir la ventana",
)


def _ventana() -> OdinMainWindow:
    resultado = run_bootstrap("odin")
    return OdinMainWindow(
        application=None,
        bootstrap_result=resultado,
        logger=StartupLogger(io.StringIO()),
    )


def test_el_selector_expone_circulo_recta_y_automatico() -> None:
    win = _ventana()
    modelo = win.combo_geometria.get_model()

    opciones = [modelo.get_string(i) for i in range(modelo.get_n_items())]

    assert opciones == ["Círculo", "Recta", "Automático"]


def test_el_automatico_es_la_opcion_predeterminada() -> None:
    win = _ventana()

    assert win.combo_geometria.get_selected() == 2
    assert win.controller.geometria_seleccionada is None


def test_seleccionar_circulo_fija_la_geometria() -> None:
    win = _ventana()

    win.combo_geometria.set_selected(0)

    assert win.controller.geometria_seleccionada is Geometria.CIRCULO


def test_seleccionar_recta_fija_la_geometria() -> None:
    win = _ventana()

    win.combo_geometria.set_selected(1)

    assert win.controller.geometria_seleccionada is Geometria.RECTA


def test_seleccionar_automatico_vuelve_a_no_fijar_geometria() -> None:
    win = _ventana()
    win.combo_geometria.set_selected(0)
    assert win.controller.geometria_seleccionada is Geometria.CIRCULO

    win.combo_geometria.set_selected(2)

    assert win.controller.geometria_seleccionada is None


def test_mostrar_propuesta_actualiza_el_resumen() -> None:
    win = _ventana()

    win.controller._mostrar_geometria_propuesta(
        "autodetección: círculo; confianza 0.900"
    )

    assert win.row_geometria.get_subtitle() == (
        "autodetección: círculo; confianza 0.900"
    )


def test_mostrar_indeterminada_muestra_ambos_candidatos() -> None:
    win = _ventana()

    win.controller._mostrar_geometria_indeterminada(
        "sin decisión automática; candidatos: círculo y recta; confianza 0.200"
    )

    subtitulo = win.row_geometria.get_subtitle() or ""
    assert "círculo" in subtitulo.lower()
    assert "recta" in subtitulo.lower()
    assert "0.200" in subtitulo
