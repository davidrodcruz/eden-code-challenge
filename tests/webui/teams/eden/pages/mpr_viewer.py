from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


class MprViewerPage:
    def __init__(self, page: Page, config: dict):
        self.page = page

        viewer = config["mpr_viewer"]
        selectors = viewer["selectors"]
        icons = viewer["icon_paths"]
        labels = viewer["tool_labels"]
        timeouts = viewer["timeouts"]

        self.url = config["base_url"] + viewer["url"]

        self.circular_menu_opened = selectors["circular_menu_opened"]
        self.circular_menu_item = selectors["circular_menu_item"]
        self.viewport_articles = selectors["viewport_articles"]
        self.active_tool_tab = selectors["active_tool_tab"]
        self.longitud_button = selectors["longitud_button"]

        self.ruler_icon = icons["ruler"]
        self.pan_icon = icons["pan"]
        self.zoom_icon = icons["zoom"]

        self.measurement_label = labels["measurement"]
        self.pan_label = labels["pan"]
        self.zoom_label = labels["zoom"]

        self.network_idle_timeout = timeouts["network_idle"]
        self.fallback_wait = timeouts["fallback_wait"]
        self.circular_menu_open_timeout = timeouts["circular_menu_open"]
        self.circular_menu_close_timeout = timeouts["circular_menu_close"]
        self.tool_activate_timeout = timeouts["tool_activate"]

    async def navigate(self) -> None:
        await self.page.goto(self.url, wait_until="domcontentloaded")

    async def wait_until_loaded(self) -> None:
        await self.page.wait_for_selector(self.viewport_articles, state="visible")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=self.network_idle_timeout)
        except PlaywrightTimeoutError:
            await self.page.wait_for_timeout(self.fallback_wait)

    async def screenshot(self) -> bytes:
        return await self.page.screenshot(full_page=True)

    async def open_circular_menu_on_viewport(self, viewport_index: int = 0) -> None:
        articles = self.page.locator(self.viewport_articles)
        article = articles.nth(viewport_index)
        await article.click(button="right")
        await self.page.wait_for_selector(
            self.circular_menu_opened, state="visible", timeout=self.circular_menu_open_timeout
        )

    async def is_circular_menu_visible(self) -> bool:
        return await self.page.locator(self.circular_menu_opened).is_visible()

    async def get_circular_menu_items(self) -> list[Locator]:
        return self.page.locator(self.circular_menu_item)

    async def get_circular_menu_item_count(self) -> int:
        return await self.page.locator(self.circular_menu_item).count()

    async def click_circular_menu_item(self, item_index: int) -> None:
        items = self.page.locator(self.circular_menu_item)
        await items.nth(item_index).click()

    async def click_circular_menu_item_by_svg_path(self, path_start: str) -> None:
        item = self.page.locator(
            f"{self.circular_menu_item} svg path[d^='{path_start}']"
        ).locator("..")
        await item.click()

    async def close_circular_menu(self) -> None:
        await self.page.keyboard.press("Escape")
        await self.page.wait_for_selector(
            self.circular_menu_opened, state="hidden", timeout=self.circular_menu_close_timeout
        )

    async def activate_measurement_tool(self) -> bytes:
        await self.open_circular_menu_on_viewport(0)
        await self.page.wait_for_timeout(500)
        highlight_screenshot = await self._click_circular_menu_tool(self.ruler_icon)
        await self.page.wait_for_function(
            f"""
            () => document.querySelector('{self.active_tool_tab}')
                ?.textContent.trim() === '{self.measurement_label}'
                && !!document.querySelector('{self.longitud_button}')
            """,
            timeout=self.tool_activate_timeout,
        )
        return highlight_screenshot

    async def activate_pan_tool(self) -> None:
        await self.open_circular_menu_on_viewport(0)
        await self.page.wait_for_timeout(500)
        await self._click_circular_menu_tool(self.pan_icon)
        await self.page.wait_for_function(
            f"""
            () => document.querySelector('{self.active_tool_tab}')
                ?.textContent.trim() === '{self.pan_label}'
            """,
            timeout=self.tool_activate_timeout,
        )

    async def activate_zoom_tool(self) -> None:
        await self.open_circular_menu_on_viewport(0)
        await self.page.wait_for_timeout(500)
        await self._click_circular_menu_tool(self.zoom_icon)
        await self.page.wait_for_function(
            f"""
            () => document.querySelector('{self.active_tool_tab}')
                ?.textContent.trim() === '{self.zoom_label}'
            """,
            timeout=self.tool_activate_timeout,
        )

    async def clear_annotations(self, viewport_index: int = 0) -> None:
        await self.page.evaluate(
            """
            (viewportIndex) => {
                const svgs = document.querySelectorAll('.viewport-element svg');
                const svg = svgs[viewportIndex];
                if (!svg) return;
                const groups = svg.querySelectorAll('g[data-annotation-uid]');
                groups.forEach(g => g.remove());
            }
            """,
            viewport_index,
        )

    async def _click_circular_menu_tool(self, path_start: str) -> bytes:
        position = await self.page.evaluate(
            """
            (pathStart) => {
                const path = [...document.querySelectorAll(
                    '#circular-menu.opened-nav > ul > li > a svg path'
                )].find(element => element.getAttribute('d')?.startsWith(pathStart));
                const svg = path?.closest('svg');
                if (!svg) return null;

                const rect = svg.getBoundingClientRect();
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
            }
            """,
            path_start,
        )
        if not position:
            raise ValueError(f"Circular menu tool not found: {path_start}")

        canvas_style = await self.page.add_style_tag(
            content="canvas { pointer-events: none !important; }"
        )
        try:
            await self.page.mouse.move(position["x"], position["y"])
            await self.page.wait_for_timeout(300)
            highlight_screenshot = await self.page.screenshot(full_page=True)
            await self.page.mouse.click(position["x"], position["y"])
        finally:
            await canvas_style.evaluate("element => element.remove()")

        await self.page.wait_for_selector(
            self.circular_menu_opened, state="hidden", timeout=5000
        )
        return highlight_screenshot

    async def get_viewport_center(self, viewport_index: int = 0) -> dict:
        articles = self.page.locator(self.viewport_articles)
        article = articles.nth(viewport_index)
        box = await article.bounding_box()
        if not box:
            raise ValueError(f"Viewport {viewport_index} not found")
        return {
            "x": box["x"] + box["width"] / 2,
            "y": box["y"] + box["height"] / 2,
            "width": box["width"],
            "height": box["height"],
        }

    async def draw_line_on_viewport(
        self, viewport_index: int = 0, x1: float = None, y1: float = None,
        x2: float = None, y2: float = None
    ) -> None:
        center = await self.get_viewport_center(viewport_index)
        if x1 is None:
            x1 = center["x"] - center["width"] * 0.2
        if y1 is None:
            y1 = center["y"] - center["height"] * 0.1
        if x2 is None:
            x2 = center["x"] + center["width"] * 0.2
        if y2 is None:
            y2 = center["y"] + center["height"] * 0.1

        await self.page.mouse.click(x1, y1)
        await self.page.wait_for_timeout(300)
        await self.page.mouse.click(x2, y2)
        await self.page.wait_for_timeout(500)

    async def click_point_on_viewport(
        self, viewport_index: int = 0, x: float = None, y: float = None
    ) -> None:
        center = await self.get_viewport_center(viewport_index)
        if x is None:
            x = center["x"]
        if y is None:
            y = center["y"]
        await self.page.mouse.click(x, y)
        await self.page.wait_for_timeout(300)

    async def double_click_point_on_viewport(
        self, viewport_index: int = 0, x: float = None, y: float = None
    ) -> None:
        center = await self.get_viewport_center(viewport_index)
        if x is None:
            x = center["x"]
        if y is None:
            y = center["y"]
        await self.page.mouse.dblclick(x, y)
        await self.page.wait_for_timeout(500)

    async def drag_on_viewport(
        self, viewport_index: int = 0,
        x1: float = None, y1: float = None,
        x2: float = None, y2: float = None,
    ) -> None:
        center = await self.get_viewport_center(viewport_index)
        if x1 is None:
            x1 = center["x"] - center["width"] * 0.15
        if y1 is None:
            y1 = center["y"]
        if x2 is None:
            x2 = center["x"] + center["width"] * 0.15
        if y2 is None:
            y2 = center["y"]
        await self.page.mouse.move(x1, y1)
        await self.page.mouse.down()
        await self.page.mouse.move(x2, y2, steps=10)
        await self.page.mouse.up()
        await self.page.wait_for_timeout(500)

    async def close_circular_menu_by_clicking_outside(self) -> None:
        box = await self.page.locator(self.viewport_articles).nth(0).bounding_box()
        if not box:
            raise ValueError("Viewport not found for outside click")
        outside_x = box["x"] + 5
        outside_y = box["y"] + 5
        canvas_style = await self.page.add_style_tag(
            content="canvas { pointer-events: none !important; }"
        )
        try:
            await self.page.mouse.click(outside_x, outside_y)
        finally:
            await canvas_style.evaluate("element => element.remove()")
        await self.page.wait_for_timeout(300)

    async def scroll_up_on_viewport(self, viewport_index: int = 0) -> None:
        center = await self.get_viewport_center(viewport_index)
        await self.page.mouse.move(center["x"], center["y"])
        await self.page.mouse.wheel(0, -120)
        await self.page.wait_for_timeout(500)

    async def scroll_down_on_viewport(self, viewport_index: int = 0) -> None:
        center = await self.get_viewport_center(viewport_index)
        await self.page.mouse.move(center["x"], center["y"])
        await self.page.mouse.wheel(0, 120)
        await self.page.wait_for_timeout(500)

    async def get_annotations_on_viewport(self, viewport_index: int = 0) -> list[dict]:
        return await self.page.evaluate(
            """
            (viewportIndex) => {
                const svgs = document.querySelectorAll('.viewport-element svg');
                const svg = svgs[viewportIndex];
                if (!svg) return [];
                
                const annotations = [];
                const groups = svg.querySelectorAll('g[data-annotation-uid]');
                
                groups.forEach(g => {
                    const uid = g.getAttribute('data-annotation-uid');
                    const textEl = g.querySelector('text');
                    const text = textEl?.textContent?.trim() || null;
                    
                    const line = svg.querySelector(`line[data-id="${uid}-line"]`);
                    const lineData = line ? {
                        x1: parseFloat(line.getAttribute('x1')),
                        y1: parseFloat(line.getAttribute('y1')),
                        x2: parseFloat(line.getAttribute('x2')),
                        y2: parseFloat(line.getAttribute('y2'))
                    } : null;
                    
                    annotations.push({ uid, text, lineData });
                });
                
                return annotations;
            }
            """,
            viewport_index,
        )

    async def get_annotation_count(self, viewport_index: int = 0) -> int:
        return await self.page.evaluate(
            """
            (viewportIndex) => {
                const svgs = document.querySelectorAll('.viewport-element svg');
                const svg = svgs[viewportIndex];
                if (!svg) return 0;
                return svg.querySelectorAll('g[data-annotation-uid]').length;
            }
            """,
            viewport_index,
        )

    async def get_measurement_text(self, viewport_index: int = 0) -> str:
        return await self.page.evaluate(
            """
            (viewportIndex) => {
                const svgs = document.querySelectorAll('.viewport-element svg');
                const svg = svgs[viewportIndex];
                if (!svg) return null;
                const textEl = svg.querySelector('g[data-annotation-uid] text');
                return textEl?.textContent?.trim() || null;
            }
            """,
            viewport_index,
        )

    async def get_measurement_value_mm(self, viewport_index: int = 0) -> float | None:
        text = await self.get_measurement_text(viewport_index)
        if not text:
            return None
        import re
        match = re.search(r"([\d.]+)\s*mm", text)
        return float(match.group(1)) if match else None
