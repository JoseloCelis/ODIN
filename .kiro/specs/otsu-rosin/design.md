# Design Document — otsu-rosin

## 1. Revisión de la implementación

`MtoOtsu.py` (194 líneas) quedó refactorizado en sesiones previas (commit
`3662e0d`): dos helpers privados + tres funciones públicas.

| Símbolo | Rol | Llamadores |
|---|---|---|
| `_preparar_histograma(IG)` | filtra `IG > 0`, 256 bins, centros | 2 (internos) |
| `_umbral_otsu(counts, xcenters)` | Otsu vectorizado | 2 (internos) |
| `umbralRosinYOtsu(IG, histo)` | Otsu + Rosin + histograma | `main.py:424` |
| `umbralOtsu(IG, histo)` | solo Otsu | **0** (API pública) |
| `dibujar_en_hilo_principal(...)` | matplotlib | vía `GLib.idle_add` |

## 2. Evidencia de ejecución (batería previa al spec)

### Otsu vs referencia independiente (barrido sobre valores reales)

| Caso | ODIN | Referencia | Diferencia | Lectura |
|---|---|---|---|---|
| unimodal + cola exponencial | 0.23537 | 0.23544 | 0.00008 (0.01 bins) | ✓ correcto |
| bimodal σ=0.12 | 0.50105 | 0.50260 | 0.00155 (0.4 bins) | ✓ correcto |
| bimodal σ=0.20 | 0.50226 | 0.50450 | 0.00224 (0.6 bins) | ✓ correcto |
| bimodal σ=0.05 (compacta) | 0.44477 | 0.51619 | 0.07142 (20 bins) | **meseta**, no error |

**Prueba de la meseta**: `vB(0.45321) = vB(0.51478) = 0.062669804206` —
idénticos a 12 decimales. La meseta es una propiedad de Otsu con clusters
compactos y separados, no un defecto de la implementación.

### Casos degenerados

| Entrada | Resultado actual | Comentario |
|---|---|---|
| todo ceros | `0.0, 0.0` | ✓ guarda |
| vacío / solo negativos | `0.0, 0.0` | ✓ guarda |
| con `NaN` | `0.2996, 0.2035` | ✓ `NaN` filtrado por `IG > 0` |
| constante 0.5 | `0.5` | ✓ D1: un solo bin centrado en el valor |
| constante 0.7 | `0.7` | ✓ D1: un solo bin centrado en el valor |
| constante 0.05 | `0.05` | ✓ D1: un solo bin centrado en el valor |
| casi-constante (rango mínimo) | `0.5` (centro del valor) | ✓ D1: fallback a un solo bin cuando `np.histogram` no admite 256 bins |

Causa exacta de D1: `np.histogram` con `min == max` expande el rango a
`(v − 0.5, v + 0.5)`; el único bin ocupado es el 128; `vB` es cero en todas las
posiciones (`safe_mask` vacía) y `np.argmax` devuelve 0 → `xcenters[0] = v −
0.5 + ½bin`.

### Rosin

En datos bimodales (pico 12000 muestras en 0.10; segundo cluster en 0.60) cae en
`0.1417`, el flanco del pico dominante. Es el comportamiento esperado: Rosin es
un criterio para histogramas **unimodales** (pico dominante + cola), y ODIN lo
usa solo para dibujar. El respaldo cuando la recta es indefinida ya existe.

### Escala

`IG × 10` → umbral × 10.0000 ✓ (los bins se adaptan al rango de datos).

## 3. Divergencias registradas

- **D1 (defecto real, degenerado) — RESUELTO**: dos casos de histogramas con un solo bin no vacío devolvían `v − 0.5 + ½bin`, que podía ser negativo. (a) Valores activos todos iguales (`vmin == vmax`): `np.histogram` expande el rango a `(v − 0.5, v + 0.5)`; (b) Casi-constante con rango mínimo (`vmin != vmax` pero el rango es demasiado chico para 256 bins finitos): `np.histogram` lanza `ValueError: Too many bins for data range`. Resolución final: la guarda vive en `_preparar_histograma`, que en ambos casos devuelve un histograma de **un solo bin centrado exactamente en el valor** (`vmin`). Nota de proceso: el primer intento devolvía el centro del bin del histograma artificial y falló para valores diminutos (0.001 → −0.000953); el bin no es el valor. Se deja además una guarda defensiva en `_umbral_otsu` para cualquier caso futuro de un solo bin ocupado.
- **D2 (contrato, no defecto)**: meseta de Otsu documentada en R3.
- **D3 (deuda arquitectónica)**: `GLib.idle_add` incondicional en
  `umbralRosinYOtsu` y `umbralOtsu`; el módulo importa `gi`. Deuda ya anotada
  en `AGENTS.md`; se resuelve en el refactor `src/odin/` con callback inyectado,
  no acá.
- **D4 (revisión de uso, lección de la etapa ③)**: `umbralOtsu` tiene **cero
  llamadores**, pero es una API pública legítima (devuelve solo el umbral de
  Otsu, reutilizable). `utilidad ≠ uso`: se recomienda conservarla y no
  borrarla.
- **D5 (menor)**: Rosin usa distancia absoluta e incluye el bin del pico en la
  zona de búsqueda. Sin efecto práctico porque su valor es solo diagnóstico.

## 4. Decisiones (resueltas por el usuario)

1. Fix de D1 — **aplicado** (ver §3).
2. D3 — queda como deuda documentada para el refactor `src/odin/`.
3. `umbralOtsu` — **se conserva** como API pública.

## 5. Verificación

Batería reutilizable: referencia Otsu independiente por barrido, prueba de
meseta (`vB` en dos puntos), escala, casos degenerados, y geometría de Rosin.
Tras cualquier cambio en el módulo, reejecutarla.
