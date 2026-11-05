"""Controlador principal de ODIN.

Orquestador de eventos y coordinación entre la vista y los módulos de
procesamiento. Contiene la lógica de negocio sin depender directamente de
widgets GTK.
"""

import gi
import os
import threading
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gdk, Gio, GLib, Gtk

import numpy as np


class EstadoDiametro:
    """Estado del campo de diámetro: lo detectado por el barrido vs lo que
    declaró el usuario.

    Mantener los dos valores separados evita el error sutil de R6.3: si el
    valor que precarga el barrido se tomara como un valor escrito a mano, la
    siguiente ejecución se volvería manual sin que nadie lo pidiera.
    """

    def __init__(self):
        self.detectado = None
        self.usuario = None
        self.ambiguo = False

    def registrar_detectado(self, diametro, ambiguo=False):
        """Guarda lo que estimó el barrido. No cuenta como decisión del usuario."""
        self.detectado = float(diametro)
        self.ambiguo = bool(ambiguo)

    def declarar_usuario(self, diametro):
        """Marca un valor escrito a mano. `None` o <= 0 vuelve a automático."""
        if diametro is None or float(diametro) <= 0:
            self.usuario = None
        else:
            self.usuario = float(diametro)
        return self.usuario

    def volver_a_auto(self):
        self.usuario = None

    @property
    def es_manual(self):
        return self.usuario is not None

    def diametro_para_procesar(self):
        return self.usuario

    def valor_visible(self):
        if self.es_manual:
            return self.usuario
        return self.detectado if self.detectado is not None else 0.0

    def texto_estado(self):
        if self.es_manual:
            return f"Manual: {self.usuario:.1f} px (se omite la estimación)"
        if self.detectado is None:
            return "Se estima al procesar"
        aviso = " · revisar: hay otro candidato parecido" if self.ambiguo else ""
        return f"Detectado: {self.detectado:.1f} px{aviso}"


def resolver_radio(diametro_usuario, bordes, r0, aprox_hough):
    """Devuelve `(radio, pico, ambiguedad, origen)`.

    Un diámetro declarado por el usuario se usa tal cual y **omite** el
    barrido (spec hough-circles, R6.2). Sin diámetro, se estima en dos
    escalas (R3, R10).

    `aprox_hough` es el módulo `houghCircles` (alias `aproxHough`): se pasa
    como dependencia porque `main.py` no importa `Preprocesamiento` en nivel
    de módulo (spec odin-startup-structure, el arranque lo carga vía
    `bootstrap_result.modules.preprocesamiento`).
    """
    if diametro_usuario is not None and float(diametro_usuario) > 0:
        return float(diametro_usuario) / 2.0, 0, 0.0, "usuario"

    radio, pico, ambiguedad = aprox_hough.estimar_radio_dominante(bordes, r0)
    return radio, pico, ambiguedad, "automatico"


