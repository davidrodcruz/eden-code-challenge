from tqdm import tqdm


def _normalize_tag(tag: str) -> str:
    """Remove @ prefix from tag if present."""
    return tag[1:] if tag.startswith("@") else tag


def _matches_tags(scenario_tags: list[str], filter_tags: list[str]) -> bool:
    """Check if scenario tags match the filter tags."""
    if not filter_tags:
        return True
    
    scenario_tags_normalized = [_normalize_tag(t) for t in scenario_tags]
    required_tags = [_normalize_tag(t) for t in filter_tags if not t.startswith("~")]
    excluded_tags = [_normalize_tag(t[1:]) if t.startswith("~") else _normalize_tag(t) for t in filter_tags if t.startswith("~")]
    
    for tag in excluded_tags:
        if tag in scenario_tags_normalized:
            return False
    
    if required_tags:
        return any(t in scenario_tags_normalized for t in required_tags)
    
    return True


def init_progress_bar(context, feature) -> None:
    """Initialize the progress bar with the count of scenarios that will run."""
    filter_tags = getattr(context.config, "tags", [])
    if filter_tags:
        total = sum(1 for s in feature.scenarios if _matches_tags(s.tags, filter_tags))
    else:
        total = len(feature.scenarios)

    if total > 0:
        context.pbar = tqdm(
            total=total,
            desc="Executing scenarios",
            unit="scenario",
            ncols=80,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        )
    else:
        context.pbar = None


def update_progress_bar(context, scenario_name: str) -> None:
    """Update the progress bar with the current scenario name."""
    if hasattr(context, "pbar") and context.pbar:
        context.pbar.set_description(f"Executing: {scenario_name[:50]}")
        context.pbar.update(1)


def close_progress_bar(context) -> None:
    """Close the progress bar safely."""
    if hasattr(context, "pbar") and context.pbar:
        context.pbar.close()
        context.pbar = None
