from behave import step
from allure import attach
from allure_commons.types import AttachmentType
from pages.mpr_viewer import MprViewerPage
from core.drivers.playwright_driver import BrowserManager


@step("the user navigates to the MPR viewer")
async def step_navigate_mpr(context):
    await BrowserManager.ensure_page(context)
    context.mpr_page = MprViewerPage(context.page, context.team_config)
    await context.mpr_page.navigate()


@step("the MPR viewer has finished loading")
async def step_wait_for_mpr(context):
    await context.mpr_page.wait_until_loaded()
    attach("MPR viewer finished loading", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("take a screenshot of the page")
async def step_take_screenshot(context):
    screenshot = await context.mpr_page.screenshot()
    attach(screenshot, name="MPR Viewer Screenshot", attachment_type=AttachmentType.PNG)


@step("the user opens the circular menu on viewport {index:d}")
async def step_open_circular_menu(context, index):
    await context.mpr_page.open_circular_menu_on_viewport(index)
    attach(f"Opened circular menu on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the circular menu should be visible")
async def step_verify_circular_menu_visible(context):
    is_visible = await context.mpr_page.is_circular_menu_visible()
    attach(f"Menu visible: {is_visible}", name="Response", attachment_type=AttachmentType.TEXT)
    assert is_visible, "Circular menu is not visible"


@step("the circular menu should have {count:d} items")
async def step_verify_circular_menu_items(context, count):
    actual = await context.mpr_page.get_circular_menu_item_count()
    attach(f"Expected: {count}, Actual: {actual}", name="Response", attachment_type=AttachmentType.TEXT)
    assert actual == count, f"Expected {count} items, found {actual}"


@step("the user activates the measurement tool")
async def step_activate_measurement(context):
    highlight_screenshot = await context.mpr_page.activate_measurement_tool()
    attach(
        highlight_screenshot,
        name="Longitud highlighted in circular menu",
        attachment_type=AttachmentType.PNG,
    )
    attach("Measurement tool activated", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user draws a line on viewport {index:d}")
async def step_draw_line(context, index):
    await context.mpr_page.draw_line_on_viewport(index)
    attach(f"Line drawn on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("viewport {index:d} should have {count:d} annotation")
@step("viewport {index:d} should have {count:d} annotations")
async def step_verify_annotation_count(context, index, count):
    actual = await context.mpr_page.get_annotation_count(index)
    attach(f"Expected: {count}, Actual: {actual}", name="Response", attachment_type=AttachmentType.TEXT)
    assert actual == count, f"Expected {count} annotations, found {actual}"


@step('the measurement unit should be "{expected}"')
async def step_verify_measurement_unit(context, expected):
    unit = await context.mpr_page.get_measurement_unit(0)
    attach(f"Measurement unit: {unit}", name="Response", attachment_type=AttachmentType.TEXT)
    assert unit == expected, f"Expected unit '{expected}', got '{unit}'"


@step("the measurement value should be a positive number")
async def step_verify_measurement_value(context):
    value = await context.mpr_page.get_measurement_value_mm(0)
    attach(f"Measurement value: {value}", name="Response", attachment_type=AttachmentType.TEXT)
    assert value is not None, "No measurement value found"
    assert value > 0, f"Measurement value should be positive, got {value}"


@step("the user activates the pan tool from the circular menu")
async def step_activate_pan(context):
    await context.mpr_page.activate_pan_tool()
    attach("Pan tool activated", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user activates the zoom tool from the circular menu")
async def step_activate_zoom(context):
    await context.mpr_page.activate_zoom_tool()
    attach("Zoom tool activated", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user drags on viewport {index:d}")
async def step_drag_on_viewport(context, index):
    await context.mpr_page.drag_on_viewport(index)
    attach(f"Dragged on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user scrolls up on viewport {index:d}")
async def step_scroll_up_on_viewport(context, index):
    await context.mpr_page.scroll_up_on_viewport(index)
    attach(f"Scrolled up on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user scrolls down on viewport {index:d}")
async def step_scroll_down_on_viewport(context, index):
    await context.mpr_page.scroll_down_on_viewport(index)
    attach(f"Scrolled down on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user draws a line at coordinates on viewport {index:d}")
async def step_draw_line_at_coords(context, index):
    await context.mpr_page.draw_line_on_viewport(index)
    attach(f"Line drawn at coordinates on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user draws a second line on viewport {index:d}")
async def step_draw_second_line(context, index):
    center = await context.mpr_page.get_viewport_center(index)
    x1 = center["x"] + center["width"] * 0.05
    y1 = center["y"] + center["height"] * 0.15
    x2 = center["x"] + center["width"] * 0.25
    y2 = center["y"] + center["height"] * 0.25
    await context.mpr_page.draw_line_on_viewport(index, x1, y1, x2, y2)
    attach(f"Second line drawn on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user double-clicks on viewport {index:d}")
async def step_double_click_on_viewport(context, index):
    await context.mpr_page.double_click_point_on_viewport(index)
    attach(f"Double-clicked on viewport {index}", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the user closes the circular menu by clicking outside")
async def step_close_menu_outside(context):
    await context.mpr_page.close_circular_menu_by_clicking_outside()
    attach("Circular menu closed by clicking outside", name="Step Info", attachment_type=AttachmentType.TEXT)


@step("the circular menu should not be visible")
async def step_verify_menu_not_visible(context):
    is_visible = await context.mpr_page.is_circular_menu_visible()
    attach(f"Menu visible: {is_visible}", name="Response", attachment_type=AttachmentType.TEXT)
    assert not is_visible, "Circular menu should not be visible but it is"


@step("the browser is closed and the video is saved")
async def step_close_and_save_video(context):
    await BrowserManager.close(context)
    attach("Browser closed, video will be attached to report", name="Step Info", attachment_type=AttachmentType.TEXT)
