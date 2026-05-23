"""
cortex_cycle_budget — Static cycle-count estimation for ARM Cortex-M binaries.

Supports Cortex-M0, M4, M7, and M33 instruction timing models.  Estimates
cycle consumption for user-defined critical paths through an ELF binary by
parsing ``arm-none-eabi-objdump`` output.

Public API:
    parse_disassembly        — disassembly → Function list
    analyze_stages           — Function list + config → PathStage list
    walk_call_graph          — recursive cycle attribution
    generate_report          — full markdown report
    generate_pr_comment      — concise PR comment markdown
    generate_cpu_budget_table — budget table only (markdown)
    generate_annotated_disasm — annotated disassembly markdown
    generate_json_metrics    — machine-readable metrics dict
    validate_config          — raise ConfigError on invalid configs
    EXCEPTION_OVERHEAD       — per-variant ISR entry/exit cycles
    TIMING                   — resolved timing table for the default variant
    BASE_TIMING              — variant-agnostic timing table
    VARIANT_OVERRIDES        — per-variant overrides applied on top of BASE_TIMING
    SUPPORTED_VARIANTS       — frozenset of supported Cortex-M variants
"""

from __future__ import annotations

from cortex_cycle_budget.analysis import analyze_stages, walk_call_graph
from cortex_cycle_budget.config import validate_config
from cortex_cycle_budget.models import (
    ConfigError,
    Function,
    Instruction,
    PathStage,
    StageMatchError,
)
from cortex_cycle_budget.parser import parse_disassembly
from cortex_cycle_budget.reports import (
    generate_annotated_disasm,
    generate_cpu_budget_table,
    generate_json_metrics,
    generate_pr_comment,
    generate_report,
)
from cortex_cycle_budget.timing_model import (
    BASE_TIMING,
    EXCEPTION_OVERHEAD,
    SUPPORTED_VARIANTS,
    TIMING,
    VARIANT_OVERRIDES,
    classify_instruction,
    get_timing,
    normalize_mnemonic,
    resolve_timing_table,
)
from cortex_cycle_budget.tooling import log, run_objdump, run_size

__version__ = "0.2.0"

__all__ = [
    "BASE_TIMING",
    "EXCEPTION_OVERHEAD",
    "SUPPORTED_VARIANTS",
    "TIMING",
    "VARIANT_OVERRIDES",
    "ConfigError",
    "Function",
    "Instruction",
    "PathStage",
    "StageMatchError",
    "__version__",
    "analyze_stages",
    "classify_instruction",
    "generate_annotated_disasm",
    "generate_cpu_budget_table",
    "generate_json_metrics",
    "generate_pr_comment",
    "generate_report",
    "get_timing",
    "log",
    "normalize_mnemonic",
    "parse_disassembly",
    "resolve_timing_table",
    "run_objdump",
    "run_size",
    "validate_config",
    "walk_call_graph",
]
