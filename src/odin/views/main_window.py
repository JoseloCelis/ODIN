"""Ventana principal de ODIN.

Contiene toda la lógica de la interfaz de usuario (GTK 4 / Libadwaita).
Sin algoritmos de procesamiento ni convoluciones.
"""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

import os
import sys
import time
import argparse
from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from odin.bootstrap import run_bootstrap, DisplayValidator, StartupLogger
from odin.controllers.main_controller import OdinController
from odin.views.interactive_viewer import VisualizadorInteractivo


class OdinMainWindow(Adw.ApplicationWindow):
    """Ventana principal de ODIN.

    Solo posicionamiento de widgets, estilos y renderizado.
    Toda la lógica de negocio vive en OdinController.
    """

    def __init__(self, *args, bootstrap_result, logger, **kwargs):
        super().__init__(*args, **kwargs)

        self._bootstrap_result = bootstrap_result
        self._logger = logger

        # Crear el controlador (inyecta los módulos de bootstrap)
        self.controller = OdinController(
            bootstrap_result, logger, self
        )

        # Atributos expuestos para compatibilidad con el controlador
        self.kernelSeparable = self.controller.kernelSeparable
        self.MagnitudGradiente = self.controller.MagnitudGradiente
        self.NonMaxSup = self.controller.NonMaxSup
        self.Otsu = self.controller.Otsu
        self.DoubleTh = self.controller.DoubleTh
        self.aproxHough = self.controller.aproxHough
        self.circleFilter = self.controller.circleFilter
        self.LSC = self.controller.LSC
        self.handle = self.controller.handle

        # Variables de control
        self.ruta_imagen = None
        self.image_loaded = None
        self.estado_diametro = self.controller.estado_diametro
        self._actualizando_diametro = self.controller._actualizando_diametro

        # Configuración de la ventana principal
        self.set_title("ODIN")
        self.set_default_size(1600, 900)
        self.set_size_request(width=1024, height=600)

        # Timing para WINDOW_INIT
        self._t0_window = time.monotonic()

        # Construir la UI
        self._construir_ui()

    def _construir_ui(self):
        """Construye toda la interfaz de usuario."""
        # Contenedor principal adaptativo
        toolbar_view = Adw.ToolbarView.new()
        self.set_content(toolbar_view)

        # --- BARRA SUPERIOR (HeaderBar) ---
        header_bar = Adw.HeaderBar.new()
        toolbar_view.add_top_bar(header_bar)

        # Botón abrir archivo (Extremo izquierdo)
        open_button = Gtk.Button.new_from_icon_name("document-open-symbolic")
        open_button.set_tooltip_text("Cargar nueva imagen")
        open_button.connect('clicked', self.show_openDialog)
        header_bar.pack_start(open_button)

        # Botones de control (Extremo derecho)
        menu = Gio.Menu.new()
        menu.append("Cargar Imagen", "win.cargar_imagen")
        menu.append("Acerca de...", "win.about")

        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_icon_name("open-menu-symbolic")
        self.hamburger.set_tooltip_text("Menú principal")
        self.hamburger.set_menu_model(menu)
        header_bar.pack_end(self.hamburger)

        settings_button = Gtk.Button.new_from_icon_name("emblem-system-symbolic")
        header_bar.pack_end(settings_button)

        reset_button = Gtk.Button.new_with_label("Volver a Original")
        header_bar.pack_end(reset_button)

        # --- CUERPO PRINCIPAL (Panel Dividido) ---
        split_view = Adw.NavigationSplitView.new()
        split_view.set_min_sidebar_width(340)
        split_view.set_max_sidebar_width(380)
        toolbar_view.set_content(split_view)

        # --- BARRA LATERAL DE CONTROLES ---
        vbox_sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll_sidebar = Gtk.ScrolledWindow.new()
        scroll_sidebar.set_vexpand(True)
        vbox_sidebar.append(scroll_sidebar)

        pag_opciones = Adw.PreferencesPage.new()
        pag_opciones.set_margin_start(20)
        pag_opciones.set_margin_end(16)
        pag_opciones.set_margin_top(24)
        pag_opciones.set_margin_bottom(24)
        scroll_sidebar.set_child(pag_opciones)

        # Grupo: Archivo
        grupo_archivo = Adw.PreferencesGroup.new()
        grupo_archivo.set_title("Origen de datos")
        grupo_archivo.set_margin_top(28)
        grupo_archivo.add_css_class("margin-bottom-12")
        pag_opciones.add(grupo_archivo)

        row_cargar = Adw.ActionRow.new()
        row_cargar.set_title("Selecciona un archivo")

        btn_cargar = Gtk.Button.new_with_label("Cargar Imagen")
        btn_cargar.add_css_class("suggested-action")
        btn_cargar.set_valign(Gtk.Align.CENTER)
        btn_cargar.connect('clicked', self.show_openDialog)
        row_cargar.add_suffix(btn_cargar)
        grupo_archivo.add(row_cargar)

        # Grupo: Modo de Recorte
        grupo_recorte = Adw.PreferencesGroup.new()
        grupo_recorte.set_title("Selección / Recorte")
        grupo_recorte.set_margin_top(28)
        grupo_recorte.set_margin_bottom(12)
        pag_opciones.add(grupo_recorte)

        self.combo_recorte = Adw.ComboRow.new()
        self.combo_recorte.set_title("Tipo de área")
        lista_modos = Gtk.StringList.new(
            ["Imagen Completa", "Rectángulo", "Por Puntos (Polígono)"]
        )
        self.combo_recorte.set_model(lista_modos)
        grupo_recorte.add(self.combo_recorte)

        row_limpiar = Adw.ActionRow.new()
        row_limpiar.set_title("Memoria de trazado")
        row_limpiar.set_subtitle("Borrar máscara actual")

        self.btn_limpiar_recorte = Gtk.Button.new_with_label("Limpiar")
        self.btn_limpiar_recorte.add_css_class("flat")
        self.btn_limpiar_recorte.set_valign(Gtk.Align.CENTER)
        self.btn_limpiar_recorte.set_sensitive(False)
        row_limpiar.add_suffix(self.btn_limpiar_recorte)
        grupo_recorte.add(row_limpiar)

        # Grupo: Parámetros científicos
        grupo_parametros = Adw.PreferencesGroup.new()
        grupo_parametros.set_title("Parámetros del Algoritmo")
        grupo_parametros.set_margin_top(28)
        grupo_parametros.set_margin_bottom(12)
        pag_opciones.add(grupo_parametros)

        adj_sigma = Gtk.Adjustment.new(3, 0.1, 10.0, 0.1, 1.0, 0.0)
        self.sigma = int(adj_sigma.get_value())
        adj_sigma.connect('value_changed', self.slider_changed)
        self.row_sigma = Adw.SpinRow.new(
            adjustment=adj_sigma, climb_rate=0.1, digits=1
        )
        self.row_sigma.set_title("Sigma (σ)")
        grupo_parametros.add(self.row_sigma)

        # Diámetro (etapa 7, R6)
        adj_diametro = Gtk.Adjustment.new(0.0, 0.0, 20000.0, 1.0, 100.0, 0.0)
        self.row_diametro = Adw.SpinRow.new(
            adjustment=adj_diametro, climb_rate=1.0, digits=1
        )
        self.row_diametro.set_title("Diámetro (px)")
        self.row_diametro.set_subtitle(
            self.estado_diametro.texto_estado()
        )

        self.btn_diametro_auto = Gtk.Button.new_with_label("Auto")
        self.btn_diametro_auto.add_css_class("flat")
        self.btn_diametro_auto.set_valign(Gtk.Align.CENTER)
        self.btn_diametro_auto.set_tooltip_text(
            "Volver a estimar el diámetro automáticamente"
        )
        self.btn_diametro_auto.connect("clicked", self._volver_a_diametro_auto)
        self.row_diametro.add_suffix(self.btn_diametro_auto)

        adj_diametro.connect('value_changed', self._diametro_cambiado)
        grupo_parametros.add(self.row_diametro)

        # --- GRUPO PARA EL BOTÓN PROCESAR ---
        grupo_accion_procesar = Adw.PreferencesGroup.new()
        grupo_accion_procesar.set_margin_top(24)
        pag_opciones.add(grupo_accion_procesar)

        row_procesar = Adw.ActionRow.new()
        row_procesar.set_title("Ejecutar filtro")
        row_procesar.set_subtitle("Iniciar detección de bordes")

        self.btn_procesar = Gtk.Button.new_with_label("⚡ Procesar")
        self.btn_procesar.add_css_class("accent")
        self.btn_procesar.set_valign(Gtk.Align.CENTER)
        self.btn_procesar.set_size_request(120, 40)
        self.btn_procesar.connect("clicked", self.on_process_clicked)
        row_procesar.add_suffix(self.btn_procesar)

        grupo_accion_procesar.add(row_procesar)

        # Asignar sidebar al split view
        pagina_sidebar = Adw.NavigationPage.new(vbox_sidebar, "Controles")
        split_view.set_sidebar(sidebar=pagina_sidebar)

        # --- PANEL CENTRAL DE VISUALIZACIÓN ---
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll_visualizador = Gtk.ScrolledWindow()
        scroll_visualizador.set_hexpand(True)
        scroll_visualizador.set_vexpand(True)
        main_box.append(scroll_visualizador)

        try:
            self.image_container = self.handle.VisualizadorInteractivo()
        except Exception as e:
            self.image_container = Gtk.Picture()
            self.image_container.set_hexpand(True)
            self.image_container.set_vexpand(True)
            self.image_container.set_can_shrink(True)
            self.image_container.set_content_fit(Gtk.ContentFit.CONTAIN)
            self._logger.log(
                "WINDOW_INIT",
                "WARNING",
                f"VisualizadorInteractivo falló, usando Gtk.Picture como respaldo: "
                f"{type(e).__name__}: {e}",
            )

        scroll_visualizador.set_child(self.image_container)

        separador_inferior = Gtk.Separator(
            orientation=Gtk.Orientation.HORIZONTAL
        )
        main_box.append(separador_inferior)

        self.resultados_stack = Adw.ViewStack()
        self.resultados_stack.set_size_request(-1, 150)
        self.resultados_stack.set_vexpand(False)

        paginas = [
            ("Original", "image-x-generic-symbolic"),
            ("Gradiente X", "go-next-symbolic"),
            ("Gradiente Y", "go-down-symbolic"),
            ("Magnitud", "view-grid-symbolic"),
            ("Maximos", "view-grid-symbolic"),
            ("Bordes debiles", "view-conceal-symbolic"),
            ("Bordes fuertes", "focus-windows-symbolic"),
            ("Bordes", "focus-windows-symbolic"),
        ]

        self.vistas_procesadas = {}

        for nombre, icono in paginas:
            id_pestaña = nombre.lower()

            box_pestaña = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, spacing=4
            )
            img_result = Gtk.Picture()
            img_result.set_can_shrink(True)
            img_result.set_content_fit(Gtk.ContentFit.CONTAIN)
            box_pestaña.append(img_result)

            self.vistas_procesadas[id_pestaña] = img_result

            self.resultados_stack.add_titled_with_icon(
                box_pestaña, id_pestaña, nombre, icono
            )

        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_stack(self.resultados_stack)
        view_switcher.set_halign(Gtk.Align.CENTER)
        view_switcher.set_margin_top(8)
        view_switcher.set_margin_bottom(8)
        main_box.append(view_switcher)

        main_box.append(self.resultados_stack)

        pagina_contenido = Adw.NavigationPage.new(
            main_box, "Visualizador"
        )
        split_view.set_content(content=pagina_contenido)

    # --- Métodos de la ventana (delegan al controlador) ---

    def slider_changed(self, spinRow):
        print(spinRow.get_value())
        self.sigma = int(spinRow.get_value())

    def _diametro_cambiado(self, ajuste):
        """El usuario tocó el campo: su valor pasa a mandar sobre el barrido."""
        if self._actualizando_diametro:
            return
        self.estado_diametro.declarar_usuario(ajuste.get_value())
        self.row_diametro.set_subtitle(
            self.estado_diametro.texto_estado()
        )

    def _volver_a_diametro_auto(self, _boton):
        """Descarta el valor manual y vuelve a estimar en la próxima corrida."""
        self.estado_diametro.volver_a_auto()
        self._escribir_campo_diametro(
            self.estado_diametro.valor_visible()
        )
        self.row_diametro.set_subtitle(
            self.estado_diametro.texto_estado()
        )

    def _escribir_campo_diametro(self, valor):
        """Escribe el campo sin que cuente como cambio del usuario (R6.3)."""
        self._actualizando_diametro = True
        self.row_diametro.get_adjustment().set_value(valor)
        self._actualizando_diametro = False

    def _mostrar_diametro_detectado(self, diametro, ambiguo):
        """Corre en el hilo principal, vía GLib.idle_add."""
        self.estado_diametro.registrar_detectado(diametro, ambiguo)
        if not self.estado_diametro.es_manual:
            self._escribir_campo_diametro(
                self.estado_diametro.valor_visible()
            )
        self.row_diametro.set_subtitle(
            self.estado_diametro.texto_estado()
        )
        return False

    def _registrar_acciones(self):
        """Inicializa y registra las acciones lógicas de la ventana."""
        GLib.set_application_name("My App ODIN")

        action_cargar = Gio.SimpleAction.new("cargar_imagen", None)
        action_cargar.connect("activate", self.show_openDialog)
        self.add_action(action_cargar)

        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.show_about)
        self.add_action(action_about)

    def show_openDialog(self, button, *args):
        self.controller.on_open_dialog(button, *args)

    def on_file_opened_callback(self, dialog, response):
        self.controller.on_file_opened_callback(dialog, response)

    def on_process_clicked(self, button):
        self.controller.on_process_clicked(button)

    def finalizar_proceso_exitoso(self):
        """Este método corre en el hilo principal de la UI cuando la
        matemática termina."""
        self.mostrar_alerta(
            titulo="¡Proceso Completado!",
            mensaje=(
                "Los bordes se han calculado con éxito mediante "
                "el kernel separable."
            ),
            es_error=False,
        )

    def mostrar_alerta(self, titulo, mensaje, es_error=True):
        """Crea una ventana flotante independiente con la estética exacta
        de Adwaita."""
        dialog_win = Gtk.Window(
            title=titulo,
            transient_for=self,
            modal=True,
            resizable=False,
        )
        dialog_win.set_deletable(True)

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=16
        )
        main_box.set_margin_top(32)
        main_box.set_margin_bottom(32)
        main_box.set_margin_start(32)
        main_box.set_margin_end(32)
        dialog_win.set_child(main_box)

        lbl_mensaje = Gtk.Label()
        lbl_mensaje.set_markup(mensaje)
        lbl_mensaje.set_justify(Gtk.Justification.CENTER)
        lbl_mensaje.set_wrap(True)
        lbl_mensaje.set_max_width_chars(40)
        main_box.append(lbl_mensaje)

        button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=12
        )
        button_box.set_homogeneous(True)
        main_box.append(button_box)

        btn_cancelar = Gtk.Button(label="Cancelar")
        btn_cancelar.connect("clicked", lambda w: dialog_win.destroy())
        button_box.append(btn_cancelar)

        btn_accion = Gtk.Button(
            label="Entendido" if es_error else "Aceptar"
        )
        if es_error:
            btn_accion.add_css_class("destructive-action")
        else:
            btn_accion.add_css_class("suggested-action")

        btn_accion.connect("clicked", lambda w: dialog_win.destroy())
        button_box.append(btn_accion)

        dialog_win.add_css_class("dialog")

        css_provider = Gtk.CssProvider()
        css_code = """
            window.dialog {
                border-radius: 12px;
            }
            window.dialog > box {
                background-color: #242424;
                border: 1px solid #353535;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """
        display = dialog_win.get_display()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        dialog_win.present()

    def show_about(self, action, param):
        self.about = Gtk.AboutDialog()
        self.about.set_transient_for(self)
        self.about.set_modal(True)
        self.about.set_authors(["José Armando López Celis"])
        self.about.set_copyright("Copyright 2026 José Armando López Celis")
        self.about.set_license_type(Gtk.License.GPL_3_0)
        self.about.set_website("http://example.com")
        self.about.set_website_label("My Website")
        self.about.set_version("1.0")
        self.about.set_logo_icon_name("org.example.example")
        self.about.set_visible(True)


