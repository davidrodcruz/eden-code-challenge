import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from utils.shared_actions import SharedActions

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


class BasePage(SharedActions):
    def __init__(self, page: Page):
        super().__init__(page)
        self.hook = MCPHook()

    def _record_action(
        self, action_type: str, target: Any, value: Any = None, **kwargs
    ) -> None:
        self.hook.record_action(
            action_type, str(target), value=value, **kwargs
        )

    async def screenshot(self, name: str) -> bytes:
        return await self.take_screenshot(path=name)
