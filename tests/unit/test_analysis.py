"""Tests for stage analysis."""

from __future__ import annotations

from typing import Any

import pytest

from cortex_cycle_budget.analysis import analyze_stages, path_breakdown, path_options
from cortex_cycle_budget.models import PathStage, StageMatchError
from cortex_cycle_budget.parser import parse_disassembly
from cortex_cycle_budget.paths import analyze_paths

# isr → (blx r3) ... ; step calls leaf twice; fast and slow are alternatives.
DISASM = """
00000100 <isr>:
     100:	b510      	push	{r4, lr}
     102:	4798      	blx	r3
     104:	bd10      	pop	{r4, pc}

00000110 <step>:
     110:	b510      	push	{r4, lr}
     112:	f000 f805 	bl	120 <leaf>
     116:	f000 f803 	bl	120 <leaf>
     11a:	bd10      	pop	{r4, pc}

00000120 <leaf>:
     120:	3001      	adds	r0, #1
     122:	4770      	bx	lr

00000130 <fast>:
     130:	3001      	adds	r0, #1
     132:	4770      	bx	lr

00000140 <slow>:
     140:	3001      	adds	r0, #1
     142:	3001      	adds	r0, #1
     144:	3001      	adds	r0, #1
     146:	4770      	bx	lr

00000150 <branchy>:
     150:	2800      	cmp	r0, #0
     152:	d005      	beq.n	160 <branchy+0x10>
     154:	3001      	adds	r0, #1
     156:	3001      	adds	r0, #1
     158:	3001      	adds	r0, #1
     15a:	3001      	adds	r0, #1
     15c:	3001      	adds	r0, #1
     15e:	4770      	bx	lr
     160:	4770      	bx	lr

00000170 <looper>:
     170:	2300      	movs	r3, #0
     172:	3301      	adds	r3, #1
     174:	2b04      	cmp	r3, #4
     176:	d1fc      	bne.n	172 <looper+0x2>
     178:	4770      	bx	lr
"""

LEAF = 1 + 4
STEP_OWN = (1 + 2) + 4 + 4 + (1 + 2 + 3)


def _analyze(stages: list[dict[str, Any]], **top: Any) -> list[PathStage]:
    functions = parse_disassembly(DISASM)
    config = {"path_stages": stages, "cortex": "m4", **top}
    return analyze_stages(config, functions, {f.demangled: f for f in functions})


