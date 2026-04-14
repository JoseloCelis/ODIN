import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk,Gdk,Adw

boton=Gtk.Button(label="Hola")


def setup_display_settings():

# En tu método do_activate o __init__
    style_manager = Adw.StyleManager.get_default()
    style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
    
    

def on_activate(app):
    setup_display_settings()
    window = Gtk.ApplicationWindow(application=app)
    
    # Detectar qué renderizador estamos usando
    # GSK_RENDERER es la variable que enviamos desde el script .sh
    renderer = os.environ.get('GSK_RENDERER', 'No definido (default)')
    
    #window.set_default_size(600, 400)
    window.present()
    # Creamos una barra de título nativa de GTK (HeaderBar)
    header = Gtk.HeaderBar()
    window.set_titlebar(header)
        
    # Cambiar título según el modo
    if renderer == 'opengl':
        window.set_title(f"🚀 Modo GPU (Acelerado)")
    elif renderer == 'cairo':
        window.set_title(f"🐢 Modo CPU (Cairo)")
    else:
        window.set_title(f"App GTK - Render: {renderer}")

    # Contenido básico
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_margin_top(20)
    label = Gtk.Label(label=f"Renderizador actual: {renderer.upper()}")
    box.append(label)
    
    window.set_child(box)
    window.set_default_size(500, 300)
    window.present()

#app = Gtk.Application(application_id='com.tu.app')
app = Gtk.Application(application_id='com.debug.render')
app.connect('activate', on_activate)
app.run(None)




