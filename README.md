# eden-code-challenge — Eden PACS QA Framework

Web UI test automation framework (BDD) for **Eden PACS** — a medical DICOM image viewer (MPR - Multi-Planar Reconstruction).

**Target:** `https://pacs.evacenter.com/v2/mpr`

**14 scenarios** covering measurement creation, spatial transforms, multiplanar isolation, mutation, tool state, circular menu, and viewer loading.

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
│   ├── base_page.py                   # Base page and MCP action logging
│   └── drivers/
│       └── playwright_driver.py       # PlaywrightDriver + BrowserManager singleton
│
├── handlers/                           # Browser state and test handlers
│   ├── cornerstone_test_bridge.py      # Sync Playwright model bridge + math assertions
│   └── cornerstone_test_bridge.js      # Pre-navigation webpack bridge injection
│
├── utils/                              # Reusable test utilities
│   ├── progress_utils.py               # Progress output helpers
│   ├── run_tests_utils.py              # CLI logic: behave commands and allure
│   ├── shared_actions.py               # Generic async Playwright actions
│
├── tests/webui/teams/eden/            # Team "eden" - Eden PACS tests
│   ├── config.yaml                    # Team config (URL, browser, selectors, timeouts)
│   ├── pages/
│   │   └── mpr_viewer.py             # Page Object: selectors + MPR viewer actions
│   └── features/
│       ├── environment.py             # Behave hooks (screenshots, cleanup, config load)
│       ├── mpr_viewer.feature         # 14 Gherkin scenarios
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

  timeouts:
    network_idle: 15000
    fallback_wait: 5000
    circular_menu_open: 5000
    circular_menu_close: 2000
    tool_activate: 10000
```

Overrides via env vars: `EDEN_BASE_URL`, `EDEN_BROWSER`, `EDEN_HEADLESS`, `EDEN_TIMEOUT`.

---

## Test Suite

| # | Tag | Scenario | What it verifies |
|---|-----|----------|------------------|
| 1 | `@smoke` | Page load | Viewer loads, 4 viewports visible |
| 2 | `@measurement` | Exact measurement geometry | World-space distance matches the reported millimeter value |
| 3 | `@persist` | Unique measurement state | Multiple measurements retain unique UIDs |
| 4 | `@zerodistance` | Ghost annotation prevention | Zero-distance input registers no annotation |
| 5 | `@zoom` | Zoom transform integrity | UID and points persist after zoom |
| 6 | `@pan` | Pan transform integrity | World coordinates remain unchanged after pan |
| 7 | `@scroll` | Slice isolation | Annotation is hidden on adjacent slice and persists in state |
| 8 | `@crossplane` | Axial/coronal isolation | Axial annotation is not registered on coronal plane |
| 9 | `@crossplane` | Sagittal/axial isolation | Sagittal annotation is not registered on axial plane |
| 10 | `@edit` | Measurement mutation | Endpoint movement changes points and length, preserving UID |
| 11 | `@delete` | State cleanup | Deleting a selected measurement removes its UID |
| 12 | `@toolswitch` | Non-annotative navigation | Pan does not create measurements |
| 13 | `@toolswitch` | Tool toggle integrity | Switching tools preserves old state and allows a second measurement |
| 14 | `@menu` | Menu close | Outside click closes circular menu |

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

## CI/CD (GitHub Actions)

Automated test execution via `.github/workflows/e2e-tests.yml`.

### Triggers

| Trigger | Description |
|---------|-------------|
| `pull_request` → `main` | Runs on every PR targeting main |
| `repository_dispatch` | External webhooks (`run-tests-webhook`) |
| `workflow_dispatch` | Manual execution from GitHub UI |

### Pipeline Steps

1. **Checkout** — Clone repository
2. **Docker Build** — Build image with layer caching (GHA cache)
3. **Run Tests** — Execute `@smoke` tests in headless mode
4. **PR Comment** — Sticky comment with result (🟢/🔴)
5. **Upload Artifacts** — Allure reports + videos (2-day retention)
6. **Evaluate** — Fail pipeline if tests failed

### Execution

```bash
# Triggered automatically on PR, or manually:
docker compose run --rm tests -t eden --tags @smoke --headless
```

### Why Only @smoke in CI?

WebGL-dependent tests (measurement, zoom, scroll) require GPU rendering. GitHub Actions runners use software rendering (SwiftShader) which is too slow for interactive WebGL operations. Smoke tests verify the deployment without WebGL dependencies.

Full test suite runs locally:
```bash
docker compose run --rm tests -t eden --headless
```

### PR Comment Example

```
## E2E Tests - Eden PACS MPR

