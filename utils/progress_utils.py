import sys
from tqdm import tqdm


def _normalize_tag(tag: str) -> str:
    return tag[1:] if tag.startswith("@") else tag


def _matches_tags(scenario_tags: list[str], filter_tags: list[str]) -> bool:
    if not filter_tags:
        return True
    scenario_tags_normalized = [_normalize_tag(t) for t in scenario_tags]
    required_tags = [_normalize_tag(t) for t in filter_tags if not t.startswith("~")]
    excluded_tags = [_normalize_tag(t[1:]) for t in filter_tags if t.startswith("~")]
    for tag in excluded_tags:
        if tag in scenario_tags_normalized:
            return False
    if required_tags:
        return any(t in scenario_tags_normalized for t in required_tags)
    return True


def _get_console_output():
    """Return a file object that writes directly to the terminal/console.

    Behave captures ``sys.stdout`` and ``sys.stderr`` by default, which hides
    ``tqdm`` progress bars. Opening the controlling console directly bypasses
    that capture so the bar is rendered live.

    Returns ``None`` when no controlling console is available (e.g. CI or a
    non-interactive container without a TTY), in which case the progress bar
    is disabled to avoid polluting the captured output.
    """
    if sys.platform == "win32":
        try:
            return open("CONOUT$", "w", encoding="utf-8")
        except OSError:
            return None
    try:
        return open("/dev/tty", "w", encoding="utf-8")
    except OSError:
        return None


def init_progress_bar(context, feature) -> None:
    filter_tags = getattr(context.config, "tags", [])
    total = sum(1 for s in feature.scenarios if _matches_tags(s.tags, filter_tags)) if filter_tags else len(feature.scenarios)
    if total <= 0:
        context.pbar = None
        return

    context._pbar_output = _get_console_output()
    context.pbar = tqdm(
        total=total,
        desc="Executing scenarios",
        unit="scenario",
        disable=(context._pbar_output is None),
        file=context._pbar_output or sys.stderr,
        dynamic_ncols=True,
        miniters=1,
    )


def update_progress_bar(context, scenario_name: str) -> None:
    if hasattr(context, "pbar") and context.pbar:
        context.pbar.update(1)


def close_progress_bar(context) -> None:
    if hasattr(context, "pbar") and context.pbar:
        context.pbar.close()
        context.pbar = None
    if hasattr(context, "_pbar_output") and context._pbar_output:
        try:
            context._pbar_output.close()
        except Exception:
            pass
        context._pbar_output = None
