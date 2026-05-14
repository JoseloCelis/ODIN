#[ MGr, angle ] 
import numpy as np

def MagFase( GrX, GrY ):
    MGr=np.sqrt(GrX*GrX+GrY*GrY)
    MGr=MGr/MGr.max()
    angle=np.atan2(GrY,GrX)*180/np.pi
    return MGr, angle