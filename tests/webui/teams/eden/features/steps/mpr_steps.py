import json

from allure import attach
from allure_commons.types import AttachmentType
from behave import step

from handlers.cornerstone_test_bridge import (
    assert_annotation_persisted,
    assert_measurement_geometry,
)
from core.drivers.playwright_driver import BrowserManager
from pages.mpr_viewer import MprViewerPage


def _attach_json(name: str, value) -> None:
    attach(
        json.dumps(value, indent=2, sort_keys=True),
        name=name,
        attachment_type=AttachmentType.JSON,
    )


def _baseline(context) -> dict:
    baseline = context.shared_data.get("measurement_baseline")
    if not baseline:
        raise AssertionError("No measurement baseline was captured")
    return baseline


async def _capture_measurement_baseline(context, viewport_index: int) -> None:
    annotations = await context.mpr_page.get_annotations_on_viewport(viewport_index)
    viewport_state = await context.mpr_page.get_viewport_state(viewport_index)
    current = {
        "viewport_index": viewport_index,
        "annotations": annotations,
        "viewport": viewport_state,
    }
    context.shared_data["last_annotations"] = current
    context.shared_data.setdefault("measurement_baseline", current)


@step("the user navigates to the MPR viewer")
async def step_navigate_mpr(context):
    await BrowserManager.ensure_page(context)
    context.mpr_page = MprViewerPage(context.page, context.team_config)
    await context.mpr_page.navigate()


@step("the MPR viewer has finished loading")
async def step_wait_for_mpr(context):
    await context.mpr_page.wait_until_loaded()
    await context.mpr_page.clear_all_annotations()
    attach(
        "MPR viewer finished loading",
        name="Step Info",
        attachment_type=AttachmentType.TEXT,
    )


@step("take a screenshot of the page")
async def step_take_screenshot(context):
    screenshot = await context.mpr_page.screenshot()
    attach(screenshot, name="MPR Viewer Screenshot", attachment_type=AttachmentType.PNG)


@step("the measurement tool is active")
@step("the user activates the measurement tool")
@step("the user activates the measurement tool from the circular menu")
async def step_activate_measurement(context):
    highlight_screenshot = await context.mpr_page.activate_measurement_tool()
    attach(
        highlight_screenshot,
        name="Measurement tool activation",
        attachment_type=AttachmentType.PNG,
    )


@step("the pan tool is active")
@step("the user activates the pan tool from the circular menu")
async def step_activate_pan(context):
    await context.mpr_page.activate_pan_tool()
    context.shared_data["persistence_tolerance"] = 0.0


@step("the user activates the zoom tool from the circular menu")
async def step_activate_zoom(context):
    await context.mpr_page.activate_zoom_tool()
    context.shared_data["persistence_tolerance"] = 0.1


@step("the user draws a line on viewport {index:d}")
async def step_draw_line(context, index):
    await context.mpr_page.draw_line_on_viewport(index)
    await _capture_measurement_baseline(context, index)
    attach(f"Measurement created on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user draws a second line on viewport {index:d}")
async def step_draw_second_line(context, index):
    center = await context.mpr_page.get_viewport_center(index)
    x1 = center["x"] + center["width"] * 0.05
    y1 = center["y"] + center["height"] * 0.15
    x2 = center["x"] + center["width"] * 0.25
    y2 = center["y"] + center["height"] * 0.25
    await context.mpr_page.draw_line_on_viewport(index, x1, y1, x2, y2)
    await _capture_measurement_baseline(context, index)


@step("the user double-clicks on viewport {index:d}")
async def step_double_click_on_viewport(context, index):
    await context.mpr_page.double_click_point_on_viewport(index)


@step("the user drags on viewport {index:d}")
async def step_drag_on_viewport(context, index):
    await context.mpr_page.drag_on_viewport(index)


@step("the user scrolls up on viewport {index:d}")
async def step_scroll_up_on_viewport(context, index):
    await context.mpr_page.scroll_up_on_viewport(index)


@step("the user scrolls down on viewport {index:d}")
async def step_scroll_down_on_viewport(context, index):
    await context.mpr_page.scroll_down_on_viewport(index)


@step("the user opens the circular menu on viewport {index:d}")
async def step_open_circular_menu(context, index):
    await context.mpr_page.open_circular_menu_on_viewport(index)


@step("the circular menu should be visible")
async def step_verify_circular_menu_visible(context):
    assert await context.mpr_page.is_circular_menu_visible()


@step("the user closes the circular menu by clicking outside")
async def step_close_menu_outside(context):
    await context.mpr_page.close_circular_menu_by_clicking_outside()


@step("the circular menu should not be visible")
async def step_verify_menu_not_visible(context):
    assert not await context.mpr_page.is_circular_menu_visible()


