# Troubleshooting

## `ERROR: No functions found in the disassembly.`

**Causes**:

- The ELF is stripped (`-s` linker flag or `strip` post-build).
- Wrong tool used — `arm-none-eabi-objdump` ≠ system `objdump`.
- The ELF is empty or contains no `.text` section.

**Fix**: rebuild without stripping (or pass `--disasm-file` to a manually
generated disassembly).

## `ERROR: objdump tool not found: 'arm-none-eabi-objdump'`

Install the ARM toolchain:

```bash
# Ubuntu/Debian
sudo apt-get install gcc-arm-none-eabi

# macOS
brew install --cask gcc-arm-embedded
```

Or pass an explicit path:

```bash
cortex-cycle-budget … --objdump /opt/arm-toolchain/bin/arm-none-eabi-objdump
```

## `ERROR: Stage '<X>': no functions matched any of the … patterns`

Strict mode is on (the default). Either:

1. **Fix the regex** in your config (try matching against
   `full_disassembly.txt`).
2. Mark the stage `"required": false` if it is genuinely optional.
3. Add `--no-strict` to relax globally (not recommended for CI).

## My PR comment is not being posted/updated

- Make sure `permissions.pull-requests: write` is set on the workflow.
- Verify the event is `pull_request` (the action skips other events).
- Confirm the comment isn't being created by a different bot using the same
  marker. The marker is exactly `<!-- cortex-cycle-budget-comment -->`.

## M7 cycle counts seem too high

The static analyzer assumes **worst-case latency** for FPU operations and
does **not** model dual-issue or cache behavior. Real measurements on
cache-resident hot paths will often be lower.

For accurate measurements:

```c
DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
uint32_t start = DWT->CYCCNT;
critical_path();
uint32_t cycles = DWT->CYCCNT - start;
```

## `ConfigError: cortex 'm99' is not a supported variant`

Only `m0`, `m4`, `m7`, `m33` are supported. If you need another variant (M23,
M55, M85, M3), please open an issue with TRM citations for the relevant
cycle counts.

## CI fails with `--fail-over-max-cycles`

This is **intended**: the analyzer exits with code 2 when the estimated max
exceeds the threshold. To investigate:

1. Open the uploaded artifact (`cycle-analysis/`).
2. Read `cycle_estimation_report.md` for the per-stage breakdown.
3. Look at `annotated_disassembly.md` to find the hottest instructions.

## "Cannot find file: README.md" when running `pip install -e .`

The `pyproject.toml` declares `readme = "README.md"`. If you cloned a fork
without the README, create an empty placeholder or run from a complete
checkout.
