import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt

from Preprocesamiento.Convolucion import *

print("DeriGauss.py =", __package__, ",",  __name__)

def DerivGauss(E,sigma,wk,wConv,wr):
    nr, nc = E.shape[:2]
    
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
    if sigma<=0:
        return np.zeros_like(E), np.zeros_like(E)
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
    
    DGX=Convolucion.Conv2D(E,dgk,gk,nk,nr,nc)
    DGY=Convolucion.Conv2D(E,gk,dgk,nk,nr,nc)
    
    
    
    
    resized_image = cv.resize(DGXocv, (1280,720))
    cv.imshow("filtered image", resized_image)
    
    y = [10]
    x = [1]
    if wk:
        fig, ax = plt.subplots(1, 2, figsize=(14, 8))
        ax[0].plot(gk)
        ax[0].set_title("Kernel")
        ax[0].set_xlabel("X")
        ax[0].set_ylabel("y")
        ax[1].plot(dgk)
        ax[1].set_title("Derivada Kernel")
        ax[1].set_xlabel("x")
        ax[1].set_ylabel("y")

    if (wConv):
        fig1, ay = plt.subplots(1, 2, figsize=(14, 8))
        ay[0].plot(DGX[wr,:])
        ay[1].plot(DGY[:,640])
        
    return DGX, DGY