@step("the measurement state should record accurate physical dimensions in {unit}")
async def step_verify_measurement_geometry(context, unit):
    baseline = _baseline(context)
    annotations = await context.mpr_page.get_annotations_on_viewport(
        baseline["viewport_index"]
    )
    assert len(annotations) == 1, f"Expected one annotation, found {len(annotations)}"
    annotation = annotations[0]
    assert annotation["measurement"]["unit"] == unit
    assert annotation["measurement"]["value"] > 0.01
    assert_measurement_geometry(annotation, tolerance=0.01)
    _attach_json("Measurement model", annotation)


@step("viewport {index:d} should have {count:d} active annotation")
@step("viewport {index:d} should have {count:d} active annotations")
async def step_verify_active_annotation_count(context, index, count):
    await context.mpr_page.wait_for_annotation_count(index, count)
    actual = await context.mpr_page.get_annotation_count(index)
    assert actual == count, f"Expected {count} active annotations, found {actual}"


@step("viewport {index:d} should have {count:d} annotations registered in the state")
@step("viewport {index:d} should have {count:d} annotation registered in the state")
async def step_verify_registered_annotation_count(context, index, count):
    await context.mpr_page.wait_for_annotation_count(index, count)
    actual = await context.mpr_page.get_annotation_count(index)
    assert actual == count, f"Expected {count} registered annotations, found {actual}"


@step("viewport {index:d} should have {count:d} visible annotations")
async def step_verify_visible_annotation_count(context, index, count):
    await context.mpr_page.wait_for_annotation_count(index, count, visible=True)
    actual = await context.mpr_page.get_visible_annotation_count(index)
    assert actual == count, f"Expected {count} visible annotations, found {actual}"


@step("each measurement must have a unique state UID")
async def step_verify_unique_annotation_uids(context):
    viewport_index = _baseline(context)["viewport_index"]
    annotations = await context.mpr_page.get_annotations_on_viewport(viewport_index)
    uids = [annotation.get("uid") for annotation in annotations]
    assert len(uids) == len(set(uids)), f"Duplicate annotation UIDs found: {uids}"
    assert all(uids), f"Missing annotation UID: {uids}"


@step("the exact measurement spatial data must persist without degradation")
async def step_verify_measurement_persistence(context):
    baseline = _baseline(context)
    after = await context.mpr_page.get_annotations_on_viewport(
        baseline["viewport_index"]
    )
    tolerance = context.shared_data.get("persistence_tolerance", 0.1)
    assert_annotation_persisted(
        {"annotations": baseline["annotations"]},
        {"annotations": after},
        tolerance=tolerance,
    )


@step("the viewport {index:d} measurement slice is captured")
async def step_capture_measurement_slice(context, index):
    state = await context.mpr_page.get_viewport_state(index)
    context.shared_data["measurement_slice"] = state["sliceIndex"]


@step("the viewport slice should have changed")
async def step_verify_slice_changed(context):
    index = _baseline(context)["viewport_index"]
    state = await context.mpr_page.get_viewport_state(index)
    expected = context.shared_data["measurement_slice"]
    assert state["sliceIndex"] != expected, "Slice index did not change"


@step("the viewport slice should return to the measurement slice")
async def step_verify_slice_returned(context):
    index = _baseline(context)["viewport_index"]
    state = await context.mpr_page.get_viewport_state(index)
    expected = context.shared_data["measurement_slice"]
    assert state["sliceIndex"] == expected, "Viewport did not return to original slice"


@step("the user drags the endpoint of the existing measurement")
async def step_drag_measurement_endpoint(context):
    baseline = _baseline(context)
    annotation = baseline["annotations"][0]
    context.shared_data["edited_uid"] = annotation["uid"]
    context.shared_data["edited_previous_value"] = annotation["measurement"]["value"]
    await context.mpr_page.drag_annotation_endpoint(
        baseline["viewport_index"], annotation["uid"]
    )


@step("the measurement length state should dynamically update")
async def step_verify_measurement_updated(context):
    baseline = _baseline(context)
    uid = context.shared_data["edited_uid"]
    previous_value = context.shared_data["edited_previous_value"]
    await context.mpr_page.wait_for_measurement_value_change(
        uid,
        previous_value,
        baseline["viewport_index"],
    )
    updated = await context.mpr_page.get_annotation_by_uid(
        uid, baseline["viewport_index"]
    )
    assert updated["uid"] == uid
    assert updated["measurement"]["value"] > 0
    assert updated["points"] != baseline["annotations"][0]["points"]
    assert abs(updated["measurement"]["value"] - previous_value) > 0.01
    _attach_json("Updated measurement model", updated)


@step("the user selects the measurement and presses Delete")
async def step_delete_measurement(context):
    baseline = _baseline(context)
    uid = baseline["annotations"][0]["uid"]
    await context.mpr_page.select_annotation(baseline["viewport_index"], uid)
    await context.mpr_page.delete_selected_annotation()
    await context.mpr_page.wait_for_annotation_count(
        baseline["viewport_index"], 0
    )


@step("the browser is closed and the video is saved")
async def step_close_and_save_video(context):
    await BrowserManager.close(context)
