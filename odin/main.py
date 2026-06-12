import gi

#from gi.repository.Gio import ActionGroup, ApplicationFlags, MenuModel

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk,Adw,Gio,GLib,Gdk

import sys,os
import threading
import numpy as np

#from src.utils import loadImage
#from src.Preprocesamiento import kernelSeparable
#from odin import handle, kernelSeparable
from utils import handle
from Preprocesamiento import kernelSeparable, MagnitudGradiente, Otsu, NonMaxSup, DoubleTh, aproxHough, circleFilter, LSC

class MainWindow(Adw.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Variables de control
        self.ruta_imagen = None
        self.image_loaded = None
        
        # Configuración de la ventana principal
        self.set_title("ODIN")
        self.set_default_size(1600, 900)
        self.set_size_request(width=1024, height=600)
        
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

        # Botones de control (Extremo derecho - De derecha a izquierda)
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

        # Registro de acciones lógicas de la ventana
        self._registrar_acciones()

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

        # Usamos Adw.PreferencesPage con márgenes perimetrales amplios
        pag_opciones = Adw.PreferencesPage.new()
        pag_opciones.set_margin_start(20)   # Más separación del borde izquierdo
        pag_opciones.set_margin_end(16)     # Más separación de la zona del visualizador
        pag_opciones.set_margin_top(24)     # Aire superior generoso
        pag_opciones.set_margin_bottom(24)  # Aire inferior generoso
        scroll_sidebar.set_child(pag_opciones)
        
        # Grupo: Archivo
        grupo_archivo = Adw.PreferencesGroup.new()
        grupo_archivo.set_title("Origen de datos")
        grupo_archivo.set_margin_top(28)
        grupo_archivo.add_css_class("margin-bottom-12")
        pag_opciones.add(grupo_archivo)
        
        row_cargar = Adw.ActionRow.new()
        row_cargar.set_title("Selecciona un archivo")
        #row_cargar.set_subtitle("Selecciona un archivo del disco")
        
        btn_cargar = Gtk.Button.new_with_label("Cargar Imagen")
        btn_cargar.add_css_class("suggested-action")
        btn_cargar.set_valign(Gtk.Align.CENTER)
        btn_cargar.connect("clicked", self.show_openDialog)
        row_cargar.add_suffix(btn_cargar)
        grupo_archivo.add(row_cargar)

        # Grupo: Modo de Recorte
        grupo_recorte = Adw.PreferencesGroup.new()
        grupo_recorte.set_title("Selección / Recorte")
        grupo_recorte.set_margin_top(28)     # Separación contundente entre bloques (Bloque anterior -> Bloque nuevo)
        grupo_recorte.set_margin_bottom(12)  # Despega el título de su tarjeta
        pag_opciones.add(grupo_recorte)

        self.combo_recorte = Adw.ComboRow.new()
        self.combo_recorte.set_title("Tipo de área")
        #self.combo_recorte.set_subtitle("Elige cómo interactuar con el ratón")
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

        adj_sigma = Gtk.Adjustment.new(2.5, 0.1, 10.0, 0.1, 1.0, 0.0)
        adj_sigma.connect('value_changed', self.slider_changed)
        self.row_sigma = Adw.SpinRow.new(adjustment=adj_sigma, climb_rate=0.1, digits=1)
        self.row_sigma.set_title("Sigma (σ)")
        grupo_parametros.add(self.row_sigma)

        """adj_umb_bajo = Gtk.Adjustment.new(50.0, 0.0, 255.0, 1.0, 10.0, 0.0)
        self.row_umbral_bajo = Adw.SpinRow.new(adjustment=adj_umb_bajo, climb_rate=1.0, digits=0)
        self.row_umbral_bajo.set_title("Umbral Mínimo (Histéresis)")
        grupo_parametros.add(self.row_umbral_bajo)

        adj_umb_alto = Gtk.Adjustment.new(150.0, 0.0, 255.0, 1.0, 10.0, 0.0)
        self.row_umbral_alto = Adw.SpinRow.new(adjustment=adj_umb_alto, climb_rate=1.0, digits=0)
        self.row_umbral_alto.set_title("Umbral Máximo (Histéresis)")
        grupo_parametros.add(self.row_umbral_alto)"""
        
        # --- NUEVO GRUPO INDEPENDIENTE PARA EL BOTÓN PROCESAR ---
        grupo_accion_procesar = Adw.PreferencesGroup.new()
        grupo_accion_procesar.set_margin_top(24)  # Genera la separación física con las SpinRows de arriba
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
        
        # Lo añadimos al nuevo contenedor aislado
        grupo_accion_procesar.add(row_procesar)

        # Asignamos al Sidebar
        pagina_sidebar = Adw.NavigationPage.new(vbox_sidebar, "Controles")
        split_view.set_sidebar(sidebar=pagina_sidebar)
        
        # --- PANEL CENTRAL DE VISUALIZACIÓN ---
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)       
                
        # Superior: Visualizador de Imagen Principal con Scroll
        scroll_visualizador = Gtk.ScrolledWindow()
        scroll_visualizador.set_hexpand(True)
        scroll_visualizador.set_vexpand(True) 
        main_box.append(scroll_visualizador)
        
        try:
            self.image_container = handle.VisualizadorInteractivo() 
        except NameError:
            self.image_container = Gtk.Picture()
            self.image_container.set_hexpand(True)
            self.image_container.set_vexpand(True) 
            self.image_container.set_can_shrink(True)
            self.image_container.set_content_fit(Gtk.ContentFit.CONTAIN)
            print("Aviso: 'VisualizadorInteractivo' no detectado, usando contenedor temporal.")
        
        scroll_visualizador.set_child(self.image_container)
        
        # Separador inferior para resultados
        separador_inferior = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(separador_inferior)
        
        # Inferior: Conmutador de resultados (Adw.ViewStack)
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
            ("Bordes", "focus-windows-symbolic")
        ]   
        
        self.vistas_procesadas = {}    
       
        for nombre, icono in paginas:
            id_pestaña = nombre.lower()
            
            box_pestaña = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            #box_pestana.set_margin_all()
            img_result = Gtk.Picture()
            img_result.set_can_shrink(True)
            img_result.set_content_fit(Gtk.ContentFit.CONTAIN)
            box_pestaña.append(img_result)
            
            self.vistas_procesadas[id_pestaña] = img_result
            
            self.resultados_stack.add_titled_with_icon(box_pestaña, id_pestaña, nombre, icono)
            
            #label_temp = Gtk.Label(label=f"Visualización de {nombre} pendiente ...")        
            #label_temp.set_hexpand(True)
            #label_temp.set_vexpand(True)
            #self.resultados_stack.add_titled_with_icon(label_temp, nombre.lower(), nombre, icono)
            
        # El conmutador visual de pestañas
        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_stack(self.resultados_stack)
        view_switcher.set_halign(Gtk.Align.CENTER) 
        view_switcher.set_margin_top(8)
        view_switcher.set_margin_bottom(8)
        main_box.append(view_switcher)
        
        main_box.append(self.resultados_stack)
        
        # Integración del bloque central al split view
        pagina_contenido = Adw.NavigationPage.new(main_box, "Visualizador")
        split_view.set_content(content=pagina_contenido)
        
    def slider_changed(self, spinRow):
            print(spinRow.get_value())    
            self.sigma = int(spinRow.get_value())

    def _registrar_acciones(self):
        """Inicializa y registra las acciones lógicas de la ventana."""
        GLib.set_application_name("My App ODIN")

        action_cargar = Gio.SimpleAction.new("cargar_imagen", None)
        action_cargar.connect("activate", self.show_openDialog)
        self.add_action(action_cargar)

        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.show_about)
        self.add_action(action_about)
        
                    
        # Añadimos los componentes de resultados abajo de la imagen
        #area_derecha_box.append(view_switcher)
        #area_derecha_box.append(self.resultados_stack)
                

        
        
