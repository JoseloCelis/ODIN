#[ MGr, angle ] 
import numpy as np
import cv2 as cv

def MagFase( GrX, GrY ):
    #MGr=np.sqrt(GrX*GrX+GrY*GrY)
    MGr=np.hypot(GrX,GrY)
    MGr_max = np.max(np.abs(MGr))
    if MGr_max > 0:
        MGr = MGr / MGr_max
    #MGr=MGr/MGr.max()
    angle=np.atan2(GrY,GrX)*180/np.pi
    return MGr, angle