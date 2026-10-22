# Design Document — mag-fase

## 1. Revisión de la implementación actual

Código completo revisado (`MagFase.py`, 13 líneas):

```python
def MagFase( GrX, GrY ):
    MGr=np.hypot(GrX,GrY)
    MGr_max = np.max(np.abs(MGr))
    if MGr_max > 0:
        MGr = MGr / MGr_max
    angle=np.atan2(GrY,GrX)*180/np.pi
    return MGr, angle
```

**Veredicto: sin bugs críticos.** A diferencia de la etapa ① (donde el spec
encontró el off-by-one del soporte del kernel), acá la matemática es correcta y
las guardas existen (`MGr_max > 0`). Es un spec de caracterización: fija el
contrato correcto.

### Evidencia de ejecución (batería previa al spec)

| Caso | Resultado |
|---|---|
| `GrX=3, GrY=4` | `MGr=1.0`, `angle=53.1301°` ✓ teórico |
| Imagen plana (zeros) | salida ceros, sin división por cero ✓ |
| 50×50 aleatoria | `MGr ∈ [0.0041, 1.0]`; `angle ∈ (-180, 180]`; `mod360 ∈ [0, 360)` ✓ |
| `MGr × max == hypot` crudo | `True` (rtol 1e-12) ✓ |
| Arrays vacíos | `ValueError` de NumPy (D3) |

## 2. Divergencias registradas

- **D1 (menor)**: `import cv2 as cv` sin uso — dependencia muerta; viola R4.1.
  Quitarlo es trivial y elimina el requisito implícito de que el módulo tenga
  OpenCV instalado para importarse.
- **D2 (cosmético)**: `np.abs(MGr)` es redundante — `hypot` siempre devuelve
  ≥ 0. Sin efecto numérico; se documenta, no se toca (cambiarlo no aporta).
- **D3 (degradado)**: entradas vacías → `ValueError` con mensaje interno de
  NumPy. Imposible en el flujo real de la app (siempre hay imagen cargada),
  pero frágil como contrato de librería. Opción: retorno de tuplas vacías.
- **D4 (contrato, intencional)**: la normalización global hace que `MGr` no sea
  comparable entre imágenes; es la base para que Otsu opere en `[0,1]`.
  Documentado como R2.4, no es un defecto.

## 3. Decisiones pendientes (usuario)

1. Quitar `import cv2` (D1) — recomendado, cambio de una línea.
2. Guarda de arrays vacíos (D3) — recomendado posponer: agregarla solo cuando
   exista suite de tests que la ejerza; hoy sería código sin consumidor.

## 4. Verificación

La batería previa a este spec (tabla de arriba) cubre R1-R3 y R5-D3. Tras
cualquier cambio en el módulo, reejecutarla; los valores concretos de los ACs
(3-4-5, rangos) son el contrato.
