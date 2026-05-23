"""Report generators: Markdown, PR comment, annotated disassembly, JSON metrics."""

from __future__ import annotations

import re
from typing import Any

from cortex_cycle_budget.analysis import walk_call_graph
from cortex_cycle_budget.models import Function, PathStage
from cortex_cycle_budget.timing_model import classify_instruction


def _budget_status(pct_max: float) -> str:
    if pct_max > 100:
        return "🔴 OVER"
    if pct_max > 50:
        return "🟡 WARN"
    return "🟢 OK"


def _budget_rows(clock_mhz: int, total_min: int, total_max: int,
                 loop_rates: list[int | float]) -> list[str]:
    rows: list[str] = []
    for rate in loop_rates:
        avail = int(clock_mhz * 1_000_000 // (rate * 1_000))
        pct_min = total_min / avail * 100 if avail > 0 else 0.0
        pct_max = total_max / avail * 100 if avail > 0 else 0.0
        rows.append(
            f"| {rate} kHz | {avail} | {total_min} ({pct_min:.1f}%) "
            f"| {total_max} ({pct_max:.1f}%) | {_budget_status(pct_max)} |"
        )
    return rows


def generate_report(
    config: dict[str, Any],
    stages: list[PathStage],
    all_fns: list[Function],
    lookup: dict[str, Function],
) -> str:
    """Full Markdown report (Executive Summary + budgets + breakdowns + mix)."""
    target = config["target"]
    build_config = config["build_config"]
    clock = config["clock_mhz"]
    loop_rates = config.get("loop_rates_khz", [10, 20, 40])

    total_min = sum(s.min_cycles for s in stages)
    total_max = sum(s.max_cycles for s in stages)
    total_instructions = sum(s.instruction_count for s in stages)
    total_code_size = sum(s.code_size for s in stages)
    total_fpu = sum(s.fpu_ops for s in stages)

    path_name = config.get("path_name", "Critical Path")
    lines: list[str] = [
        "# Cycle Estimation Report",
        "",
        f"**Target**: `{target}` | **Build**: `{build_config}` | **Clock**: {clock} MHz",
        f"**Path**: {path_name}",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Estimated Cycles (min) | **{total_min}** |",
        f"| Estimated Cycles (max) | **{total_max}** |",
        f"| Total Instructions | {total_instructions} |",
        f"| Total Code Size | {total_code_size} bytes |",
        f"| FPU Operations | {total_fpu} |",
        f"| Path Stages | {len(stages)} |",
        "",
        "## CPU Utilization Budget",
        "",
        "| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |",
        "|-----------|-----------------|-----------|-----------|--------|",
    ]
    lines.extend(_budget_rows(clock, total_min, total_max, loop_rates))
    lines.append("")

    # ── Path Breakdown ────────────────────────────────────────────────────
    lines.extend(("## Path Breakdown", "", "```"))
    max_label = max((len(s.label) for s in stages), default=1)
    for i, stage in enumerate(stages):
        bar_len = max(1, stage.max_cycles * 40 // max(total_max, 1))
        bar = "█" * bar_len + "░" * (40 - bar_len)
        pct = stage.max_cycles / max(total_max, 1) * 100
        lines.append(
            f"  {stage.label:<{max_label}}  {bar}  "
            f"{stage.min_cycles:>4d}–{stage.max_cycles:<4d} cycles ({pct:5.1f}%)"
        )
        if i < len(stages) - 1:
            lines.append(f"  {'':>{max_label}}  │")
    lines.extend(("```", ""))

    lines.append("| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |")
    lines.append("|-------|-----------|-----------|-------------|-----------|---------|-----------|")
    for stage in stages:
        fn_count = len(stage.functions)
        overhead_note = " *(hw overhead)*" if stage.is_overhead else ""
        lines.append(
            f"| {stage.label}{overhead_note} | {stage.min_cycles} | {stage.max_cycles} "
            f"| {stage.instruction_count} | {stage.code_size} B | {stage.fpu_ops} | {fn_count} |"
        )
    lines.append(
        f"| **TOTAL** | **{total_min}** | **{total_max}** "
        f"| **{total_instructions}** | **{total_code_size} B** | **{total_fpu}** | |"
    )
    lines.append("")

    # ── Per-Function Detail ───────────────────────────────────────────────
    for scfg in config["path_stages"]:
        if not scfg.get("entry"):
            continue
        entry_pattern = scfg["entry"]
        entry_fn = next(
            (fn for fn in all_fns if re.search(entry_pattern, fn.demangled)),
            None,
        )
        if entry_fn is None:
            continue
        breakdown = walk_call_graph(entry_fn, lookup)
        lines.append(f"## Per-Function Detail — {scfg['label']}")
        lines.append("")
        lines.append("| Function | Calls | Min Cycles | Max Cycles | FPU | Load/Store | Branch | ALU |")
        lines.append("|----------|-------|-----------|-----------|-----|------------|--------|-----|")

        sorted_fns = sorted(breakdown.items(), key=lambda x: x[1]["max"], reverse=True)
        for fn_name, stats in sorted_fns:
            short = fn_name[:60] + "..." if len(fn_name) > 60 else fn_name
            lines.append(
                f"| `{short}` | {stats['call_count']}x "
                f"| {stats['min']} | {stats['max']} "
                f"| {stats['fpu_ops']} | {stats['load_store']} "
                f"| {stats['branch']} | {stats['alu']} |"
            )
        lines.append("")

    # ── Instruction Mix ───────────────────────────────────────────────────
    lines.extend(("## Instruction Mix", ""))
    mix: dict[str, int] = {"FPU": 0, "Load/Store": 0, "Branch": 0, "ALU": 0, "Mul/Div": 0}
    for stage in stages:
        for fn_name in stage.functions:
            fn = lookup.get(fn_name)
            if fn is None:
                continue
            mix["FPU"] += fn.fpu_ops
            mix["Load/Store"] += fn.load_store_ops
            mix["Branch"] += fn.branch_ops
            mix["ALU"] += fn.alu_ops
            mix["Mul/Div"] += fn.mul_div_ops
    total_instrs = sum(mix.values()) or 1

    lines.append("```")
    for label, count in mix.items():
        pct = count / total_instrs * 100
        bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
        lines.append(f"  {label:12s} {bar} {count:4d} ({pct:5.1f}%)")
    lines.extend(("```", ""))

    # ── Optimization Indicators ───────────────────────────────────────────
    lines.extend(("## Optimization Quality Indicators", ""))

    fpu_ratio = mix["FPU"] / total_instrs
    ls_ratio = mix["Load/Store"] / total_instrs

    if fpu_ratio > 0.3:
        lines.append(f"- ✅ **High FPU utilization** ({fpu_ratio:.0%}) — good use of hardware FPU")
    elif fpu_ratio > 0.15:
        lines.append(f"- ⚠️ **Moderate FPU utilization** ({fpu_ratio:.0%}) — some overhead from non-FPU ops")
    else:
        lines.append(f"- ❌ **Low FPU utilization** ({fpu_ratio:.0%}) — excessive overhead")

    if ls_ratio > 0.4:
        lines.append(f"- ❌ **High load/store ratio** ({ls_ratio:.0%}) — register spilling or poor data locality")
    elif ls_ratio > 0.25:
        lines.append(f"- ⚠️ **Moderate load/store ratio** ({ls_ratio:.0%})")
    else:
        lines.append(f"- ✅ **Low load/store ratio** ({ls_ratio:.0%}) — efficient register usage")

    has_vfma = False
    has_vsqrt_vdiv = False
    for fn in all_fns:
        for instr in fn.instructions:
            ml = instr.mnemonic.lower()
            if ml.startswith("vfma"):
                has_vfma = True
            if ml in ("vsqrt.f32", "vdiv.f32"):
                has_vsqrt_vdiv = True
        if has_vfma and has_vsqrt_vdiv:
            break

    if has_vfma:
        lines.append("- ✅ **FMA instructions detected** — fused multiply-add in use")
    else:
        lines.append("- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics")

    if has_vsqrt_vdiv:
        cortex = config.get("cortex", "m4")
        if cortex == "m7":
            lines.append("- ℹ️ **vsqrt/vdiv detected** — 7 cycles each on Cortex-M7")
        else:
            lines.append("- ⚠️ **vsqrt/vdiv detected** — 14 cycles each; consider LUT approximations")
    lines.append("")

    return "\n".join(lines)


def generate_cpu_budget_table(config: dict[str, Any], stages: list[PathStage]) -> str:
    """Generate only the CPU utilization budget markdown table rows (no headings)."""
    clock = config["clock_mhz"]
    loop_rates = config.get("loop_rates_khz", [10, 20, 40])

    total_min = sum(s.min_cycles for s in stages)
    total_max = sum(s.max_cycles for s in stages)

    lines = [
        "| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |",
        "|-----------|-----------------|-----------|-----------|--------|",
    ]
    lines.extend(_budget_rows(clock, total_min, total_max, loop_rates))
    return "\n".join(lines)


def generate_pr_comment(config: dict[str, Any], stages: list[PathStage]) -> str:
    """Generate a concise PR comment banner with Executive Summary + CPU Budget."""
    target = config["target"]
    build_config = config["build_config"]
    clock = config["clock_mhz"]
    loop_rates = config.get("loop_rates_khz", [10, 20, 40])

    total_min = sum(s.min_cycles for s in stages)
    total_max = sum(s.max_cycles for s in stages)
    total_instructions = sum(s.instruction_count for s in stages)
    total_code_size = sum(s.code_size for s in stages)

    path_name = config.get("path_name", "Critical Path")
    lines: list[str] = [
        "## 🏎️ Cycle Estimation",
        "",
        f"**Target**: `{target}` | **Build**: `{build_config}` | **Clock**: {clock} MHz",
        f"**Path**: {path_name}",
        "",
        "### Executive Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Estimated Cycles (min — max) | **{total_min}** — **{total_max}** |",
        f"| Total Instructions | {total_instructions} |",
        f"| Code Size | {total_code_size} bytes |",
        f"| Path Stages | {len(stages)} |",
        "",
        "### CPU Utilization Budget",
        "",
        "| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |",
        "|-----------|-----------------|-----------|-----------|--------|",
    ]
    lines.extend(_budget_rows(clock, total_min, total_max, loop_rates))
    lines.append("")

    lines.extend(("### Path Breakdown", "", "| Stage | Cycles | % |", "|-------|--------|---|"))
    for stage in stages:
        pct = stage.max_cycles / max(total_max, 1) * 100
        lines.append(f"| {stage.label} | {stage.min_cycles}–{stage.max_cycles} | {pct:.0f}% |")
    lines.append(f"| **Total** | **{total_min}–{total_max}** | |")
    lines.append("")
    lines.append("> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.")

    return "\n".join(lines)


def generate_annotated_disasm(
    config: dict[str, Any],
    all_fns: list[Function],
    stages: list[PathStage],
) -> str:
    """Generate annotated disassembly for all functions in the path."""
    path_name = config.get("path_name", "Critical Path")
    lines: list[str] = [f"# Annotated Disassembly — {path_name}", ""]

    seen: set[str] = set()
    fn_by_name = {f.demangled: f for f in all_fns}

    for stage in stages:
        if stage.is_overhead:
            continue
        lines.extend((f"## Stage: {stage.label}", ""))

        for fn_name in sorted(stage.functions):
            if fn_name in seen:
                continue
            seen.add(fn_name)
            fn = fn_by_name.get(fn_name)
            if fn is None:
                continue

            short = fn_name[:80] + "..." if len(fn_name) > 80 else fn_name
            lines.extend((f"### `{short}`", ""))
            lines.append(
                f"Address: `0x{fn.start_addr:08x}`–`0x{fn.end_addr:08x}` "
                f"| {fn.code_size} bytes | {fn.instruction_count} instructions "
                f"| {fn.total_min_cycles}–{fn.total_max_cycles} cycles"
            )
            lines.extend((
                "",
                "```asm",
                f"; {'Addr':>10s}  {'Bytes':<14s}  {'Mn':>3s} {'Mx':>3s}  Instruction",
                f"; {'-' * 10}  {'-' * 14}  {'-' * 3} {'-' * 3}  {'-' * 40}",
            ))

            for instr in fn.instructions:
                cat = classify_instruction(instr.mnemonic)
                marker = {"fpu": "F", "load_store": "M", "branch": "B",
                          "mul_div": "X"}.get(cat, " ")
                lines.append(
                    f"  0x{instr.address:08x}  {instr.raw_bytes:<14s}  "
                    f"{instr.min_cycles:>3d} {instr.max_cycles:>3d} {marker} "
                    f"{instr.mnemonic}\t{instr.operands}"
                )
            lines.extend(("```", ""))

            if fn.calls:
                lines.append("**Calls:**")
                for callee in fn.calls:
                    short_callee = callee[:70] + "..." if len(callee) > 70 else callee
                    lines.append(f"  - `{short_callee}`")
                lines.append("")

    return "\n".join(lines)


def generate_json_metrics(
    config: dict[str, Any],
    stages: list[PathStage],
) -> dict[str, Any]:
    """Build the machine-readable metrics dict (serialize with json.dump)."""
    total_min = sum(s.min_cycles for s in stages)
    total_max = sum(s.max_cycles for s in stages)
    total_instr = sum(s.instruction_count for s in stages)
    total_code_size = sum(s.code_size for s in stages)
    clock = config["clock_mhz"]
    loop_rates = config.get("loop_rates_khz", [20])

    # Compute min/max percentages in a single pass, but emit all `*_min_pct`
    # keys before all `*_max_pct` keys to preserve the historical JSON key
    # ordering relied upon by downstream consumers.
    min_pcts: dict[str, float] = {}
    max_pcts: dict[str, float] = {}
    for rate in loop_rates:
        avail = clock * 1_000_000 // (rate * 1_000)
        if avail <= 0:
            continue
        min_pcts[f"{rate}khz_min_pct"] = round(total_min / avail * 100, 2)
        max_pcts[f"{rate}khz_max_pct"] = round(total_max / avail * 100, 2)
    utilization: dict[str, float] = {**min_pcts, **max_pcts}

    return {
        "target": config["target"],
        "build_config": config["build_config"],
        "clock_mhz": clock,
        "cortex": config.get("cortex", "m4"),
        "path": config.get("path_name", "Critical Path"),
        "summary": {
            "estimated_min_cycles": total_min,
            "estimated_max_cycles": total_max,
            "total_instructions": total_instr,
            "total_code_size_bytes": total_code_size,
            "path_stages": len(stages),
        },
        "utilization": utilization,
        "stages": [
            {
                "label": s.label,
                "min_cycles": s.min_cycles,
                "max_cycles": s.max_cycles,
                "instructions": s.instruction_count,
                "code_size_bytes": s.code_size,
                "fpu_ops": s.fpu_ops,
                "is_overhead": s.is_overhead,
                "functions": s.functions,
            }
            for s in stages
        ],
    }
