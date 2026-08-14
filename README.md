# Project Patriot — Eden PACS QA Framework

Web UI test automation framework (BDD) for **Eden PACS** — a medical DICOM image viewer (MPR - Multi-Planar Reconstruction).

**Target:** `https://pacs.evacenter.com/v2/mpr`

**9 scenarios** covering measurement tools, circular menu, viewports, and scroll/zoom navigation.

---

## Stack

| Technology | Usage |
|------------|-------|
| **Python 3.11+** | Primary language |
| **Playwright** | Browser automation (async API) |
| **Behave** | BDD runner (Gherkin `.feature`) |
| **Allure** | Reporting with screenshots and evidence |
| **PyYAML** | Multi-team config |
| **Docker** | Containerized execution |

---

## Structure

```
eden-code-challenge/
├── core/                              # Framework core (reusable)
│   ├── config.py                      # Multi-team YAML config loader
│   ├── run_tests_utils.py             # CLI logic: behave commands, parallel, allure
│   └── drivers/
│       └── playwright_driver.py       # PlaywrightDriver + BrowserManager singleton
│
├── tests/webui/teams/eden/            # Team "eden" - Eden PACS tests
│   ├── config.yaml                    # Team config (URL, browser, selectors, timeouts)
│   ├── pages/
│   │   └── mpr_viewer.py             # Page Object: selectors + MPR viewer actions
│   └── features/
│       ├── environment.py             # Behave hooks (screenshots, cleanup, config load)
│       ├── mpr_viewer.feature         # 9 Gherkin scenarios
│       └── steps/
│           └── mpr_steps.py           # Step definitions (thin wrappers → Page Object)
│
├── results/                           # Auto-generated artifacts
│   ├── allure-results/                # Raw Allure JSON + screenshots
│   ├── allure-report/                 # HTML report
│   └── videos/                        # Browser session recordings (.webm)
│
├── run_tests.py                       # CLI entry point
├── Dockerfile                         # Python 3.11 + Playwright + Allure
├── docker-compose.yml                 # Docker test runner
├── requirements.txt
├── .env.example
└── allure.config.cjs
```

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure (optional)

```bash
cp .env.example .env
```

### 3. Run

```bash
python run_tests.py -t eden                     # All scenarios
python run_tests.py -t eden --tags="@smoke"     # Smoke only
python run_tests.py -t eden --headless          # No window
```

---

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --team` | Team name (required) | — |
| `-f, --feature` | Specific feature | All |
| `--tags` | Behave filter (`@smoke`, `@measurement`, etc.) | All |
| `-p, --parallel` | Parallel execution (N teams) | 1 |
| `--headless` | Force headless (override `config.yaml`) | yaml value |

---

## Team Config

Each team lives in `tests/webui/teams/<team>/config.yaml`:

```yaml
team_name: eden
base_url: https://pacs.evacenter.com
browser: chromium       # chromium | firefox | webkit
headless: true
timeout: 60000          # default context timeout (ms)

mpr_viewer:
  url: '/v2/mpr?studyId=...&tab=images&ac=...&md=1&...'

  selectors:
    circular_menu_opened: '.circular-menu.opened-nav'
    circular_menu_item: '#circular-menu.opened-nav > ul > li > a'
    viewport_articles: article
    active_tool_tab: '[role="tab"][aria-selected="true"]'
    longitud_button: 'button[data-cy="button-Longitud"]'

  icon_paths:
    ruler: 'M4 9a1 1 0 0 1 1-1h14'
    pan: 'M11.293 4.293a1 1 0 011.414 0l'
    zoom: 'M11 6a5 5 0 100 10 5 5 0 000-1'

  tool_labels:
    measurement: Measurement
    pan: Pan
    zoom: Zoom

  timeouts:
    network_idle: 15000
    fallback_wait: 5000
    circular_menu_open: 5000
    circular_menu_close: 2000
    tool_activate: 10000