# View Stack
        """self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        #self.root_box.append(self.stack)
        
# 4. Añadir una Página de Estado (Status Page)
# Es un widget visualmente atractivo para bienvenidas o pantallas vacías
        pagina_estado = Adw.StatusPage()
        pagina_estado.set_title("¡ODIN Medición de distancias!")
        pagina_estado.set_description("Selecciona una imagen BMP/PNG para iniciar la detección.")
        pagina_estado.set_icon_name("scanner-symbolic")
        self.stack.add_child(pagina_estado)

"""

    def show_openDialog(self, button, *args):
        fileDialog = Gtk.FileDialog.new()
        fileDialog.set_title("Selecciona la imagen")
        
        # Localizar tu carpeta de usuario en Windows desde WSL
        # Normalmente el usuario de WSL coincide o se puede buscar en /mnt/c/Users/
        
        win_path = f"/mnt/c/Users/jolopez"
        
        # Si la carpeta existe, le pedimos al diálogo que empiece ahí
        if os.path.exists(win_path):
            folder = Gio.File.new_for_path(win_path)
            fileDialog.set_initial_folder(folder)
            
        # Filtro para imágenes
        filtros = Gio.ListStore.new(Gtk.FileFilter)
        filtro_img = Gtk.FileFilter()
        filtro_img.set_name("Imágenes (bmp, tiff, jpeg)")
        filtro_img.add_mime_type("image/bmp")
        filtro_img.add_mime_type("image/tiff")
        filtro_img.add_mime_type("image/jpeg")
        filtros.append(filtro_img)
        fileDialog.set_filters(filtros)

        fileDialog.open(self, None, self.on_file_opened_callback)
        
    # Configurar el selector de archivos
    def on_file_opened_callback(self, dialog, response):
        try:
            file = dialog.open_finish(response)
            if file:
                self.ruta_imagen = file.get_path()
                print(f"File path is {file.get_path()}")
                is_error, message, self.image_loaded = handle.load_GrayImage(self, self.ruta_imagen)
                pixbuff = handle.matriz_a_pixbuf(self.image_loaded)
                self.mostrar_alerta("Mensaje Imagen", message, is_error)
