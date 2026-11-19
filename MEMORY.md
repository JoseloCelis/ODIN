# MEMORY.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

Última modificación: 2026-11-19

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Release `v0.1.0` publicada** (tag + `CHANGELOG.md`). Cadena de PRs cerrada: GitHub #1–#10 mergeados, Azure #2–#6 completados, PR Azure #1 `rama-Hybrida`→`main` abandonado.
- **Remoto limpio:** GitHub solo `main`; Azure `main`, `master`, `rama`, `rama-Hybrida`. Local: `main` (= `github/main`), `rama`, `rama-Hybrida`, `backup/chore-completo` (backup del árbol original).
- `main` está protegido: exige PR + checks `test`/`security` (GH013 si se empuja directo). Patrón usado: rama → PR → merge.
- **Suite verde:** `xvfb-run -a ODIN_TEST_LENTO=1 python3 -m pytest tests` → **188 passed, 0 skipped**.
- Tests en `tests/unit/<dominio>/` + `tests/integration/`; `RAIZ` `parents[3]` (`091da78`); shadowing `find_circle` resuelto (`d9b9209`).
- `AGENTS.md` en inglés (única doc técnica en inglés, decisión del usuario); código/comentarios/commits en español.
- Type hints completos en `src/odin/` (`ca595b0`); API pública por dominio (`b783395`); `bootstrap.py` revisado (`d9f6902`).
- CI en GitHub: `.github/workflows/{ci-odin,docker-ci-image,release-please,gemini-release-notes,security}.yml`. Secrets: `MY_RELEASE_PLEASE_TOKEN`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`.
- Azure DevOps **sin CI**: `azure-pipelines.yml` queda en repo, pero la policy `Validacion CI ODIN` (id 4) y la pipeline `ODIN` (id 1) están deshabilitadas (sin hosted parallelism). Release-Please y Security Review viven solo en GitHub.
- Máquina: **WSL2 Ubuntu**, no el "PC Personal Mint" de AGENTS.md §5.1; GPU passthrough D3D12 (`/usr/lib/wsl/lib`).
- Estructura por dominios: ①-② `Preprocesamiento/models/` · ③④⑥⑦ `Procesamiento/models/` · ⑧⑨ `Ajustes/models/` (alias `LSC` exportado por `Ajustes`).

## Tooling del repo (GGA / gentle-ai)
- `gentle-ai` **4.6.0** en `~/.local/bin/gentle-ai` y en `.../gentle-shell/install/agent/bin/gentle-ai`; `gga` (GGA) **2.10.1** en `~/.local/bin/gga`.
- Hook `.git/hooks/pre-commit` (local, no versionado): `if command -v gga >/dev/null 2>&1; then gga run || exit 1; fi` → enforcea cuando gga es alcanzable, no rompe commits si no lo es.
- GGA lee config global en orden `APPDATA` → `XDG_CONFIG_HOME` → `~/.config/gga/config`; en gentle-shell `XDG_CONFIG_HOME` está definido, por eso la config se replica en ambas rutas.
- `.gga` del repo: `PROVIDER="opencode"` (binario en `~/.gentle-ai/bin/opencode`), `FILE_PATTERNS="*.ts,*.tsx,*.js,*.jsx,*.py"`.

## Decisiones (y por qué)
- Acrónimo oficial: ODIN = *Otsu + Directional + Intensity + Non-Maximum Suppression*.
- `requirements.txt` en UTF-8 (UTF-16LE fue error histórico).
- Si Engram y MEMORY.md chocan: preguntar al usuario cuál manda.
- No renombrar `odin/` a `src`; el layout es `src/odin/` preservando el paquete Python.
- Kernel 5×5 (no 7×7) por decisión de usuario; medido inocuo y mejor bajo ruido.
- `.kiro/skills/` y `design/` quedan untracked; `.gga` ignorado (contiene config local).
- Notas de release las genera Gemini con salida Markdown directa (sin preámbulo): `systemInstruction` + saneo `sed`/`awk` desde el primer título; si ningún modelo responde, el workflow falla antes de `gh release edit`.
- Modelos Gemini operativos: `gemini-3.5-flash-lite` / `gemini-flash-lite-latest`; `2.5-*` da 404 y `3.6/3.7/3.8-flash` dan 503.

## Aprendizajes y errores a evitar
- `hypothesis` en el host vía apt (`python3-hypothesis`); el sandbox del agente no tiene sudo.
- Deuda documentada (`.kiro/specs/kernel-separable/design.md`, D4): `sigma` flotante truena en `DerivGauss`; se castea `int(3*sigma)`. **No borrar esta deuda.**
- Kiro tiende a truncar/reescribir AGENTS.md: revisar tras cada sesión.
- Al cambiar firma de helper compartido, verificar TODOS los llamadores.
- Nunca `jq -r ... > archivo` sin validar la salida: un `null` de Gemini destruyó las notas de `v0.1.0` una vez.
- El asset de gentle-ai usa guiones bajos (`gentle-ai_4.6.0_linux_amd64.tar.gz`); la variante con guiones devuelve 9 bytes de error.
- `gentle-ai install` global falla por preflight de `pi`; acotar `--agents <uno mapeado>` reduce el plan y evita tocar Pi/OpenCode.

## Próximos pasos
- Implementar Patrón Estrategia (`DeteccionStrategy` en `src/odin/Procesamiento/models/strategies/base_strategy.py`, AGENTS.md §4.2).
- Modularizar `main_window.py` / `main_controller.py` solo si hace falta desacoplar componentes gráficos.
- Reintentar notas Gemini de `v0.1.0` solo si se quiere reemplazar el texto actual.
