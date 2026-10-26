# Design Document — edge-track-hyst (etapa ⑥)

## 1. Estado del módulo

`DThEdgeTrackHyst.py` (152 líneas) contiene **dos implementaciones**:

| Símbolo | Algoritmo | Llamadores | Estado |
|---|---|---|---|
| `EdgeTrack_Hyst(strong, weaks)` | OpenCV: dilate 7×7 + connectedComponents(8) | `main.py:426` | **en producción** |
| `DThEdgeTrack(MG, threshold)` | MATLAB: 3 pasadas + recursión | **0** | código muerto |
| `FindConnectedWeakEdges(Gmag, row, col)` | recursiva, ventana 7×7 | 1 (la anterior) | código muerto |

`main.py` hace:

```python
HighE, LowE = NonMaxSup.DobleThreshold(GNMaxS, uOtsu)
DetectedEdges = DoubleTh.EdgeTrack_Hyst(HighE, LowE)
print(f"Total de bordes detectados (Px): {np.sum(DetectedEdges == 1)}")
```

## 2. Evidencia ejecutada

### 2.1 Radio de alcance (máscaras reales de `DobleThreshold`, débil = 0.30)

| Distancia | Horizontal | Diagonal |
|---|---|---|
| 1 | conservado | — |
| 2 | conservado | conservado |
| 3 | conservado | conservado |
| 4 | **descartado** | **descartado** |
| 5 | descartado | — |

→ coincide exactamente con la dilatación 7×7 (Chebyshev ≤ 3), que a su vez
preserva el radio ±3 de la versión MATLAB.

### 2.2 Vectorizada vs recursiva

| Caso | vec | rec | solo_vec | solo_rec |
|---|---|---|---|---|
| fuerte + débil d=3 + débil d=6 | 2 | 3 | 0 | **1** |
| fuerte + línea débil continua | 13 | 13 | 0 | 0 |
| fuerte + débiles cada 3 px | 2 | 7 | 0 | **5** |
| aleatoria uniforme 60×60 | 2714 | 2765 | 0 | **51** |
| aleatoria sesgada 60×60 | 1782 | 1896 | 0 | **114** |

`solo_vec = 0` **siempre**: todo lo que conserva la vectorizada lo conserva la
recursiva, y no al revés. La recursiva propaga saltos de hasta 3 px **entre
islas**, cosa que la vectorizada no hace (R5).

### 2.3 Rendimiento y límites

| Implementación | 300×300 (ruido, umbral 0.5) |
|---|---|
| vectorizada | **6.9 ms**, 67 537 blancos |
| recursiva | **RecursionError** (`maximum recursion depth exceeded`) |

La recursiva no sobrevive a una imagen de 300×300. Además
`sys.setrecursionlimit(10000)` es un **efecto global** que no se restaura.

### 2.4 Casos degenerados

| Entrada | Resultado |
|---|---|
| fuerte vacío, débil lleno | 0 blancos ✓ |
| fuerte 1 px, débil vacío | 1 blanco ✓ |
| ambos vacíos | 0 blancos ✓ |
| arreglo `(0, 0)` | **ValueError** (D1) → **hoy devuelve salida vacía** |
| `1×1` | ok |

Causa de D1: los `print` de diagnóstico calculan `np.max(strong)` sobre un
arreglo vacío; `np.max` no tiene identidad para tamaño cero.

### 2.5 Contrato de la salida

`dtype=uint8`, valores únicos `[0, 255]`, `np.sum(salida == 1) == 0`.

## 3. Divergencias registradas

- **D1 (defecto real) — RESUELTO**: entrada vacía → `ValueError` por `np.max`.
  Causa: los `print` de diagnóstico calculan `np.max(strong)` sobre un arreglo
  vacío y `np.max` no tiene identidad para tamaño cero (además OpenCV rechaza
  imágenes vacías). Fix aplicado: guarda temprana en `EdgeTrack_Hyst`
  (`strong.size == 0` → salida vacía con su forma; `weaks.size == 0` → solo
  fuertes). Test en rojo primero, verde después.
- **D2 (semántica, no defecto)**: la vectorizada no une islas separadas por
  huecos ≤ 3 px; la recursiva sí. Se conserva el comportamiento vectorizado
  (es el de producción y coincide con la histéresis clásica 8-conexa).
- **D3 (código muerto) — RESUELTO**: `DThEdgeTrack` + `FindConnectedWeakEdges`
  eliminados (cero llamadores, `RecursionError` en 300×300,
  `setrecursionlimit` global), junto con `import sys`. Archivo 152 → 79 líneas.
  La verificación de utilidad exigida por la regla del proyecto está en §2.2 y
  §2.3: superada y inutilizable a escala.
- **D4 (cosmético en `main.py`) — RESUELTO**: `np.sum(DetectedEdges == 1)`
  imprimía siempre 0 porque la salida es 0/255; ahora cuenta `> 0`.
- **D5 (diagnóstico) — RESUELTO**: los 8 `print` por llamada salieron del
  modelo. Era el único módulo con salida por llamada (verificado: el resto
  solo imprime al importarse, y esos prints son intencionales). El resumen
  vive ahora en `main.py`, en una línea: fuertes, débiles y total tras la
  histéresis. De paso se corrigió el comentario obsoleto que hablaba de un
  kernel 3×3 cuando el código usa 7×7 (radio Chebyshev ≤ 3, el del spec).

## 4. Decisiones (usuario)

1. ~~Aplicar D1 (guarda de entrada vacía)~~ — hecho, con test en rojo primero.
2. ~~Eliminar el código muerto recursivo (D3)~~ — hecho.
3. ~~Corregir el diagnóstico de `main.py` (D4)~~ — hecho.
4. ~~Mantener o condicionar los `print` (D5)~~ — hecho: fuera del modelo,
   resumen de una línea en el orquestador.

## 5. Verificación

`tests/test_etapa6_edge_track_hyst.py`: radio Chebyshev (3 sí / 4 no, en eje y
diagonal), isla continua completa, isla lejana descartada, hueco ≤3 no une
islas, sin fuertes → vacío, sin débiles → solo fuertes, `uint8 {0,255}`,
argumentos no modificados, entrada vacía sin excepción.
