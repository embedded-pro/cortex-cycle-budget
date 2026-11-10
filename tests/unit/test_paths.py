"""Tests for the worst-case path analysis."""

from __future__ import annotations

from cortex_cycle_budget.models import Function, FunctionPath
from cortex_cycle_budget.parser import parse_disassembly
from cortex_cycle_budget.paths import PathOptions, analyze_paths, classify_flow, direct_callees


def _functions(*bodies: str) -> list[Function]:
    return parse_disassembly("\n".join(bodies))


def _path(functions: list[Function], name: str, options: PathOptions | None = None) -> FunctionPath:
    root = next(f for f in functions if f.demangled == name)
    return analyze_paths(functions, [root], options)[root.start_addr]


STRAIGHT = """
00000100 <straight>:
     100:	2001      	movs	r0, #1
     102:	3001      	adds	r0, #1
     104:	4770      	bx	lr
"""

# The long arm falls through the branch (1 cycle); the short arm takes it (up to 4).
BRANCHY = """
00000200 <branchy>:
     200:	2800      	cmp	r0, #0
     202:	d005      	beq.n	210 <branchy+0x10>
     204:	3001      	adds	r0, #1
     206:	3001      	adds	r0, #1
     208:	3001      	adds	r0, #1
     20a:	3001      	adds	r0, #1
     20c:	3001      	adds	r0, #1
     20e:	4770      	bx	lr
     210:	4770      	bx	lr
"""

DO_WHILE = """
00000300 <do_while>:
     300:	2300      	movs	r3, #0
     302:	3301      	adds	r3, #1
     304:	2b04      	cmp	r3, #4
     306:	d1fc      	bne.n	302 <do_while+0x2>
     308:	4770      	bx	lr
"""

# The test is at the top and the body ends in an unconditional jump back to it.
WHILE = """
00000400 <while_loop>:
     400:	2800      	cmp	r0, #0
     402:	d003      	beq.n	40c <while_loop+0xc>
     404:	3801      	subs	r0, #1
     406:	3101      	adds	r1, #1
     408:	3101      	adds	r1, #1
     40a:	e7f9      	b.n	400 <while_loop>
     40c:	4770      	bx	lr
"""

NESTED = """
00000f00 <nested>:
     f00:	2200      	movs	r2, #0
     f02:	2300      	movs	r3, #0
     f04:	3001      	adds	r0, #1
     f06:	3301      	adds	r3, #1
     f08:	2b03      	cmp	r3, #3
     f0a:	d1fb      	bne.n	f04 <nested+0x4>
     f0c:	3201      	adds	r2, #1
     f0e:	2a03      	cmp	r2, #3
     f10:	d1f7      	bne.n	f02 <nested+0x2>
     f12:	4770      	bx	lr
"""

CALLER = """
00000500 <caller>:
     500:	b510      	push	{r4, lr}
     502:	f000 f805 	bl	510 <leaf>
     506:	f000 f803 	bl	510 <leaf>
     50a:	f000 f801 	bl	510 <leaf>
     50e:	bd10      	pop	{r4, pc}

00000510 <leaf>:
     510:	3001      	adds	r0, #1
     512:	4770      	bx	lr
"""

TAIL_CALLER = """
00000600 <tail_caller>:
     600:	3001      	adds	r0, #1
     602:	f000 b801 	b.w	608 <tail_target>

00000608 <tail_target>:
     608:	3001      	adds	r0, #1
     60a:	3001      	adds	r0, #1
     60c:	4770      	bx	lr
"""

INDIRECT = """
00000700 <indirect>:
     700:	b510      	push	{r4, lr}
     702:	4798      	blx	r3
     704:	bd10      	pop	{r4, pc}
"""

# Asserting is cheap on the path that passes and long on the one that aborts.
ASSERTING = """
00000800 <asserting>:
     800:	b508      	push	{r3, lr}
     802:	2800      	cmp	r0, #0
     804:	d100      	bne.n	808 <asserting+0x8>
     806:	bd08      	pop	{r3, pc}
     808:	3001      	adds	r0, #1
     80a:	3001      	adds	r0, #1
     80c:	3001      	adds	r0, #1
     80e:	3001      	adds	r0, #1
     810:	3001      	adds	r0, #1
     812:	3001      	adds	r0, #1
     814:	f000 f802 	bl	81c <abort>
     818:	bf00      	nop
     81a:	bf00      	nop

0000081c <abort>:
     81c:	e7fe      	b.n	81c <abort>
"""