class OdinController:
    """Orquestador de eventos de la ventana principal.

    Conecta las acciones de la UI con los módulos de procesamiento.
    No contiene lógica matemática ni renderizado de widgets.
    """

    def __init__(self, bootstrap_result, logger, main_window):
        self.bootstrap_result = bootstrap_result
        self.logger = logger
        self.main_window = main_window

        # Obtener módulos cargados vía bootstrap
        preproc = bootstrap_result.modules.preprocesamiento
        handle_mod = bootstrap_result.modules.handle

        # Asignar módulos como atributos para uso posterior
        self.kernelSeparable = preproc["kernelSeparable"]
        self.MagnitudGradiente = preproc["MagnitudGradiente"]
        self.NonMaxSup = preproc["NonMaxSup"]
        self.Otsu = preproc["Otsu"]
        self.DoubleTh = preproc["DoubleTh"]
        self.aproxHough = preproc["aproxHough"]
        self.circleFilter = preproc["circleFilter"]
        self.LSC = preproc["LSC"]
        self.handle = handle_mod

        # Variables de control
        self.ruta_imagen = None
        self.image_loaded = None
        self.estado_diametro = EstadoDiametro()
        self._actualizando_diametro = False

        # Timing para WINDOW_INIT
        self._t0_window = None
        self.sigma = None

    def registrar_acciones(self):
        """Registra las acciones lógicas de la ventana."""
        self.logger.set_application_name("My App ODIN")

        action_cargar = Gio.SimpleAction.new("cargar_imagen", None)
        action_cargar.connect("activate", self.on_open_dialog)
        self.main_window.add_action(action_cargar)

        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.show_about)
        self.add_action(action_about)

    def on_open_dialog(self, button, *args):
        """Abre el diálogo de selección de archivo."""
        fileDialog = Gtk.FileDialog.new()
        fileDialog.set_title("Selecciona la imagen")

        home_dir = str(self.bootstrap_result.env.base_path)

        if not os.path.exists(home_dir):
            home_dir = str(Path.home())

        if os.path.exists(home_dir):
            folder = Gio.File.new_for_path(home_dir)
            fileDialog.set_initial_folder(folder)

        filtros = Gio.ListStore.new(Gtk.FileFilter)
        filtro_img = Gtk.FileFilter()
        filtro_img.set_name("Imágenes (bmp, tiff, jpeg)")
        filtro_img.add_mime_type("image/bmp")
        filtro_img.add_mime_type("image/tiff")
        filtro_img.add_mime_type("image/jpeg")
        filtros.append(filtro_img)
        fileDialog.set_filters(filtros)

        fileDialog.open(self.main_window, None, self.on_file_opened_callback)

    def on_file_opened_callback(self, dialog, response):
        try:
            file = dialog.open_finish(response)
            if file:
                self.ruta_imagen = file.get_path()
                print(f"File path is {file.get_path()}")
                is_error, message, self.image_loaded = self.handle.load_GrayImage(
                    self, self.ruta_imagen
                )
                self.main_window.image_loaded = self.image_loaded
                pixbuff = self.handle.matriz_a_pixbuf(self.image_loaded)
                self.main_window.mostrar_alerta("Mensaje Imagen", message, is_error)
                if hasattr(self.main_window.image_container, "cargar_imagen"):
                    self.main_window.image_container.cargar_imagen(pixbuff)
                else:
                    self.main_window.image_container.set_filename(
                        self.ruta_imagen
                    )
        except GLib.Error as error:
            print(f"Error al abrir el archivo: {error.message}")

    def on_process_clicked(self, button):
        if self.ruta_imagen:
            self.main_window.mostrar_alerta(
                "Procesando", "Iniciando el cálculo de bordes...", es_error=False
            )

            self.current_image = self.handle.recortar_imagen(self.main_window)
            if self.current_image is None:
                self.main_window.mostrar_alerta(
                    "Error", "No se pudo obtener la imagen para procesar.", es_error=True
                )
                return

            hilo_matematico = threading.Thread(
                target=self._tarea_pesada_computacional
            )
            hilo_matematico.start()

    def _tarea_pesada_computacional(self):
        """Ejecuta la matemática pesada en un hilo de fondo."""
        try:
            print("Hilo secundario: Iniciando convoluciones...")
            resultadosProcesamiento = {}
            resultadosProcesamiento["inicial"] = self.handle.matriz_a_pixbuf(
                self.current_image
            )
            Gx, Gy = self.kernelSeparable.DerivGauss(
                self.current_image, self.main_window.sigma, 1, 1, 360
            )
            MG, Tetha = self.MagnitudGradiente.MagFase(Gx, Gy)
            GNMaxS = self.NonMaxSup.LinearInterpolation(MG, Gx, Gy, Tetha)
            uOtsu, _uRosin = self.Otsu.umbralRosinYOtsu(GNMaxS, histo=True)
            HighE, LowE = self.NonMaxSup.DobleThreshold(GNMaxS, uOtsu)
            DetectedEdges = self.DoubleTh.EdgeTrack_Hyst(HighE, LowE)
            print(
                f"Bordes: {np.sum(HighE > 0)} fuertes, "
                f"{np.sum(LowE > 0)} débiles, "
                f"{np.sum(DetectedEdges > 0)} tras histéresis"
            )

            resultadosProcesamiento["gx"] = self.handle.matriz_a_pixbuf(Gx)
            resultadosProcesamiento["gy"] = self.handle.matriz_a_pixbuf(Gy)
            resultadosProcesamiento["mag"] = self.handle.matriz_a_pixbuf(MG)
            resultadosProcesamiento["maximos"] = self.handle.matriz_a_pixbuf(
                GNMaxS
            )
            resultadosProcesamiento["bordesdebiles"] = self.handle.matriz_a_pixbuf(
                LowE
            )
            resultadosProcesamiento["bordesfuertes"] = self.handle.matriz_a_pixbuf(
                HighE
            )
            resultadosProcesamiento["bordes"] = self.handle.matriz_a_pixbuf(
                DetectedEdges
            )

            self.main_window.vistas_procesadas["original"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["inicial"])
            )
            self.main_window.vistas_procesadas["gradiente x"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["gx"])
            )
            self.main_window.vistas_procesadas["gradiente y"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["gy"])
            )
            self.main_window.vistas_procesadas["magnitud"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["mag"])
            )
            self.main_window.vistas_procesadas["maximos"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["maximos"])
            )
            self.main_window.vistas_procesadas["bordes debiles"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordesdebiles"])
            )
            self.main_window.vistas_procesadas["bordes fuertes"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordesfuertes"])
            )
            self.main_window.vistas_procesadas["bordes"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordes"])
            )

            # Etapa 7: el radio no es una constante (spec hough-circles, R2).
            alto, ancho = DetectedEdges.shape[:2]
            r0 = min(alto, ancho) / 2
            radio, pico, ambiguedad, origen = resolver_radio(
                self.estado_diametro.diametro_para_procesar(),
                DetectedEdges,
                r0,
                self.aproxHough,
            )
            if radio <= 0:
                raise ValueError(
                    "No se pudo estimar el radio del circulo en el recorte."
                )

            if origen == "automatico":
                GLib.idle_add(
                    self._mostrar_diametro_detectado,
                    2 * radio,
                    ambiguedad >= self.aproxHough.UMBRAL_AMBIGUEDAD,
                )

            xRecortada, yRecortada, n, accumulador = (
                self.aproxHough.hough_circles_vectorizado(DetectedEdges, radio, 0.8)
            )
            centro = self.aproxHough.mejor_centro(
                xRecortada, yRecortada, accumulador
            )
            if centro is None:
                raise ValueError(
                    "La transformada de Hough no encontro centros."
                )

            aviso = (
                " (revisar: hay otro candidato parecido)"
                if ambiguedad >= self.aproxHough.UMBRAL_AMBIGUEDAD
                else ""
            )
            print(
                f"Radio {radio:.1f} px (diametro {2 * radio:.1f}) [{origen}], "
                f"pico {pico}, ambiguedad {ambiguedad:.2f}{aviso}"
            )

            puntosFiltrados = self.circleFilter.find_circle(
                DetectedEdges, radio, (centro[0], centro[1])
            )

            # Etapa 8: la selección tiene que RODEAR el círculo.
            anillo_ok, motivo = self.circleFilter.validar_anillo(
                puntosFiltrados, (centro[0], centro[1])
            )
            if not anillo_ok:
                raise ValueError(f"No se puede medir el circulo: {motivo}.")

            x, y, r, pv = self.LSC.Circulo_simple(puntosFiltrados)
            x = self.main_window.xRecorte + x
            y = self.main_window.yRecorte + y
            GLib.idle_add(self.main_window.finalizar_proceso_exitoso)

        except Exception as e:
            GLib.idle_add(
                self.main_window.mostrar_alerta,
                "No se pudo procesar la imagen",
                str(e),
                True,
            )
            GLib.idle_add(self.main_window.btn_procesar.set_sensitive, True)

    def _mostrar_diametro_detectado(self, diametro, ambiguo):
        """Corre en el hilo principal, vía GLib.idle_add."""
        self.estado_diametro.registrar_detectado(diametro, ambiguo)
        if not self.estado_diametro.es_manual:
            self._escribir_campo_diametro(
                self.estado_diametro.valor_visible()
            )
        self.main_window.row_diametro.set_subtitle(
            self.estado_diametro.texto_estado()
        )
        return False

    def _escribir_campo_diametro(self, valor):
        """Escribe el campo sin que cuente como cambio del usuario (R6.3)."""
        self._actualizando_diametro = True
        self.main_window.row_diametro.get_adjustment().set_value(valor)
        self._actualizando_diametro = False
