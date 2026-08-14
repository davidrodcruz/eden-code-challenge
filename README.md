# Proyect Patriot — Eden PACS QA Framework

Framework de automatización de pruebas Web UI (BDD) para **Eden PACS** — un visor médico de imágenes DICOM (MPR - Multi-Planar Reconstruction).

**Target:** `https://pacs.evacenter.com/v2/mpr`

**9 escenarios** cubriendo herramientas de medición, menú circular, viewports y navegación scroll/zoom.

---

## Stack

| Tecnología | Uso |
|------------|-----|
| **Python 3.11+** | Lenguaje principal |
| **Playwright** | Browser automation (async API) |
| **Behave** | BDD runner (Gherkin `.feature`) |
| **Allure** | Reporting con screenshots y evidencia |
| **PyYAML** | Config multi-team |
| **Docker** | Ejecución containerizada |

---

## Estructura

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
│   │   └── mpr_viewer.py             # Page Object: selectors + acciones MPR viewer
│   └── features/
│       ├── environment.py             # Behave hooks (screenshots, cleanup, config load)
│       ├── mpr_viewer.feature         # 9 Gherkin scenarios
│       └── steps/
│           └── mpr_steps.py           # Step definitions (thin wrappers → Page Object)
│
├── results/                           # Artifacts auto-generados
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

## Inicio Rápido

### 1. Instalar dependencias

```bash
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar (opcional)

```bash
cp .env.example .env
```

### 3. Ejecutar

```bash
python run_tests.py -t eden                     # Todos los escenarios
python run_tests.py -t eden --tags="@smoke"     # Solo smoke
python run_tests.py -t eden --headless          # Sin ventana
```

---

## CLI Options

| Opción | Descripción | Default |
|--------|-------------|---------|
| `-t, --team` | Nombre del equipo (requerido) | — |
| `-f, --feature` | Feature específico | Todos |
| `--tags` | Filtro Behave (`@smoke`, `@measurement`, etc.) | Todos |
| `-p, --parallel` | Ejecución paralela (N equipos) | 1 |
| `--headless` | Forzar headless (override de `config.yaml`) | valor del yaml |

---

## Config por equipo

Cada equipo vive en `tests/webui/teams/<team>/config.yaml`:

```yaml
team_name: eden
base_url: https://pacs.evacenter.com
browser: chromium       # chromium | firefox | webkit
headless: true
timeout: 60000          # default timeout del contexto (ms)

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
    measurement: Medición
    pan: Mover
    zoom: Zoom

  timeouts:
    network_idle: 15000
    fallback_wait: 5000
    circular_menu_open: 5000
    circular_menu_close: 2000
    tool_activate: 10000
