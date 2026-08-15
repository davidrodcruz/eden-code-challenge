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


def init_progress_bar(context, feature) -> None:
    filter_tags = getattr(context.config, "tags", [])
    total = sum(1 for s in feature.scenarios if _matches_tags(s.tags, filter_tags)) if filter_tags else len(feature.scenarios)
    context.pbar = tqdm(total=total, desc="Executing scenarios", unit="scenario", disable=False) if total > 0 else None


def update_progress_bar(context, scenario_name: str) -> None:
    if hasattr(context, "pbar") and context.pbar:
        context.pbar.update(1)


def close_progress_bar(context) -> None:
    if hasattr(context, "pbar") and context.pbar:
        context.pbar.close()
        context.pbar = None
