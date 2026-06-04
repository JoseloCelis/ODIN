#from gi.repository import GdkPixbuf,Gdk

#import sys
import cv2 as cv
import numpy as np
from gi.repository import Gtk, Gdk, GdkPixbuf



def load_GrayImage(self, path):
# --- Carga para Procesamiento ---
    current_image = cv.imread(path)
    if current_image is None or len(current_image) < 2:
        return True, "No se pudo cargar la imagen", None
    else:
        print("La imagen se cargo correctamente")
    
    # obtener full shape 
    full_shape = current_image.shape
    print(f"Full shape imagen original: {full_shape}")
            
    try:
        if len(current_image.shape) == 3:
            grayImage = cv.cvtColor(current_image, cv.COLOR_BGR2GRAY)   
        else:
            grayImage = current_image
        
        # Obtenemos dimensiones
        full_shape = grayImage.shape
        print(f"Full shape imagen gris: {full_shape}")

        return False, "Imagen seleccionada cargada correctamente.", grayImage
    
    except Exception as e:
        return True, f"<small>Detalle técnico: {str(e)}</small>", None
       

def matriz_a_pixbuf(matriz_numpy):
    # Convierte una matriz de OpenCV/NumPy (BGR o Grises) a GdkPixbuf.Pixbuf.

    img = matriz_numpy.copy()
    
    print(f"Tipo: {img.dtype} | Dimensiones: {img.shape}")

    if img.dtype != np.uint8:
        normalized = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        cv.normalize(img, normalized, 0, 255, cv.NORM_MINMAX, cv.CV_8UC1, None)
        img=normalized

    if len(img.shape) == 2:
        matriz_rgb = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    else:
        matriz_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        
    datosBytes = matriz_rgb.tobytes()
    
    # Creamos el Pixbuf a partir de los bytes puros de memoria
    pixbuff = GdkPixbuf.Pixbuf.new_from_data(
        data=datosBytes,
        colorspace=GdkPixbuf.Colorspace.RGB,
        has_alpha=False,
        bits_per_sample=8,
        width=matriz_rgb.shape[1],  # type: ignore[union-attr],
        height=matriz_rgb.shape[0],  # type: ignore[union-attr],
        rowstride= matriz_rgb.shape[1]* matriz_rgb.shape[2]
    )
    return pixbuff

def recortar_imagen(self):
        #Calcula el área de recorte real sobre la matriz NumPy original."""
        if self.image_loaded is None:
            return None

        # Si el modo seleccionado es "Imagen Completa" (índice 0), devolvemos todo
        if self.combo_recorte.get_selected() == 0:
            return self.image_loaded.copy()

        # Dimensiones de la matriz original
        alto_imagen, ancho_imagen = self.image_loaded.shape[:2]

        # Dimensiones del widget en pantalla
        ancho_widget = self.image_container.get_width()
        alto_widget = self.image_container.get_height()

        if ancho_widget == 0 or alto_widget == 0:
            return self.image_loaded.copy()

        # Al usar Gtk.ContentFit.CONTAIN, la imagen se escala manteniendo el aspecto.
        # Calculamos el factor de escala que aplicó GTK:
        escala = min(ancho_widget / ancho_imagen, alto_widget / alto_imagen)

        # Calculamos el tamaño real de la imagen pintada en pantalla
        ancho_pintado = ancho_imagen * escala
        alto_pintado = alto_imagen * escala

        # Esquinas donde inicia la imagen dentro del widget (centrado)
        offset_x = (ancho_widget - ancho_pintado) / 2
        offset_y = (alto_widget - alto_pintado) / 2

        # 2. Traducimos las coordenadas del mouse a píxeles de la matriz
        self.xRecorte = x1 = int((self.image_container.x1 - offset_x) / escala)
        self.yRecorte = y1 = int((self.image_container.y1 - offset_y) / escala)
        x2 = int((self.image_container.x2 - offset_x) / escala)
        y2 = int((self.image_container.y2 - offset_y) / escala)
        

        # Aseguramos límites para no salirnos de la matriz (Clamping)
        x1 = max(0, min(x1, ancho_imagen))
        y1 = max(0, min(y1, alto_imagen))
        x2 = max(0, min(x2, ancho_imagen))
        y2 = max(0, min(y2, alto_imagen))

        # Si el recuadro es ridículamente pequeño (un clic fantasma), procesa completa
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return self.image_loaded.copy()

        # ¡Slicing puro de NumPy! Extraemos la submatriz
        submatriz = self.image_loaded[y1:y2, x1:x2]
        return submatriz 

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
        self.x1 = min(self.inicio_x, self.actual_x)
        self.y1 = min(self.inicio_y, self.actual_x)
        self.x2 = max(self.inicio_x, self.actual_x)
        self.y2 = max(self.inicio_y, self.actual_y)
        ancho = abs(self.actual_x - self.inicio_x)
        alto = abs(self.actual_y - self.inicio_y)
        
        print(f"Recorte solicitado en coordenadas: X:{self.x1}, Y:{self.y1}, Ancho:{ancho}, Alto:{alto}")
        # TODO: Aquí mandas estas coordenadas a tu función de OpenCV/NumPy para recortar la matriz
        
        # Limpiamos el rectángulo de la pantalla al terminar
        self.inicio_x = self.inicio_y = self.actual_x = self.actual_y = 0
        self.capa_dibujo.queue_draw()

    def draw_callback(self, drawing_area, cr, width, height, user_data=None):
        """Función encargada de pintar el rectángulo usando Cairo CSS."""
        if self.arrastrando:

            
            #alto_matriz, ancho_matriz = self.image_loaded.shape[:2]

            # Calculamos dimensiones correctas sin importar la dirección del arrastre            
            x = min(self.inicio_x, self.actual_x)
            y = min(self.inicio_y, self.actual_y)
            ancho = abs(self.actual_x - self.inicio_x)
            alto = abs(self.actual_y - self.inicio_y)
            print (width,height,alto, ancho)
            
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


# Handle loading file from here
        #current_pixbuff = GdkPixbuf.Pixbuf.new_from_data(
        #data=np.array(current_image).ravel(),  # type: ignore[union-attr]
        #colorspace=GdkPixbuf.Colorspace.RGB,
        #has_alpha=False,
        #bits_per_sample=8,
        #width=current_image.shape[1],  # type: ignore[union-attr]
        #height=current_image.shape[0],  # type: ignore[union-attr]
        #rowstride=current_image.shape[1] * current_image.shape[2],  # type: ignore[union-attr]
        #)
        #texture = Gdk.Texture.new_for_pixbuf(current_pixbuff)
        #self._image_container = Gtk.Picture.new_for_paintable(texture)
        #self._image_container.set_content_fit(Gtk.ContentFit.CONTAIN)
        #self._image_container.set_halign(Gtk.Align.CENTER)
        #self._image_container.set_valign(Gtk.Align.CENTER)
        #self._image_container.set_vexpand(True)
        #self._image_container.set_hexpand(True)"""
        
        #picture.set_paintable()
        
        #dw=CustomDraw()
        #area_dibujo = PictureWidget(dw)
                      
        #self.box3.append(dw)
        
        
        #self.box3.append(self._image_container)
                    