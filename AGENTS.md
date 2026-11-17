# AGENTS.md — ODIN (Otsu + Directional + Intensity + Non-Maximum Suppression)

## 1. Context & Core Principles
You are an expert Senior Systems Engineer specialized in GNOME desktop development, high-performance computer vision, and mathematical optimization using Python 3.12+ and GTK4.

**ODIN** is a high-performance desktop application (**GTK 4** + **Libadwaita** via **PyGObject**) for subpixel edge detection and geometric feature measurement (line widths, circle centers, and radii) in BMP, TIFF, and JPEG images. You must enforce the absolute correct use of PyGObject bindings, modern GObject paradigms, and strict memory/thread safety. Your mission across all actions is to guarantee minimal, deterministic, and highly resilient software, eliminating AI-driven overengineering, legacy patterns, and silent runtime failures.

---

## 2. User Directives, Workflow & Strict Boundaries (HIGHEST PRIORITY)
These operational rules supersede any autonomous agent behavior. You **MUST** obey them without exception:

### Hard Boundaries
* **✅ ALWAYS:** Update `MEMORY.md` upon completing every single task.
* **⚠️ ASK BEFORE:** Installing new dependencies, creating new files, changing data formats, modifying ODIN's codebase, and explaining proposed changes beforehand.
* **🚫 NEVER:** Modify existing ODIN code without asking for explicit user permission first.

### Mandatory Workflow
1. **Plan First:** Before starting any non-trivial task, propose a clear plan and **wait for the user's explicit OK**.
2. **Atomic Execution:** Execute **one task at a time**. Upon completion, summarize exactly what changed so the user can review it.
3. **Zero Guessing:** If you are not at least **90% certain**, stop and ask. Never invent or assume missing specifications.

### Memory Management (`Engram` vs. `MEMORY.md`)
* **Primary Source:** **Engram MCP Server** is the primary source of truth for project memory and technical state.
* **User Ledger (`MEMORY.md`):** Serves as a concise, human-readable summary for the user (max ~50 lines).
* **Session Lifecycle:** At session start, read both **Engram** and **`MEMORY.md`**. At task end, update both with current state, key decisions (including *why*), and errors to avoid.
* **Conflict Resolution:** If a discrepancy arises between **Engram** and **`MEMORY.md`**, **stop and ask the user** which source prevails before proceeding.
* **Hygiene:** Never store sensitive data (keys, tokens, personal info). Prune outdated entries; promote permanent findings to `AGENTS.md`.

---

## 3. Multi-Agent Environment & Skill Registry Protocol
This workspace operates via an interchangeable, non-hierarchical tool pipeline (`opecode`, `agy`, and `harness pi`), coordinated globally by `gentle-shell` under Alan Buscaglia's **Receive-Driven Development (RDD)** framework. Do not inject raw `SKILL.md` payloads into the main orchestrator context window.

### Skills — Loading and Registry Dependencies

This workspace relies on the **Open Agent Skills** ecosystem, installed locally via `npx skills`. On this machine, skill sources live in `/home/jolopez/.agents/skills/<name>` and are exposed to the repo as **symbolic links** under `.agents/skills/` (gitignored, per repo `.gitignore`), which agent configuration directories (OpenCode, agy, GitHub Copilot) and *gentle-shell* resolve at runtime. **Do not embed inline skill definitions (*skill payloads*) in prompts, and do not attempt to reinstall pre-linked local skills.**

### Core Knowledge Units (Gentle AI Skills)
* **Workflows:** Utilize **Gentle AI Skills** as reusable knowledge units for recurring development tasks (branches/PRs, commits, code reviews, design, issues, etc.).

### Registry Dependencies (`skills.sh`)
* **Runtime Logic:** `miles990/claude-software-skills` (Skill: `python`)
* **UI/UX Engine:** `gotar/opencode-config` (Skill: `gtk-ui-ux-engineer`)
* **Environment Sync:** `zjkal/sync-skills-wsl-skill` (Skill: `sync-skills-wsl`)
* **OS Telemetry:** `evolv3-ai/vibe-skills` (Skill: `admin`)

