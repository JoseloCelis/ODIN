import gi
#from gi.repository.Gio import ActionGroup, ApplicationFlags, MenuModel

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk,Adw,Gio,GLib,Gdk,GdkPixbuf

import sys,os
import threading

#from src.utils import loadImage
#from src.Preprocesamiento import kernelSeparable
#from odin import handle, kernelSeparable
from utils import handle
from Preprocesamiento import kernelSeparable

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #print("Entorno gráfico activo:", Gtk.get_major_version(), "en", Gdk.Display.get_default().get_name())

        # Variable para guardar la ruta del archivo actual
        self.ruta_imagen = None
        
        self.set_title("ODIN")
        self.set_default_size(1600, 900)
        
        #self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
# Contenedor principal adaptativo
        toolbar_view = Adw.ToolbarView.new()
        self.set_content(toolbar_view)
        #self.set_child(toolbar_view)
        
# Añadir la Barra superior  
        header_bar = Adw.HeaderBar.new()
        toolbar_view.add_top_bar(header_bar)

        #header_bar = Gtk.HeaderBar.new()
        #self.set_titlebar(header_bar)

# Botón para abrir archivo de imagen (extremo izquierdo)
        #open_button = Gtk.Button(label="Abrir Imagen")
        #open_button.set_icon_name("document-open-symbolic")
        open_button = Gtk.Button.new_from_icon_name("document-open-symbolic")
        open_button.set_tooltip_text("Cargar nueva imagen")
        open_button.connect('clicked', self.show_openDialog)
        header_bar.pack_start(open_button)
        
# Botones (extremo derecho)
# Nota: pack_end inserta de derecha a izquierda. 
        # Insertamos el menú hamburguesa PRIMERO para que ocupe la esquina derecha absoluta.
        menu = Gio.Menu.new()
        menu.append("Cargar Imagen", "win.cargar_imagen")
        #menu.append("Do Something", "win.something")  # Or you would do app.something if you had attached the action to the application
        menu.append("Acerca de...", "win.about")  
        #menu.append("Salir", "app.quit")
        #Creación del menu manualmente        
        #self.popover = Gtk.PopoverMenu()  
        #self.popover.set_menu_model(menu)
        self.hamburger = Gtk.MenuButton()
        #self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")  
        self.hamburger.set_tooltip_text("Menú principal")
        #self.hamburger.set_use_popover(False)                          ----------REVISAR
        self.hamburger.set_menu_model(menu)
        header_bar.pack_end(self.hamburger)
        
# Dar nombre a la aplicación y registrar acción
        GLib.set_application_name("My App ODIN")
        action_cargar = Gio.SimpleAction.new("cargar_imagen", None)
        action_cargar.connect("activate", self.show_openDialog)
        self.add_action(action_cargar)
        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.show_about)
        self.add_action(action_about)

# Botón para Procesar (Inicia desactivado)
        """self.btn_process = Gtk.Button(label="Procesar Bordes")
        self.btn_process.set_icon_name("media-playback-start-symbolic")
        self.btn_process.set_sensitive(False) # Desactivado al inicio
        self.btn_process.add_css_class("suggested-action") # Color azul/llamativo
        self.btn_process.connect('clicked', self.on_process_clicked)
        
        right_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right_buttons_box.append(self.btn_process)
        right_buttons_box.append(self.hamburger)
        
        # Registramos la caja al final de la HeaderBar
        header_bar.pack_end(right_buttons_box)"""
        # Add menu button to the header bar
        """
        #header_bar.pack_end(self.btn_process)
        """

# Diseño del Cuerpo Principal (Panel Dividido)
        # Usamos un Box horizontal para separar los controles de la imagen
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)       
        #main_box.set_hexpand(True)
        #main_box.set_vexpand(True) 
        toolbar_view.set_content(main_box)
                
        # PANEL IZQUIERDO: Controles de parámetros (Sigma, Umbrales, etc.)
        self.panel_controles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.panel_controles.set_size_request(200, -1) # Ancho fijo para las herramientas
        #self.panel_controles.set_margin_all(12)
        self.panel_controles.set_margin_start(6)
        self.panel_controles.set_margin_end(6)
        self.panel_controles.set_margin_top(6)
        self.panel_controles.set_margin_bottom(6)
        main_box.append(self.panel_controles)
        
        # Aquí puedes añadir tus Gtk.Scale (sliders) para Sigma y Umbrales...
        lbl_placeholder = Gtk.Label(label="⚙️ Parámetros de Filtrado")
        #lbl_placeholder.set_css_classes(["title-2"])
        self.panel_controles.append(lbl_placeholder)

