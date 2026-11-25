"""El registro de la aplicación va por `logging`, nunca por stdout (deuda 4).

Reglas cubiertas:

- ningún módulo de `src/odin/` escribe con `print`: hay un sistema de registro
  configurado en `bootstrap.py` y las trazas de depuración no deben llegar a la
  salida estándar;
- el visor interactivo registra el recorte solicitado, y no imprime nada durante
  el repintado, que ocurre en cada movimiento del ratón;
- la ventana principal registra el valor del ajuste y no lo imprime.
"""

import logging
from pathlib import Path

import pytest

from src.odin.views.interactive_viewer import VisualizadorInteractivo
from src.odin.views.main_window import OdinMainWindow

RAIZ_FUENTE = Path(__file__).resolve().parents[2] / "src" / "odin"


def test_ningun_modulo_de_la_aplicacion_escribe_por_stdout():
    """La regla completa: `print` prohibido en `src/odin/`, sin excepciones."""
    ofensores: list[str] = []
    for ruta in sorted(RAIZ_FUENTE.rglob("*.py")):
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            desnuda = linea.strip()
            if desnuda.startswith("#"):
                continue
            if "print(" in desnuda:
                ofensores.append(f"{ruta.relative_to(RAIZ_FUENTE)}:{numero}: {desnuda}")

    assert not ofensores, "registro por stdout en:\n" + "\n".join(ofensores)


class _Superficie:
    """Doble mínimo de la capa de dibujo: solo necesita aceptar el repintado."""

    def __init__(self) -> None:
        self.repintados = 0

    def queue_draw(self) -> None:
        self.repintados += 1


class _VisorFalso:
    """Estado mínimo que `on_drag_end` consulta y modifica."""

    def __init__(self) -> None:
        self.arrastrando = True
        self.inicio_x = 1.0
        self.inicio_y = 2.0
        self.actual_x = 4.0
        self.actual_y = 6.0
        self.x1 = self.y1 = self.x2 = self.y2 = 0.0
        self.capa_dibujo = _Superficie()


def test_el_visor_registra_el_recorte_sin_imprimir(capsys, caplog):
    """Sustituye al `print` del recorte: mismo dato, canal de registro."""
    visor = _VisorFalso()
    with caplog.at_level(logging.DEBUG, logger="src.odin.views.interactive_viewer"):
        VisualizadorInteractivo.on_drag_end(visor, None, 0.0, 0.0)

    assert capsys.readouterr().out == ""
    mensajes = " ".join(registro.getMessage() for registro in caplog.records)
    assert "X:1.0" in mensajes and "Y:2.0" in mensajes
    assert "Ancho:3.0" in mensajes and "Alto:4.0" in mensajes
    assert visor.capa_dibujo.repintados == 1


def test_la_ventana_registra_el_ajuste_sin_imprimir(capsys, caplog):
    """Sustituye al `print(spinRow.get_value())`: valor etiquetado, no desnudo."""
    class _FilaFalsa:
        def get_value(self) -> float:
            return 20.0

    class _VentanaFalsa:
        sigma = 0

    ventana = _VentanaFalsa()
    with caplog.at_level(logging.DEBUG, logger="src.odin.views.main_window"):
        OdinMainWindow.slider_changed(ventana, _FilaFalsa())

    assert capsys.readouterr().out == ""
    assert ventana.sigma == 20
    mensajes = " ".join(registro.getMessage() for registro in caplog.records)
    assert "20.0" in mensajes
