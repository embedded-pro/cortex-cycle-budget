"""Tests for the report generators."""

from __future__ import annotations

import json

import pytest

from cortex_cycle_budget.models import PathStage
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
