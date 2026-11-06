FROM python:3.12.13-slim-trixie

# Variables de entorno básicas
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    #PIP_NO_CACHE_DIR=1
    # Variables para asegurar que GTK encuentre los recursos
    XDG_DATA_DIRS=/usr/local/share:/usr/share
    
USER root

# Instalación de dependencias del sistema
RUN apt-get update && apt-get install -y python-is-python3\
# Herramientas de compilación
    # gcc
    cmake pkg-config \
    python3-dev libcairo2-dev build-essential \    
# Dependencias de GTK4 y Core
    #python3-gi python3-gi-cairo \
    libgtk-4-1 libgtk-4-dev gtk-4-examples \
    gir1.2-gtk-4.0 libgirepository-2.0-dev \
# Dependencias adwaita    
    libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev \
# Temas e iconos oficiales    
    adwaita-icon-theme-full \
    gnome-themes-extra \    
# Drivers de Video Aceleración por Hardware (Mesa/EGL y GLVND)
    libegl1 libgl1-mesa-dri \
    #libglx0  libglx-mesa0 libgles2 mesa-utils mesa-vulkan-drivers\    
    dbus-x11 x11-xserver-utils \
    xdg-desktop-portal xdg-desktop-portal-gtk \
# Utilidades adicionales
    git\
    gvfs gvfs-backends \
    fonts-noto-core fonts-dejavu-core fonts-noto-color-emoji\
    libnotify-bin \
    #ca-certificates \ 
    #&& python3 -m pip install --no-cache-dir git+https://github.com/pygobject/pygobject-stubs.git \
    #--ignore-installed
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# (Opcional) UUID de D-Bus si tus apps lo requieren
RUN mkdir -p /var/lib/dbus && dbus-uuidgen > /var/lib/dbus/machine-id    

# Actualizar toolchain de Python
RUN pip3 install --upgrade pip setuptools wheel


RUN python3 -m pip install --no-cache-dir \
    pygobject \
    pygobject-stubs
#--break-system-packages 

# Crear directorio de trabajo
WORKDIR /workspaces/ODIN

# Instalación de requerimientos
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Verifica que el binding de GTK4 sea importable usando el Python de la imagen (no /usr/bin/python3)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" || exit 1

#COPY . /workspaces/code

# El código fuente NO se copia a la imagen (solo requirements.txt): llega con el mount del
# devcontainer en /workspaces/ODIN. Por eso el entrypoint real es src/main.py.
CMD [ "python3", "src/main.py" ]