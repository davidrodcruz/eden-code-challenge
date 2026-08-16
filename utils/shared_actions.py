from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from playwright.async_api import Locator, Page


PageTarget = str | Locator


class SharedActions:
    """Reusable Playwright actions for any page object or Behave step."""

    def __init__(self, page: Page):
        self.page = page

    def _record_action(
        self, action_type: str, target: Any, value: Any = None, **kwargs
    ) -> None:
        """Hook for BasePage's MCP action recorder."""

    @staticmethod
    def _target_name(target: PageTarget) -> str:
        return target if isinstance(target, str) else repr(target)

    def locator(self, target: PageTarget) -> Locator:
        return self.page.locator(target) if isinstance(target, str) else target

    async def navigate(
        self, url: str, wait_until: str = "domcontentloaded"
    ) -> None:
        self._record_action("navigate", url)
        await self.page.goto(url, wait_until=wait_until)

    async def click(
        self,
        target: PageTarget,
        *,
        button: str = "left",
        timeout: int = 30_000,
    ) -> None:
        target_name = self._target_name(target)
        self._record_action("click", target_name, button=button)
        await self.locator(target).click(button=button, timeout=timeout)

    async def right_click(self, target: PageTarget, timeout: int = 30_000) -> None:
        await self.click(target, button="right", timeout=timeout)

    async def fill(
        self, target: PageTarget, value: str, timeout: int = 30_000
    ) -> None:
        target_name = self._target_name(target)
        self._record_action("fill", target_name, value=value)
        await self.locator(target).fill(value, timeout=timeout)

    async def wait_for(
        self,
        target: PageTarget,
        state: str = "visible",
        timeout: int = 30_000,
    ) -> Locator:
        target_name = self._target_name(target)
        self._record_action("wait_for", target_name, state=state)
        locator = self.locator(target)
        if isinstance(target, str):
            await self.page.wait_for_selector(
                target, state=state, timeout=timeout
            )
        else:
            await locator.wait_for(state=state, timeout=timeout)
        return locator

    async def wait_for_function(
        self,
        expression: str,
        *,
        arg: Any = None,
        timeout: int = 30_000,
    ) -> None:
        self._record_action("wait_for_function", expression)
        if arg is None:
            await self.page.wait_for_function(expression, timeout=timeout)
        else:
            await self.page.wait_for_function(expression, arg=arg, timeout=timeout)

    async def wait_for_load_state(
        self, state: str = "load", timeout: int = 30_000
    ) -> None:
        self._record_action("wait_for_load_state", state)
        await self.page.wait_for_load_state(state, timeout=timeout)

    async def wait_for_timeout(self, milliseconds: float) -> None:
        self._record_action("wait_for_timeout", str(milliseconds))
        await self.page.wait_for_timeout(milliseconds)

    async def get_text(self, target: PageTarget, timeout: int = 30_000) -> str:
        locator = await self.wait_for(target, timeout=timeout)
        return await locator.text_content() or ""

    async def is_visible(self, target: PageTarget, timeout: int = 5_000) -> bool:
        try:
            await self.wait_for(target, state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    async def take_screenshot(
        self,
        *,
        path: str | None = None,
        full_page: bool = False,
    ) -> bytes:
        self._record_action("screenshot", path or "page", full_page=full_page)
        return await self.page.screenshot(path=path, full_page=full_page)

    async def get_url(self) -> str:
        return self.page.url

    async def get_attribute(
        self,
        target: PageTarget,
        attribute: str,
        timeout: int = 30_000,
    ) -> str | None:
        locator = await self.wait_for(target, timeout=timeout)
        return await locator.get_attribute(attribute)

    async def select_option(
        self, target: PageTarget, value: str, timeout: int = 30_000
    ) -> None:
        self._record_action("select_option", self._target_name(target), value=value)
        await self.locator(target).select_option(value, timeout=timeout)

    async def hover(self, target: PageTarget, timeout: int = 30_000) -> None:
        self._record_action("hover", self._target_name(target))
        await self.locator(target).hover(timeout=timeout)

    async def press_key(
        self, target: PageTarget, key: str, timeout: int = 30_000
    ) -> None:
        self._record_action("press_key", self._target_name(target), key=key)
        await self.locator(target).press(key, timeout=timeout)

    async def press_key_global(self, key: str) -> None:
        self._record_action("press_key", "keyboard", key=key)
        await self.page.keyboard.press(key)

    async def move_mouse(self, x: float, y: float) -> None:
        self._record_action("move_mouse", f"{x},{y}")
        await self.page.mouse.move(x, y)

    async def click_at(self, x: float, y: float) -> None:
        self._record_action("click_at", f"{x},{y}")
        await self.page.mouse.click(x, y)

    async def double_click_at(self, x: float, y: float) -> None:
        self._record_action("double_click_at", f"{x},{y}")
        await self.page.mouse.dblclick(x, y)

    async def drag(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        steps: int = 10,
    ) -> None:
        self._record_action("drag", f"{x1},{y1}->{x2},{y2}")
        await self.page.mouse.move(x1, y1)
        await self.page.mouse.down()
        try:
            await self.page.mouse.move(x2, y2, steps=steps)
        finally:
            await self.page.mouse.up()

    async def scroll(
        self,
        delta_y: float,
        *,
        x: float | None = None,
        y: float | None = None,
    ) -> None:
        self._record_action("scroll", f"{x},{y}", delta_y=delta_y)
        if x is not None and y is not None:
            await self.page.mouse.move(x, y)
        await self.page.mouse.wheel(0, delta_y)

    async def bounding_box(
        self, target: PageTarget, index: int | None = None
    ) -> dict[str, float]:
        locator = self.locator(target)
        if index is not None:
            locator = locator.nth(index)
        box = await locator.bounding_box()
        if not box:
            raise ValueError(f"Target not found or not visible: {self._target_name(target)}")
        return box

    async def center_of(
        self, target: PageTarget, index: int | None = None
    ) -> dict[str, float]:
        box = await self.bounding_box(target, index=index)
        return {
            "x": box["x"] + box["width"] / 2,
            "y": box["y"] + box["height"] / 2,
            "width": box["width"],
            "height": box["height"],
        }

    @asynccontextmanager
    async def canvas_pointer_events_disabled(self) -> AsyncIterator[None]:
        """Route coordinate events to the viewport container instead of canvas."""
        style = await self.page.add_style_tag(
            content="canvas { pointer-events: none !important; }"
        )
        try:
            yield
        finally:
            await style.evaluate("element => element.remove()")
