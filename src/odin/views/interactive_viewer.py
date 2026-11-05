"""Visualizador interactivo de ODIN.

Lienzo Cairo para dibujar el rectángulo de recorte sobre la imagen.
"""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, cairo


class VisualizadorInteractivo(Gtk.Overlay):
    """Área de dibujo con recorte Cairo."""

    def __init__(self):
        super().__init__()

        # Variables de control para el recorte
        self.inicio_x = 0
        self.inicio_y = 0
        self.actual_x = 0
        self.actual_y = 0
        self.arrastrando = False

        # El widget de la imagen de fondo
        self.picture = Gtk.Picture.new()
        self.picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.set_child(self.picture)

        # Capa transparente para dibujar el rectángulo
        self.capa_dibujo = Gtk.DrawingArea()
        self.capa_dibujo.set_draw_func(self.draw_callback)
        self.add_overlay(self.capa_dibujo)

        # Capturar gestos del ratón (clic y arrastre)
        self.controlador_arrastre = Gtk.GestureDrag.new()
        self.controlador_arrastre.set_button(1)
        self.controlador_arrastre.connect("drag-begin", self.on_drag_begin)
        self.controlador_arrastre.connect("drag-update", self.on_drag_update)
        self.controlador_arrastre.connect("drag-end", self.on_drag_end)
        self.capa_dibujo.add_controller(self.controlador_arrastre)

    def cargar_imagen(self, pixbuf: GdkPixbuf.Pixbuf):
        """Asigna un nuevo Pixbuf al visualizador de forma nativa."""
        textura = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.picture.set_paintable(textura)

    def on_drag_begin(self, gesto, x, y):
        """Se activa justo en el momento del primer clic."""
        self.inicio_x = x
        self.inicio_y = y
        self.arrastrando = True

    def on_drag_update(self, gesto, offset_x, offset_y):
        """Se ejecuta continuamente mientras el usuario arrastra el ratón."""
        self.actual_x = self.inicio_x + offset_x
        self.actual_y = self.inicio_y + offset_y
        self.capa_dibujo.queue_draw()

    def on_drag_end(self, gesto, offset_x, offset_y):
        """Se activa cuando el usuario suelta el botón del ratón."""
        self.arrastrando = False

        self.x1 = min(self.inicio_x, self.actual_x)
        self.y1 = min(self.inicio_y, self.actual_y)
        self.x2 = max(self.inicio_x, self.actual_x)
        self.y2 = max(self.inicio_y, self.actual_y)
        ancho = abs(self.actual_x - self.inicio_x)
        alto = abs(self.actual_y - self.inicio_y)

        print(
            f"Recorte solicitado en coordenadas: "
            f"X:{self.x1}, Y:{self.y1}, Ancho:{ancho}, Alto:{alto}"
        )

        self.inicio_x = self.inicio_y = self.actual_x = self.actual_y = 0
        self.capa_dibujo.queue_draw()

    def draw_callback(self, drawing_area, cr, width, height, user_data=None):
        """Pinta el rectángulo de recorte usando Cairo."""
        if self.arrastrando:
            x = min(self.inicio_x, self.actual_x)
            y = min(self.inicio_y, self.actual_y)
            ancho = abs(self.actual_x - self.inicio_x)
            alto = abs(self.actual_y - self.inicio_y)
            print(width, height, alto, ancho)

            cr.set_source_rgba(0.0, 0.4, 1.0, 0.15)
            cr.rectangle(x, y, ancho, alto)
            cr.fill_preserve()

            cr.set_source_rgba(0.0, 0.4, 1.0, 0.8)
            cr.set_line_width(2.0)
            cr.set_dash([4.0, 4.0], 0)
            cr.stroke()
