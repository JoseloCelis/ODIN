"""El hilo de fondo no toca GTK: §6.3 y §4 de AGENTS.md.

`_tarea_pesada_computacional` corre en un `threading.Thread` y desde ahí
llamaba `set_paintable` sobre `main_window.vistas_procesadas`: GTK desde un
hilo de fondo (§6.3) y, además, el controlador mutando widgets internos de la
vista (§4). Ahora el hilo entrega el resultado por `GLib.idle_add` y la vista
renderiza.
"""

import ast
import inspect
import threading
import types
from pathlib import Path

import numpy as np

from src.odin.controllers import main_controller
from src.odin.utils import handleImage

RAIZ = Path(__file__).resolve().parents[3]


class _VentanaFalsa:
    """Vista mínima que registra accesos y desde qué hilo se la usa."""

    def __init__(self) -> None:
        self.sigma = 1.0
        self.accesos: list[str] = []
        self.hilos_de_render: list[threading.Thread] = []
        self.btn_procesar = types.SimpleNamespace(set_sensitive=lambda _v: None)

    @property
    def vistas_procesadas(self) -> dict:
        self.accesos.append("vistas_procesadas")
        return {}

    def mostrar_resultados(self, imagenes: dict) -> None:
        self.hilos_de_render.append(threading.current_thread())

    def finalizar_proceso_exitoso(self) -> None:
        pass

    def mostrar_alerta(self, *_a, **_k) -> None:
        pass


def _controlador(ventana: _VentanaFalsa):
    """Controlador sin `__init__`: solo lo que el pipeline toca."""
    ctrl = main_controller.OdinController.__new__(main_controller.OdinController)
    cero = np.zeros((4, 4))
    ctrl.main_window = ventana
    ctrl.current_image = np.zeros((4, 4))
    ctrl.handle = types.SimpleNamespace(matriz_a_pixbuf=lambda a: a)
    ctrl.kernelSeparable = types.SimpleNamespace(
        DerivGauss=lambda *_a, **_k: (cero, cero)
    )
    ctrl.MagnitudGradiente = types.SimpleNamespace(
        MagFase=lambda _gx, _gy: (cero, cero)
    )
    ctrl.NonMaxSup = types.SimpleNamespace(
        LinearInterpolation=lambda *_a: cero,
        DobleThreshold=lambda *_a: (cero, cero),
    )
    ctrl.Otsu = types.SimpleNamespace(umbralRosinYOtsu=lambda *_a, **_k: (0.5, 0.5))
    ctrl.DoubleTh = types.SimpleNamespace(EdgeTrack_Hyst=lambda *_a: cero)
    return ctrl


def test_el_hilo_de_fondo_no_toca_widgets(monkeypatch):
    """§6.3 y §4: el resultado sale por `idle_add`, la vista renderiza."""
    ventana = _VentanaFalsa()
    despachos: list[tuple] = []
    monkeypatch.setattr(
        main_controller,
        "GLib",
        types.SimpleNamespace(
            idle_add=lambda fn, *a: despachos.append((fn, a)),
            Error=Exception,
        ),
    )
    ctrl = _controlador(ventana)

    hilo = threading.Thread(target=ctrl._tarea_pesada_computacional)
    hilo.start()
    hilo.join()

    assert ventana.accesos == [], "el hilo de fondo no debe tocar la vista"
    assert despachos, "el resultado debe despacharse por GLib.idle_add"
    assert despachos[0][0] == ventana.mostrar_resultados
    assert isinstance(despachos[0][1][0], dict)


def test_los_controladores_no_llaman_set_paintable():
    """§4: renderizar es tarea de la vista, no del controlador."""
    rutas = list((RAIZ / "src/odin/controllers").glob("*.py"))

    # Un glob que no matchea nada pasaría el test sin mirar una sola línea.
    assert rutas, "no se encontraron controladores: la ruta base está mal"
    for ruta in rutas:
        texto = ruta.read_text(encoding="utf-8")
        assert "set_paintable" not in texto, f"{ruta.name} muta widgets de la vista"


def test_main_controller_no_conoce_las_texturas_de_gdk():
    """§6.3: la conversión a textura ocurre en el hilo principal, en la vista."""
    texto = (RAIZ / "src/odin/controllers/main_controller.py").read_text(
        encoding="utf-8"
    )

    assert "Gdk.Texture" not in texto


def test_cada_modulo_declara_la_version_de_gdk_que_usa():
    """`main_window` usa `Gdk.Texture`: es quien debe declarar su versión.

    `bootstrap` ya llama `require_version('Gdk', '4.0')` antes de los imports
    pesados, pero la declaración local no depende del orden de importación.
    El controlador, que ya no toca `Gdk`, no debe mencionarlo.
    """
    vista = (RAIZ / "src/odin/views/main_window.py").read_text(encoding="utf-8")
    controlador = (RAIZ / "src/odin/controllers/main_controller.py").read_text(
        encoding="utf-8"
    )

    assert "gi.require_version('Gdk', '4.0')" in vista
    assert "Gdk" not in controlador, "el controlador ya no usa Gdk"


def test_matriz_a_pixbuf_produce_solo_datos():
    """La conversión corre en el hilo de fondo, así que no puede tocar la UI.

    `GdkPixbuf.Pixbuf` es un buffer de CPU refcontado, no un widget ni una
    textura de GPU: crearlo fuera del hilo principal es seguro y mantiene la
    conversión pesada lejos de la UI. `Gdk.Texture` y `set_paintable` sí exigen
    el hilo principal, y viven en la vista.
    """
    arbol = ast.parse(inspect.getsource(handleImage.matriz_a_pixbuf))
    atributos = {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    cualificados = {
        f"{n.value.id}.{n.attr}"
        for n in ast.walk(arbol)
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
    }

    # Se inspeccionan los accesos reales, no el texto: el docstring nombra esas
    # APIs justamente para explicar dónde está el límite.
    assert "Gdk.Texture" not in cualificados
    assert "set_paintable" not in atributos
    assert not any(n.startswith("Gtk.") for n in cualificados)
    assert any(n.startswith("GdkPixbuf.") for n in cualificados), (
        "debe seguir produciendo un objeto de datos"
    )
