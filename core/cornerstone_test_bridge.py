from __future__ import annotations

import json
from math import dist
from pathlib import Path
from typing import Any, Sequence

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError


BRIDGE_SCRIPT_PATH = Path(__file__).with_name("cornerstone_test_bridge.js")


class CornerstoneBridgeError(RuntimeError):
    """Raised when the Cornerstone model bridge is not available or invalid."""


class CornerstoneTestBridge:
    """Read CornerstoneTools state without coupling tests to rendered overlays."""

    def __init__(self, page: Page, timeout_ms: int = 30_000):
        self.page = page
        self.timeout_ms = timeout_ms

    @staticmethod
    def install_on_context(context: BrowserContext) -> None:
        """Install before the first navigation so webpack initialization is observable."""
        context.add_init_script(path=str(BRIDGE_SCRIPT_PATH))

    def install(self) -> None:
        """Install for this page; call before navigating to the viewer."""
        self.page.add_init_script(path=str(BRIDGE_SCRIPT_PATH))

    def wait_until_ready(self, timeout_ms: int | None = None) -> None:
        timeout = timeout_ms if timeout_ms is not None else self.timeout_ms
        try:
            self.page.wait_for_function(
                """
                () => Boolean(
                    window.__E2E_TEST_BRIDGE__?.status?.().toolsAvailable
                )
                """,
                timeout=timeout,
            )
        except PlaywrightTimeoutError as error:
            raise CornerstoneBridgeError(
                f"Cornerstone test bridge was not ready after {timeout} ms"
            ) from error

    def status(self) -> dict[str, Any]:
        return self._call("status")

    def get_annotations(
        self,
        *,
        viewport_id: int | str | None = None,
        tool_name: str | None = None,
    ) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if viewport_id is not None:
            options["viewportId"] = str(viewport_id)
        if tool_name is not None:
            options["toolName"] = tool_name
        return self._call("getAnnotations", options)

    def get_annotation_count(
        self,
        *,
        viewport_id: int | str | None = None,
        tool_name: str | None = None,
    ) -> int:
        return int(
            self.get_annotations(
                viewport_id=viewport_id,
                tool_name=tool_name,
            )["count"]
        )

    def get_viewport_state(self, viewport_id: int | str) -> dict[str, Any] | None:
        return self._call("getViewportState", str(viewport_id))

    def get_active_tools(self) -> dict[str, Any]:
        return self._call("getActiveTools")

    def snapshot(self, viewport_ids: Sequence[int | str] | None = None) -> dict[str, Any]:
        options = None
        if viewport_ids is not None:
            options = {"viewportIds": [str(viewport_id) for viewport_id in viewport_ids]}
        return self._call("getState", options)

    def clear_annotations(
        self, *, viewport_id: int | str | None = None
    ) -> dict[str, Any]:
        argument = None
        if viewport_id is not None:
            argument = {"viewportId": str(viewport_id)}
        return self._call("clearAnnotations", argument)

    def _call(self, method: str, argument: Any = None) -> Any:
        result = self.page.evaluate(
            """
            ({ method, argument }) => {
                const bridge = window.__E2E_TEST_BRIDGE__;
                if (!bridge || typeof bridge[method] !== "function") {
                    throw new Error(`Missing Cornerstone bridge method: ${method}`);
                }
                return bridge[method](argument);
            }
            """,
            {"method": method, "argument": argument},
        )
        return _json_value(result)


def assert_vector_close(
    actual: Sequence[float],
    expected: Sequence[float],
    *,
    tolerance: float = 1e-3,
    label: str = "vector",
) -> None:
    """Compare world-space vectors without image, canvas, or text assertions."""
    if len(actual) != len(expected):
        raise AssertionError(
            f"{label} dimensions differ: {len(actual)} != {len(expected)}"
        )
    if dist(actual, expected) > tolerance:
        raise AssertionError(
            f"{label} differs by more than {tolerance}: "
            f"actual={list(actual)}, expected={list(expected)}"
        )


def assert_annotation_points_close(
    actual_annotation: dict[str, Any],
    expected_points: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-3,
) -> None:
    actual_points = actual_annotation.get("points", [])
    if len(actual_points) != len(expected_points):
        raise AssertionError(
            f"annotation point count differs: {len(actual_points)} != "
            f"{len(expected_points)}"
        )
    for index, (actual, expected) in enumerate(zip(actual_points, expected_points)):
        assert_vector_close(
            actual,
            expected,
            tolerance=tolerance,
            label=f"annotation point {index}",
        )


def assert_annotation_persisted(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    tolerance: float = 1e-3,
) -> None:
    """Assert UID and world points survive navigation to another slice."""
    before_annotations = before.get("annotations", [])
    after_by_uid = {
        annotation.get("uid"): annotation
        for annotation in after.get("annotations", [])
    }
    if not before_annotations:
        raise AssertionError("No annotation existed before slice navigation")

    for annotation in before_annotations:
        uid = annotation.get("uid")
        persisted = after_by_uid.get(uid)
        if persisted is None:
            raise AssertionError(f"Annotation UID was not persisted: {uid}")
        assert_annotation_points_close(
            persisted,
            annotation.get("points", []),
            tolerance=tolerance,
        )


def _json_value(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise CornerstoneBridgeError(
            "Cornerstone bridge returned a non-JSON value"
        ) from error
