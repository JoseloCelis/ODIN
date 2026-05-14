import numpy as np
from Preprocesamiento.Convolucion.ConvR import *
from Preprocesamiento.Convolucion.ConvC import *

print("Conv2D.py =", __package__, ",",  __name__)


def Conv2D(g,gkr,gkc,nk,nr,nc):
    h=np.zeros((nr,nc))
    f=np.zeros((nr,nc))
    for i in range(0, nr):
        temp=ConvR(g,gkr,nk,nc,i)
        #DGXocv = cv.sepFilter2D(E, -1, gk, gk)
        h[i,:]=temp
    for i in range(0, nc):
        temp=ConvC(h,gkc,nk,nr,i)
        f[:,i]=temp
    return f
    
