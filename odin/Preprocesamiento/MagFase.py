#[ MGr, angle ] 
import numpy as np

def MagFase( GrX, GrY ):
    # Entradas vacias: devolvemos tupla vacia en vez de dejar que np.max
    # truene con su mensaje interno (contrato R5.1 del spec mag-fase)
    if GrX.size == 0 or GrY.size == 0:
        return np.empty(0), np.empty(0)

    #MGr=np.sqrt(GrX*GrX+GrY*GrY)
    MGr=np.hypot(GrX,GrY)
    MGr_max = np.max(np.abs(MGr))
    if MGr_max > 0:
        MGr = MGr / MGr_max
    #MGr=MGr/MGr.max()
    angle=np.atan2(GrY,GrX)*180/np.pi
    # El spec exige (-180, 180]: -180 no puede aparecer. NumPy puede devolverlo
    # para atan2(-0.0, negativo); se mapea a 180 para cumplir el contrato.
    angle = np.where(angle == -180.0, 180.0, angle)
    return MGr, angle