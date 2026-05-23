"""
ARM Cortex-M instruction timing model.

Supports the following variants:

* ``m0``  — ARMv6-M / Cortex-M0 / Cortex-M0+
* ``m4``  — ARMv7E-M / Cortex-M4 (with optional FPv4-SP-D16)
* ``m7``  — ARMv7E-M / Cortex-M7 (with FPv5-SP/DP, dual-issue capable)
* ``m33`` — ARMv8-M Mainline / Cortex-M33 (with FPv5-SP)

References:
    * ARM Cortex-M0  TRM (DDI0432C)
    * ARM Cortex-M4  TRM (DDI0439D) §3
    * ARM Cortex-M7  TRM (DDI0489F) §6  — single FPU latencies, dual-issue
    * ARM Cortex-M33 TRM (DDI0479D) §A
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# Supported variants
# ──────────────────────────────────────────────────────────────────────────────

SUPPORTED_VARIANTS: frozenset[str] = frozenset({"m0", "m4", "m7", "m33"})


# ──────────────────────────────────────────────────────────────────────────────
# Base (variant-agnostic) instruction timing table  (min, max) cycles
# ──────────────────────────────────────────────────────────────────────────────

BASE_TIMING: dict[str, tuple[int, int]] = {
    # ── Integer Data Processing ───────────────────────────────────────────
    "add": (1, 1), "adds": (1, 1), "adc": (1, 1), "adcs": (1, 1),
    "sub": (1, 1), "subs": (1, 1), "sbc": (1, 1), "sbcs": (1, 1),
    "rsb": (1, 1), "rsbs": (1, 1), "rsc": (1, 1),
    "and": (1, 1), "ands": (1, 1), "orr": (1, 1), "orrs": (1, 1),
    "eor": (1, 1), "eors": (1, 1), "bic": (1, 1), "bics": (1, 1),
    "orn": (1, 1), "orns": (1, 1),
    "mov": (1, 1), "movs": (1, 1), "mvn": (1, 1), "mvns": (1, 1),
    "movw": (1, 1), "movt": (1, 1),
    "cmp": (1, 1), "cmn": (1, 1), "tst": (1, 1), "teq": (1, 1),
    # ── Shift / Rotate ────────────────────────────────────────────────────
    "lsl": (1, 1), "lsls": (1, 1), "lsr": (1, 1), "lsrs": (1, 1),
    "asr": (1, 1), "asrs": (1, 1), "ror": (1, 1), "rors": (1, 1),
    "rrx": (1, 1),
    # ── Multiply ──────────────────────────────────────────────────────────
    "mul": (1, 1), "muls": (1, 1), "mla": (1, 1), "mls": (1, 1),
    "smull": (1, 1), "umull": (1, 1), "smlal": (1, 1), "umlal": (1, 1),
    "smulbb": (1, 1), "smulbt": (1, 1), "smultb": (1, 1), "smultt": (1, 1),
    "smlabb": (1, 1), "smlabt": (1, 1), "smlatb": (1, 1), "smlatt": (1, 1),
    "smulwb": (1, 1), "smulwt": (1, 1), "smlawb": (1, 1), "smlawt": (1, 1),
    # ── Division ──────────────────────────────────────────────────────────
    "sdiv": (2, 12), "udiv": (2, 12),
    # ── Saturating / Packing / Extend ─────────────────────────────────────
    "ssat": (1, 1), "usat": (1, 1),
    "qadd": (1, 1), "qsub": (1, 1), "qdadd": (1, 1), "qdsub": (1, 1),
    "pkhbt": (1, 1), "pkhtb": (1, 1),
    "sxtb": (1, 1), "sxth": (1, 1), "uxtb": (1, 1), "uxth": (1, 1),
    "sxtab": (1, 1), "sxtah": (1, 1), "uxtab": (1, 1), "uxtah": (1, 1),
    "sxtb16": (1, 1), "uxtb16": (1, 1),
    "sbfx": (1, 1), "ubfx": (1, 1), "bfi": (1, 1), "bfc": (1, 1),
    # ── Bit manipulation ─────────────────────────────────────────────────
    "rev": (1, 1), "rev16": (1, 1), "revsh": (1, 1), "rbit": (1, 1),
    "clz": (1, 1),
    # ── Load single ──────────────────────────────────────────────────────
    "ldr": (2, 2), "ldrb": (2, 2), "ldrh": (2, 2),
    "ldrsb": (2, 2), "ldrsh": (2, 2), "ldrd": (2, 2),
    "ldr.w": (2, 2), "ldrb.w": (2, 2), "ldrh.w": (2, 2),
    # ── Store single ─────────────────────────────────────────────────────
    "str": (2, 2), "strb": (2, 2), "strh": (2, 2), "strd": (2, 2),
    "str.w": (2, 2), "strb.w": (2, 2), "strh.w": (2, 2),
    # ── Load / Store multiple ────────────────────────────────────────────
    "ldm": (1, 2), "ldmia": (1, 2), "ldmdb": (1, 2),
    "stm": (1, 2), "stmia": (1, 2), "stmdb": (1, 2),
    "push": (1, 2), "pop": (1, 2),
    # ── Branch ───────────────────────────────────────────────────────────
    "b": (1, 4), "b.w": (1, 4), "b.n": (1, 4),
    "bx": (1, 4),
    "bl": (1, 4), "blx": (1, 4),
    "bne": (1, 4), "bne.n": (1, 4), "bne.w": (1, 4),
    "beq": (1, 4), "beq.n": (1, 4), "beq.w": (1, 4),
    "blt": (1, 4), "blt.n": (1, 4), "blt.w": (1, 4),
    "bgt": (1, 4), "bgt.n": (1, 4), "bgt.w": (1, 4),
    "ble": (1, 4), "ble.n": (1, 4), "ble.w": (1, 4),
    "bge": (1, 4), "bge.n": (1, 4), "bge.w": (1, 4),
    "bhi": (1, 4), "bhi.n": (1, 4), "bhi.w": (1, 4),
    "bls": (1, 4), "bls.n": (1, 4), "bls.w": (1, 4),
    "bcc": (1, 4), "bcc.n": (1, 4), "bcc.w": (1, 4),
    "bcs": (1, 4), "bcs.n": (1, 4), "bcs.w": (1, 4),
    "bmi": (1, 4), "bmi.n": (1, 4), "bmi.w": (1, 4),
    "bpl": (1, 4), "bpl.n": (1, 4), "bpl.w": (1, 4),
    "bvs": (1, 4), "bvs.n": (1, 4), "bvs.w": (1, 4),
    "bvc": (1, 4), "bvc.n": (1, 4), "bvc.w": (1, 4),
    "cbz": (1, 4), "cbnz": (1, 4),
    "tbb": (2, 4), "tbh": (2, 4),
    # ── IT (conditional execution) ───────────────────────────────────────
    "it": (1, 1), "ite": (1, 1), "itt": (1, 1),
    "ittt": (1, 1), "itte": (1, 1), "itet": (1, 1), "itee": (1, 1),
    # ── Misc ─────────────────────────────────────────────────────────────
    "nop": (1, 1), "svc": (1, 1), "bkpt": (1, 1),
    "dmb": (1, 4), "dsb": (1, 4), "isb": (1, 4),
    "cpsie": (1, 2), "cpsid": (1, 2),
    "mrs": (2, 2), "msr": (2, 2),
    # ── FPv4-SP-D16  (default: Cortex-M4 single-precision HW FPU) ────────
    "vadd.f32": (1, 1), "vsub.f32": (1, 1),
    "vmul.f32": (1, 1), "vnmul.f32": (1, 1),
    "vfma.f32": (1, 1), "vfms.f32": (1, 1),
    "vfnma.f32": (1, 1), "vfnms.f32": (1, 1),
    "vmla.f32": (3, 3), "vmls.f32": (3, 3),
    "vneg.f32": (1, 1), "vabs.f32": (1, 1),
    "vcmp.f32": (1, 1), "vcmpe.f32": (1, 1),
    "vmov": (1, 1), "vmov.f32": (1, 1), "vmov.f64": (1, 1),
    "vcvt.f32.s32": (1, 1), "vcvt.s32.f32": (1, 1),
    "vcvt.f32.u32": (1, 1), "vcvt.u32.f32": (1, 1),
    "vcvt.f64.f32": (1, 1), "vcvt.f32.f64": (1, 1),
    "vcvtr.s32.f32": (1, 1), "vcvtr.u32.f32": (1, 1),
    "vcvt.f32.s16": (1, 1), "vcvt.f32.u16": (1, 1),
    "vsqrt.f32": (14, 14),
    "vdiv.f32": (14, 14),
    "vldr": (2, 2), "vldr.32": (2, 2),
    "vstr": (2, 2), "vstr.32": (2, 2),
    "vpush": (1, 2), "vpop": (1, 2),
    "vmrs": (1, 1), "vmsr": (1, 1),
    "vldm": (1, 2), "vldmia": (1, 2), "vldmdb": (1, 2),
    "vstm": (1, 2), "vstmia": (1, 2), "vstmdb": (1, 2),
    "vsel.f32": (1, 1),
    "vmaxnm.f32": (1, 1), "vminnm.f32": (1, 1),
}


# ──────────────────────────────────────────────────────────────────────────────
# Per-variant timing overrides (applied on top of BASE_TIMING)
# ──────────────────────────────────────────────────────────────────────────────

VARIANT_OVERRIDES: dict[str, dict[str, tuple[int, int]]] = {
    # Cortex-M0: no Thumb-2, no hardware divide, no DSP, no FPU. Most
    # instructions fall through to BASE; we override the multiply latencies
    # (single-cycle MUL is a Cortex-M0+ option; classic M0 is 32-cycle).
    # Conservative range covers both.
    "m0": {
        "mul": (1, 32),
        "muls": (1, 32),
        # No hardware divide on M0
        "sdiv": (0, 0),
        "udiv": (0, 0),
    },

    # Cortex-M4: baseline matches BASE_TIMING — no overrides required.
    "m4": {},

    # Cortex-M7: FPv5 has faster vsqrt / vdiv. The dual-issue pipeline is
    # not modeled by default (see analyze with dual_issue=True for an
    # opt-in 0.85x scaling on min cycles).
    # Reference: ARM Cortex-M7 TRM DDI0489F Table 6-2.
    "m7": {
        # FPU
        "vsqrt.f32": (7, 7),     # M4: 14
        "vdiv.f32": (7, 7),      # M4: 14
        "vmla.f32": (3, 3),      # same
        # Integer divide is faster on M7 (2..7 cycles vs M4's 2..12)
        "sdiv": (2, 7),
        "udiv": (2, 7),
    },

    # Cortex-M33: ARMv8-M Mainline with FPv5-SP-D16. Same FPU latencies
    # as M4 for the supported instruction subset.
    "m33": {},
}


# ──────────────────────────────────────────────────────────────────────────────
# Cortex-M exception entry/exit overhead (cycles)
# ──────────────────────────────────────────────────────────────────────────────

EXCEPTION_OVERHEAD: dict[str, dict[str, int]] = {
    "m0": {
        "entry_min": 16, "entry_max": 16,
        "exit_min": 16,  "exit_max": 16,
        "tail_chain": 6,
    },
    "m4": {
        "entry_min": 12,   # Integer-only context (R0-R3,R12,LR,PC,xPSR)
        "entry_max": 29,   # With FPU lazy stacking (+ S0-S15, FPSCR)
        "exit_min": 12,
        "exit_max": 29,
        "tail_chain": 6,
    },
    "m7": {
        # M7 has slightly lower minimum due to faster bus, but worst-case
        # with FPU lazy stacking matches M4.
        "entry_min": 12,
        "entry_max": 29,
        "exit_min": 12,
        "exit_max": 29,
        "tail_chain": 6,
    },
    "m33": {
        "entry_min": 12,
        "entry_max": 29,
        "exit_min": 12,
        "exit_max": 29,
        "tail_chain": 6,
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Cortex-M7 dual-issue opt-in scaling factor (applied to min cycles)
# ──────────────────────────────────────────────────────────────────────────────

DUAL_ISSUE_MIN_SCALE: dict[str, float] = {
    # Empirical: ~15% of integer pairs in straight-line code can dual-issue
    # on the M7 (ALU + load/store, ALU + branch). Conservative default.
    "m7": 0.85,
}


# ──────────────────────────────────────────────────────────────────────────────
# Conditional suffixes (for normalize_mnemonic)
# ──────────────────────────────────────────────────────────────────────────────

COND_SUFFIXES: list[str] = [
    "eq", "ne", "cs", "hs", "cc", "lo",
    "mi", "pl", "vs", "vc", "hi", "ls",
    "ge", "lt", "gt", "le", "al",
]


# ──────────────────────────────────────────────────────────────────────────────
# Resolved table for the historical default variant (M4)
# ──────────────────────────────────────────────────────────────────────────────

def resolve_timing_table(variant: str = "m4") -> dict[str, tuple[int, int]]:
    """Return BASE_TIMING merged with the variant-specific overrides.

    Raises:
        ValueError: if *variant* is not in :data:`SUPPORTED_VARIANTS`.
    """
    if variant not in SUPPORTED_VARIANTS:
        valid = ", ".join(sorted(SUPPORTED_VARIANTS))
        raise ValueError(f"Unsupported Cortex variant '{variant}'. Valid: {valid}")
    merged = dict(BASE_TIMING)
    merged.update(VARIANT_OVERRIDES[variant])
    return merged


# Backwards-compatible alias used by the historical API.
TIMING: dict[str, tuple[int, int]] = resolve_timing_table("m4")


# ──────────────────────────────────────────────────────────────────────────────
# Instruction helpers
# ──────────────────────────────────────────────────────────────────────────────

def normalize_mnemonic(
    mnemonic: str,
    timing: dict[str, tuple[int, int]] | None = None,
) -> str:
    """Normalize a mnemonic to a key present in *timing* (default: M4 TIMING)."""
    table = TIMING if timing is None else timing
    m = mnemonic.lower().strip()
    if m in table:
        return m
    for suffix in (".w", ".n"):
        if (m + suffix) in table:
            return m + suffix
    base = m.rstrip(".wn")
    if base in table:
        return base
    if len(m) > 3:
        for cond in COND_SUFFIXES:
            if m.endswith(cond):
                base_cond = m[: -len(cond)]
                if base_cond in table:
                    return base_cond
    return m


def classify_instruction(mnemonic: str) -> str:
    """Return one of: ``fpu``, ``load_store``, ``branch``, ``mul_div``, ``alu``."""
    m = mnemonic.lower()
    if m.startswith("v"):
        if any(x in m for x in ("ldr", "str", "push", "pop", "ldm", "stm")):
            return "load_store"
        return "fpu"
    if any(m.startswith(x) for x in ("ldr", "str", "ldm", "stm", "push", "pop")):
        return "load_store"
    if any(m.startswith(x) for x in ("b", "bl", "bx", "cb", "tb")):
        if m in ("bic", "bics", "bfi", "bfc"):
            return "alu"
        return "branch"
    if any(m.startswith(x) for x in (
        "mul", "mla", "mls", "smul", "umul", "smlal", "umlal", "sdiv", "udiv",
    )):
        return "mul_div"
    return "alu"


def get_timing(
    mnemonic: str,
    timing: dict[str, tuple[int, int]] | None = None,
) -> tuple[int, int]:
    """Look up (min, max) cycles for *mnemonic* in *timing* (default: M4)."""
    table = TIMING if timing is None else timing
    normalized = normalize_mnemonic(mnemonic, table)
    if normalized in table:
        return table[normalized]
    m = mnemonic.lower()
    if m.startswith("v"):
        return (1, 2)
    if "ldr" in m or "str" in m:
        return (2, 2)
    if m.startswith("b") and m not in ("bic", "bics", "bfi", "bfc"):
        return (1, 4)
    return (1, 1)