# ÁREA CENTRAL DE VISUALIZACIÓN (Panel derecha)
        # Usamos un Box VERTICAL para poner la Imagen ARRIBA y las Pestañas ABAJO
        area_derecha_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        area_derecha_box.set_hexpand(True) # Absorbe todo el ancho disponible al maximizar
        area_derecha_box.set_vexpand(True) # Absorbe todo el alto disponible
        main_box.append(area_derecha_box)
        
        # PARTE SUPERIOR: Visualizador de Imagen Principal con Scroll e Interacción
        
        scroll_visualizador = Gtk.ScrolledWindow()
        
        scroll_visualizador.set_hexpand(True)
        scroll_visualizador.set_vexpand(True) # Se estira para dominar la pantalla
        
        area_derecha_box.append(scroll_visualizador)
        
        # SEPARADOR ESTÉTICO (Opcional)
        separador = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        area_derecha_box.append(separador)
        
        # Instanciamos la clase híbrida con el Overlay y el DrawingArea que hicimos en el paso anterior
        # Aquí se acopla tu clase interactiva (con Overlay/DrawingArea)
        try:
            self.image_container = VisualizadorInteractivo() 
        except NameError:
            # Fallback temporal por si corres este script solo
            self.image_container = Gtk.Picture()
            self.image_container.set_hexpand(True)
            self.image_container.set_vexpand(True) 
            self.image_container.set_can_shrink(True)
            self.image_container.set_content_fit(Gtk.ContentFit.CONTAIN) # Ajustar sin deformar
            print("Aviso: 'VisualizadorInteractivo' no detectado, usando contenedor temporal.")
        
        scroll_visualizador.set_child(self.image_container)
        
        # PARTE INFERIOR: El conmutador de resultados (Adw.ViewSwitcher + Adw.ViewStack)
        # Aquí es donde el usuario alternará entre [Original] [Kernel] [Derivada] [Bordes]
        self.resultados_stack = Adw.ViewStack()
        self.resultados_stack.set_hexpand(True)
        self.resultados_stack.set_vexpand(False) # Altura limitada para que no tape la imagen
        self.resultados_stack.set_size_request(-1, 150) # Altura fija sugerida para la sección de resultados
        
        """id_pantalla = Gdk.Display.get_default()
        tema_iconos = Gtk.IconTheme.get_for_display(id_pantalla)
        tema_iconos.add_search_path("/usr/share/icons/Adwaita/scalable")
        tema_iconos.add_search_path("/usr/share/icons/Adwaita/symbolic")
        tema_iconos.add_search_path("/usr/share/icons/Adwaita")"""
        
        # Creamos las páginas de resultados simuladas
        paginas = [
            ("Original", "document-open-symbolic"),
            ("Kernel", "media-playlist-consecutive-symbolic"),
            ("Derivada", "edit-find-symbolic"),
            ("Magnitud", "preferences-system-symbolic"),
            ("Bordes", "focus-windows-symbolic")
        ]       
       
        for nombre, icono in paginas:
            label_temp = Gtk.Label(label=f"Visualización de {nombre} pendiente ...")        
            label_temp.set_hexpand(True)
            label_temp.set_vexpand(True)
            self.resultados_stack.add_titled_with_icon(label_temp, nombre.lower(), nombre, icono)
        
         # El conmutador visual de pestañas (barra de botones)
        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_stack(self.resultados_stack)
        view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE) # Botones anchos y claros
        view_switcher.set_hexpand(True)
        view_switcher.set_halign(Gtk.Align.FILL) 
        #view_switcher.set_valign(Gtk.Align.CENTER)
        view_switcher.set_size_request(-1, 75)
        view_switcher.set_margin_top(12)
        view_switcher.set_margin_bottom(12)
                    
        # Añadimos los componentes de resultados abajo de la imagen
        area_derecha_box.append(view_switcher)
        area_derecha_box.append(self.resultados_stack)
                

        
        
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
        filtro_img.set_name("Imágenes (bmp, png, )")
        filtro_img.add_mime_type("image/bmp")
        filtro_img.add_mime_type("image/png")
        #filtro_img.add_mime_type("image/jpeg")
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
                is_error, message, image_loaded = handle.load_GrayImage(self, self.ruta_imagen)
                pixbuff = handle.matriz_a_pixbuf(image_loaded)
                self.mostrar_alerta("Mensaje Imagen", message, is_error)
