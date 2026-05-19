import sys,os
import threading

import gi
#from gi.repository.Gio import ActionGroup, ApplicationFlags, MenuModel

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk,Adw,Gio,GLib,Gdk

#from src.utils import loadImage
#from src.Preprocesamiento import kernelSeparable
#from odin import handle, kernelSeparable
from utils import handle
from Preprocesamiento import kernelSeparable

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("ODIN")
        self.set_default_size(1600, 900)
        
        # Variable para guardar la ruta del archivo actual
        self.ruta_imagen = None
        
        #print("Entorno gráfico activo:", Gtk.get_major_version(), "en", Gdk.Display.get_default().get_name())
        
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_content(self.root_box)
           
# 3. Añadir la HeaderBar (Barra superior)
        header_bar = Adw.HeaderBar()
        self.root_box.append(header_bar)

# Botón para abrir archivo
        open_button = Gtk.Button(label="Abrir Imagen")
        open_button.set_icon_name("document-open-symbolic")
        open_button.connect('clicked', self.show_openDialog)
        header_bar.pack_start(open_button)
        
# Botón para Procesar (Inicia desactivado)
        self.btn_process = Gtk.Button(label="Procesar Bordes")
        self.btn_process.set_icon_name("media-playback-start-symbolic")
        self.btn_process.set_sensitive(False) # Desactivado al inicio
        self.btn_process.add_css_class("suggested-action") # Color azul/llamativo
        self.btn_process.connect('clicked', self.on_process_clicked)
        header_bar.pack_start(self.btn_process)

# View Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.root_box.append(self.stack)
        
# 4. Añadir una Página de Estado (Status Page)
# Es un widget visualmente atractivo para bienvenidas o pantallas vacías
        pagina_estado = Adw.StatusPage()
        pagina_estado.set_title("¡ODIN Medición de distancias!")
        pagina_estado.set_description("Selecciona una imagen BMP/PNG para iniciar la detección.")
        pagina_estado.set_icon_name("scanner-symbolic")
        self.stack.add_child(pagina_estado)

# Contenedor de Imagen (Scrolled Window)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_vexpand(True)
        self.scroll.set_hexpand(True)        
# Usamos Gtk.Picture para visualizar
        self.image_container = Gtk.Picture()
        self.image_container.set_can_shrink(True)
        self.image_container.set_content_fit(Gtk.ContentFit.CONTAIN) # Ajustar sin deformar
        self.scroll.set_child(self.image_container)
        
        self.stack.add_child(self.scroll)

        menu = Gio.Menu.new()
        menu.append("Do Something", "win.something")  # Or you would do app.something if you had attached the
                                                      # action to the application

        # Create a popover
        self.popover = Gtk.PopoverMenu()  # Create a new popover menu
        self.popover.set_menu_model(menu)

        # Create a menu button
        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")  # Give it a nice icon

        # Add menu button to the header bar
        header_bar.pack_start(self.hamburger)
        # Set app name
        GLib.set_application_name("My App")

        # Create an action to run a *show about dialog* function we will create 
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.show_about)
        self.add_action(action)
        
        menu.append("About", "win.about")


    def show_openDialog(self,button):
        fileDialog = Gtk.FileDialog.new()
        fileDialog.set_title("Selecciona imagen")
        
        # Intentamos localizar tu carpeta de usuario en Windows desde WSL
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
    def on_file_opened_callback(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.ruta_imagen = file.get_path()
                print(f"File path is {file.get_path()}")
# --- Visualización
                self.image_container.set_file(file)
                self.stack.set_visible_child(self.scroll)
                
# ¡Activamos el abotón de procesar ahora que hay imagen!
                self.btn_process.set_sensitive(True)
                
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
        """Lanza un diálogo flotante perfectamente centrado, redondeado y estilizado."""
        # 1. Creamos el diálogo base completamente limpio (sin heading ni body nativos)
        # para que no choquen con nuestros márgenes personalizados.
        alert_dialog = Adw.AlertDialog.new(heading="", body="")
        
        # 2. Contenedor principal para encapsular TODO el contenido del popup
        # Le damos un ancho mínimo de 380px para mantener la estética de escritorio.
        contenedor_dialogo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        contenedor_dialogo.set_size_request(380, -1)
        
        # --- AQUÍ ESTÁ EL TRUCO DE LAS ESQUINAS INFERIORES Y MÁRGENES ---
        # Al darle 16 píxeles de margen a todo el bloque, despegamos los botones de la base
        # y los lados, permitiendo que las curvas nativas de Libadwaita se dibujen abajo.
        contenedor_dialogo.set_margin_end(16)
        contenedor_dialogo.set_margin_top(8) # Ajuste sutil para que no quede muy caído

        # 3. Título personalizado (Perfectamente centrado y despegado)
        lbl_titulo = Gtk.Label()
        lbl_titulo.set_markup(f"<b><span size='large'>{titulo}</span></b>")
        lbl_titulo.set_halign(Gtk.Align.CENTER)  # <-- Fuerza el centrado horizontal
        lbl_titulo.set_justify(Gtk.Justification.CENTER)
        contenedor_dialogo.append(lbl_titulo)

        # 4. Mensaje del cuerpo
        lbl_cuerpo = Gtk.Label(label=mensaje)
        lbl_cuerpo.set_wrap(True)
        lbl_cuerpo.set_justify(Gtk.Justification.CENTER)
        contenedor_dialogo.append(lbl_cuerpo)

        # 5. Caja horizontal compacta para los botones
        caja_botones = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        caja_botones.set_halign(Gtk.Align.CENTER)
        
        # Botón Cancelar
        btn_cancelar = Gtk.Button(label="Cancelar")
        btn_cancelar.set_size_request(110, 34)
        btn_cancelar.connect("clicked", lambda widget: alert_dialog.close())
        caja_botones.append(btn_cancelar)

        # Botón de Acción Principal (Aceptar / Entendido)
        texto_accion = "Entendido" if es_error else "Aceptar"
        btn_accion = Gtk.Button(label=texto_accion)
        btn_accion.set_size_request(110, 34)
        
        if es_error:
            btn_accion.get_style_context().add_class("destructive")
        else:
            btn_accion.get_style_context().add_class("suggested-action")
            
        btn_accion.connect("clicked", lambda widget: alert_dialog.close())
        caja_botones.append(btn_accion)

        # Añadimos la botonera al contenedor principal
        contenedor_dialogo.append(caja_botones)

        # 6. Inyectamos todo nuestro bloque estructurado al AlertDialog
        alert_dialog.set_extra_child(contenedor_dialogo)

        # Presentamos pasando None para mantener la sombra flotante impecable en Wayland
        GLib.idle_add(alert_dialog.present, None)
        
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
        #self.connect('activate', self.do_activate)
        
    def do_activate(self):
        self.win = MainWindow(application=self)        
        self.win.present()
    
    """def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()"""

# Instanciar y ejecutar la aplicación
app = ODINAdwaita(application_id="com.detectorDistancias.GTKApp")
exit_status = app.run(sys.argv)
sys.exit(exit_status)


