"""La arquitectura documentada y el código no deben divergir.

`worker_thread.py` era un segundo camino asíncrono sin un solo importador que
`AGENTS.md` seguía nombrando en tres lugares. Se retiró el módulo y se corrigió
el contrato: el camino canónico es el hilo de `main_controller.py`.

Estas pruebas existen para que la divergencia no vuelva. No prueban que el
código cumpla §6.3 —hoy no lo cumple, y eso es deuda registrada—, sino que no
haya un módulo fantasma y que el contrato no lo nombre.
"""

import importlib
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
AGENTS = RAIZ / "AGENTS.md"


def test_el_segundo_camino_asincrono_ya_no_existe():
    """Solo queda el hilo del controlador; el módulo paralelo se retiró."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("src.odin.controllers.worker_thread")


def test_agents_no_nombra_el_modulo_retirado():
    """El contrato no puede apuntar a un archivo que no existe."""
    texto = AGENTS.read_text(encoding="utf-8")

    assert "worker_thread" not in texto
    assert "WorkerThread" not in texto


def test_agents_conserva_la_regla_de_despacho_a_la_ui():
    """§6.3 sigue vigente: es una regla normativa, no la descripción del código."""
    texto = AGENTS.read_text(encoding="utf-8")

    assert "GLib.idle_add" in texto
