import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)


class MCPHook:
    """Manages MCP hooks for recording user actions."""

    def __init__(self):
        self.actions: list[dict[str, Any]] = []
        self._output_dir = Path("results/mcp")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def record_action(self, action_type: str, target: str, value: Any = None, **kwargs) -> None:
        """Record an action to the hook log."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "target": target,
        }
        if value is not None:
            entry["value"] = value
        entry.update(kwargs)
        self.actions.append(entry)
        logger.debug(f"MCP Hook: {action_type} on {target}")

    def save_actions(self, session_id: str) -> Path:
        """Save recorded actions to a JSON file."""
        output_file = self._output_dir / f"actions_{session_id}.json"
        output_file.write_text(json.dumps(self.actions, indent=2))
        return output_file

    def clear(self) -> None:
        """Clear recorded actions."""
        self.actions.clear()


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.hook = MCPHook()

    async def navigate(self, url: str) -> None:
        self.hook.record_action("navigate", url)
        await self.page.goto(url)

    async def click(self, selector: str, timeout: int = 30000) -> None:
        self.hook.record_action("click", selector)
        await self.page.click(selector, timeout=timeout)

    async def fill(self, selector: str, value: str, timeout: int = 30000) -> None:
        self.hook.record_action("fill", selector, value=value)
        await self.page.fill(selector, value, timeout=timeout)

    async def wait_for(
        self, selector: str, state: str = "visible", timeout: int = 30000
    ) -> Locator:
        self.hook.record_action("wait_for", selector, state=state)
        locator = self.page.locator(selector)
        await locator.wait_for(state=state, timeout=timeout)
        return locator

    async def get_text(self, selector: str, timeout: int = 30000) -> str:
        self.hook.record_action("get_text", selector)
        locator = await self.wait_for(selector, timeout=timeout)
        return await locator.text_content() or ""

    async def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        self.hook.record_action("is_visible", selector)
        try:
            await self.page.wait_for_selector(
                selector, state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    async def screenshot(self, name: str) -> bytes:
        self.hook.record_action("screenshot", name)
        return await self.page.screenshot(name=name)

    async def get_url(self) -> str:
        return self.page.url

    async def get_attribute(
        self, selector: str, attribute: str, timeout: int = 30000
    ) -> Optional[str]:
        self.hook.record_action("get_attribute", selector, attribute=attribute)
        locator = await self.wait_for(selector, timeout=timeout)
        return await locator.get_attribute(attribute)

    async def select_option(self, selector: str, value: str) -> None:
        self.hook.record_action("select_option", selector, value=value)
        await self.page.select_option(selector, value)

    async def hover(self, selector: str) -> None:
        self.hook.record_action("hover", selector)
        await self.page.hover(selector)

    async def press_key(self, selector: str, key: str) -> None:
        self.hook.record_action("press_key", selector, key=key)
        await self.page.press(selector, key)
