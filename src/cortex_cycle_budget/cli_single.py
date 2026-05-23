"""Single-mode CLI: ``cortex-cycle-budget`` and ``python -m cortex_cycle_budget``."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

from cortex_cycle_budget.analysis import analyze_stages
from cortex_cycle_budget.config import validate_config
from cortex_cycle_budget.models import ConfigError, StageMatchError
from cortex_cycle_budget.parser import parse_disassembly
from cortex_cycle_budget.reports import (
    generate_annotated_disasm,
    generate_cpu_budget_table,
    generate_json_metrics,
    generate_pr_comment,
    generate_report,
)
from cortex_cycle_budget.timing_model import (
    EXCEPTION_OVERHEAD,
    SUPPORTED_VARIANTS,
    resolve_timing_table,
)
from cortex_cycle_budget.tooling import log, run_objdump, run_size


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cortex-cycle-budget",
        description="Static ARM Cortex-M cycle estimation for a critical path.",
    )
    parser.add_argument("config", help="JSON configuration file")
    parser.add_argument("--elf", required=True, help="Path to ELF binary")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--objdump", default="arm-none-eabi-objdump")
    parser.add_argument("--size-tool", default="arm-none-eabi-size")
    parser.add_argument("--disasm-file", help="Pre-generated disassembly file")
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not fail when path stages match no functions",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target board identifier (free-form label, e.g. NUCLEO-H743ZI)",
    )
    parser.add_argument(
        "--build-config",
        required=True,
        help="Build configuration label (e.g. Release, Debug, RelWithDebInfo)",
    )
    parser.add_argument(
        "--clock-mhz",
        required=True,
        type=int,
        help="CPU clock frequency in MHz (positive integer)",
    )
    parser.add_argument(
        "--cortex",
        default="m4",
        choices=sorted(SUPPORTED_VARIANTS),
        help="Cortex-M variant for timing model (default: m4)",
    )
    parser.add_argument(
        "--fail-over-max-cycles",
        type=int,
        default=None,
        help=(
            "Exit with non-zero status if total estimated max cycles "
            "exceeds this threshold."
        ),
    )
    parser.add_argument(
        "--fail-over-max-pct",
        type=float,
        default=None,
        metavar="RATE_KHZ,PCT",
        help=argparse.SUPPRESS,  # legacy reserved; prefer --fail-over-max-cycles
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not os.path.isfile(args.config):
        log(f"ERROR: Config file not found: {args.config}")
        return 1

    if not args.disasm_file and not os.path.isfile(args.elf):
        log(f"ERROR: ELF file not found: {args.elf}")
        return 1

    try:
        with open(args.config) as f:
            config: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as exc:
        log(f"ERROR: Failed to parse config JSON: {exc}")
        return 1

    config["target"] = args.target
    config["build_config"] = args.build_config
    config["clock_mhz"] = args.clock_mhz
    config["cortex"] = args.cortex

    if args.clock_mhz <= 0:
        log(f"ERROR: --clock-mhz must be a positive integer, got {args.clock_mhz}")
        return 1
    if args.cortex not in EXCEPTION_OVERHEAD:
        valid = ", ".join(sorted(EXCEPTION_OVERHEAD))
        log(f"ERROR: --cortex '{args.cortex}' is not supported. Valid values: {valid}")
        return 1

    try:
        validate_config(config)
    except ConfigError as exc:
        log(f"ERROR: {exc}")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    if args.disasm_file:
        if not os.path.isfile(args.disasm_file):
            log(f"ERROR: Disassembly file not found: {args.disasm_file}")
            return 1
        with open(args.disasm_file) as f:
            disasm = f.read()
    else:
        try:
            disasm = run_objdump(args.elf, args.objdump)
        except FileNotFoundError:
            log(f"ERROR: objdump tool not found: '{args.objdump}'")
            log("Install the ARM toolchain or pass --objdump with the correct path.")
            return 1
        except subprocess.CalledProcessError as exc:
            log(f"ERROR: objdump failed (exit {exc.returncode}): {exc.stderr}")
            return 1

    disasm_path = os.path.join(args.output_dir, "full_disassembly.txt")
    with open(disasm_path, "w") as f:
        f.write(disasm)
    log(f"Full disassembly: {disasm_path}")

    if not args.disasm_file:
        size_out = run_size(args.elf, args.size_tool)
        if size_out:
            with open(os.path.join(args.output_dir, "size_report.txt"), "w") as f:
                f.write(size_out)

    timing = resolve_timing_table(args.cortex)
    all_fns = parse_disassembly(disasm, timing=timing)
    lookup = {fn.demangled: fn for fn in all_fns}
    log(f"Parsed {len(all_fns)} functions")

    if len(all_fns) == 0:
        log("ERROR: No functions found in the disassembly.")
        log("The ELF may be stripped, empty, or not an ARM binary.")
        return 1

    try:
        stages = analyze_stages(config, all_fns, lookup, strict=not args.no_strict)
    except StageMatchError as exc:
        log(f"ERROR: {exc}")
        return 1

    log("Path stages:")
    for s in stages:
        log(
            f"  {s.label}: {s.min_cycles}–{s.max_cycles} cycles, "
            f"{s.instruction_count} instrs, {len(s.functions)} fns"
        )

    total_min = sum(s.min_cycles for s in stages)
    total_max = sum(s.max_cycles for s in stages)

    report = generate_report(config, stages, all_fns, lookup)
    with open(os.path.join(args.output_dir, "cycle_estimation_report.md"), "w") as f:
        f.write(report)

    budget = generate_cpu_budget_table(config, stages)
    with open(os.path.join(args.output_dir, "cpu_budget.md"), "w") as f:
        f.write(budget)

    pr_comment = generate_pr_comment(config, stages)
    with open(os.path.join(args.output_dir, "pr_comment.md"), "w") as f:
        f.write(pr_comment)

    annotated = generate_annotated_disasm(config, all_fns, stages)
    with open(os.path.join(args.output_dir, "annotated_disassembly.md"), "w") as f:
        f.write(annotated)

    metrics = generate_json_metrics(config, stages)
    with open(os.path.join(args.output_dir, "cycle_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    clock = config["clock_mhz"]
    avail_20k = clock * 1_000_000 // 20_000
    path_name = config.get("path_name", "Critical Path")
    print(f"\n{'=' * 65}")
    print(f" Cycle Estimation ({config['target']} {config['build_config']}, "
          f"Cortex-{args.cortex.upper()})")
    print(f"{'=' * 65}")
    print(f" Path: {path_name}")
    print(f" Estimated cycles: {total_min} — {total_max}")
    if avail_20k > 0:
        print(
            f" Budget @ 20 kHz / {clock} MHz: {avail_20k} cycles "
            f"({total_max / avail_20k * 100:.1f}% max)"
        )
    print(f" Stages: {len(stages)}")
    for s in stages:
        pct = s.max_cycles / max(total_max, 1) * 100
        print(f"   {s.label:<40s}  {s.min_cycles:>4d}–{s.max_cycles:<4d}  ({pct:.0f}%)")
    print(f"{'=' * 65}")

    if args.fail_over_max_cycles is not None and total_max > args.fail_over_max_cycles:
        log(
            f"ERROR: Estimated max cycles ({total_max}) exceeds threshold "
            f"({args.fail_over_max_cycles})."
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
