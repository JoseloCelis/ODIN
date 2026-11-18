# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Última modificación: 2026-11-18

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **PRs en slices abiertos (GitHub, stacked):** la rama `chore/agents-arquitectura-skills` (26 commits) se partió en 4 PRs encadenados — #1 `chore/agents-docs` → `main` (+175/−167), #2 `test/suite-reorg` → #1 (+149/−6), #3 `fix/auditoria-src` → #2 (+160/−151), #4 `ci/release-workflows` → #3 (+141/−1). Árbol final idéntico al de la rama original; backup en `backup/chore-completo`.
- **Suite verde:** `xvfb-run -a ODIN_TEST_LENTO=1 python3 -m pytest tests` → **188 passed, 0 skipped** (host). Sin xvfb falla solo `--version` (por diseño, requiere DISPLAY).
- Tests reorganizados a `tests/unit/<dominio>/` + `tests/integration/` (`3773618`, `ebd8342`); `RAIZ` `parents[3]` (`091da78`); shadowing `find_circle` resuelto (`d9b9209`).
- `AGENTS.md` reescrito en inglés (única doc técnica en inglés, decisión del usuario): arquitectura real `src/odin/`, carga de skills (`.agents/skills/` → symlinks a `~/.agents/skills/`), commits compatibles con Release Please.
- Type hints completos en `src/odin/` (`ca595b0`): 90/90 defs con retorno anotado, 0 params sin anotar.
- API pública encapsulada por dominio (`b783395`, `603dc72`): `Procesamiento` exporta NonMaxSup/Otsu/DoubleTh/aproxHough, `Ajustes` circleFilter/circuloSimple/LSC; `Preprocesamiento` solo sus 2 etapas. `config/config.yaml` **no existe** (referencia corregida en AGENTS.md).
- `bootstrap.py` revisado con skill `python` (`d9f6902`): `raise ... from e` ×2, `MAX_WARN_LEN` eliminada, `env_type` documentado placeholder, typing moderno, print de import en utils eliminado.
- CI: `.github/workflows/{release-please,gemini-release-notes,security}.yml`. Requieren secrets `MY_RELEASE_PLEASE_TOKEN` y `CLAUDE_API_KEY` en el remoto antes de mergear #4.
- Máquina: **WSL2 Ubuntu** (kernel 6.18.58.1-microsoft-standard-WSL2), NO el "PC Personal Mint" de AGENTS.md §5.1; GPU passthrough D3D12/DXCore (`/usr/lib/wsl/lib`), perfil ~"Debug GPU (Híbrido Automatico)".
- Eliminada carpeta legacy `odin/`: todo el código en `src/` (.git de 2.3 GB a 1.4 MB); dataset `src/data/` purgado del historial e ignorado en `.gitignore`.
- Estructura por dominios: ①-② `Preprocesamiento/models/` · ③④⑥⑦ `Procesamiento/models/` · ⑧⑨ `Ajustes/models/`.
- Resueltos hallazgos RDD (Judgment Day W1 y W4): exposición de `MagFase` en `models/__init__.py` y tests blindados ante dependencias de UI en `test_etapa7_hough_circles.py`.
- Fix de integración UI: sincronización de `image_loaded` en `main_controller.py` y `.vscode/launch.json`.
- Specs en `.kiro/specs/` con las rutas reales del layout.

## Mediciones Task 14 / Task 16 (Xvfb :99)
- Task 14 (checkpoint GUI): COMPLETA — PACKAGE y SCRIPT, 4 fases en orden, sin errores.
- Task 16 (checkpoint final): COMPLETA — 11 propiedades GREEN (`tests/test_bootstrap_arranque.py`, Hypothesis); commits `d4e15f8`, `22333f4`, `f62042c`.
- Bootstrap 0.1 ms, ENV_PROBE 0.2 ms, WINDOW_INIT 15.8 ms ✅

## Doc-staleness pendiente (barrido ①-⑧)
- (ninguna pendiente; R3.2 y etapa ④ resueltas)

## Decisiones (y por qué)
- Acrónimo oficial: ODIN = *Otsu + Directional + Intensity + Non-Maximum Suppression*.
- `requirements.txt` en UTF-8 (fijado por el usuario; UTF-16LE fue error histórico).
- Si Engram y MEMORY.md chocan: preguntar al usuario cuál manda.
- No renombrar `odin/` a `src`; el src layout es `src/odin/` preservando paquete Python.
- Kernel 5×5 (no 7×7) por decisión de usuario; medido inocuo y mejor bajo ruido.
- `.kiro/skills/` y `design/` quedan untracked (decisión del usuario).

## Aprendizajes y errores a evitar
- `hypothesis` instalado en el host vía apt (`python3-hypothesis` 6.151.5-1; el sandbox del agente no puede sudo). También en devcontainer y CI.
- Deuda documentada (`.kiro/specs/kernel-separable/design.md`, D4): `sigma` flotante truena en `DerivGauss` (`range(3*sigma)` → TypeError). En `deri_gauss.py` se castea `int(3*sigma)` antes de dimensionar arrays. **No borrar esta deuda.**
- Kiro tiende a truncar/reescribir AGENTS.md al generar documentación: revisar tras cada sesión.
- Al cambiar firma de helper compartido, verificar TODOS los llamadores.
- El presupuesto de review se mide sobre el diff neto por slice, no sobre la suma por commit.

## Próximos pasos
- Revisar y mergear los 4 PRs en orden (#1 → #4); configurar secrets antes de mergear #4.
- Implementar Patrón Estrategia (`DeteccionStrategy` en `src/odin/Procesamiento/models/strategies/base_strategy.py`, AGENTS.md §4.2).
- Modularizar vista y controlador monolíticos (`main_window.py` / `main_controller.py`) solo si se requiere desacoplar componentes gráficos.
