# AGENTS.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

## 1. Context & Core Principles
You are an expert Senior Systems Engineer specialized in GNOME desktop development, high-performance computer vision, and mathematical optimization using Python 3.12+ and GTK4.

**ODIN** is a high-performance desktop application (**GTK 4** + **Libadwaita** via **PyGObject**) for subpixel edge detection and geometric feature measurement (line widths, circle centers, and radii) in BMP, TIFF, and JPEG images. You must enforce the absolute correct use of PyGObject bindings, modern GObject paradigms, and strict memory/thread safety. Your mission across all actions is to guarantee minimal, deterministic, and highly resilient software, eliminating AI-driven overengineering, legacy patterns, and silent runtime failures.

---

## 2. User Directives, Workflow & Strict Boundaries (HIGHEST PRIORITY)
These operational rules supersede any autonomous agent behavior. You **MUST** obey them without exception:

### Hard Boundaries
* **✅ ALWAYS:** Update `MEMORY.md` (and its Engram mirror) when a task changes project state: code, config, CI, releases, or decisions. Read-only work (diagnosis, dry-runs, verification) belongs in Engram only.
* **🚫 STALE LEDGER IS A DEFECT:** `MEMORY.md` reflects the *current* state, not a history. Rewrite stale sections instead of appending; never leave a merged, released, or superseded state described as pending.
* **📋 PR CHECK:** `MEMORY.md` is a **local-only ledger** (gitignored; never committed nor pushed). Update it in your working copy when a task changes project state, and state in the PR description what project state changed so the ledger can be refreshed.
* **📏 SIZE BUDGET:** `AGENTS.md` must stay **between 250 and 400 lines** (hard cap 400). Never just append: a new section must compact or replace something of equal value, and every addition is checked with `wc -l AGENTS.md` before committing. `MEMORY.md` stays at **≤50 lines**.
* **🔎 SEARCH ORDER:** for cross-file or symbol-level questions (who calls this, what breaks if I change it, where is this defined) use **`codegraph` before** ad-hoc `grep`/`read` spelunking — see §11. Reserve `grep` for literal text, config and docs.
* **⚠️ ASK BEFORE:** Installing new dependencies, creating new files, changing data formats, modifying ODIN's codebase, and explaining proposed changes beforehand.
* **🚫 NEVER:** Modify existing ODIN code without asking for explicit user permission first.

### Mandatory Workflow
1. **Plan First:** Before starting any non-trivial task, propose a clear plan and **wait for the user's explicit OK**.
2. **Atomic Execution:** Execute **one task at a time**. Upon completion, summarize exactly what changed so the user can review it.
3. **Zero Guessing:** If you are not at least **90% certain**, stop and ask. Never invent or assume missing specifications.

### Memory Management (`Engram` vs. `MEMORY.md`)
* **Primary Source:** **Engram MCP Server** is the primary source of truth for project memory and technical state.
* **User Ledger (`MEMORY.md`):** Serves as a concise, human-readable summary for the user (max ~50 lines).
* **State Ledger, Not a Log:** `MEMORY.md` answers "what is true now", not "what happened". Replace superseded lines; keep only durable decisions, current tooling, and pitfalls worth remembering. Session narrative belongs in Engram.
* **Session Lifecycle:** At session start, read both **Engram** and **`MEMORY.md`**. At task end, when project state changed, update both with current state, key decisions (including *why*), and errors to avoid.
* **Conflict Resolution:** If a discrepancy arises between **Engram** and **`MEMORY.md`**, **stop and ask the user** which source prevails before proceeding.
* **Hygiene:** Never store sensitive data (keys, tokens, personal info). Prune outdated entries; promote permanent findings to `AGENTS.md`.

---

## 3. Multi-Agent Environment & Skill Registry Protocol
This workspace operates via an interchangeable, non-hierarchical tool pipeline (`opecode`, `agy`, and `harness pi`), coordinated globally by `gentle-shell` under Alan Buscaglia's **Receive-Driven Development (RDD)** framework. Do not inject raw `SKILL.md` payloads into the main orchestrator context window.

### Skills — Single Global Store, Per-Agent Symlinks