# --- Visualización
                if hasattr(self.image_container, "cargar_imagen"):
                    self.image_container.cargar_imagen(pixbuff)
                else:
                    self.image_container.set_filename(self.ruta_imagen)
        except GLib.Error as error:
            
            print(f"Error al abrir el archivo: {error.message}")   
            
        
    
    def on_process_clicked(self, button):
        if self.ruta_imagen:
            # Desactivamos el botón mientras procesa para evitar clics dobles
            self.btn_process.set_sensitive(False)
            self.mostrar_alerta("Procesando", "Iniciando el cálculo de bordes...", es_error=False)
            
            # 3. Creamos un hilo de fondo para que la matemática no congele la pantalla
            hilo_matematico = threading.Thread(target=self._tarea_pesada_computacional)
            hilo_matematico.start()
         
    def _tarea_pesada_computacional(self):
        """Aquí corre toda la matemática pesada de ODIN sin congelar la app."""
        try:
            print("Hilo secundario: Iniciando convoluciones...")
            
            # --- SIMULACIÓN DE TU PROCESO REAL ---
            # Aquí es donde llamas a tus funciones de: Preprocesamiento, kernelSeparable, etc.
            # resultado = kernelSeparable.aplicar(self.ruta_imagen)
            
            # --------------------------------------
               # Lanzamos el proceso (puedes añadir un Spinner/indicador de carga aquí)
            error, mensaje, image_loaded = handle.load_GrayImage(self, self.ruta_imagen)
            
            if error:
                #self.label_estado.set_text(f"⚠️ Error: {mensaje}")
                self.mostrar_alerta("Error al cargar archivo", mensaje, error)
                self.btn_process.set_sensitive(False)
                 #print(f" Mini-alerta de error: {mensaje}")
            else:
            # Obtenemos dimensiones
                height, width = image_loaded.shape
                #rowstride = width * channels
                Gx,Gy = kernelSeparable.DerivGauss(image_loaded,3,1,1,360)

            """IGx_normalized = np.zeros((Gx.shape[0], Gx.shape[1]))
            IGx_normalized = cv.normalize(Gx, IGx_normalized, 0, 255, cv.NORM_MINMAX, dtype=cv.CV_8UC1)
            resized_Gx = cv.resize(IGx_normalized, (1280,720))
            IGy_normalized = np.zeros((Gy.shape[0], Gy.shape[1]))
            IGy_normalized = cv.normalize(Gy, IGy_normalized, 0, 255, cv.NORM_MINMAX, dtype=cv.CV_8UC1)
            resized_Gy = cv.resize(IGy_normalized, (1280,720))
            cv.imshow("Gradiente Gx", resized_Gx)
            cv.imshow("Gradiente Gy", resized_Gy)
            MG, Tetha =MagFaseGradiente.MagFase( Gx, Gy )
            #IMG_normalized = np.zeros((MG.shape[0], MG.shape[1]))
            #IMG_normalized = cv.normalize(Gx, IMG_normalized, 0, 255, cv.NORM_MINMAX, dtype=cv.CV_8UC1)
            resized_IMG = cv.resize(MG, (1280,720))
            cv.imshow("Magnitud Gradiente", resized_IMG)"""
            #GLib.idle_add(loadImage.Carga_imagen_gray, self, self.ruta_imagen, image_loaded)

            # 4. Si todo sale bien, le pedimos al hilo principal de GTK que avise al usuario.
            # IMPORTANTE: Para modificar la UI desde un hilo, usamos siempre GLib.idle_add
            GLib.idle_add(self.finalizar_proceso_exitoso)

        except Exception as e:
            # Si algo truena en la matemática, capturamos el error y avisamos de forma segura
            GLib.idle_add(self.mostrar_alerta, "Error Matemático", str(e), True)
            GLib.idle_add(self.btn_process.set_sensitive, True)

    def finalizar_proceso_exitoso(self):
        """Este método corre en el hilo principal de la UI cuando la matemática termina."""
        # Reactivamos el botón
        self.btn_process.set_sensitive(True)
        
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
        css_provider.load_from_data(css_code.encode('utf-8'))
        dialog_win.get_style_context().add_provider(
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        # -----------------------------------------------------------

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
        
class VisualizadorInteractivo(Gtk.Overlay):
    def __init__(self):
        super().__init__()
        
        # 1. Variables de control para el recorte
        self.inicio_x = 0
        self.inicio_y = 0
        self.actual_x = 0
        self.actual_y = 0
        self.arrastrando = False
        
        # 2. El Widget de la Imagen de Fondo
        self.picture = Gtk.Picture.new()
        #self.picture.set_hexpand(True)
        #self.picture.set_vexpand(True) 
        #self.picture.set_can_shrink(True)
        self.picture.set_content_fit(Gtk.ContentFit.CONTAIN) # Ajustar sin deformar
                 
        # Mantiene la relación de aspecto y escala de forma limpia en GTK 4
        #self.picture.set_keep_aspect_ratio(True)
        self.set_child(self.picture) # Se añade como el hijo base del Overlay
        
        # 3. Capa Transparente para Dibujar el Rectángulo
        self.capa_dibujo = Gtk.DrawingArea()
        # Le decimos a GTK que use la función 'draw_callback' para pintar las líneas
        self.capa_dibujo.set_draw_func(self.draw_callback)
        self.add_overlay(self.capa_dibujo) # Se encima sobre la foto
        
        # 4. Capturar los Gestos del Ratón (Clic y Arrastre)
        self.controlador_arrastre = Gtk.GestureDrag.new()
        # Registramos el clic izquierdo (botón 1)
        self.controlador_arrastre.set_button(1) 
        
        # Conectamos las señales del ciclo de arrastre
        self.controlador_arrastre.connect("drag-begin", self.on_drag_begin)
        self.controlador_arrastre.connect("drag-update", self.on_drag_update)
        self.controlador_arrastre.connect("drag-end", self.on_drag_end)
        
        # Añadimos el controlador a la capa de dibujo para que intercepte el ratón
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
        # Calculamos la posición actual sumando el desplazamiento (offset) al inicio
        self.actual_x = self.inicio_x + offset_x
        self.actual_y = self.inicio_y + offset_y
        
        # Le ordenamos al DrawingArea que se borre y se vuelva a pintar de inmediato
        self.capa_dibujo.queue_draw()

    def on_drag_end(self, gesto, offset_x, offset_y):
        """Se activa cuando el usuario suelta el botón del ratón."""
        self.arrastrando = False
        
        # Coordenadas finales calculadas del rectángulo
        x1 = min(self.inicio_x, self.actual_x)
        y1 = min(self.inicio_y, self.actual_y)
        ancho = abs(self.actual_x - self.inicio_x)
        alto = abs(self.actual_y - self.inicio_y)
        
        print(f"Recorte solicitado en coordenadas: X:{x1}, Y:{y1}, Ancho:{ancho}, Alto:{alto}")
        # TODO: Aquí mandas estas coordenadas a tu función de OpenCV/NumPy para recortar la matriz
        
        # Limpiamos el rectángulo de la pantalla al terminar
        self.inicio_x = self.inicio_y = self.actual_x = self.actual_y = 0
        self.capa_dibujo.queue_draw()

    def draw_callback(self, drawing_area, cr, width, height, user_data=None):
        """Función encargada de pintar el rectángulo usando Cairo CSS."""
        if self.arrastrando:
            # Calculamos dimensiones correctas sin importar la dirección del arrastre
            x = min(self.inicio_x, self.actual_x)
            y = min(self.inicio_y, self.actual_y)
            ancho = abs(self.actual_x - self.inicio_x)
            alto = abs(self.actual_y - self.inicio_y)
            
            # 1. Pintamos un fondo semi-transparente azul dentro del cuadro
            cr.set_source_rgba(0.0, 0.4, 1.0, 0.15) # Azul Libadwaita con 15% opacidad
            cr.rectangle(x, y, ancho, alto)
            cr.fill_preserve() # Rellena manteniendo la silueta para el borde
            
            # 2. Pintamos la línea del borde del rectángulo
            cr.set_source_rgba(0.0, 0.4, 1.0, 0.8)  # Azul más sólido
            cr.set_line_width(2.0)                  # Grosor de la línea
            # Opcional: Hacer la línea punteada estilo 'marching ants'
            cr.set_dash([4.0, 4.0], 0)
            cr.stroke() # Dibuja la línea
        
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


