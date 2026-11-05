#import matplotlib
#matplotlib.use('Agg')

import numpy as np

import matplotlib.pyplot as plt
#from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg as FigureCanvas
#from matplotlib.figure import Figure

from gi.repository import GLib

from .Convolucion import Conv2D as Convolucion

print("DeriGauss.py =", __package__, ",",  __name__)

def DerivGauss(E,sigma,wk,wConv,wr):
    nr, nc = E.shape[:2]
    
    # Validar sigma ANTES de dimensionar gk/dgk con n = 3*sigma
    # (con sigma negativo, np.zeros(n*2+1) lanzaria ValueError antes del guard)
    if sigma<=0:
        return np.zeros_like(E), np.zeros_like(E)

    """if nargin < 5
        wr=round(nr/2);
        wc=round(nc/2);
    end
    if nargin < 4
        wConv=0;
    end
    if nargin < 3
        wConv=0;
        wk=0;
    end"""

#//////////////////////// genera kernel derivada gaussiana   
    ds = 0
    #s2 = 2.0*sigma**2
    #s2 = 2*np.pow(sigma,2)
    s2 = 2*pow(sigma, 2)
    n=3*sigma
    #gk=[0]*((n*2)+1)
    gk=np.zeros((n*2)+1)
    dgk=np.zeros((n*2)+1)
    #dgk=[0]*((n*2)+1)
    k=0
    l=0
    s=0
    for i in range(-n, n+1):
       gk[k] = np.exp(-(i**2)/s2 )
       s=s+gk[k]
       k=k+1
    k=0
    l=0
    s2 = 1.0/pow(sigma,2)
    for i in range(-n, n+1):
        gk[k] = gk[k]/s
        dgk[k] = -s2*i*gk[k]
        k=k+1
    
    nk = 3*sigma
    
    DGX=np.zeros((nr,nc))
    DGY=np.zeros((nr,nc))
    #DGx_normalized = np.zeros((nr, nc))
    #DGy_normalized = np.zeros((nr, nc))
    
    DGX = Convolucion.Conv2D(E,dgk,gk,nk,nr,nc)
    #GLib.idle_add(dibujar_en_hilo_principal,gk, dgk, wk, 0, wr, DGX, DGY)    
    DGY = Convolucion.Conv2D(E,gk,dgk,nk,nr,nc)
    GLib.idle_add(dibujar_en_hilo_principal,gk, dgk, wk, wConv, wr, DGX, DGY)
    
    
    return DGX,DGY

def dibujar_en_hilo_principal(gk, dgk, wk, wConv, wr, DGX, DGY):
    """ventana_popup = Adw.Window()
    ventana_popup.set_title("Visualización de Kernels")
    ventana_popup.set_default_size(900, 500)
    ventana_popup.set_destroy_with_parent(False)"""
    
    if wk:
        """fig = Figure (figsize=(10,4), dpi=100)
        kernel = [fig.add_subplot(1,2,1)]
        kernel = [fig.add_subplot(1,2,2)]
        kernel[0].plot(gk)
        kernel[0].set_title("Kernel")
        kernel[0].set_xlabel("X")
        kernel[0].set_ylabel("y")
        kernel[1].plot(dgk)
        kernel[1].set_title("Derivada Kernel")
        kernel[1].set_xlabel("x")
        kernel[1].set_ylabel("y")
        
        fig1.tight_layout()
        
        canvas = FigureCanvas(fig)
        canvas.set_hexpand(True)
        canvas.set_vexpand(True)
        
        ventana_popup.set_content(canvas)
        ventana_popup.present()"""
        
        fig1, kernel = plt.subplots(1, 2, figsize=(12, 6)) 
        kernel[0].plot(gk)
        kernel[0].set_title("Kernel")
        kernel[0].set_xlabel("X")
        kernel[0].set_ylabel("y")
        kernel[1].plot(dgk)
        kernel[1].set_title("Derivada Kernel")
        kernel[1].set_xlabel("x")
        kernel[1].set_ylabel("y")
        plt.show(block=False)

    if (wConv):
        # Acotar cortes al tamaño real de la imagen
        # (la columna 640 estaba hardcodeada: IndexError con <641 columnas)
        # nr/nc no viven en este scope; usar la forma de DGX directamente.
        wr_valido = min(max(wr, 0), DGX.shape[0] - 1)
        wc = min(640, DGX.shape[1] - 1)
        gradientes, ay = plt.subplots(1, 2, figsize=(12, 6))
        ay[0].set_title("Derivada Gradiente en X")
        ay[0].plot(DGX[wr_valido,:])
        ay[1].set_title("Derivada Gradiente en Y")
        ay[1].plot(DGY[:,wc])
        plt.show(block=False)
    
    return False