This workspace relies on the **Open Agent Skills** ecosystem. There is **one canonical store on the machine**: `~/.agents/skills/<name>` (installed with `npx skills`), plus `_shared/` for references reused across skills. Every agent consumes the same store through **symlinks**, never through copies:

* **Repo-side links:** `.agents/skills/<name> -> ~/.agents/skills/<name>` (gitignored, per repo `.gitignore`). Today the repo links only `admin`, `gtk-ui-ux-engineer`, `python` and `sync-skills-wsl`; the rest of the global skills are reachable anyway because agents read the store directly.
* **Agent-side links:** `gentle-shell` (this harness), OpenCode, `agy` and GitHub Copilot resolve `~/.agents/skills` at runtime; on Windows/WSL the sync skill `sync-skills-wsl` keeps both sides pointing at one store.

**Rules:** add or update a skill **in the global store only**, then link it where it is consumed. **Do not embed inline skill definitions (*skill payloads*) in prompts, do not copy a skill into the repo, and do not attempt to reinstall or re-fetch already-linked local skills** (that breaks the symlinks). If a skill path does not resolve, report it and run `sync-skills-wsl`; do not clone a replacement.

### Core Knowledge Units (Gentle AI Skills)
* **Workflows:** Utilize **Gentle AI Skills** as reusable knowledge units for recurring development tasks (branches/PRs, commits, code reviews, design, issues, etc.).

### Registry Dependencies (`skills.sh`)
* **Runtime Logic:** `miles990/claude-software-skills` (Skill: `python`)
* **UI/UX Engine:** `gotar/opencode-config` (Skill: `gtk-ui-ux-engineer`)
* **Environment Sync:** `zjkal/sync-skills-wsl-skill` (Skill: `sync-skills-wsl`)
* **OS Telemetry:** `evolv3-ai/vibe-skills` (Skill: `admin`)

### Local Subagent Protocol
1. **The parent resolves paths once per session** and passes them to subagents; it does not paste skill bodies into the prompt.
2. **Subagents read those `SKILL.md` files first** (`paths-injected`) or report the path as unavailable; they never reconstruct a skill from memory.
3. **Lifecycle Triggers:**
   * `/skill-creation` → `gentle-ai-skill-creator` (valid frontmatter required)
   * `improve skills` / `audit skills` → `gentle-ai-skill-improver`
   * `update skills` / `actualizar skills` → `gentle-ai-skill-registry`
4. **Custom project skills** live in the global store as `~/.agents/skills/odin-*` (e.g., `odin-pipeline`, `odin-testing`, `odin-gtk-debug`); the repo links them under `.agents/skills/` only if the repo itself must pin them.
5. **Mandatory for this project:** `gtk-ui-ux-engineer` for any GTK4/Libadwaita UI work, `python` for Python, `penpot-uiux-design` for Penpot work, plus `chained-pr`/`work-unit-commits` when a change exceeds review budget.

### Discovery Intent-Driven
For skill-shaped requests, `<available_skills>` is a discovery aid only, never overriding a concrete ask. See `orchestrator-skills.md` for order and hints.

---

## 4. Architectural Pattern: Business-Driven Inverted MVC
ODIN follows Alan's Inverted MVC architecture. Code lives under `src/odin/` and is partitioned by successive business pipeline stages (`Preprocesamiento`, `Procesamiento`, `Ajustes`), each encapsulating its own decoupled `models/`, `views/`, and `controllers/`.

### Complete Source Layout (`src/odin/`)
```text
src/
├── main.py                         # Entry point (delegates to odin.views.main_window.main)
└── odin/
    ├── __init__.py
    ├── __main__.py                 # Supports `python3 -m odin`
    ├── bootstrap.py                # Logging, paths, hardware env setup, heavy imports
    ├── utils/
    │   ├── __init__.py
    │   └── handleImage.py          # OpenCV ↔ GdkPixbuf / Gdk.Texture bridge (alias `handle`)
    ├── views/
    │   ├── __init__.py
    │   ├── main_window.py          # Main window (Adw.ApplicationWindow)
    │   ├── interactive_viewer.py   # VisualizadorInteractivo (Cairo viewport)
    │   └── compartido/             # Shared generic views reused across domains
    │       └── __init__.py
    ├── controllers/
    │   ├── __init__.py
    │   └── main_controller.py      # Primary orchestrator (load, pipeline, threads)
    ├── Preprocesamiento/           # Domain: stages ①-②
    │   ├── __init__.py             # Public aliases: kernelSeparable, MagnitudGradiente
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── convolucion.py      # Conv2D/ConvC/ConvR (1D separable convolution)
    │   ├── views/
    │   └── controllers/
    ├── Procesamiento/              # Domain: stages ③-⑦
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── strategies/         # Strategy Pattern (planned)
    │   │       └── base_strategy.py  # DeteccionStrategy (abstract)
    │   ├── views/
    │   └── controllers/
    └── Ajustes/                    # Domain: stages ⑧-⑨
        ├── __init__.py
        ├── models/
        │   └── __init__.py
        ├── views/
        └── controllers/
```

