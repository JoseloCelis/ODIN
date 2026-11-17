# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Última modificación: 2026-11-06

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- Bootstrap revisado con skill `python` (fix `d9f6902`): `raise ... from e` ×2, `MAX_WARN_LEN` eliminada, `env_type` documentado placeholder, typing moderno, print de import en utils eliminado. Suite devcontainer 181 passed.
- Type hints completos en `src/odin/` (commit `ca595b0`): 90/90 defs con retorno anotado, 0 params sin anotar. Bonus: `worker_thread.py` con `gi.require_version('Gdk')` (calla PyGIWarning preexistente).
- API pública encapsulada por dominio (commit `b783395`): `Procesamiento` exporta NonMaxSup/Otsu/DoubleTh/aproxHough, `Ajustes` circleFilter/circuloSimple/LSC; `Preprocesamiento` solo sus 2 etapas. Engram actualizado.
- Suite de tests reorganizada a `tests/unit/<dominio>/` + `tests/integration/` (commit `3773618`). **Verificado en devcontainer** (imagen `vsc-odin-a8b2d91c9521796425d0e2ffb7ce0c54fdd4e8418fae4b93b7b5408946ddcf96`): `pytest tests` → **181 passed, 6 skipped, 1 failed** (`test_version_flag`, sin DISPLAY; headless). Hypothesis corre dentro del devcontainer (2026-11-17, commits `3773618`, `ebd8342`); en el host Mint se omite (sin pip).
- Eliminada carpeta legacy `odin/`: todo el código fuente reside exclusivamente en `src/` (`src/main.py`, `src/bootstrap.py`, `src/odin/`).
- Dataset de imágenes en `src/data/` purgado del historial Git (.git reducido de 2.3 GB a 1.4 MB) e ignorado en `.gitignore`.
- Estructura modular consolidada por dominios:
  - Etapas ① y ②: `src/odin/Preprocesamiento/models/`
  - Etapas ③, ④, ⑥ y ⑦: `src/odin/Procesamiento/models/`
  - Etapas ⑧ y ⑨: `src/odin/Ajustes/models/`
- Aliases públicos consolidados en `src/odin/Preprocesamiento/__init__.py` (según AGENTS.md).
- Resueltos hallazgos RDD (Judgment Day W1 y W4): exposición de `MagFase` en `models/__init__.py` y tests blindados ante dependencias de UI en `test_etapa7_hough_circles.py`.
- Fix de integración UI: sincronización de `image_loaded` en `main_controller.py` y configuración de depuración en `.vscode/launch.json`.
- Specs en `.kiro/specs/` actualizados con las rutas reales del nuevo layout.

## Mediciones Task 14 / Task 16 (con pantalla virtual Xvfb :99)
- ENV_PROBE (detección entorno): 0.2 ms (umbral < 200 ms) ✅ OK
- Bootstrap completo: 0.1 ms (umbral < 3000 ms) ✅ OK (en proceso existente)
- Suite pytest: 182 passed ✅ OK
- DISPLAY_VALID: verificada con X11Display (DISPLAY=:99 + GDK_BACKEND=x11) ✅ OK
- WINDOW_INIT: verificada con Xvfb :99 (15.8 ms) ✅ OK
- Task 14 (checkpoint integración GUI): COMPLETA — verificada en ambos modos (PACKAGE y SCRIPT) con Xvfb :99: las 4 fases en orden y sin errores.
- Task 16 (checkpoint final): COMPLETA — 11 propiedades de corrección GREEN (`tests/test_bootstrap_arranque.py`, Hypothesis), 182 passed, 3 reviews de gentle-ai approved. Commits `d4e15f8`, `22333f4`, `f62042c`.

## Doc-staleness pendiente (barrido ①-⑧)
- (ninguna pendiente; R3.2 resuelta, etapa ④ resuelta)

## Decisiones (y por qué)
- Acrónimo oficial: ODIN = *Otsu + Directional + Intensity + Non-Maximum Suppression* (usuario).
- `requirements.txt` en UTF-8 (fijado por el usuario; UTF-16LE fue error histórico corregido).
- Si Engram y MEMORY.md chocan: preguntar al usuario cuál manda.
- No renombrar `odin/` a `src`; futuro src layout será `src/odin/` preservando paquete Python.
- Kernel 5×5 (no 7×7) por decisión de usuario; medido inocuo y mejor bajo ruido.

## Aprendizajes y errores a evitar
- `hypothesis` figura en `requirements.txt` (dev/test) y vive en el **devcontainer** (`Dockerfile`: `pip3 install -r requirements.txt`; CI igual). El host Mint `/usr/bin/python3` (3.14, sin pip) **no lo tiene** → las suites `_prop.py` y `TestPropiedadesCorreccion` se omiten en el host. Decisión (2026-11-16): correr tests en el devcontainer, no instalar hypothesis en el host. Imagen `vsc-odin-...:latest` ya existe localmente.
- Deuda documentada (`.kiro/specs/kernel-separable/design.md`, D4): `sigma` flotante truena en `DerivGauss` (`range(3*sigma)` → TypeError). En `src/odin/.../models/deri_gauss.py` ya se castea `int(3*sigma)` antes de dimensionar arrays. No borrar esta deuda de MEMORY.md ni de Engram.
- Kiro tiende a truncar/reescriturar AGENTS.md al generar documentación: revisar tras cada sesión de Kiro.
- Al cambiar firma de helper compartido, verificar TODOS los llamadores.
- Barrido con un solo paso grueso da márgenes frágiles: refinar candidatos gruesos convierte decisión en 2.6:1 por ~3 s.

## Próximos pasos
- Implementar Patrón Estrategia (`DeteccionStrategy` en `src/odin/Procesamiento/models/strategies/base_strategy.py`, según AGENTS.md §4.2).
- Modularizar la vista y el controlador monolíticos (`main_window.py` / `main_controller.py`) hacia sus dominios (`Preprocesamiento`, `Procesamiento`, `Ajustes`) solo si se requiere desacoplar componentes gráficos independientes.
