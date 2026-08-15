import asyncio
import sys
from pathlib import Path

import allure
from allure_commons.types import AttachmentType

from core.config import config
from core.progress_utils import init_progress_bar, update_progress_bar, close_progress_bar

_TEAM_DIR = Path(__file__).resolve().parent.parent
TEAM = _TEAM_DIR.name
if str(_TEAM_DIR) not in sys.path:
    sys.path.insert(0, str(_TEAM_DIR))


def before_all(context):
    context.shared_data = {}
    context.team = TEAM
    context.team_config = config.get_team_config(TEAM)
    context.pbar = None


def before_feature(context, feature):
    """Initialize progress bar with the total number of scenarios in this feature."""
    init_progress_bar(context, feature)


def before_scenario(context, scenario):
    context.shared_data = {}


def after_step(context, step):
    if not hasattr(context, "page") or not context.page:
        return

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_take_screenshot(context, step))
        else:
            loop.run_until_complete(_take_screenshot(context, step))
    except RuntimeError:
        asyncio.run(_take_screenshot(context, step))


async def _take_screenshot(context, step):
    try:
        screenshot = await context.page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=f"{step.keyword} {step.name}",
            attachment_type=AttachmentType.PNG,
        )
    except Exception:
        pass


def after_scenario(context, scenario):
    update_progress_bar(context, scenario.name)
    context.shared_data = {}


def after_all(context):
    close_progress_bar(context)