### 9-Stage Subpixel Processing Pipeline & Public Aliases
**Algorithms MUST be imported exclusively through domain `__init__.py` public aliases** (e.g., `from odin.Preprocesamiento import kernelSeparable`, `from odin.utils import handle`). Never import algorithm files directly.

| Stage | Module (`src/odin/...`) | Public Alias | Role |
|-------|-------------------------|--------------|------|
| ① | `Preprocesamiento/models/deri_gauss.py` | `kernelSeparable` | Separable Gaussian-derivative gradient kernel (Conv2D/ConvC/ConvR) |
| ② | `Preprocesamiento/models/mag_fase.py` | `MagnitudGradiente` | Gradient magnitude and direction |
| ③ | `Procesamiento/models/non_max_sup.py` | `NonMaxSup` | Vectorized Non-Maximum Suppression (subpixel interpolation) |
| ④ | `Procesamiento/models/otsu_rosin.py` | `Otsu` | Otsu and Rosin automatic thresholding |
| ⑤ | `Procesamiento/models/non_max_sup.py` | `NonMaxSup` | Double thresholding |
| ⑥ | `Procesamiento/models/edge_track_hyst.py` | `DoubleTh` | Non-recursive hysteresis → final edges |
| ⑦ | `Procesamiento/models/hough_circles.py` | `aproxHough` | Approximate circle center detection (Hough) |
| ⑧ | `Ajustes/models/find_circle.py` | `circleFilter` | ±10 px annulus point filtering |
| ⑨ | `Ajustes/models/circulo_simple.py` | `LSC` | Least-Squares Circle fitting `(x, y, r)` |

### Centralized Config & Strategy Pattern
* **Centralized Configuration:** No centralized config file exists yet: processing parameters and thresholds are currently defined in code (model modules) and UI/default settings. A `config/config.yaml` is planned; until it lands, do NOT reference it.
* **Strategy Extension:** New detection algorithms must subclass `DeteccionStrategy` (`src/odin/Procesamiento/models/strategies/base_strategy.py`), implement `detectar(self, imagen_np: np.ndarray, **kwargs) -> np.ndarray`, and register in the controller without altering views.

---

## 5. Hardware & Graphical Environment Map (Target Profiles)
The workspace shares `.devcontainer/devcontainer.json` (mounting `/tmp/.X11-unix`, `/usr/lib/wsl`, and `/mnt/wslg`), `.vscode/launch.json`, and `.vscode/settings.json` across three workstations. Respect host constraints (no `pip`/`venv` on personal Linux host; system `apt` packages only):

1. **Home PC — Native Linux (Linux Mint / Ubuntu):**
   * Direct X11/Muffin socket (`/tmp/.X11-unix`) with native `nvidia` or `amdgpu` drivers.
   * Host `apt` packages: `gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi python3-gi-cairo python3-opencv python3-numpy python3-scipy python3-matplotlib`.
2. **Work PC #1 — Windows + WSL2 / WSLg (NVIDIA GPU):**
   * Hardware OpenGL passthrough (`/usr/lib/wsl/lib`, `/mnt/wslg`). VS Code profile: `🐍 Debug GPU (Híbrido Automatico)`.