```

Overrides vía env vars: `PATRIOT_BASE_URL`, `PATRIOT_BROWSER`, `PATRIOT_HEADLESS`, `PATRIOT_TIMEOUT`.

---

## Suite de Tests

| # | Tag | Scenario | Qué verifica |
|---|-----|----------|--------------|
| 1 | `@smoke` | Page load | Viewer carga, 4 viewports visibles |
| 2 | `@measurement` | Ruler happy path | Draw line → annotation + texto + valor > 0 |
| 3 | `@toolswitch` | Pan after measurement | Pan drag no crea annotations extra |
| 4 | `@zoom` | Zoom persistence | Annotation sobrevive operación de zoom |
| 5 | `@persist` | Consecutive draws | 2 líneas = 2 annotations (tool sigue activo) |
| 6 | `@menu` | Menu close | Outside click cierra menú circular |
| 7 | `@zerodistance` | Double-click edge case | Click en mismo punto = 0 annotations |
| 8 | `@crossplane` | Viewport independence | Draw en viewport 1 no afecta viewport 0 |
| 9 | `@scroll` | Scroll behavior | Annotation desaparece scroll up, reaparece scroll down |

Filtrar por tag:

```bash
python run_tests.py -t eden --tags="@measurement"
python run_tests.py -t eden --tags="@pacs"          # Todos los PACS
```

---

## Docker

```bash
docker compose build
docker compose run --rm tests -t eden
docker compose run --rm tests -t eden --tags @smoke
docker compose run --rm tests -t eden --headless
```

Los resultados se guardan en `./results/` (volumen montado).

---

## Arquitectura

### Multi-Team

Cada equipo es auto-contenido en `tests/webui/teams/<team>/` con su propio config, features y pages. `run_tests.py -t team1,team2 -p 2` ejecuta equipos en paralelo.

### Page Object Model

`MprViewerPage` (`pages/mpr_viewer.py`) centraliza todos los selectores e interacciones. Los step definitions son wrappers finos que llaman métodos del Page Object y adjuntan evidencia. Los selectores se cargan desde `config.yaml` — no hay constantes hardcodeadas en la clase.

### Async Playwright + Behave

Todas las interacciones del browser usan Playwright async. Los steps son `async def`. El `BrowserManager` singleton maneja el lifecycle del browser (launch → context → page → cleanup).

### Evidence Collection

- Cada step recibe un screenshot automático vía `after_step` hook.
- Steps específicos adjuntan evidencia named (highlight screenshots, assertion values).
- Video de sesión completo por escenario (`results/videos/*.webm`).
- Reporte Allure single-file con screenshots, textos y video.

---

## Decisiones Técnicas

### Menú Circular (no Toolbar)

Eden usa un **menú circular** (right-click en viewport) para seleccionar herramientas, no la toolbar. El menú es un SVG radial con CSS transforms que hacen clicks estándar de Playwright poco confiables.

### Canvas Interception Fix

Cornerstone3D renderiza en `<canvas>` que intercepta pointer events. Solución: inyectar CSS temporalmente antes de interactuar:

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

Los items del sub-menú tienen CSS transforms que hacen clicks por coordenadas poco confiables. Las herramientas se identifican por su **SVG `d` attribute**:

| Tool | SVG path starts with |
|------|---------------------|
| Ruler (Longitud) | `M4 9a1 1 0 0 1 1-1h14` |
| Pan | `M11.293 4.293a1 1 0 011.414 0l` |
| Zoom | `M11 6a5 5 0 100 10 5 5 0 000-1` |

Para agregar una nueva herramienta: inspeccionar el `<path d="...">` en el circular menu.

### WebGL + Headless

El viewer usa WebGL (Cornerstone3D). En headless mode, los canvas WebGL frecuentemente renderizan en gris/blank. El default en `config.yaml` es `headless: true`; si necesitás ver el browser, poné `headless: false`.

### Page Load Strategy

El viewer carga DICOM data pesado. `networkidle` es poco confiable por WebSockets. Estrategia:

1. `goto()` con `wait_until="domcontentloaded"`
2. `wait_for_selector("article")` — viewer shell existe
3. `wait_for_load_state("networkidle", timeout=15000)` con fallback de 5s

### SVG Annotation Overlays

Las mediciones son SVG overlays sobre el canvas WebGL, NO dentro del canvas. Se pueden queryar vía DOM:

```javascript
document.querySelectorAll('.viewport-element svg g[data-annotation-uid]')
```

---

## Cómo Extender

### Nueva herramienta del circular menu

1. Inspeccionar SVG `<path d="...">` de la herramienta en el circular menu.
2. Agregar el `icon_path` en `config.yaml` → `mpr_viewer.icon_paths`.
3. Crear método de activación en `mpr_viewer.py` (usar `activate_measurement_tool` como template).
4. Agregar step definition en `mpr_steps.py`.
5. Escribir scenario en `mpr_viewer.feature`.

### Nueva interacción de viewport

Usar `draw_line_on_viewport()` como template: obtener centro con `get_viewport_center()`, calcular offsets, usar `page.mouse.click()`.

### Nueva assertion de annotations

Las annotations son SVG con estructura consistente:

```
.viewport-element svg
  g[data-annotation-uid="xxx"]
    text              # Valor de medición (ej: "206 mm")
    line[data-id]     # Ruler line
    circle[data-id]   # Endpoints (opcional)
```

Query `g[data-annotation-uid]` groups e inspeccionar child elements.

---

## Selectores

| Elemento | Selector |
|----------|----------|
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

| Index | Contenido |
|-------|-----------|
| 0 | Axial (primario, mediciones) |
| 1 | Coronal |
| 2 | Sagittal |
| 3 | 3D / Patient info |

---

## Convenciones de Imports

Cada equipo es auto-contenido. `environment.py` agrega el directorio del equipo a `sys.path`:

```python
from pages.mpr_viewer import MprViewerPage      # local del equipo
from core.config import config                    # framework core
from core.drivers.playwright_driver import BrowserManager
```

No se usan imports absolutos tipo `tests.webui...` (la carpeta raíz tiene guion).

---

## Pitfalls Comunes

| Problema | Causa | Fix |
|----------|-------|-----|
| Click pega en elemento equivocado | Canvas intercepta pointer events | Inyectar `canvas { pointer-events: none !important; }` |
| Circular menu item no encontrado | Animación del menú incompleta | Agregar `wait_for_timeout(500)` después de abrir |
| Medición no se crea | Tool no se activó completamente | Agregar `wait_for_function` verificando tab/button |
| Viewports grises/blank | WebGL no renderiza en headless | Usar `headless: false` en config |
| Timeout en `networkidle` | WebSocket connections abiertas | Catch timeout, fallback a wait fijo |
| Sub-menu selecciona herramienta equivocada | CSS transforms desplazan posiciones | Identificar tools por SVG `d` attribute |
| State leak entre escenarios | Browser no cerrado | `BrowserManager.close()` en `after_scenario` |

---

## Archivos a Modificar al Extender

| Qué hacer | Archivos |
|-----------|----------|
| Nueva herramienta | `config.yaml` + `pages/mpr_viewer.py` + `steps/mpr_steps.py` + `mpr_viewer.feature` |
| Nueva interacción viewport | `pages/mpr_viewer.py` |
| Nueva assertion | `pages/mpr_viewer.py` |
| Cambiar config del equipo | `tests/webui/teams/eden/config.yaml` |
| Nuevo equipo | Crear `tests/webui/teams/<team>/` con `config.yaml` + `features/` + `pages/` |

---

## Autor

**Davo** — Software Engineer in Test
