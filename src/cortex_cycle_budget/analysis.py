"""Stage analysis: configuration + disassembly → :class:`PathStage` list."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from cortex_cycle_budget.models import (
    Function,
    FunctionPath,
    FunctionShare,
    PathStage,
    StageMatchError,
)
from cortex_cycle_budget.paths import PathOptions, analyze_paths, direct_callees
from cortex_cycle_budget.timing_model import EXCEPTION_OVERHEAD, classify_instruction
from cortex_cycle_budget.tooling import log


def path_options(config: dict[str, Any]) -> PathOptions:
    """The path-analysis settings of *config*."""
    return PathOptions(
        loop_bounds=dict(config.get("loop_bounds", {})),
        cold_calls=tuple(config.get("cold_calls", [])),
    )


def path_breakdown(
    root: FunctionPath,
    paths: dict[int, FunctionPath],
    *,
    best_case: bool = False,
) -> dict[int, int]:
    """How often each function runs on the worst (or best) path from *root*.

    Returns ``{function start address: calls}``, the root included.
    """
    calls: dict[int, int] = {}

    def visit(path: FunctionPath, times: int, active: frozenset[int]) -> None:
        calls[path.start_addr] = calls.get(path.start_addr, 0) + times
        for callee, count in path.min_callees if best_case else path.callees:
            if callee in paths and callee not in active:
                visit(paths[callee], times * count, active | {callee})

    visit(root, 1, frozenset({root.start_addr}))
    return calls


@dataclass
class _Charge:
    """Cycles and functions one stage is charged."""

    min_cycles: int = 0
    calls: dict[int, int] = field(default_factory=dict)  # worst path: start address → calls
    notes: list[str] = field(default_factory=list)


def _short(name: str, limit: int = 110) -> str:
    return name if len(name) <= limit else name[: limit - 3] + "..."


def _match_stage(stage_cfg: dict[str, Any], all_fns: list[Function], errors: list[str]) -> list[Function]:
    matched: list[Function] = []
    for fn in all_fns:
        if fn.instruction_count == 0:  # a data object, such as a table
            continue
        for pat in stage_cfg.get("patterns", []):
            try:
                if re.search(pat, fn.demangled):
                    matched.append(fn)
                    break
            except re.error as exc:
                msg = f"Stage '{stage_cfg['label']}': invalid regex pattern '{pat}': {exc}"
                errors.append(msg)
                log(f"  ERROR: {msg}")
                break
    return matched


def _called_by(matched: Sequence[Function], all_fns: list[Function]) -> dict[int, int]:
    """Matched functions that another matched function reaches by direct calls: callee → caller."""
    by_start = {fn.start_addr: fn for fn in matched}
    reach: dict[int, set[int]] = {}
    for fn in matched:
        seen: set[int] = set()
        work = [fn]
        while work:
            for callee in direct_callees(work.pop(), all_fns):
                if callee.start_addr not in seen and callee.start_addr != fn.start_addr:
                    seen.add(callee.start_addr)
                    work.append(callee)
        reach[fn.start_addr] = seen
    callers: dict[int, int] = {}
    for caller, reached in reach.items():
        for address in reached:
            if address in by_start and caller not in reach[address]:
                callers.setdefault(address, caller)
    return callers


def _distribute(
    root: FunctionPath,
    home: int,
    paths: dict[int, FunctionPath],
    stage_of: dict[int, int],
    charges: list[_Charge],
) -> None:
    """Charge the worst and best paths from *root* to the stages that name each function.

    A function no stage names is charged to the stage of the function that calls it.
    """
    def walk(path: FunctionPath, times: int, stage: int, active: frozenset[int], *, best: bool) -> None:
        stage = stage_of.get(path.start_addr, stage)
        charge = charges[stage]
        if best:
            charge.min_cycles += path.own_min_cycles * times
        else:
            charge.calls[path.start_addr] = charge.calls.get(path.start_addr, 0) + times
        for callee, count in path.min_callees if best else path.callees:
            if callee in paths and callee not in active:
                walk(paths[callee], times * count, stage, active | {callee}, best=best)

    walk(root, 1, home, frozenset({root.start_addr}), best=False)
    walk(root, 1, home, frozenset({root.start_addr}), best=True)


def _path_notes(charged: Sequence[FunctionPath]) -> list[str]:
    """What the analysis could not see on the worst paths of *charged*, one note per kind."""
    def names(paths: Sequence[FunctionPath], count: str | None = None) -> str:
        return ", ".join(
            f"`{_short(p.function)}`" + (f" ({getattr(p, count)})" if count else "") for p in paths
        )

    notes: list[str] = []
    indirect = [p for p in charged if p.indirect_calls]
    if indirect:
        notes.append(
            "calls through a register are not followed, name their targets in a stage: "
            + names(indirect, "indirect_calls")
        )
    unbounded = [p for p in charged if p.unbounded_loops]
    if unbounded:
        notes.append(
            "loops are charged for one iteration, set `loop_bounds` to charge more: "
            + names(unbounded, "unbounded_loops")
        )
    bounded = [p for p in charged if p.loop_bound is not None]
    if bounded:
        notes.append("loops are charged their configured bound: " + names(bounded, "loop_bound"))
    whole = [p for p in charged if p.whole_body]
    if whole:
        notes.append("control flow not resolved, every instruction is charged: " + names(whole))
    return notes


def _uncharged(caller: int | None, functions: dict[int, Function], charges: list[_Charge]) -> str:
    """Why a matched function is on no charged path."""
    if caller is None:
        return "is not on a charged path"
    name = f"`{_short(functions[caller].demangled)}`"
    if any(caller in charge.calls for charge in charges):
        return f"is not on the worst path of {name}, which calls it"
    return f"is not charged: {name}, which calls it, is not charged either"


def _fill(stage: PathStage, charge: _Charge, paths: dict[int, FunctionPath],
          functions: dict[int, Function]) -> None:
    stage.min_cycles = charge.min_cycles
    stage.notes.extend(charge.notes)
    for address, times in charge.calls.items():
        path, fn = paths[address], functions[address]
        on_path = frozenset(path.addresses)
        executed = [i for i in fn.instructions if i.address in on_path]
        stage.breakdown.append(FunctionShare(
            function=fn.demangled,
            start_addr=address,
            calls=times,
            max_cycles=path.own_max_cycles * times,
            instructions=len(executed) * times,
            code_size=fn.code_size,
            fpu_ops=sum(1 for i in executed if classify_instruction(i.mnemonic) == "fpu") * times,
            addresses=on_path,
        ))
        stage.indirect_calls += path.indirect_calls * times
    stage.notes.extend(_path_notes([paths[address] for address in charge.calls]))
    stage.breakdown.sort(key=lambda s: (-s.max_cycles, s.function))
    stage.functions = sorted({s.function for s in stage.breakdown})
    stage.max_cycles = sum(s.max_cycles for s in stage.breakdown)
    stage.instruction_count = sum(s.instructions for s in stage.breakdown)
    stage.code_size = sum(s.code_size for s in stage.breakdown)
    stage.fpu_ops = sum(s.fpu_ops for s in stage.breakdown)


def analyze_stages(
    config: dict[str, Any],
    all_fns: list[Function],
    lookup: dict[str, Function],
    *,
    strict: bool = True,
) -> list[PathStage]:
    """Resolve the configured ``path_stages`` against the disassembled binary.

    Every matched function that no other matched function calls directly is a
    root. A root is charged its worst path, the functions that path calls
    directly included. Each function on that path is charged to the stage that
    names it, or else to the stage of its caller.

    Args:
        config: Parsed JSON configuration (must include ``path_stages``).
        all_fns: Output of :func:`parse_disassembly`.
        lookup: ``{fn.demangled: fn}`` mapping over *all_fns* (kept for API
            compatibility; functions are resolved by address).
        strict: When ``True``, raise :class:`StageMatchError` if any required
            stage matches no functions.

    Raises:
        StageMatchError: in strict mode, when at least one required stage
            fails to match.
    """
    del lookup
    cortex = config.get("cortex", "m4")
    overhead = EXCEPTION_OVERHEAD.get(cortex, EXCEPTION_OVERHEAD["m4"])
    stage_cfgs: list[dict[str, Any]] = config["path_stages"]
    errors: list[str] = []

    matched_by_stage = [
        [] if cfg.get("type") else _match_stage(cfg, all_fns, errors) for cfg in stage_cfgs
    ]
    stage_of: dict[int, int] = {}
    for index, matched in enumerate(matched_by_stage):
        for fn in matched:
            stage_of.setdefault(fn.start_addr, index)
    functions = {fn.start_addr: fn for fn in all_fns}
    every_match = [functions[address] for address in stage_of]
    caller_of = _called_by(every_match, all_fns)
    charges = [_Charge() for _ in stage_cfgs]
    explained: set[int] = set()  # matched functions whose absence from a path is already noted

    roots_by_stage: list[list[Function]] = []
    for index, (cfg, matched) in enumerate(zip(stage_cfgs, matched_by_stage, strict=True)):
        roots: list[Function] = []
        entry_pattern = cfg.get("entry")
        if cfg.get("type"):
            pass
        elif entry_pattern:
            roots = [fn for fn in matched if re.search(entry_pattern, fn.demangled)][:1]
            explained.update(fn.start_addr for fn in matched)
            if not roots:
                msg = (
                    f"Stage '{cfg['label']}': entry function matching "
                    f"'{entry_pattern}' not found in binary"
                )
                if cfg.get("required", True):
                    errors.append(msg)
                log(f"  ERROR: {msg}")
        else:
            if not matched and cfg.get("required", True):
                msg = (
                    f"Stage '{cfg['label']}': no functions matched any "
                    f"of the {len(cfg.get('patterns', []))} configured patterns"
                )
                errors.append(msg)
                log(f"  ERROR: {msg}")
            for fn in matched:
                if stage_of[fn.start_addr] != index:
                    charges[index].notes.append(
                        f"`{_short(fn.demangled)}` is already charged to stage "
                        f"'{stage_cfgs[stage_of[fn.start_addr]]['label']}'"
                    )
                elif fn.start_addr not in caller_of:
                    roots.append(fn)
        roots_by_stage.append(roots)

    paths = analyze_paths(all_fns, [fn for roots in roots_by_stage for fn in roots], path_options(config))

    for index, (cfg, roots) in enumerate(zip(stage_cfgs, roots_by_stage, strict=True)):
        root_paths = [paths[fn.start_addr] for fn in roots]
        if cfg.get("combine", "sum") == "max" and len(root_paths) > 1:
            chosen = max(root_paths, key=lambda p: p.max_cycles)
            for other in root_paths:
                if other is not chosen:
                    explained.add(other.start_addr)
                    charges[index].notes.append(
                        f"alternative `{_short(other.function)}` ({other.max_cycles} cycles) is not "
                        f"charged: `{_short(chosen.function)}` ({chosen.max_cycles} cycles) costs more"
                    )
            root_paths = [chosen]
        for root in root_paths:
            _distribute(root, index, paths, stage_of, charges)

    stages: list[PathStage] = []
    for index, cfg in enumerate(stage_cfgs):
        stage_type = cfg.get("type")
        if stage_type in ("exception_entry", "exception_exit"):
            side = "entry" if stage_type == "exception_entry" else "exit"
            stages.append(PathStage(
                label=cfg["label"],
                min_cycles=overhead[f"{side}_min"],
                max_cycles=overhead[f"{side}_max"],
                is_overhead=True,
            ))
            continue
        stage = PathStage(label=cfg["label"])
        _fill(stage, charges[index], paths, functions)
        for fn in matched_by_stage[index]:
            charged = fn.start_addr in charges[index].calls or fn.start_addr in explained
            if stage_of[fn.start_addr] == index and not charged:
                stage.notes.append(
                    f"`{_short(fn.demangled)}` {_uncharged(caller_of.get(fn.start_addr), functions, charges)}"
                )
        stages.append(stage)

    if strict and errors:
        log("")
        log("Stage matching failed — the configuration does not align with the binary.")
        log("Unmatched stages:")
        for e in errors:
            log(f"  • {e}")
        log("")
        log("Ensure the path_stages patterns in your config JSON match the ")
        log("demangled symbol names in the ELF. You can inspect them with:")
        log("  arm-none-eabi-objdump -d -C <elf> | grep '^[0-9a-f].*<.*>:$'")
        raise StageMatchError(
            f"{len(errors)} path stage(s) matched no functions in the binary. "
            f"See stderr for details."
        )

    return stages
