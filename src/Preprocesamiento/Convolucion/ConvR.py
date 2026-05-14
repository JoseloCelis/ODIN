import numpy as np

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