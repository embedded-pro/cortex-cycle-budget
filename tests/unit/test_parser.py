"""Tests for the disassembly parser."""

from __future__ import annotations

from cortex_cycle_budget.parser import parse_disassembly
from cortex_cycle_budget.timing_model import resolve_timing_table

SAMPLE_DISASM = """\

example.elf:     file format elf32-littlearm


Disassembly of section .text:

00000100 <foo>:
     100:	b500      	push	{lr}
     102:	2001      	movs	r0, #1
     104:	f000 f802 	bl	10c <bar>
     108:	bd00      	pop	{pc}
     10a:	bf00      	nop

0000010c <bar>:
     10c:	4770      	bx	lr

00000110 <fpu_user>:
     110:	ee70 0a00 	vsub.f32	s1, s0, s0
     114:	eeb1 0bc1 	vsqrt.f32	s0, s2
     118:	4770      	bx	lr
"""


class TestParseDisassembly:
    def test_function_count(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        assert len(fns) == 3
        assert [f.demangled for f in fns] == ["foo", "bar", "fpu_user"]

    def test_function_addresses(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        foo, bar, fpu = fns
        assert foo.start_addr == 0x100
        assert bar.start_addr == 0x10C
        assert fpu.start_addr == 0x110

    def test_instruction_counts(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        foo, bar, fpu = fns
        assert foo.instruction_count == 5
        assert bar.instruction_count == 1
        assert fpu.instruction_count == 3

    def test_call_extracted_from_bl(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        foo = fns[0]
        assert "bar" in foo.calls

    def test_classification_counts(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        foo = fns[0]
        # push, movs, bl, pop, nop  → 1 load/store (push), 1 alu (movs),
        # 1 branch (bl), 1 load/store (pop), 1 alu (nop)
        assert foo.load_store_ops == 2
        assert foo.branch_ops == 1
        assert foo.alu_ops == 2
        fpu = fns[2]
        assert fpu.fpu_ops == 2
        assert fpu.branch_ops == 1  # bx lr

    def test_min_max_cycles_m4_default(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        fpu = fns[2]
        # vsub.f32 (1,1) + vsqrt.f32 (14,14) + bx (1,4)
        assert fpu.total_min_cycles == 1 + 14 + 1
        assert fpu.total_max_cycles == 1 + 14 + 4

    def test_min_max_cycles_m7_variant(self) -> None:
        timing = resolve_timing_table("m7")
        fns = parse_disassembly(SAMPLE_DISASM, timing=timing)
        fpu = fns[2]
        # On M7 vsqrt.f32 = 7
        assert fpu.total_min_cycles == 1 + 7 + 1
        assert fpu.total_max_cycles == 1 + 7 + 4

    def test_code_size_summed(self) -> None:
        fns = parse_disassembly(SAMPLE_DISASM)
        bar = fns[1]
        # bx lr is 2 bytes (one 16-bit Thumb instruction)
        assert bar.code_size == 2

    def test_empty_input(self) -> None:
        assert parse_disassembly("") == []

    def test_orphan_instructions_ignored(self) -> None:
        # Instructions before any function header are skipped
        garbage = "     100:	bf00      	nop\n"
        assert parse_disassembly(garbage) == []
