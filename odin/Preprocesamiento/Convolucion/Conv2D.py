import numpy as np

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
    
def ConvR(f,gk,nk,n,ir):
    g=np.zeros((1,n))
    for i in range (0, n):
        s = 0
        j0 = i - nk 
        if j0 < 1:
            j0 = 0
        j1 = i + nk
        if j1 > n: 
            j1 = n
        for j in range(j0, j1):
            s=s + f[ir,j]*gk[i-j+nk]
        g[0,i]=s
    return g

def ConvC(f,gk,nk,n,ic):
    g=np.zeros((1,n))
    for i in range (0, n):
        s = 0
        j0 = i - nk
        if j0 < 1:
            j0 = 0
        j1 = i + nk; 
        if j1 > n: 
            j1 = n
        for j in range(j0, j1):
            s=s + f[j,ic]*gk[i-j+nk]
        g[0,i] = s
    return g
"""    if (jc==250)
        plot(g(1,:));
    plot(g(1,:));
"""