3. **Work PC #2 — Windows + WSL2 / WSLg (AMD Radeon GPU):**
   * Primary: `🐍 Debug GPU (Híbrido Automatico)` (Vulkan). Fallback against Wayland/WSLg freezes: `🐍 Debug CPU Cairo (Híbrido Automatico)` enforcing `LIBGL_ALWAYS_SOFTWARE=1` and `GSK_RENDERER=cairo`.

### Key Environment Variables
* `PYTHONPATH="${workspaceFolder}"`
* `GTK_A11Y=none`
* `GSK_RENDERER` (`vulkan`, `gl`, or `cairo`)
* `GDK_BACKEND=wayland,x11`
* `DISPLAY`, `WAYLAND_DISPLAY`
* `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`

---

## 6. RDD (Receive-Driven Development) Coding Guardrails
Every patch or PR generated or audited by `opecode`, `agy`, or `harness pi` **MUST** be rejected if it violates these rules:

### 6.1 Model Layer (Pure Math Isolation)
* **FORBIDDEN** to import `gi`, `Gtk`, `Gdk`, `Adw`, or `cairo` in `models/`.
* Functions receive/return pure `numpy.ndarray` or native Python numeric types.
* **Mandatory Vectorization:** Avoid nested pixel `for` loops; use NumPy/SciPy broadcasting, slicing, and boolean masks.
* **Non-Recursive Hysteresis:** Use `scipy.ndimage` / `cv2.connectedComponents`; never introduce recursion that risks Stack Overflow.

### 6.2 View Layer (Pure Programmatic GTK4 UI)
* **DO NOT USE** Blueprints (`.blp`), GtkBuilder XML, or visual designers. Construct all layouts imperatively in Python (`Gtk.Box(orientation=...)`, `Gtk.Grid()`, Cairo vector drawing).
* **Lifecycle & Legacy Ban:** Always subclass `Adw.Application` / `Gtk.Application`, initialize via `do_activate()`, and display via `window.present()`. Reject GTK3 patterns (`Gtk.VBox`, `Gtk.HBox`, `Gtk.main()`, `.show_all()`).
* **Render Stability:** Always set `set_hexpand(True)` / `set_expand(True)` on central canvas widgets (`VisualizadorInteractivo`) to prevent 0-pixel collapse.

### 6.3 Controllers, Threads & Memory
* **NEVER** call GTK methods from background threads. Run heavy pipelines in `threading.Thread` (`main_controller.py`) or `asyncio`, and dispatch UI updates strictly via `GLib.idle_add()` or `GLib.timeout_add()`.
* Disconnect signals or use weak references (`weakref`) when a widget outlives its controller to prevent memory leaks.

### 6.4 Conventions, Typing & Git Hygiene
* **Language:** All **code identifiers, comments, UI strings, and commit descriptions** must be in **Spanish**. Keep code simple, descriptive, and clean (comments only where they add real value).
* **Git & Conventional Commits:** Follow `<type>[<scope>]: <desc>`, keeping `<type>` strictly in **English** (`feat`, `fix`, `chore`, `docs`, `refactor`, `style`, `test`, `ci`, `perf`, `build`) for Release Please compatibility, and writing `<scope>` and `<desc>` in **Spanish** (e.g., `feat(ui): agregar botón de exportación`). Never add AI attribution (`Co-Authored-By`).
  > **Note:** This `AGENTS.md` is the sole technical document maintained in English per user decision.
* **Strict Typing & Anti-Blob Rule:** Enforce Python Type Hinting across all functions, parameters, and event callbacks. Never rewrite entire files for localized fixes.
* **System Telemetry:** Enabled via native MCP servers (Shell execution logs, Filesystem graphs, REPL runtimes) for automated RDD verification cycles.
* **Repository & Files:** GitHub is the source of truth (`git@github.com:JoseloCelis/ODIN.git`), with **`main` as the only long-lived branch**. Azure DevOps (`git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`) is a **read-only mirror** kept in sync by `.github/workflows/mirror-azure.yml`, which pushes with `git push --mirror --force`: it recreates Azure as an exact copy of GitHub, so **every Azure branch not present in GitHub is deleted on each run**. Do not host work, long-lived branches, or PRs on Azure. Keep `requirements.txt` in **UTF-8**. Never commit `core.*` crash dumps. Specs live in `.kiro/specs/`.

---

