import gi
#from gi.repository.Gio import ActionGroup, ApplicationFlags, MenuModel

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk,Adw,Gio,GLib

import sys,os

from Preprocesamiento import *
from utils import *

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("ODIN")
        self.set_default_size(1600, 900)
        
        # Variable para guardar la ruta del archivo actual
        self.ruta_imagen = None
        
        
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
        pagina_estado.set_icon_name("sscanner-symbolic")
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



    def show_openDialog(self,button):
        fileDialog = Gtk.FileDialog.new()
        fileDialog.set_title("Selecciona imagen")
        
        # Intentamos localizar tu carpeta de usuario en Windows desde WSL
        # Normalmente el usuario de WSL coincide o se puede buscar en /mnt/c/Users/
        
        win_path = f"/mnt/c"
        
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
            # Lanzamos el proceso (puedes añadir un Spinner/indicador de carga aquí)
            image_loaded = loadImage.Carga_imagen_gray(self,self.ruta_imagen)
            # Obtenemos dimensiones
            height, width = image_loaded.shape
            #rowstride = width * channels
            Gx, Gy = kernelGaussiano.DerivGauss(image_loaded,3,1,1,360)
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