class TestPatternStage:
    def test_stage_is_charged_the_worst_path_not_the_whole_body(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^branchy$"]}])
        assert stage.max_cycles == 1 + 1 + 5 + 4
        assert stage.min_cycles == 1 + 1 + 1
        assert stage.instruction_count == 8
        assert stage.functions == ["branchy"]

    def test_direct_callees_are_charged_once_per_call(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^step$"]}])
        assert stage.max_cycles == STEP_OWN + 2 * LEAF
        assert stage.functions == ["leaf", "step"]
        calls = {share.function: share.calls for share in stage.breakdown}
        assert calls == {"step": 1, "leaf": 2}

    def test_matched_functions_add_up(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^fast$", "^slow$"]}])
        assert stage.max_cycles == (1 + 4) + (3 + 4)

    def test_function_matched_with_its_caller_is_not_charged_twice(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^step$", "^leaf$"]}])
        assert stage.max_cycles == STEP_OWN + 2 * LEAF

    def test_call_through_a_register_is_noted(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^isr$"]}])
        assert stage.indirect_calls == 1
        assert any("through a register" in note for note in stage.notes)

    def test_loop_is_noted_until_it_has_a_bound(self) -> None:
        (once,) = _analyze([{"label": "S", "patterns": ["^looper$"]}])
        assert any("one iteration" in note and "`looper` (1)" in note for note in once.notes)
        (bounded,) = _analyze([{"label": "S", "patterns": ["^looper$"]}], loop_bounds={"^looper$": 4})
        assert bounded.max_cycles > once.max_cycles
        assert any("configured bound" in note and "`looper` (4)" in note for note in bounded.notes)


class TestStageAttribution:
    def test_callee_named_by_another_stage_is_charged_there(self) -> None:
        caller, callee = _analyze([
            {"label": "Caller", "patterns": ["^step$"]},
            {"label": "Callee", "patterns": ["^leaf$"]},
        ])
        assert caller.max_cycles == STEP_OWN
        assert caller.functions == ["step"]
        assert callee.max_cycles == 2 * LEAF
        assert callee.functions == ["leaf"]

    def test_total_does_not_depend_on_how_stages_are_cut(self) -> None:
        split = _analyze([
            {"label": "Caller", "patterns": ["^step$"]},
            {"label": "Callee", "patterns": ["^leaf$"]},
        ])
        (whole,) = _analyze([{"label": "S", "patterns": ["^step$"]}])
        assert sum(s.max_cycles for s in split) == whole.max_cycles
        assert sum(s.min_cycles for s in split) == whole.min_cycles

    def test_function_named_twice_is_charged_to_the_first_stage(self) -> None:
        first, second = _analyze([
            {"label": "First", "patterns": ["^fast$"]},
            {"label": "Second", "patterns": ["^fast$"]},
        ])
        assert first.max_cycles == 1 + 4
        assert second.max_cycles == 0
        assert any("already charged to stage 'First'" in note for note in second.notes)


class TestAlternatives:
    def test_combine_max_charges_the_costliest_function_only(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^fast$", "^slow$"], "combine": "max"}])
        assert stage.max_cycles == 3 + 4
        assert stage.functions == ["slow"]
        assert any("alternative `fast`" in note for note in stage.notes)

    def test_combine_max_counts_what_the_alternatives_call(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^slow$", "^step$"], "combine": "max"}])
        assert stage.max_cycles == STEP_OWN + 2 * LEAF


class TestEntry:
    def test_entry_charges_only_the_entry_function_and_what_it_calls(self) -> None:
        (stage,) = _analyze([{"label": "S", "entry": "^step$", "patterns": ["^step$", "^slow$"]}])
        assert stage.max_cycles == STEP_OWN + 2 * LEAF
        assert stage.functions == ["leaf", "step"]

    def test_missing_entry_fails_in_strict_mode(self) -> None:
        with pytest.raises(StageMatchError):
            _analyze([{"label": "S", "entry": "^nope$", "patterns": ["^step$"]}])


class TestColdCalls:
    def test_cold_call_is_left_out_of_the_stage(self) -> None:
        (stage,) = _analyze([{"label": "S", "patterns": ["^step$"]}], cold_calls=["^leaf$"])
        assert "leaf" not in stage.functions


class TestOverheadStages:
    @pytest.mark.parametrize(("cortex", "low", "high"), [("m4", 12, 29), ("m0", 16, 16)])
    def test_exception_entry_uses_variant_overhead(self, cortex: str, low: int, high: int) -> None:
        config = {"path_stages": [{"label": "ISR Entry", "type": "exception_entry"}], "cortex": cortex}
        (stage,) = analyze_stages(config, [], {})
        assert stage.is_overhead is True
        assert (stage.min_cycles, stage.max_cycles) == (low, high)

    def test_exception_exit_stage(self) -> None:
        config = {"path_stages": [{"label": "ISR Exit", "type": "exception_exit"}], "cortex": "m7"}
        (stage,) = analyze_stages(config, [], {})
        assert stage.is_overhead is True
        assert stage.min_cycles == 12


class TestStrictness:
    def test_strict_failure_raises(self) -> None:
        with pytest.raises(StageMatchError):
            _analyze([{"label": "Missing", "patterns": ["^never_matches$"]}])

    def test_non_strict_does_not_raise(self) -> None:
        config = {"path_stages": [{"label": "Missing", "patterns": ["^never_matches$"]}]}
        (stage,) = analyze_stages(config, [], {}, strict=False)
        assert stage.min_cycles == 0

    def test_optional_stage_not_required(self) -> None:
        (stage,) = _analyze([{"label": "Opt", "patterns": ["^never$"], "required": False}])
        assert stage.functions == []


class TestPathBreakdown:
    def test_counts_calls_on_the_worst_path(self) -> None:
        functions = parse_disassembly(DISASM)
        step = next(f for f in functions if f.demangled == "step")
        paths = analyze_paths(functions, [step], path_options({}))
        assert path_breakdown(paths[step.start_addr], paths) == {0x110: 1, 0x120: 2}