FAULT_PATH = """
00000900 <guarded>:
     900:	b508      	push	{r3, lr}
     902:	2800      	cmp	r0, #0
     904:	d001      	beq.n	90a <guarded+0xa>
     906:	f000 f803 	bl	910 <trip>
     90a:	3001      	adds	r0, #1
     90c:	bd08      	pop	{r3, pc}
     90e:	bf00      	nop

00000910 <trip>:
     910:	3001      	adds	r0, #1
     912:	3001      	adds	r0, #1
     914:	3001      	adds	r0, #1
     916:	3001      	adds	r0, #1
     918:	4770      	bx	lr
"""

# Three table entries; the third arm is the longest.
JUMP_TABLE = """
00000a00 <switchy>:
     a00:	2802      	cmp	r0, #2
     a02:	d809      	bhi.n	a18 <switchy+0x18>
     a04:	e8df f000 	tbb	[pc, r0]
     a08:	0402      	.short	0x0402
     a0a:	0006      	.short	0x0006
     a0c:	3001      	adds	r0, #1
     a0e:	4770      	bx	lr
     a10:	3002      	adds	r0, #2
     a12:	4770      	bx	lr
     a14:	3003      	adds	r0, #3
     a16:	3003      	adds	r0, #3
     a18:	4770      	bx	lr
"""

OPAQUE_TABLE = """
00000b00 <opaque>:
     b00:	e8df f000 	tbb	[pc, r0]
     b04:	3001      	adds	r0, #1
     b06:	4770      	bx	lr
"""

LITERAL_POOL = """
00000c00 <with_pool>:
     c00:	4b01      	ldr	r3, [pc, #4]	@ (c08 <void Invoke<{lambda()#1}>()+0x8>)
     c02:	6818      	ldr	r0, [r3, #0]
     c04:	4770      	bx	lr
     c06:	bf00      	nop
     c08:	20000000 	.word	0x20000000
"""

RECURSIVE = """
00000d00 <recursive>:
     d00:	b508      	push	{r3, lr}
     d02:	f7ff fffd 	bl	d00 <recursive>
     d06:	bd08      	pop	{r3, pc}
"""

CONDITIONAL_RETURN = """
00000e00 <early>:
     e00:	2800      	cmp	r0, #0
     e02:	bf08      	it	eq
     e04:	4770      	bxeq	lr
     e06:	3001      	adds	r0, #1
     e08:	3001      	adds	r0, #1
     e0a:	4770      	bx	lr
"""


class TestStraightLine:
    def test_every_instruction_is_on_the_path(self) -> None:
        path = _path(_functions(STRAIGHT), "straight")
        assert path.addresses == (0x100, 0x102, 0x104)
        assert path.max_cycles == 1 + 1 + 4
        assert path.min_cycles == 1 + 1 + 1


class TestBranches:
    def test_worst_path_takes_the_costlier_arm(self) -> None:
        path = _path(_functions(BRANCHY), "branchy")
        assert path.addresses == (0x200, 0x202, 0x204, 0x206, 0x208, 0x20A, 0x20C, 0x20E)
        # cmp + branch not taken + five adds + return
        assert path.max_cycles == 1 + 1 + 5 + 4

    def test_best_path_takes_the_cheaper_arm(self) -> None:
        path = _path(_functions(BRANCHY), "branchy")
        assert path.min_cycles == 1 + 1 + 1

    def test_cost_is_below_the_whole_body(self) -> None:
        functions = _functions(BRANCHY)
        path = _path(functions, "branchy")
        assert path.max_cycles < functions[0].total_max_cycles

    def test_conditional_return_in_an_it_block_has_two_ways_on(self) -> None:
        path = _path(_functions(CONDITIONAL_RETURN), "early")
        assert path.max_cycles == 1 + 1 + 1 + 1 + 1 + 4
        assert path.min_cycles == 1 + 1 + 1


