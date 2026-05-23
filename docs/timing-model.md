# Timing model

`cortex-cycle-budget` ships a static per-instruction timing table for each
supported Cortex-M variant. Each entry is a `(min, max)` cycle tuple.

The tables live in
[`src/cortex_cycle_budget/timing_model.py`](../src/cortex_cycle_budget/timing_model.py).

---

## Layered design

```text
BASE_TIMING                  ←  variant-agnostic Cortex-M instruction costs
       │
       ▼
VARIANT_OVERRIDES[variant]   ←  per-variant deltas
       │
       ▼
resolve_timing_table(variant) → final lookup table used by parser & analysis
```

`BASE_TIMING` is the **Cortex-M4 baseline** (most common reference). Each
variant in `VARIANT_OVERRIDES` lists only the entries that differ.

`TIMING` (top-level constant) is `resolve_timing_table("m4")`, kept for
backwards compatibility with code that does not yet pass a variant.

---

## Source citations

All entries are sourced from the ARM Technical Reference Manuals.

| Variant      | Source                                                          |
| ------------ | --------------------------------------------------------------- |
| Cortex-M0    | ARM DDI 0419D — *Cortex-M0 Technical Reference Manual*          |
| Cortex-M4    | ARM DDI 0439D — *Cortex-M4 Technical Reference Manual*          |
| Cortex-M7    | ARM DDI 0489F — *Cortex-M7 Technical Reference Manual*          |
| Cortex-M33   | ARM DDI 0479D — *Cortex-M33 Technical Reference Manual*         |

---

## Key per-variant differences

### FPU operations

| Operation       | M0  | M4    | M7    | M33   |
| --------------- | :-: | :---: | :---: | :---: |
| `vadd.f32`      |  —  |  1    |  1    |  1    |
| `vmul.f32`      |  —  |  1    |  1    |  1    |
| `vfma.f32`      |  —  |  3    |  3    |  3    |
| **`vsqrt.f32`** |  —  | **14**| **7** | **14**|
| **`vdiv.f32`**  |  —  | **14**| **7** | **14**|

> Cortex-M7 cuts `vsqrt`/`vdiv` cost in half thanks to a redesigned FPU
> pipeline (ARM DDI 0489F §7.5).

### Integer divide

| Operation     | M0     | M4    | M7    | M33   |
| ------------- | :----: | :---: | :---: | :---: |
| `sdiv`/`udiv` | 0 *(†)*| 2–12  | 2–7   | 2–12  |

> *(†)* Cortex-M0 has **no** hardware divide. The table holds `(0, 0)` and
> the entries are flagged in reports so users know the cost will instead
> come from a soft-divide helper (e.g., `__aeabi_uidiv`).

### Exception entry/exit overhead

| Variant | Entry (min/max) | Exit (min/max) | Tail-chain |
| ------- | :-------------: | :------------: | :--------: |
| M0      | 16 / 16         | 16 / 16        | 16         |
| M4      | 12 / 29         | 12 / 12        | 6          |
| M7      | 12 / 29         | 12 / 12        | 6          |
| M33     | 12 / 29         | 12 / 12        | 6          |

Used by the `exception_entry` / `exception_exit` stage types.

---

## Heuristics for unknown mnemonics

When `normalize_mnemonic()` does not find an exact entry (after stripping
condition suffixes and `.w`/`.n` widths), `classify_instruction()` falls back
to a prefix-based heuristic to return a sensible default:

| Prefix / family   | Default `(min, max)` |
| ----------------- | :------------------: |
| `v…` (FPU)        | `(1, 2)`             |
| `ldr…` / `vldr…`  | `(2, 2)`             |
| `str…` / `vstr…`  | `(2, 2)`             |
| `b…` (branch)     | `(1, 4)`             |
| `mul…` / `…div…`  | `(2, 5)`             |
| ALU / default     | `(1, 1)`             |

If a heuristic produces visibly wrong numbers in your reports, **please file
an issue** with the offending mnemonic — adding it to `BASE_TIMING` or the
relevant `VARIANT_OVERRIDES` entry is usually a 1-line PR.

---

## What is **not** modeled

- I-cache / D-cache hits & misses (Cortex-M7).
- AXI bus contention.
- TCM vs. external memory wait states.
- Branch prediction accuracy.
- M7 limited dual-issue at the instruction-pair level *(planned;
  see `DUAL_ISSUE_MIN_SCALE`)*.
- Speculative execution effects.

For accurate per-cycle measurement, complement this tool with
**DWT/CYCCNT** instrumentation on hardware.
