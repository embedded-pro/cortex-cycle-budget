"""Config schema validation — public ``validate_config()`` API."""

from __future__ import annotations

import re
from typing import Any

from cortex_cycle_budget.models import ConfigError
from cortex_cycle_budget.timing_model import SUPPORTED_VARIANTS


def validate_config(config: dict[str, Any]) -> None:
    """Validate required config fields and value ranges.

    Raises:
        ConfigError: with a multi-line message listing every problem.
    """
    errors: list[str] = []

    if "path_stages" not in config:
        errors.append("Missing required field 'path_stages'")
    else:
        stages = config["path_stages"]
        if not isinstance(stages, list) or len(stages) == 0:
            errors.append("'path_stages' must be a non-empty list")
        else:
            for i, stage in enumerate(stages):
                _validate_stage(i, stage, errors)

    if "loop_rates_khz" in config:
        rates = config["loop_rates_khz"]
        if not isinstance(rates, list):
            errors.append("'loop_rates_khz' must be a list of positive numbers")
        else:
            for rate in rates:
                if not isinstance(rate, (int, float)) or isinstance(rate, bool) or rate <= 0:
                    errors.append(f"'loop_rates_khz' contains invalid rate: {rate!r}")

    if "cortex" in config:
        cortex = config["cortex"]
        if cortex not in SUPPORTED_VARIANTS:
            valid = ", ".join(sorted(SUPPORTED_VARIANTS))
            errors.append(f"'cortex' = {cortex!r} is not supported. Valid: {valid}")

    bounds = config.get("loop_bounds", {})
    if not isinstance(bounds, dict):
        errors.append("'loop_bounds' must map function-name regexes to iteration counts")
    else:
        for pattern, iterations in bounds.items():
            _validate_regex(pattern, f"'loop_bounds' key '{pattern}'", errors)
            per_loop = iterations if isinstance(iterations, list) else [iterations]
            if not per_loop or not all(_positive_integer(n) for n in per_loop):
                errors.append(
                    f"'loop_bounds' ['{pattern}'] must be a positive integer, "
                    f"or a list of them with one per loop, got {iterations!r}"
                )

    cold = config.get("cold_calls", [])
    if not isinstance(cold, list) or not all(isinstance(p, str) for p in cold):
        errors.append("'cold_calls' must be a list of function-name regexes")
    else:
        for pattern in cold:
            _validate_regex(pattern, f"'cold_calls' entry '{pattern}'", errors)

    if "clock_mhz" in config:
        clk = config["clock_mhz"]
        if not isinstance(clk, (int, float)) or isinstance(clk, bool) or clk <= 0:
            errors.append(f"'clock_mhz' must be a positive number, got {clk!r}")

    if errors:
        raise ConfigError(
            "Configuration validation failed:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _validate_regex(pattern: str, what: str, errors: list[str]) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:
        errors.append(f"{what} is not valid regex: {exc}")


def _validate_stage(index: int, stage: Any, errors: list[str]) -> None:
    if not isinstance(stage, dict):
        errors.append(f"path_stages[{index}]: must be an object")
        return

    label = stage.get("label", "?")
    if "label" not in stage:
        errors.append(f"path_stages[{index}]: missing 'label'")

    stage_type = stage.get("type")
    if stage_type is not None and stage_type not in ("exception_entry", "exception_exit"):
        errors.append(
            f"path_stages[{index}] ('{label}'): unknown type '{stage_type}'. "
            f"Valid: exception_entry, exception_exit"
        )

    if stage_type is None and not stage.get("patterns"):
        errors.append(
            f"path_stages[{index}] ('{label}'): must have 'type' or 'patterns'"
        )

    for j, pat in enumerate(stage.get("patterns", [])):
        try:
            re.compile(pat)
        except re.error as exc:
            errors.append(
                f"path_stages[{index}] ('{label}'): "
                f"pattern[{j}] '{pat}' is not valid regex: {exc}"
            )

    combine = stage.get("combine", "sum")
    if combine not in ("sum", "max"):
        errors.append(
            f"path_stages[{index}] ('{label}'): unknown combine '{combine}'. Valid: sum, max"
        )

    entry = stage.get("entry")
    if entry is not None:
        try:
            re.compile(entry)
        except re.error as exc:
            errors.append(
                f"path_stages[{index}] ('{label}'): "
                f"entry '{entry}' is not valid regex: {exc}"
            )