class TestLoops:
    def test_loop_body_is_charged_once_and_reported(self) -> None:
        path = _path(_functions(DO_WHILE), "do_while")
        # movs + adds + cmp + latch charged as taken + return
        assert path.max_cycles == 1 + 1 + 1 + 4 + 4
        assert path.unbounded_loops == 1
        assert path.loop_bound is None

    def test_loop_bound_multiplies_the_body(self) -> None:
        path = _path(_functions(DO_WHILE), "do_while", PathOptions(loop_bounds={"^do_while$": 4}))
        assert path.max_cycles == 1 + 4 * (1 + 1 + 4) + 4
        assert path.unbounded_loops == 0
        assert path.loop_bound == 4

    def test_loop_bound_applies_to_matching_functions_only(self) -> None:
        path = _path(_functions(DO_WHILE), "do_while", PathOptions(loop_bounds={"^other$": 4}))
        assert path.loop_bound is None

    def test_loop_bound_multiplies_through_nested_loops(self) -> None:
        path = _path(_functions(NESTED), "nested", PathOptions(loop_bounds={"^nested$": 3}))
        inner = 1 + 1 + 1 + 4
        outer_only = 1 + 1 + 1 + 4
        assert path.max_cycles == 1 + 9 * inner + 3 * outer_only + 4

    def test_nested_loops_without_a_bound_are_charged_once(self) -> None:
        path = _path(_functions(NESTED), "nested")
        assert path.max_cycles == 1 + (1 + 1 + 1 + 4) + (1 + 1 + 1 + 4) + 4
        assert path.unbounded_loops == 2

    def test_body_ending_in_a_jump_back_is_on_the_worst_path(self) -> None:
        path = _path(_functions(WHILE), "while_loop")
        assert 0x404 in path.addresses
        # test, body, jump back, then the test again and out
        body = 1 + 1 + 1 + 1 + 1 + 4
        way_out = 1 + 4 + 4
        assert path.max_cycles == body + way_out

    def test_best_path_skips_the_loop(self) -> None:
        path = _path(_functions(WHILE), "while_loop")
        assert path.min_cycles == 1 + 1 + 1


class TestCalls:
    def test_callee_is_charged_at_every_call_site(self) -> None:
        functions = _functions(CALLER)
        path = _path(functions, "caller")
        leaf = 1 + 4
        assert path.callees == ((0x510, 3),)
        assert path.own_max_cycles == 3 + 3 * 4 + (1 + 2 + 3)
        assert path.max_cycles == path.own_max_cycles + 3 * leaf

    def test_tail_call_is_followed(self) -> None:
        path = _path(_functions(TAIL_CALLER), "tail_caller")
        assert path.callees == ((0x608, 1),)
        assert path.max_cycles == (1 + 4) + (1 + 1 + 4)

    def test_call_through_a_register_is_counted_not_followed(self) -> None:
        path = _path(_functions(INDIRECT), "indirect")
        assert path.indirect_calls == 1
        assert path.callees == ()

    def test_recursion_terminates(self) -> None:
        path = _path(_functions(RECURSIVE), "recursive")
        assert path.max_cycles > 0
        assert path.callees == ()

    def test_direct_callees_lists_each_function_once(self) -> None:
        functions = _functions(CALLER)
        assert [f.demangled for f in direct_callees(functions[0], functions)] == ["leaf"]


class TestColdPaths:
    def test_path_that_never_returns_is_not_the_worst_path(self) -> None:
        path = _path(_functions(ASSERTING), "asserting")
        assert path.addresses == (0x800, 0x802, 0x804, 0x806)

    def test_function_that_only_aborts_is_charged_up_to_the_call(self) -> None:
        path = _path(_functions(ASSERTING), "abort")
        assert path.max_cycles > 0

    def test_cold_call_removes_its_path(self) -> None:
        functions = _functions(FAULT_PATH)
        hot = _path(functions, "guarded", PathOptions(cold_calls=["^trip$"]))
        assert 0x906 not in hot.addresses
        assert hot.callees == ()

    def test_without_cold_calls_the_fault_path_is_the_worst(self) -> None:
        path = _path(_functions(FAULT_PATH), "guarded")
        assert path.callees == ((0x910, 1),)


class TestJumpTables:
    def test_table_arms_are_resolved(self) -> None:
        path = _path(_functions(JUMP_TABLE), "switchy")
        assert not path.whole_body
        assert path.addresses == (0xA00, 0xA02, 0xA04, 0xA14, 0xA16, 0xA18)

    def test_unresolved_table_charges_the_whole_body(self) -> None:
        functions = _functions(OPAQUE_TABLE)
        path = _path(functions, "opaque")
        assert path.whole_body
        assert path.max_cycles == functions[0].total_max_cycles


class TestData:
    def test_literal_pool_is_not_on_the_path(self) -> None:
        path = _path(_functions(LITERAL_POOL), "with_pool")
        assert path.addresses == (0xC00, 0xC02, 0xC04)

    def test_braces_in_a_symbol_comment_are_not_a_register_list(self) -> None:
        functions = _functions(LITERAL_POOL)
        assert classify_flow(functions[0].instructions[0]).kind == "next"
