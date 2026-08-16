import atexit
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from handlers.cornerstone_test_bridge import BRIDGE_SCRIPT_PATH


class PlaywrightDriver:
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def create_context(self) -> BrowserContext:
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")
        return await self._browser.new_context()

    async def create_page(self, context: Optional[BrowserContext] = None) -> Page:
        if context:
            return await context.new_page()
        ctx = await self.create_context()
        return await ctx.new_page()


class BrowserManager:
    """Browser singleton for reusing browser across Behave scenarios."""

    _VIDEO_DIR = Path("results/videos").resolve()
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None

    @classmethod
    async def ensure_page(cls, context) -> None:
        if cls._browser is not None and cls._page is not None:
            context.page = cls._page
            return

        team_config = getattr(context, "team_config", {}) or {}
        browser_name = team_config.get("browser", "chromium")

        if "headless" in context.config.userdata:
            headless = str(context.config.userdata["headless"]).lower() == "true"
        else:
            headless = bool(team_config.get("headless", False))

        viewport = {"width": 1280, "height": 720}

        cls._VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        cls._playwright = await async_playwright().start()
        cls._browser = await cls._launch(browser_name, headless)
        context_options = {
            "viewport": viewport,
            "record_video_dir": str(cls._VIDEO_DIR),
            "record_video_size": viewport,
        }
        locale = team_config.get("locale")
        if locale:
            context_options["locale"] = locale
        cls._context = await cls._browser.new_context(**context_options)
        await cls._context.add_init_script(path=str(BRIDGE_SCRIPT_PATH))
        cls._context.set_default_timeout(int(team_config.get("timeout", 30000)))
        cls._page = await cls._context.new_page()
        context.page = cls._page
        atexit.register(cls._cleanup_sync)

    @classmethod
    async def _launch(cls, browser_name: str, headless: bool) -> Browser:
        browser_types = {
            "chromium": cls._playwright.chromium,
            "firefox": cls._playwright.firefox,
            "webkit": cls._playwright.webkit,
        }
        browser_type = browser_types.get(browser_name)
        if browser_type is None:
            raise ValueError(f"Unsupported browser: {browser_name}")
        args = [
            "--use-gl=swiftshader",
            "--enable-webgl",
            "--disable-gpu-sandbox",
        ] if headless else []
        return await browser_type.launch(headless=headless, args=args)

    @classmethod
    def _cleanup_sync(cls) -> None:
        import asyncio

        if cls._page is None:
            return

        async def _close():
            if cls._page:
                await cls._page.close()
            if cls._context:
                await cls._context.close()
            if cls._browser:
                await cls._browser.close()
            if cls._playwright:
                await cls._playwright.stop()
            cls._playwright = None
            cls._browser = None
            cls._context = None
            cls._page = None

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_close())
            else:
                loop.run_until_complete(_close())
        except RuntimeError:
            asyncio.run(_close())

    @classmethod
    async def close(cls, context) -> None:
        if cls._page:
            await cls._page.close()
        if cls._context:
            await cls._context.close()
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()

        cls._playwright = None
        cls._browser = None
        cls._context = None
        cls._page = None
        context.page = None