```

Overrides via env vars: `PATRIOT_BASE_URL`, `PATRIOT_BROWSER`, `PATRIOT_HEADLESS`, `PATRIOT_TIMEOUT`.

---

## Test Suite

| # | Tag | Scenario | What it verifies |
|---|-----|----------|------------------|
| 1 | `@smoke` | Page load | Viewer loads, 4 viewports visible |
| 2 | `@measurement` | Ruler happy path | Draw line → annotation + text + value > 0 |
| 3 | `@toolswitch` | Pan after measurement | Pan drag doesn't create extra annotations |
| 4 | `@zoom` | Zoom persistence | Annotation survives zoom operation |
| 5 | `@persist` | Consecutive draws | 2 lines = 2 annotations (tool stays active) |
| 6 | `@menu` | Menu close | Outside click closes circular menu |
| 7 | `@zerodistance` | Double-click edge case | Click on same point = 0 annotations |
| 8 | `@crossplane` | Viewport independence | Draw in viewport 1 doesn't affect viewport 0 |
| 9 | `@scroll` | Scroll behavior | Annotation disappears on scroll up, reappears on scroll down |

Filter by tag:

```bash
python run_tests.py -t eden --tags="@measurement"
python run_tests.py -t eden --tags="@pacs"          # All PACS
```

---

## Docker

```bash
docker compose build
docker compose run --rm tests -t eden
docker compose run --rm tests -t eden --tags @smoke
docker compose run --rm tests -t eden --headless
```

Results are saved in `./results/` (mounted volume).

---

## Architecture

### Multi-Team

Each team is self-contained in `tests/webui/teams/<team>/` with its own config, features, and pages. `run_tests.py -t team1,team2 -p 2` runs teams in parallel.

### Page Object Model

`MprViewerPage` (`pages/mpr_viewer.py`) centralizes all selectors and interactions. Step definitions are thin wrappers that call Page Object methods and attach evidence. Selectors are loaded from `config.yaml` — no hardcoded constants in the class.

### Async Playwright + Behave

All browser interactions use Playwright async. Steps are `async def`. The `BrowserManager` singleton manages the browser lifecycle (launch → context → page → cleanup).

### Evidence Collection

- Each step receives an automatic screenshot via `after_step` hook.
- Specific steps attach named evidence (highlight screenshots, assertion values).
- Full session video per scenario (`results/videos/*.webm`).
- Single-file Allure report with screenshots, text, and video.

---

## Technical Decisions

### Circular Menu (not Toolbar)

Eden uses a **circular menu** (right-click on viewport) to select tools, not a toolbar. The menu is an SVG radial with CSS transforms that make standard Playwright clicks unreliable.

### Canvas Interception Fix

Cornerstone3D renders on `<canvas>` that intercepts pointer events. Solution: inject CSS temporarily before interacting:

```python
canvas_style = await page.add_style_tag(
    content="canvas { pointer-events: none !important; }"
)
try:
    await page.mouse.click(x, y)
finally:
    await canvas_style.evaluate("element => element.remove()")
```

### SVG Path Tool Identification

Sub-menu items have CSS transforms that make coordinate-based clicks unreliable. Tools are identified by their **SVG `d` attribute**:

| Tool | SVG path starts with |
|------|---------------------|
| Ruler (Longitud) | `M4 9a1 1 0 0 1 1-1h14` |
| Pan | `M11.293 4.293a1 1 0 011.414 0l` |
| Zoom | `M11 6a5 5 0 100 10 5 5 0 000-1` |

To add a new tool: inspect the `<path d="...">` in the circular menu.

### WebGL + Headless

The viewer uses WebGL (Cornerstone3D). In headless mode, WebGL canvases frequently render gray/blank. The default in `config.yaml` is `headless: true`; if you need to see the browser, set `headless: false`.

### Page Load Strategy

The viewer loads heavy DICOM data. `networkidle` is unreliable due to WebSockets. Strategy:

1. `goto()` with `wait_until="domcontentloaded"`
2. `wait_for_selector("article")` — viewer shell exists
3. `wait_for_load_state("networkidle", timeout=15000)` with 5s fallback

### SVG Annotation Overlays

Measurements are SVG overlays on the WebGL canvas, NOT inside the canvas. They can be queried via DOM:

```javascript
document.querySelectorAll('.viewport-element svg g[data-annotation-uid]')
```

---

## How to Extend

### New circular menu tool

1. Inspect SVG `<path d="...">` of the tool in the circular menu.
2. Add the `icon_path` in `config.yaml` → `mpr_viewer.icon_paths`.
3. Create activation method in `mpr_viewer.py` (use `activate_measurement_tool` as template).
4. Add step definition in `mpr_steps.py`.
5. Write scenario in `mpr_viewer.feature`.

### New viewport interaction

Use `draw_line_on_viewport()` as template: get center with `get_viewport_center()`, calculate offsets, use `page.mouse.click()`.

### New annotation assertion

Annotations are SVGs with consistent structure:

```
.viewport-element svg
  g[data-annotation-uid="xxx"]
    text              # Measurement value (e.g., "206 mm")
    line[data-id]     # Ruler line
    circle[data-id]   # Endpoints (optional)
```

Query `g[data-annotation-uid]` groups and inspect child elements.

---

## Selectors

| Element | Selector |
|---------|----------|
| Circular menu (open) | `.circular-menu.opened-nav` |
| Circular menu items | `#circular-menu.opened-nav > ul > li > a` |
| Viewport articles | `article` |
| Viewport SVG overlay | `.viewport-element svg` |
| Annotation group | `g[data-annotation-uid]` |
| Measurement text | `g[data-annotation-uid] text` |
| Active tool tab | `[role="tab"][aria-selected="true"]` |
| Longitud button | `button[data-cy="button-Longitud"]` |

---

## Viewports

| Index | Content |
|-------|---------|
| 0 | Axial (primary, measurements) |
| 1 | Coronal |
| 2 | Sagittal |
| 3 | 3D / Patient info |

---

## Import Conventions

Each team is self-contained. `environment.py` adds the team directory to `sys.path`:

```python
from pages.mpr_viewer import MprViewerPage      # team local
from core.config import config                    # framework core
from core.drivers.playwright_driver import BrowserManager
```

Absolute imports like `tests.webui...` are not used (root folder has a hyphen).

---

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| Click hits wrong element | Canvas intercepts pointer events | Inject `canvas { pointer-events: none !important; }` |
| Circular menu item not found | Incomplete menu animation | Add `wait_for_timeout(500)` after opening |
| Measurement not created | Tool not fully activated | Add `wait_for_function` verifying tab/button |
| Gray/blank viewports | WebGL doesn't render in headless | Use `headless: false` in config |
| Timeout on `networkidle` | Open WebSocket connections | Catch timeout, fallback to fixed wait |
| Sub-menu selects wrong tool | CSS transforms shift positions | Identify tools by SVG `d` attribute |
| State leak between scenarios | Browser not closed | `BrowserManager.close()` in `after_scenario` |

---

## Files to Modify When Extending

| What to do | Files |
|------------|-------|
| New tool | `config.yaml` + `pages/mpr_viewer.py` + `steps/mpr_steps.py` + `mpr_viewer.feature` |
| New viewport interaction | `pages/mpr_viewer.py` |
| New assertion | `pages/mpr_viewer.py` |
| Change team config | `tests/webui/teams/eden/config.yaml` |
| New team | Create `tests/webui/teams/<team>/` with `config.yaml` + `features/` + `pages/` |

---

## Author

**davidrodcruz** — Software Engineer in Test

---

## License

MIT
