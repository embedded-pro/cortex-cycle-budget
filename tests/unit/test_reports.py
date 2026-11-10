"""Tests for the report generators."""

from __future__ import annotations

import json

import pytest

from cortex_cycle_budget.analysis import analyze_stages
from cortex_cycle_budget.models import PathStage
from cortex_cycle_budget.parser import parse_disassembly
from cortex_cycle_budget.reports import (
    generate_annotated_disasm,
    generate_cpu_budget_table,
    generate_json_metrics,
    generate_pr_comment,
    generate_report,
)


@pytest.fixture
def config() -> dict:
    return {
        "target": "demo-board",
        "build_config": "Release",
        "clock_mhz": 100,
        "cortex": "m4",
        "loop_rates_khz": [10, 20, 50],
        "path_name": "Demo Path",
        "path_stages": [
            {"label": "S1", "patterns": ["^foo$"]},
            {"label": "S2", "patterns": ["^bar$"]},
        ],
    }


@pytest.fixture
def stages() -> list[PathStage]:
    return [
        PathStage(label="S1", min_cycles=100, max_cycles=200,
                  instruction_count=50, code_size=200,
                  fpu_ops=5, functions=["foo"]),
        PathStage(label="S2", min_cycles=50, max_cycles=80,
                  instruction_count=25, code_size=100,
                  fpu_ops=2, functions=["bar"]),
    ]


class TestPrComment:
    def test_contains_target_and_clock(self, config: dict, stages: list[PathStage]) -> None:
        out = generate_pr_comment(config, stages)
        assert "demo-board" in out
        assert "100 MHz" in out

    def test_totals_correct(self, config: dict, stages: list[PathStage]) -> None:
        out = generate_pr_comment(config, stages)
        assert "**150**" in out
        assert "**280**" in out

    def test_budget_table_present(self, config: dict, stages: list[PathStage]) -> None:
        out = generate_pr_comment(config, stages)
        for rate in (10, 20, 50):
            assert f"{rate} kHz" in out


class TestCpuBudgetTable:
    def test_status_ok(self, config: dict) -> None:
        # very small load
        s = [PathStage(label="X", min_cycles=10, max_cycles=20)]
        out = generate_cpu_budget_table(config, s)
        assert "🟢 OK" in out

    def test_status_over_budget(self, config: dict) -> None:
        # 10 kHz @ 100 MHz → 10_000 cycles available
        s = [PathStage(label="X", min_cycles=20_000, max_cycles=30_000)]
        out = generate_cpu_budget_table(config, s)
        assert "🔴 OVER" in out


class TestJsonMetrics:
    def test_round_trip(self, config: dict, stages: list[PathStage]) -> None:
        m = generate_json_metrics(config, stages)
        # JSON-serializable
        s = json.dumps(m)
        m2 = json.loads(s)
        assert m2["summary"]["estimated_min_cycles"] == 150
        assert m2["summary"]["estimated_max_cycles"] == 280
        assert m2["cortex"] == "m4"
        assert len(m2["stages"]) == 2

    def test_utilization_keys(self, config: dict, stages: list[PathStage]) -> None:
        m = generate_json_metrics(config, stages)
        for rate in (10, 20, 50):
            assert f"{rate}khz_min_pct" in m["utilization"]
            assert f"{rate}khz_max_pct" in m["utilization"]


class TestFullReport:
    def test_sections_present(self, config: dict, stages: list[PathStage]) -> None:
        out = generate_report(config, stages, [], {})
        assert "# Cycle Estimation Report" in out
        assert "## Executive Summary" in out
        assert "## CPU Utilization Budget" in out
        assert "## Path Breakdown" in out
        assert "## Instruction Mix" in out
        assert "## Optimization Quality Indicators" in out


class TestAnnotatedDisasm:
    def test_overhead_stages_skipped(self, config: dict) -> None:
        s = [PathStage(label="Overhead", min_cycles=12, max_cycles=29, is_overhead=True)]
        out = generate_annotated_disasm(config, [], s)
        # No "## Stage: Overhead" because overhead stages are skipped
        assert "## Stage: Overhead" not in out


ANALYZED_DISASM = """
00000100 <isr>:
     100:	b510      	push	{r4, lr}
     102:	2800      	cmp	r0, #0
     104:	d003      	beq.n	10e <isr+0xe>
     106:	3001      	adds	r0, #1
     108:	3001      	adds	r0, #1
     10a:	3001      	adds	r0, #1
     10c:	3001      	adds	r0, #1
     10e:	4798      	blx	r3
     110:	bd10      	pop	{r4, pc}
     112:	bf00      	nop
     114:	20000000 	.word	0x20000000
"""


@pytest.fixture
def analyzed(config: dict) -> tuple[dict, list, list[PathStage]]:
    functions = parse_disassembly(ANALYZED_DISASM)
    cfg = {**config, "path_stages": [{"label": "ISR", "patterns": ["^isr$"]}]}
    return cfg, functions, analyze_stages(cfg, functions, {f.demangled: f for f in functions})


class TestPathReporting:
    def test_report_lists_each_function_on_the_path(self, analyzed: tuple) -> None:
        cfg, functions, stages = analyzed
        out = generate_report(cfg, stages, functions, {f.demangled: f for f in functions})
        assert "## Per-Function Detail — ISR" in out
        assert "| `isr` | 1x |" in out

    def test_report_lists_the_analysis_notes(self, analyzed: tuple) -> None:
        cfg, functions, stages = analyzed
        out = generate_report(cfg, stages, functions, {f.demangled: f for f in functions})
        assert "## Analysis Notes" in out
        assert "through a register" in out

    def test_report_without_notes_has_no_notes_section(self, config: dict, stages: list[PathStage]) -> None:
        assert "## Analysis Notes" not in generate_report(config, stages, [], {})

    def test_pr_comment_points_at_the_notes(self, analyzed: tuple) -> None:
        cfg, _, stages = analyzed
        assert "1 analysis note(s)" in generate_pr_comment(cfg, stages)

    def test_annotated_disassembly_marks_the_worst_path(self, analyzed: tuple) -> None:
        cfg, functions, stages = analyzed
        lines = generate_annotated_disasm(cfg, functions, stages).splitlines()
        on_path = {line.split()[1] for line in lines if line.startswith("> 0x")}
        off_path = {line.split()[0] for line in lines if line.startswith("  0x")}
        assert on_path == {f"0x{address:08x}" for address in range(0x100, 0x112, 2)}
        assert off_path == {"0x00000112", "0x00000114"}

    def test_json_carries_breakdown_and_notes(self, analyzed: tuple) -> None:
        cfg, _, stages = analyzed
        (stage,) = generate_json_metrics(cfg, stages)["stages"]
        assert stage["indirect_calls"] == 1
        assert stage["breakdown"] == [
            {"function": "isr", "calls": 1, "max_cycles": stage["max_cycles"], "instructions": 9},
        ]
        assert len(stage["notes"]) == 1
