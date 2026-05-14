from gi.repository import GdkPixbuf,Gdk

import sys
import cv2 as cv
import numpy as np


def Carga_imagen_gray(self, path):
# --- Carga para Procesamiento ---
    current_image = cv.imread(path)
    if current_image is None:
        sys.exit("No se pudo cargar la imagen")
    else:
        print("La imagen se cargo correctamente")
# obtener full shape 
    full_shape = current_image.shape
    
    if len(current_image.shape) == 3:
        grayImage = cv.cvtColor(current_image, cv.COLOR_BGR2GRAY)   
    else:
        grayImage = current_image

# Obtenemos dimensiones
    full_shape = grayImage.shape
    print(f"Full shape: {full_shape}")
    height, width = grayImage.shape[:2]
    #rowstride = width * channels

    return grayImage
    
"""
    pixbuff = GdkPixbuf.Pixbuf.new_from_data(
        edges_rgb.tobytes(),
        GdkPixbuf.Colorspace.RGB,
        False,
        8,
        width,
        height,
        rowstride
    )
# Creamos el Pixbuf para GTK
    pixbuff = GdkPixbuf.Pixbuf.new_from_data(
        image_rgb.tobytes(),
        GdkPixbuf.Colorspace.RGB,
        False,
        8,
        width,
        height,
        rowstride
    )
# Handle loading file from here
    current_pixbuff = GdkPixbuf.Pixbuf.new_from_data(
    data=np.array(current_image).ravel(),  # type: ignore[union-attr]
    colorspace=GdkPixbuf.Colorspace.RGB,
    has_alpha=False,
    bits_per_sample=8,
    width=current_image.shape[1],  # type: ignore[union-attr]
    height=current_image.shape[0],  # type: ignore[union-attr]
    rowstride=current_image.shape[1] * current_image.shape[2],  # type: ignore[union-attr]
    )
    texture = Gdk.Texture.new_for_pixbuf(current_pixbuff)"""


                    