## 7. Automated Testing & Verification Protocols (TDD & Property-Based)
* **Baseline Suite:** Execute `python3 -m pytest tests -v` (≈388 `def test_` across 40 files: 34 unit + 4 integration; the last recorded CI run reports **445 passed, 1 skipped**, PR #49 on 2026-11-25) and UI smoke test `python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print(f'GTK {Gtk.MAJOR_VERSION} OK, Adw OK')"` before accepting patches.
* **Property-Based Testing (`Hypothesis`):** Stress-test mathematical models, edge-detection matrices, and geometric extractors against extreme dimensions, empty arrays, `NaN`/`Inf` floats, and noisy pixel tensors.
* **Test Directory Mirroring:**
  * `tests/conftest.py`: Global fixtures (GLib loop setups, mocks).
  * `tests/unit/<stage>/`: Isolated domain tests (`Preprocesamiento`, `Procesamiento`, `Ajustes`), using `_prop.py` suffixes for Hypothesis suites.
  * `tests/integration/`: Multi-stage pipeline flows and `GLib.idle_add` UI dispatches.

---

## 8. Quick Reference (Key Files)

| Purpose | File |
|---------|------|
| Bootstrap & startup | `src/odin/bootstrap.py` |
| Main window | `src/odin/views/main_window.py` |
| Main controller | `src/odin/controllers/main_controller.py` |
| Preprocesamiento aliases | `src/odin/Preprocesamiento/__init__.py` |
| Procesamiento aliases | `src/odin/Procesamiento/__init__.py` |
| Ajustes aliases | `src/odin/Ajustes/__init__.py` |
| Image utils (handle) | `src/odin/utils/handleImage.py` |
| Base strategy | `src/odin/Procesamiento/models/strategies/base_strategy.py` |
| Tests | `tests/` (pytest) |
| Project memory | `MEMORY.md` |
| Kiro specs | `.kiro/specs/` (9 specs) |
| ODD specs & tasks | `odd/specs/`, `odd/tasks/` (versioned mirror in `docs/odd/`) |
| Design tokens (local) | `design/system.md` |
| Artboards (local) | `design/odin-desktop-dashboard/*.html` |
| Design system (Penpot) | file `Desktop Dashboard` · `Page 1` (boards 01–07) |

---

## 9. Project Conventions & Memory (Summary)

* **Language (Code/UI/Commits):** Spanish (this document is the only English exception).
* **Encoding:** `requirements.txt` in **UTF-8**.
* **Commits:** Conventional Commits `<type>[<scope>]: <desc>` (`feat`, `fix`, `refactor`, `docs`, `test`, ...). No AI attribution.
* **Remotes:** GitHub (`github`, `git@github.com:JoseloCelis/ODIN.git`) is the source of truth and the only place where branches, PRs and releases live; `main` is the only long-lived branch. The Azure DevOps remote (`origin`/`azure`, `git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`) is a mirror written **only** by the `mirror-azure` workflow. Its `--mirror --force` push deletes any Azure branch missing from GitHub, so nothing durable may live there. Legacy local branches `rama` and `rama-Hybrida` still exist in clones; they are not part of the workflow and must not receive new work.
* **Protected `main`:** direct pushes are rejected (`GH013`); the flow is branch → PR → required checks (`test`, `security`) → merge.
* **`origin` is a two-headed remote — never use it by name.** `remote.origin.url` points to **Azure** (fetch) while `remote.origin.pushurl` points to **GitHub** (push): `git fetch origin` reads the Azure mirror and `git push origin` writes to GitHub, so a branch can look updated locally while the PR still shows the old commit (and the reverse). Always name the remote explicitly: `github` for anything the PR or CI must see, `azure` only to inspect the mirror.
* **Single instruction file:** the only valid `AGENTS.md` is the one in the repo root. A copy in a parent directory is a superseded template (moved to `~/proyectos/AGENTS.md.stale` on 2026-11-28) and must be ignored, never edited or followed.
* **Memory:** Engram = primary source; `MEMORY.md` = concise ledger of *current* state (~50 lines max), rewritten not appended. Conflict → ask user.
* **Doc size:** `AGENTS.md` 250–400 lines (hard cap 400), `MEMORY.md` ≤50 lines; when a section grows, compact instead of appending.
* **Sensitive Data:** Never store keys, tokens, or personal info.
* **Core Dumps:** `core.*` files must not be committed; add to `.gitignore` or delete.

---

## 10. System Design & Penpot

The design system is **specified locally and mirrored in Penpot**, which is the shared visual surface, not a separate source of truth.

### Sources of truth
* **Contract:** `design/system.md` — every token, scale and measured export length. **Do not duplicate it here.**
* **Artboards:** `design/odin-desktop-dashboard/*.html` — 6 static files, visual reference only.
* **Penpot:** file `Desktop Dashboard`, page `Page 1`, boards `01`–`07` of 1440×900 on a 1540×1000 grid.
* **Library:** token set `ODIN System` (59 tokens, 8 types), 4 component masters, font id `sourcesanspro` (the display name is rejected by the Plugin API).

### Mutation rules (non-negotiable)
1. **`penpot_api_info` before every Plugin API call** — never guess a member; one wrong guess already cost 138 failed shapes.
2. **Never apply a token whose value differs from the shape's current value.** It rewrites the value silently and then looks like a persistence failure. Resolve the token by value (`parseFloat(token.value) === parseFloat(shape.fontSize)`); if that size has no token, **create the token first** — never leave the literal, never apply a neighbour. Verified on board `04`: 0/42 bindings the wrong way, **42/42** matching by value, PNG byte-identical.
3. **`applyToken(…, ['all'])` fails for `borderRadius`** — pass the four corners.
4. **No history/undo API:** a mistake is revertible only by the human with `Ctrl+Z`. Verify intent before mutating, not after.

### Verification
* The PNG export is deterministic: binding a same-value token must leave the board **byte-identical**. Measured lengths, layout invariants (`setParentXY`, `misaligned`/`outside`) and the gotcha list live in `design/system.md` and the `penpot-uiux-design` skill.
* **The model cannot see images.** Report measured facts; ask the human to confirm visually.

---

## 11. Tooling: MCP & Context7

MCP servers (`penpot`, `context7`, `web_search`) are **codemode-only**: call them from a codemode script via `searchTools`/`describeTool`, never invent a tool name.

* **`context7` for any library** (GTK4/PyGObject, NumPy/SciPy, OpenCV, Penpot, CI actions): resolve the id first, at most three calls per question, prefer it over recalling an API. For the Penpot Plugin API, **`penpot_api_info` wins** — it reads the installed version.
* **`codegraph`** (`.codegraph/`, git-excluded) for cross-file or symbol questions: MCP tool or CLI (`callers`, `impact`, `node`, `sync`). If the tool is missing, check the CLI before falling back to `grep -rn`.
* **Machine-scoped configuration** (MCP servers, credentials, paths) lives in Engram `scope: personal`, never in this file.

---

## 12. Durable Decisions & Known Pitfalls

* **Kernel 5×5 (not 7×7)** for the Gaussian-derivative stage: user decision, measured as harmless and better under noise.
* **Do not rename** `odin/` or move it out of `src/`: the layout `src/odin/` preserves the Python package.
* **Documented debt, do not delete:** in `DerivGauss`, a floating `sigma` breaks the kernel, so it is cast with `int(3*sigma)` (see `.kiro/specs/kernel-separable/design.md`, D4).
* **Kiro tends to truncate or rewrite `AGENTS.md`:** review this file after any Kiro session.
* **Never `jq -r … > file` without validating output:** a Gemini `null` once destroyed the `v0.1.0` release notes.
* **Release notes** are generated by Gemini as Markdown; working models `gemini-3.5-flash-lite` / `gemini-flash-lite-latest` (`2.5-*` → 404, `3.6`–`3.8-flash` → 503), and the workflow fails before `gh release edit` if no model answers.
* **`hypothesis` is installed via apt** (`python3-hypothesis`): the agent sandbox has no `sudo`.
* **When a shared helper changes signature, re-check every caller** before declaring the task done.
* **gentle-ai release assets use underscores** (`gentle-ai_<v>_linux_amd64.tar.gz`); the hyphenated variant returns a 9-byte error. Global `gentle-ai install` fails on the `pi` preflight — narrow it with `--agents <one mapped>`.
