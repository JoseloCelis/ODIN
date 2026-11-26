# Referencia de API Pública

## Aliases de Dominio (única forma soportada de importar algoritmos)

```python
# Preprocesamiento (etapas ①-②)
from odin.Preprocesamiento import kernelSeparable, MagnitudGradiente

# Procesamiento (etapas ③-⑦)
from odin.Procesamiento import (
    NonMaxSup, Otsu, DoubleTh, aproxHough,
    emparejar_orillas, asignar_puntos_a_orillas,
    seleccionar_trazo_por_intensidad, intensidad_interior,
    distancias_perpendiculares, picos_de_rho
)

# Ajustes (etapas ⑧-⑨)
from odin.Ajustes import circleFilter, LSC, medir_trazo, refinar_bordes_subpixel

# Utils
from odin.utils import handle  # puente OpenCV ↔ GdkPixbuf/Gdk.Texture
```

## Firmas Clave

```python
# Refinamiento subpíxel (etapa nueva, antes de medir_trazo)
def refinar_bordes_subpixel(
    puntos: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    magnitud: np.ndarray
) -> np.ndarray: ...

# Medición de trazo (firma inalterada)
def medir_trazo(
    puntos: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    theta: float,
    minimo_puntos: int = 3
) -> MedicionTrazo | None: ...

# Perfil de rho → picos + semianchuras (HWHM)
def picos_de_rho(
    puntos: np.ndarray,
    theta: float,
    paso: float = 0.5,
    percent: float = 0.6
) -> tuple[np.ndarray, np.ndarray, np.ndarray]: ...

# Asignación con ventana de pertenencia (semianchuras)
def asignar_puntos_a_orillas(
    puntos: np.ndarray,
    rhos: np.ndarray,
    thetas: np.ndarray,
    par: tuple[int, int],
    semianchuras: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]: ...
```

> **Regla:** Nunca importes módulos de algoritmos directamente (`from odin.Procesamiento.models.non_max_sup import ...`). Usa siempre los aliases del `__init__.py` de cada dominio.
