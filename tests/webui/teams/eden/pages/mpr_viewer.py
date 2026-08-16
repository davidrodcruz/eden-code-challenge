from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from core.shared_actions import SharedActions


class MprViewerPage(SharedActions):
    def __init__(self, page: Page, config: dict):
        super().__init__(page)

        viewer = config["mpr_viewer"]
        selectors = viewer["selectors"]
        icons = viewer["icon_paths"]
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

        self.network_idle_timeout = timeouts["network_idle"]
        self.fallback_wait = timeouts["fallback_wait"]
        self.circular_menu_open_timeout = timeouts["circular_menu_open"]
        self.circular_menu_close_timeout = timeouts["circular_menu_close"]
        self.tool_activate_timeout = timeouts["tool_activate"]

    async def navigate(self) -> None:
        await super().navigate(self.url, wait_until="domcontentloaded")

    async def wait_until_loaded(self) -> None:
        await self.wait_for(self.viewport_articles)
        try:
            await self.wait_for_load_state(
                "networkidle", timeout=self.network_idle_timeout
            )
        except PlaywrightTimeoutError:
            await self.wait_for_timeout(self.fallback_wait)
        await self.wait_for_function(
            """
            () => Boolean(
                window.__E2E_TEST_BRIDGE__?.status?.().toolsAvailable
            )
            """,
            timeout=self.tool_activate_timeout,
        )

    async def screenshot(self) -> bytes:
        return await self.take_screenshot(full_page=True)

    async def open_circular_menu_on_viewport(self, viewport_index: int = 0) -> None:
        articles = self.locator(self.viewport_articles)
        article = articles.nth(viewport_index)
        await self.right_click(article)
        await self.wait_for(
            self.circular_menu_opened,
            state="visible",
            timeout=self.circular_menu_open_timeout,
        )

    async def is_circular_menu_visible(self) -> bool:
        return await self.is_visible(self.circular_menu_opened)

    async def get_circular_menu_items(self) -> list[Locator]:
        return self.locator(self.circular_menu_item)

    async def get_circular_menu_item_count(self) -> int:
        return await self.locator(self.circular_menu_item).count()

    async def click_circular_menu_item(self, item_index: int) -> None:
        items = self.locator(self.circular_menu_item)
        await self.click(items.nth(item_index))

    async def click_circular_menu_item_by_svg_path(self, path_start: str) -> None:
        item = self.locator(
            f"{self.circular_menu_item} svg path[d^='{path_start}']"
        ).locator("..")
        await self.click(item)

    async def close_circular_menu(self) -> None:
        await self.press_key_global("Escape")
        await self.wait_for(
            self.circular_menu_opened,
            state="hidden",
            timeout=self.circular_menu_close_timeout,
        )

    async def activate_measurement_tool(self) -> bytes:
        await self.open_circular_menu_on_viewport(0)
        await self.wait_for_timeout(500)
        highlight_screenshot = await self._click_circular_menu_tool(self.ruler_icon)
        await self.wait_for_function(
            "selector => document.querySelector(selector) !== null",
            arg=self.active_tool_tab,
            timeout=self.tool_activate_timeout,
        )
        await self.wait_for(
            self.longitud_button,
            state="visible",
            timeout=self.tool_activate_timeout,
        )
        await self._wait_for_active_tool("Length")
        return highlight_screenshot

    async def activate_pan_tool(self) -> None:
        await self.open_circular_menu_on_viewport(0)
        await self.wait_for_timeout(500)
        await self._click_circular_menu_tool(self.pan_icon)
        await self._wait_for_active_tool("Pan")

    async def activate_zoom_tool(self) -> None:
        await self.open_circular_menu_on_viewport(0)
        await self.wait_for_timeout(500)
        await self._click_circular_menu_tool(self.zoom_icon)
        await self._wait_for_active_tool("Zoom")

    async def clear_annotations(self, viewport_index: int = 0) -> None:
        await self._bridge_call(
            "clearAnnotations", {"viewportId": str(viewport_index)}
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

        async with self.canvas_pointer_events_disabled():
            await self.move_mouse(position["x"], position["y"])
            await self.wait_for_timeout(300)
            highlight_screenshot = await self.take_screenshot(full_page=True)
            await self.click_at(position["x"], position["y"])

        await self.wait_for(
            self.circular_menu_opened,
            state="hidden",
            timeout=5000,
        )
        return highlight_screenshot

    async def get_viewport_center(self, viewport_index: int = 0) -> dict:
        return await self.center_of(self.viewport_articles, index=viewport_index)

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

        async with self.canvas_pointer_events_disabled():
            await self.click_at(x1, y1)
            await self.wait_for_timeout(300)
            await self.click_at(x2, y2)
            await self.wait_for_timeout(500)

    async def click_point_on_viewport(
        self, viewport_index: int = 0, x: float = None, y: float = None
    ) -> None:
        center = await self.get_viewport_center(viewport_index)
        if x is None:
            x = center["x"]
        if y is None:
            y = center["y"]
        async with self.canvas_pointer_events_disabled():
            await self.click_at(x, y)
            await self.wait_for_timeout(300)

    async def double_click_point_on_viewport(
        self, viewport_index: int = 0, x: float = None, y: float = None
    ) -> None:
        center = await self.get_viewport_center(viewport_index)
        if x is None:
            x = center["x"]
        if y is None:
            y = center["y"]
        async with self.canvas_pointer_events_disabled():
            await self.double_click_at(x, y)
            await self.wait_for_timeout(500)

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
        async with self.canvas_pointer_events_disabled():
            await self.drag(x1, y1, x2, y2, steps=10)
            await self.wait_for_timeout(500)

    async def close_circular_menu_by_clicking_outside(self) -> None:
        box = await self.bounding_box(self.viewport_articles, index=0)
        outside_x = box["x"] + 5
        outside_y = box["y"] + 5
        async with self.canvas_pointer_events_disabled():
            await self.click_at(outside_x, outside_y)
        await self.wait_for_timeout(300)

    async def scroll_up_on_viewport(self, viewport_index: int = 0) -> None:
        center = await self.get_viewport_center(viewport_index)
        async with self.canvas_pointer_events_disabled():
            await self.scroll(-120, x=center["x"], y=center["y"])
            await self.wait_for_timeout(500)

    async def scroll_down_on_viewport(self, viewport_index: int = 0) -> None:
        center = await self.get_viewport_center(viewport_index)
        async with self.canvas_pointer_events_disabled():
            await self.scroll(120, x=center["x"], y=center["y"])
            await self.wait_for_timeout(500)

    async def get_annotations_on_viewport(self, viewport_index: int = 0) -> list[dict]:
        result = await self._bridge_call(
            "getAnnotations", {"viewportId": str(viewport_index)}
        )
        return result["annotations"]

    async def get_annotation_count(self, viewport_index: int = 0) -> int:
        result = await self._bridge_call(
            "getAnnotations", {"viewportId": str(viewport_index)}
        )
        return result["count"]

    async def get_measurement(self, viewport_index: int = 0) -> dict | None:
        annotations = await self.get_annotations_on_viewport(viewport_index)
        return annotations[0]["measurement"] if annotations else None

    async def get_measurement_unit(self, viewport_index: int = 0) -> str | None:
        measurement = await self.get_measurement(viewport_index)
        return measurement["unit"] if measurement else None

    async def get_measurement_value_mm(self, viewport_index: int = 0) -> float | None:
        measurement = await self.get_measurement(viewport_index)
        if not measurement or measurement["unit"] != "mm":
            return None
        return measurement["value"]

    async def _wait_for_active_tool(self, tool_name: str) -> None:
        await self.wait_for_function(
            """
            toolName => window.__E2E_TEST_BRIDGE__
                ?.getActiveTools?.()
                ?.groups
                ?.some(group => group.currentActiveTool === toolName)
            """,
            arg=tool_name,
            timeout=self.tool_activate_timeout,
        )

    async def _bridge_call(self, method: str, argument=None):
        return await self.page.evaluate(
            """
            ({ method, argument }) => {
                const bridge = window.__E2E_TEST_BRIDGE__;
                if (!bridge || typeof bridge[method] !== 'function') {
                    throw new Error(`Missing Cornerstone bridge method: ${method}`);
                }
                return bridge[method](argument);
            }
            """,
            {"method": method, "argument": argument},
        )