### Result: Passed 🟢

Smoke tests executed in Docker container (python:3.11-slim-bookworm).
Command: docker compose run --rm tests -t eden --tags @smoke --headless

> Allure report and video recordings available in workflow artifacts.
```

---

## Architecture

### Multi-Team

Each team is self-contained in `tests/webui/teams/<team>/` with its own config, features, and pages. `run_tests.py -t team1,team2` runs the requested teams sequentially.

### Page Object Model

`MprViewerPage` (`pages/mpr_viewer.py`) centralizes all selectors and interactions. Step definitions are thin wrappers that call Page Object methods and attach evidence. Selectors are loaded from `config.yaml` — no hardcoded constants in the class.

### Shared Actions

`SharedActions` (`utils/shared_actions.py`) is the common interaction layer for every page object. It provides navigation, click, right-click, fill, wait, hover, keyboard, coordinate click, double-click, drag, scroll, bounding-box, center, screenshot, and canvas pointer-event actions. A new page object can reuse it directly:

```python
from utils.shared_actions import SharedActions


class AnyPage(SharedActions):
    pass
```

Domain-specific page methods should compose these actions instead of calling Playwright mouse or keyboard primitives directly. Behave steps remain thin and should call the page object or `SharedActions` instance.

### Async Playwright + Behave

All browser interactions use Playwright async. Steps are `async def`. The `BrowserManager` singleton manages the browser lifecycle (launch → context → page → cleanup).

### Evidence Collection

- Each step receives an automatic screenshot via `after_step` hook.
- Specific steps attach named evidence (highlight screenshots, assertion values).
- Full session video per scenario (`results/videos/*.webm`).
- Single-file Allure report with screenshots, text, and video.

---

## Architecture Note (Multi-Tenant Design)

The `tests/webui/teams/eden/` structure and the `-t eden` CLI flag might look over-engineered for a 14-scenario challenge. This is intentional.

My approach as a Quality Architect isn't just "automate a flow" — it's to build **scalable test infrastructure** (a Quality Platform). In a real environment like Eden, where different squads (e.g., Viewer, Patient Portal, Billing) automate against the same product, a monolithic design creates dependency conflicts and CI/CD bottlenecks.

This framework is designed to be **Multi-Tenant**:

- **Config isolation** — `config.yaml` per team
- **Isolation of Page Objects and Features** — each team owns its domain
- **Independent execution by business domain** in the pipeline (`-t viewer,portal,billing`)

The goal of this delivery is to demonstrate how I would structure the base so that **N teams can automate autonomously from day 1**.

---

## Technical Decisions

### Circular Menu (not Toolbar)

Eden uses a **circular menu** (right-click on viewport) to select tools, not a toolbar. The menu is an SVG radial with CSS transforms that make standard Playwright clicks unreliable.

### Canvas Interception Fix

Cornerstone3D renders on `<canvas>` that intercepts pointer events. `SharedActions.canvas_pointer_events_disabled()` routes coordinate events to the viewport container while preserving cleanup:

```python
async with actions.canvas_pointer_events_disabled():
    await actions.click_at(x, y)
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

### Cornerstone Model Bridge

Annotation assertions must use CornerstoneTools state, never rendered SVG, canvas pixels, or measurement labels. The deployed bundle (`viewers@0.78.0`) contains `annotation.state.getAnnotationManager()` and `getAllAnnotations()`, but it does not expose `window.cornerstoneTools` or `window.cornerstone3D`.

The frontend has a development-only `window.__viewers` object with `getMeasurements`, but it is created only when `location.hostname === "localhost"`. The PACS URL therefore needs the test-side fallback in `handlers/cornerstone_test_bridge.js`. `BrowserManager` installs it with `add_init_script()` before the application scripts execute.

The bridge locates the loaded webpack modules by exported API shape, captures the CornerstoneTools module, and returns only JSON-safe data:

- `uid` and `toolName`
- `frameOfReferenceUID`, `referencedImageId`, `volumeId`, and `sliceIndex`
- world-space `points`, plane vectors, and camera vectors
- numeric measurements and units from `data.cachedStats`
- viewport camera and current-slice state
- current-slice visibility, UID lookup, and world-to-canvas projection for interaction

The bridge deliberately does not inspect the presentation overlay or read label strings. Model annotations remain in state when a slice changes; a test should compare UID and world-space points before and after navigation rather than assert that an overlay is rendered.

Synchronous Playwright usage:

```python
from handlers.cornerstone_test_bridge import (
    CornerstoneTestBridge,
    assert_annotation_persisted,
    assert_vector_close,
)

bridge = CornerstoneTestBridge(page)
bridge.install()  # Must run before page.goto(...)
page.goto(viewer_url)
bridge.wait_until_ready()

before = bridge.get_annotations(viewport_id=0, tool_name="Length")
assert before["count"] == 1
annotation = before["annotations"][0]
assert annotation["measurement"]["unit"] == "mm"
assert annotation["measurement"]["value"] > 0

slice_before = bridge.get_viewport_state(0)
# Perform the slice interaction through the normal Page Object.
slice_after = bridge.get_viewport_state(0)
assert slice_before["sliceIndex"] != slice_after["sliceIndex"]

after = bridge.get_annotations(viewport_id=0, tool_name="Length")
assert_annotation_persisted(before, after, tolerance=0.1)
assert_vector_close(
    after["annotations"][0]["points"][0],
    before["annotations"][0]["points"][0],
    tolerance=0.1,
)
```

### Testability Assessment

The current frontend makes a stable test contract harder than necessary. CornerstoneTools is bundled privately, the useful `__viewers` bridge is gated to `localhost`, and annotation ownership is grouped by Frame of Reference rather than stored as a public viewport contract. The webpack fallback is therefore a test-only compatibility layer, not a long-term API.

The preferred frontend change is to export a stable `window.__E2E_TEST_BRIDGE__` only in an explicit E2E build or test environment. That bridge should call the imported CornerstoneTools/Core APIs directly and keep the same JSON schema. This removes dependence on webpack internals and makes bundle upgrades fail fast at the contract boundary.

---

## How to Extend

### New circular menu tool

1. Inspect SVG `<path d="...">` of the tool in the circular menu.
2. Add the `icon_path` in `config.yaml` → `mpr_viewer.icon_paths`.
3. Create activation method in `mpr_viewer.py` (use `activate_measurement_tool` as template).
4. Add step definition in `mpr_steps.py`.
5. Write scenario in `mpr_viewer.feature`.

### New viewport interaction

Use `draw_line_on_viewport()` as template: get center with `get_viewport_center()`, calculate offsets, and compose `SharedActions.click_at()`, `drag()`, or `scroll()`.

### New annotation assertion

Use `CornerstoneTestBridge.get_annotations()` and assert on `uid`, world-space `points`, `referencedImageId`, `sliceIndex`, and `measurement`. Keep tolerance explicit for floating-point world coordinates.

---

## Selectors

| Element | Selector |
|---------|----------|
| Circular menu (open) | `.circular-menu.opened-nav` |
| Circular menu items | `#circular-menu.opened-nav > ul > li > a` |
| Viewport articles | `article` |
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
| Measurement not created | Tool not fully activated | Wait for bridge `getActiveTools()` to report `Length` |
| Slice assertion is ambiguous | Model state persists off-slice | Use `get_visible_annotation_count()` for rendered slice visibility and `get_annotation_count()` for persistence |
| Endpoint interaction misses | World coordinates are local to the canvas | Project with `world_to_canvas()` and add the canvas bounding-box origin |
| Delete does nothing | Annotation was not selected | Select using the projected world-space midpoint before pressing `Delete` |
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

**davidrodcruz** — Senior Software Engineer in Test

---

## License

MIT
