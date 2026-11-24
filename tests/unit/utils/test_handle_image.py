"""Registro y recorte de `handleImage`.

Cubre cuatro reglas:
  R1. Las funciones del puente registran por `logging`, no por `print`.
  R2. El registro del recorte informa las dimensiones realmente procesadas.
  R3. `recortar_imagen` sin arrastre previo devuelve la imagen completa.
  R4. `on_drag_end` deriva la coordenada Y del eje Y, no del eje X.
"""

import logging
from types import SimpleNamespace

import cv2 as cv
import numpy as np
import pytest

from src.odin.utils import handleImage


# --- Dobles sin GTK -------------------------------------------------------


class _ComboRecorte:
    """Doble del `Gtk.ComboBoxText` de modo de recorte."""

    def __init__(self, seleccionado: int) -> None:
        self._seleccionado = seleccionado

    def get_selected(self) -> int:
        return self._seleccionado


class _CapaDibujo:
    """Doble del `Gtk.DrawingArea`: solo importa que el redibujado no falle."""

    def __init__(self) -> None:
        self.redibujos = 0

    def queue_draw(self) -> None:
        self.redibujos += 1


class _Contenedor:
    """Doble del visualizador: expone tamaño del widget y rectángulo arrastrado."""

    def __init__(self, ancho: int, alto: int, **rectangulo: float) -> None:
        self._ancho = ancho
        self._alto = alto
        for nombre, valor in rectangulo.items():
            setattr(self, nombre, valor)

    def get_width(self) -> int:
        return self._ancho

    def get_height(self) -> int:
        return self._alto


def _ventana(
    imagen: np.ndarray,
    modo: int,
    contenedor: _Contenedor,
) -> SimpleNamespace:
    """Arma el objeto que `recortar_imagen` espera: ventana + contenedor."""
    return SimpleNamespace(
        image_loaded=imagen,
        combo_recorte=_ComboRecorte(modo),
        image_container=contenedor,
    )


@pytest.fixture
def imagen_gris() -> np.ndarray:
    """Imagen 200x400 en gris, con valores distintos para detectar el recorte."""
    return np.arange(200 * 400, dtype=np.uint8).reshape(200, 400)


# --- R1: registro por logging, no por print -------------------------------


def test_load_gray_image_registra_sin_escribir_en_stdout(
    tmp_path, capsys, caplog
) -> None:
    ruta = tmp_path / "prueba.png"
    assert cv.imwrite(str(ruta), np.full((40, 60), 128, dtype=np.uint8))

    with caplog.at_level(logging.INFO):
        error, mensaje, matriz = handleImage.load_GrayImage(None, str(ruta))

    salida = capsys.readouterr()
    assert salida.out == "", f"load_GrayImage escribió en stdout: {salida.out!r}"
    assert salida.err == "", f"load_GrayImage escribió en stderr: {salida.err!r}"

    assert error is False
    assert matriz is not None and matriz.shape == (40, 60)
    assert "cargó" in caplog.text.lower()


def test_matriz_a_pixbuf_registra_sin_escribir_en_stdout(capsys) -> None:
    matriz = np.zeros((10, 10), dtype=np.uint8)

    pixbuf = handleImage.matriz_a_pixbuf(matriz)

    salida = capsys.readouterr()
    assert salida.out == "", f"matriz_a_pixbuf escribió en stdout: {salida.out!r}"
    assert pixbuf is not None
    assert (pixbuf.get_width(), pixbuf.get_height()) == (10, 10)


# --- R2: el registro informa lo procesado, no lo pedido -------------------


def test_recorte_registra_las_dimensiones_aplicadas(imagen_gris, caplog) -> None:
    # Widget 400x200 con imagen 200x400: escala 1.0 y offsets 0, así que el
    # rectángulo del widget coincide con píxeles de la matriz.
    contenedor = _Contenedor(400, 200, x1=10.0, y1=20.0, x2=110.0, y2=120.0)

    with caplog.at_level(logging.INFO):
        recorte = handleImage.recortar_imagen(_ventana(imagen_gris, 1, contenedor))

    assert recorte is not None
    assert recorte.shape == (100, 100), "el recorte no coincidió con el rectángulo"
    assert "100x100" in caplog.text, (
        f"el registro no informa las dimensiones procesadas: {caplog.text!r}"
    )


# --- R3: sin arrastre previo no hay AttributeError ------------------------


def test_recorte_sin_arrastre_devuelve_imagen_completa(imagen_gris) -> None:
    # El contenedor no tiene x1/y1/x2/y2: nunca hubo `on_drag_end`.
    contenedor = _Contenedor(400, 200)

    recorte = handleImage.recortar_imagen(_ventana(imagen_gris, 1, contenedor))

    assert recorte is not None
    assert recorte.shape == imagen_gris.shape
    assert np.array_equal(recorte, imagen_gris)


# --- R4: la coordenada Y sale del eje Y ----------------------------------


def test_on_drag_end_deriva_y_del_eje_y() -> None:
    # El método real solo toca atributos, así que un doble plano basta: no se
    # puede instanciar el widget sin pantalla ni con `object.__new__` (GObject).
    visualizador = SimpleNamespace(
        inicio_x=30.0,
        inicio_y=100.0,
        actual_x=40.0,  # menor que inicio_y: delata el cruce de ejes
        actual_y=120.0,
        arrastrando=True,
        capa_dibujo=_CapaDibujo(),
    )

    handleImage.VisualizadorInteractivo.on_drag_end(visualizador, None, 0.0, 0.0)

    assert (visualizador.x1, visualizador.y1) == (30.0, 100.0)
    assert (visualizador.x2, visualizador.y2) == (40.0, 120.0)