def main(argv=None):
    """Punto de entrada principal de ODIN.

    Puede llamarse desde otro módulo o ejecutarse directamente.
    """
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        description="ODIN — Detección de bordes y medición geométrica"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Verificar arranque e imprimir versión sin abrir la GUI",
    )
    args = parser.parse_args(argv[1:])

    if args.version:
        result = run_bootstrap(__package__)
        validator = DisplayValidator(result.logger)
        validator.validate()
        print("ODIN 1.0")
        return 0

    result = run_bootstrap(__package__)
    app = ODINAdwaita(
        bootstrap_result=result,
        logger=result.logger,
        application_id="com.detectorDistancias.Odin",
    )
    exit_status = app.run(argv)
    return exit_status


class ODINAdwaita(Adw.Application):
    def __init__(self, bootstrap_result=None, logger=None, **kwargs):
        super().__init__(**kwargs)
        self.bootstrap_result = bootstrap_result
        self.logger = logger
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        # Validación de display primero (spec: antes de construir MainWindow)
        validator = DisplayValidator(self.logger or StartupLogger())
        validator.validate()  # sys.exit(1) si falla

        self.win = OdinMainWindow(
            application=app,
            bootstrap_result=self.bootstrap_result,
            logger=self.logger,
        )

        # Logging de WINDOW_INIT completo
        if self.logger:
            duracion_ms = (time.monotonic() - self.win._t0_window) * 1000
            self.logger.log_phase_complete("WINDOW_INIT", duracion_ms)

        self.win.present()


# Instanciar y ejecutar la aplicación solo al ejecutar el archivo directamente,
# para que `import odin.views.main_window` no lance la GUI.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