# --- Visualización
                if hasattr(self.image_container, "cargar_imagen"):
                    self.image_container.cargar_imagen(pixbuff) # type: ignore
                else:
                    self.image_container.set_filename(self.ruta_imagen)  # type: ignore
        except GLib.Error as error:
            
            print(f"Error al abrir el archivo: {error.message}")   
            
        
    
    def on_process_clicked(self, button):
        if self.ruta_imagen:
            # Desactivamos el botón mientras procesa para evitar clics dobles
            #self.btn_process.set_sensitive(False)
            self.mostrar_alerta("Procesando", "Iniciando el cálculo de bordes...", es_error=False)
            
            self.current_image = handle.recortar_imagen(self)
            
            
            # 3. Creamos un hilo de fondo para que la matemática no congele la pantalla
            hilo_matematico = threading.Thread(target=self._tarea_pesada_computacional)
            hilo_matematico.start()
         
    def _tarea_pesada_computacional(self):
        """Aquí corre toda la matemática pesada de ODIN sin congelar la app."""
        try:
            print("Hilo secundario: Iniciando convoluciones...")
            # Lanzamos el proceso (puedes añadir un Spinner/indicador de carga aquí)
            #error, mensaje, image_loaded = handle.load_GrayImage(self, self.ruta_imagen)
            #if error:
                #self.label_estado.set_text(f"⚠️ Error: {mensaje}")6
            #    self.mostrar_alerta("Error al cargar archivo", mensaje, error)
            #    self.btn_procesar.set_sensitive(False)
                 #print(f" Mini-alerta de error: {mensaje}")
            #else:
            resultadosProcesamiento = {}
            resultadosProcesamiento["inicial"] = handle.matriz_a_pixbuf(self.current_image)
            
            Gx,Gy = kernelSeparable.DerivGauss(self.current_image,self.sigma,1,1,360)
            MG, Tetha = MagnitudGradiente.MagFase( Gx, Gy )
            GNMaxS = NonMaxSup.LinearInterpolation(MG, Gx, Gy, Tetha)
            umbral=Otsu.umbralOtsu(GNMaxS, histo=True);
            HighE, LowE = NonMaxSup.DobleThreshold(GNMaxS, Tetha, umbral)
            DetectedEdges = DoubleTh.EdgeTrack_Hyst(HighE, LowE)
            print(f"Total de bordes detectados (Px): {np.sum(DetectedEdges == 1)}")
            
            resultadosProcesamiento["gx"] = handle.matriz_a_pixbuf(Gx)
            resultadosProcesamiento["gy"] = handle.matriz_a_pixbuf(Gy)
            resultadosProcesamiento["mag"] = handle.matriz_a_pixbuf(MG)
            resultadosProcesamiento["maximos"] = handle.matriz_a_pixbuf(GNMaxS)
            resultadosProcesamiento["bordesdebiles"] = handle.matriz_a_pixbuf(LowE)
            resultadosProcesamiento["bordesfuertes"] = handle.matriz_a_pixbuf(HighE)
            resultadosProcesamiento["bordes"] = handle.matriz_a_pixbuf(DetectedEdges)
            
            self.vistas_procesadas["original"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["inicial"]))
            self.vistas_procesadas["gradiente x"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["gx"]))
            self.vistas_procesadas["gradiente y"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["gy"]))
            self.vistas_procesadas["magnitud"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["mag"]))
            self.vistas_procesadas["maximos"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["maximos"]))
            self.vistas_procesadas["bordes debiles"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordesdebiles"]))
            self.vistas_procesadas["bordes fuertes"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordesfuertes"]))
            self.vistas_procesadas["bordes"].set_paintable(Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordes"]))            
        
            diametro=253    
            xRecortada, yRecortada, n, accumulador = aproxHough.hough_circles_vectorizado(DetectedEdges, diametro/2, 0.8)  
            aproxCenter = (xRecortada, yRecortada)
            puntosFiltrados = circleFilter.find_circle(DetectedEdges, diametro/2, aproxCenter)
            x, y, r, pv = LSC.Circulo_simple(puntosFiltrados)
            x = self.xRecorte+x
            y = self.yRecorte+y
            GLib.idle_add(self.finalizar_proceso_exitoso)

        except Exception as e:
            # Si algo truena en la matemática, capturamos el error y avisamos de forma segura
            GLib.idle_add(self.mostrar_alerta, "Error Matemático", str(e), True)
            GLib.idle_add(self.btn_procesar.set_sensitive, True)

    def finalizar_proceso_exitoso(self):
        """Este método corre en el hilo principal de la UI cuando la matemática termina."""
        pass        # Reactivamos el botón
        #self.btn_process.set_sensitive(True)
        
        # Lanzamos el pop-up de éxito que ahora sí saldrá en su momento justo
        self.mostrar_alerta(
            titulo="¡Proceso Completado!", 
            mensaje="Los bordes se han calculado con éxito mediante el kernel separable.", 
            es_error=False
        )
        
    def mostrar_alerta(self, titulo, mensaje, es_error=True):
        """"Crea una ventana flotante independiente con la estética exacta de Adwaita."""
        # 1. Definimos una ventana secundaria real
        dialog_win = Gtk.Window(
            title=titulo,
            transient_for=self,     # Se vincula a MainWindow pero flota sobre ella
            modal=True,              # Bloquea la interacción de la ventana de atrás
            resizable=False
        )
        
        # 2. Forzamos que use las decoraciones del sistema ocultando la barra superior clásica
        # si quieres el look limpio y cuadrado/redondeado de Adw.AlertDialog
        dialog_win.set_deletable(True)
        
        # 3. Contenedor principal con fondo oscuro estilizado (Caja vertical con márgenes amplios)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(32)
        main_box.set_margin_bottom(32)
        main_box.set_margin_start(32)
        main_box.set_margin_end(32)
        dialog_win.set_child(main_box)

        # 4. Título centrado en negrita (Heading)
        """lbl_titulo = Gtk.Label()
        lbl_titulo.set_markup(f"<span weight='bold' size='large'>{titulo}</span>")
        lbl_titulo.set_justify(Gtk.Justification.CENTER)
        main_box.append(lbl_titulo)"""

        # 5. Mensaje centrado con ajuste automático de caracteres (Body)
        lbl_mensaje = Gtk.Label()
        lbl_mensaje.set_markup(mensaje)
        lbl_mensaje.set_justify(Gtk.Justification.CENTER)
        lbl_mensaje.set_wrap(True)
        lbl_mensaje.set_max_width_chars(40) # Esto emula el ancho físico que ves en tu ejemplo
        main_box.append(lbl_mensaje)

        # 6. Fila de botones (Caja horizontal con distribución homogénea)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_homogeneous(True) # Hace que ambos botones midan exactamente lo mismo
        main_box.append(button_box)

        # Botón Cancelar (Look gris estándar)
        btn_cancelar = Gtk.Button(label="Cancelar")
        btn_cancelar.connect("clicked", lambda w: dialog_win.destroy())
        button_box.append(btn_cancelar)

        # Botón de Acción Principal (Entendido / Reemplazar)
        btn_accion = Gtk.Button(label="Entendido" if es_error else "Aceptar")
        
        # Aplicamos las clases CSS oficiales de Gnome para pintar los botones de color
        if es_error:
            btn_accion.add_css_class("destructive-action") # Botón Rojo de Adwaita
        else:
            btn_accion.add_css_class("suggested-action")   # Botón Azul de Adwaita

        btn_accion.connect("clicked", lambda w: dialog_win.destroy())
        button_box.append(btn_accion)

        dialog_win.add_css_class("dialog")
        
        # 2. Inyectamos un CSS sutil para asegurar que el motor de renderizado no pinte bordes rígidos
        css_provider = Gtk.CssProvider()
        css_code = """
            window.dialog {
                border-radius: 12px;
            }
            window.dialog > box {
                background-color: #242424;    /* Color de fondo oficial Adwaita Oscuro */
                border: 1px solid #353535;    /* Borde exterior sutil para dar volumen */
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """
        display = dialog_win.get_display()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


        # 7. Desplegamos de forma flotante
        dialog_win.present()

        
    def show_about(self, action, param):
        self.about = Gtk.AboutDialog()
        self.about.set_transient_for(self)  # Makes the dialog always appear in from of the parent window
        self.about.set_modal(True)  # Makes the parent window unresponsive while dialog is showing

        self.about.set_authors(["José Armando López Celis"])
        self.about.set_copyright("Copyright 2026 José Armando López Celis")
        self.about.set_license_type(Gtk.License.GPL_3_0)
        self.about.set_website("http://example.com")
        self.about.set_website_label("My Website")
        self.about.set_version("1.0")
        self.about.set_logo_icon_name("org.example.example")  # The icon will need to be added to appropriate location"""
        
        """dialog=Adw.AboutWindow(transient_for=app.get_active_window()) 
        dialog.set_application_name("App name") 
        dialog.set_version("1.0") 
        dialog.set_developer_name("Developer") 
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0)) 
        dialog.set_comments("Adw about Window example") 
        dialog.set_website("https://github.com/Tailko2k/GTK4PythonTutorial") 
        dialog.set_issue_url("https://github.com/Tailko2k/GTK4PythonTutorial/issues") 
        dialog.add_credit_section("Contributors",["Name1 url"]) 
        dialog.set_translator_credits("Name1 url") 
        dialog.set_copyright("© 2022 developer") 
        dialog.set_developers(["Developer"]) 
        dialog.set_application_icon("com.github.devname.appname") # icon must be uploaded in ~/.local/share/icons or /usr/share/icons                                         # E.g. /usr/share/icons/hicolor/scalable/apps/org.example.example.svg
        dialog.set_visible(True)"""
        
        self.about.set_visible(True)    
        
        
        
class ODINAdwaita(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
     
    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()    
        
    """def do_activate(self):
        Adw.Application.do_activate(self)
        self.win = MainWindow(application=self)        
        self.win.present()"""

# Instanciar y ejecutar la aplicación
app = ODINAdwaita(application_id="com.detectorDistancias.Odin")
exit_status = app.run(sys.argv)
sys.exit(exit_status)


