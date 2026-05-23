"""Tests for the per-variant timing model (M0/M4/M7/M33)."""

from __future__ import annotations

import pytest

from cortex_cycle_budget.timing_model import (
    BASE_TIMING,
    EXCEPTION_OVERHEAD,
    SUPPORTED_VARIANTS,
    VARIANT_OVERRIDES,
    classify_instruction,
    get_timing,
    normalize_mnemonic,
    resolve_timing_table,
)


class TestSupportedVariants:
    def test_m4_m7_m33_and_m0_all_supported(self) -> None:
        assert {"m0", "m4", "m7", "m33"} == SUPPORTED_VARIANTS

    @pytest.mark.parametrize("variant", sorted(SUPPORTED_VARIANTS))
    def test_each_variant_has_exception_overhead(self, variant: str) -> None:
        ov = EXCEPTION_OVERHEAD[variant]
        for key in ("entry_min", "entry_max", "exit_min", "exit_max", "tail_chain"):
            assert key in ov
            assert ov[key] >= 0

    @pytest.mark.parametrize("variant", sorted(SUPPORTED_VARIANTS))
    def test_each_variant_has_override_table(self, variant: str) -> None:
        assert variant in VARIANT_OVERRIDES


class TestResolveTimingTable:
    def test_invalid_variant_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported Cortex variant"):
            resolve_timing_table("m99")

    def test_m4_baseline_matches_base(self) -> None:
        assert resolve_timing_table("m4") == BASE_TIMING

    def test_m7_overrides_vsqrt_and_vdiv(self) -> None:
        t = resolve_timing_table("m7")
        assert t["vsqrt.f32"] == (7, 7)
        assert t["vdiv.f32"] == (7, 7)
        # Base entries still present
        assert t["add"] == (1, 1)

    def test_m7_overrides_integer_divide(self) -> None:
        t = resolve_timing_table("m7")
        assert t["sdiv"] == (2, 7)
        assert t["udiv"] == (2, 7)

    def test_m0_disables_hardware_divide(self) -> None:
        t = resolve_timing_table("m0")
        # M0 has no hardware divide — entries present but zeroed out
        assert t["sdiv"] == (0, 0)
        assert t["udiv"] == (0, 0)

    def test_m33_matches_m4_for_fpu(self) -> None:
        t = resolve_timing_table("m33")
        assert t["vsqrt.f32"] == (14, 14)
        assert t["vdiv.f32"] == (14, 14)

    def test_base_timing_is_not_mutated(self) -> None:
        snapshot = dict(BASE_TIMING)
        _ = resolve_timing_table("m7")
        assert snapshot == BASE_TIMING


class TestNormalizeMnemonic:
    def test_direct_match(self) -> None:
        assert normalize_mnemonic("add") == "add"

    def test_uppercase_normalized(self) -> None:
        assert normalize_mnemonic("ADD") == "add"

    def test_whitespace_stripped(self) -> None:
        assert normalize_mnemonic("  mov  ") == "mov"

    def test_wide_suffix_recognized(self) -> None:
        assert normalize_mnemonic("ldr.w") == "ldr.w"

    def test_conditional_suffix_stripped(self) -> None:
        # `addeq` → `add`
        assert normalize_mnemonic("addeq") == "add"
        assert normalize_mnemonic("movne") == "mov"

    def test_unknown_returned_as_is(self) -> None:
        assert normalize_mnemonic("frobnicate") == "frobnicate"


class TestClassifyInstruction:
    @pytest.mark.parametrize("mn", ["vadd.f32", "vmul.f32", "vfma.f32", "vsqrt.f32"])
    def test_fpu(self, mn: str) -> None:
        assert classify_instruction(mn) == "fpu"

    @pytest.mark.parametrize("mn", ["vldr", "vstr", "vpush", "vpop"])
    def test_fpu_load_store(self, mn: str) -> None:
        assert classify_instruction(mn) == "load_store"

    @pytest.mark.parametrize("mn", ["ldr", "str", "ldm", "stm", "push", "pop"])
    def test_integer_load_store(self, mn: str) -> None:
        assert classify_instruction(mn) == "load_store"

    @pytest.mark.parametrize("mn", ["b", "bl", "blx", "bx", "cbz", "tbb"])
    def test_branch(self, mn: str) -> None:
        assert classify_instruction(mn) == "branch"

    @pytest.mark.parametrize("mn", ["bic", "bics", "bfi", "bfc"])
    def test_bit_ops_not_branch(self, mn: str) -> None:
        assert classify_instruction(mn) == "alu"

    @pytest.mark.parametrize("mn", ["mul", "mla", "smull", "sdiv", "udiv"])
    def test_mul_div(self, mn: str) -> None:
        assert classify_instruction(mn) == "mul_div"

    @pytest.mark.parametrize("mn", ["add", "sub", "mov", "and", "orr"])
    def test_alu(self, mn: str) -> None:
        assert classify_instruction(mn) == "alu"


class TestGetTiming:
    def test_known_instruction_default_m4(self) -> None:
        assert get_timing("vsqrt.f32") == (14, 14)

    def test_known_instruction_m7(self) -> None:
        t = resolve_timing_table("m7")
        assert get_timing("vsqrt.f32", t) == (7, 7)

    def test_unknown_fpu_heuristic(self) -> None:
        assert get_timing("vfoo.f32") == (1, 2)

    def test_unknown_load_heuristic(self) -> None:
        assert get_timing("ldrxyz") == (2, 2)

    def test_unknown_branch_heuristic(self) -> None:
        assert get_timing("bweird") == (1, 4)

    def test_unknown_alu_heuristic(self) -> None:
        assert get_timing("frobnicate") == (1, 1)
