"""Tests for stage analysis and call-graph walker."""

from __future__ import annotations

import pytest

from cortex_cycle_budget.analysis import analyze_stages, walk_call_graph
from cortex_cycle_budget.models import Function, Instruction, StageMatchError


def _make_fn(
    name: str,
    *,
    min_cycles: int = 10,
    max_cycles: int = 20,
    instructions: int = 5,
    calls: list[str] | None = None,
    code_size: int = 12,
    fpu_ops: int = 0,
) -> Function:
    instr_list = [
        Instruction(
            address=0, raw_bytes="00", mnemonic="nop", operands="",
            size=2, min_cycles=1, max_cycles=1,
        )
        for _ in range(instructions)
    ]
    return Function(
        name=name,
        demangled=name,
        start_addr=0,
        end_addr=code_size,
        instructions=instr_list,
        total_min_cycles=min_cycles,
        total_max_cycles=max_cycles,
        instruction_count=instructions,
        code_size=code_size,
        calls=calls or [],
        fpu_ops=fpu_ops,
        alu_ops=instructions - fpu_ops,
    )


class TestWalkCallGraph:
    def test_single_function(self) -> None:
        foo = _make_fn("foo", min_cycles=5, max_cycles=8)
        lookup = {"foo": foo}
        bd = walk_call_graph(foo, lookup)
        assert set(bd) == {"foo"}
        assert bd["foo"]["min"] == 5
        assert bd["foo"]["max"] == 8
        assert bd["foo"]["call_count"] == 1

    def test_linear_chain(self) -> None:
        bar = _make_fn("bar", min_cycles=3, max_cycles=4)
        foo = _make_fn("foo", min_cycles=10, max_cycles=20, calls=["bar"])
        lookup = {"foo": foo, "bar": bar}
        bd = walk_call_graph(foo, lookup)
        assert set(bd) == {"foo", "bar"}
        assert bd["bar"]["min"] == 3

    def test_recursion_terminates(self) -> None:
        foo = _make_fn("foo", calls=["foo"])
        lookup = {"foo": foo}
        bd = walk_call_graph(foo, lookup)
        # Recursive self-call must not blow the stack
        assert bd["foo"]["call_count"] == 1

    def test_mutual_recursion_terminates(self) -> None:
        a = _make_fn("a", calls=["b"])
        b = _make_fn("b", calls=["a"])
        lookup = {"a": a, "b": b}
        bd = walk_call_graph(a, lookup)
        assert set(bd) == {"a", "b"}

    def test_unresolved_callee_ignored(self) -> None:
        foo = _make_fn("foo", calls=["does_not_exist"])
        lookup = {"foo": foo}
        bd = walk_call_graph(foo, lookup)
        assert set(bd) == {"foo"}


class TestAnalyzeStages:
    def test_pattern_stage(self) -> None:
        foo = _make_fn("foo", min_cycles=5, max_cycles=10)
        bar = _make_fn("bar", min_cycles=3, max_cycles=4)
        all_fns = [foo, bar]
        lookup = {f.demangled: f for f in all_fns}
        config = {
            "path_stages": [
                {"label": "S1", "patterns": ["^foo$"]},
            ],
            "cortex": "m4",
        }
        stages = analyze_stages(config, all_fns, lookup)
        assert len(stages) == 1
        assert stages[0].min_cycles == 5
        assert stages[0].max_cycles == 10
        assert stages[0].functions == ["foo"]

    def test_exception_entry_stage_uses_variant_overhead(self) -> None:
        config = {
            "path_stages": [{"label": "ISR Entry", "type": "exception_entry"}],
            "cortex": "m4",
        }
        stages = analyze_stages(config, [], {})
        assert stages[0].is_overhead is True
        assert stages[0].min_cycles == 12
        assert stages[0].max_cycles == 29

    def test_exception_entry_m0(self) -> None:
        config = {
            "path_stages": [{"label": "ISR Entry", "type": "exception_entry"}],
            "cortex": "m0",
        }
        stages = analyze_stages(config, [], {})
        assert stages[0].min_cycles == 16
        assert stages[0].max_cycles == 16

    def test_exception_exit_stage(self) -> None:
        config = {
            "path_stages": [{"label": "ISR Exit", "type": "exception_exit"}],
            "cortex": "m7",
        }
        stages = analyze_stages(config, [], {})
        assert stages[0].is_overhead is True
        assert stages[0].min_cycles == 12

    def test_entry_walks_call_graph(self) -> None:
        bar = _make_fn("bar", min_cycles=3, max_cycles=4)
        foo = _make_fn("foo", min_cycles=10, max_cycles=20, calls=["bar"])
        all_fns = [foo, bar]
        lookup = {f.demangled: f for f in all_fns}
        config = {
            "path_stages": [
                {
                    "label": "Walked",
                    "entry": "^foo$",
                    "patterns": ["^foo$"],
                },
            ],
        }
        stages = analyze_stages(config, all_fns, lookup)
        # foo + bar via call graph
        assert stages[0].min_cycles == 13
        assert stages[0].max_cycles == 24

    def test_strict_failure_raises(self) -> None:
        config = {
            "path_stages": [
                {"label": "Missing", "patterns": ["^never_matches$"]},
            ],
        }
        with pytest.raises(StageMatchError):
            analyze_stages(config, [], {})

    def test_non_strict_does_not_raise(self) -> None:
        config = {
            "path_stages": [
                {"label": "Missing", "patterns": ["^never_matches$"]},
            ],
        }
        stages = analyze_stages(config, [], {}, strict=False)
        assert stages[0].min_cycles == 0

    def test_optional_stage_not_required(self) -> None:
        config = {
            "path_stages": [
                {"label": "Opt", "patterns": ["^never$"], "required": False},
            ],
        }
        # Required=False → no error even in strict mode
        stages = analyze_stages(config, [], {})
        assert stages[0].functions == []