### Local Subagent Protocol (`.skills/`)
1. **Parent resolves paths once per session** under `## Skills to load before work` (`.skills/<name>/SKILL.md`).
2. **Subagents read those `SKILL.md` files locally** (`paths-injected`) or report unavailable paths (fallbacks in `orchestrator-skills.md`).
3. **Lifecycle Triggers:**
   * `/skill-creation` → `gentle-ai-skill-creator` (valid frontmatter required)
   * `improve skills` / `audit skills` → `gentle-ai-skill-improver`
   * `update skills` / `actualizar skills` → `gentle-ai-skill-registry`
4. **Custom project skills** belong under `.skills/odin-*` (e.g., `odin-pipeline`, `odin-testing`, `odin-gtk-debug`).

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
    │   ├── main_controller.py      # Primary orchestrator (load, pipeline, threads)
    │   └── worker_thread.py        # Threading + GLib.idle_add for UI dispatch
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
* **Centralized Configuration:** All processing parameters and logic thresholds are centralized in `config/config.yaml`.
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
* **NEVER** call GTK methods from background threads. Run heavy pipelines in `threading.Thread` (`worker_thread.py`) or `asyncio`, and dispatch UI updates strictly via `GLib.idle_add()` or `GLib.timeout_add()`.
* Disconnect signals or use weak references (`weakref`) when a widget outlives its controller to prevent memory leaks.

### 6.4 Conventions, Typing & Git Hygiene
* **Language:** All **code identifiers, comments, UI strings, and Conventional Commits** (`<type>[<scope>]: <desc>`) must be in **Spanish**. Keep code simple, descriptive, and clean (comments only where they add real value). Never add AI attribution (`Co-Authored-By`).
  > **Note:** This `AGENTS.md` is the sole technical document maintained in English per user decision.
* **Strict Typing & Anti-Blob Rule:** Enforce Python Type Hinting across all functions, parameters, and event callbacks. Never rewrite entire files for localized fixes.
* **System Telemetry:** Enabled via native MCP servers (Shell execution logs, Filesystem graphs, REPL runtimes) for automated RDD verification cycles.
* **Repository & Files:** Azure DevOps remote (`git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`; long-lived branches: `master` as origin HEAD, `main`, `rama`, `rama-Hybrida`). Keep `requirements.txt` in **UTF-8**. Never commit `core.*` crash dumps. Specs live in `.kiro/specs/`.

---

## 7. Automated Testing & Verification Protocols (TDD & Property-Based)
* **Baseline Suite:** Execute `python3 -m pytest tests -v` (183+ tests) and UI smoke test `python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print(f'GTK {Gtk.MAJOR_VERSION} OK, Adw OK')"` before accepting patches.
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
| Worker thread (async) | `src/odin/controllers/worker_thread.py` |
| Preprocesamiento aliases | `src/odin/Preprocesamiento/__init__.py` |
| Procesamiento aliases | `src/odin/Procesamiento/__init__.py` |
| Ajustes aliases | `src/odin/Ajustes/__init__.py` |
| Image utils (handle) | `src/odin/utils/handleImage.py` |
| Base strategy | `src/odin/Procesamiento/models/strategies/base_strategy.py` |
| Tests | `tests/` (pytest) |
| Project memory | `MEMORY.md` |
| Kiro specs | `.kiro/specs/` |

---

## 9. Project Conventions & Memory (Summary)

* **Language (Code/UI/Commits):** Spanish (this document is the only English exception).
* **Encoding:** `requirements.txt` in **UTF-8**.
* **Commits:** Conventional Commits `<type>[<scope>]: <desc>` (`feat`, `fix`, `refactor`, `docs`, `test`, ...). No AI attribution.
* **Remote:** Azure DevOps (`git@ssh.dev.azure.com:v3/JoseloCelis/ODIN/ODIN`); long-lived branches `master`, `main`, `rama`, `rama-Hybrida`.
* **Memory:** Engram = primary source; `MEMORY.md` = concise user ledger (~50 lines max). Conflict → ask user.
* **Sensitive Data:** Never store keys, tokens, or personal info.
* **Core Dumps:** `core.*` files must not be committed; add to `.gitignore` or delete.