# Configuration schema

The JSON config file describes one **critical path** as an ordered sequence of
**stages**. Each stage selects functions by regex; the analyzer attributes
their cycle costs to that stage.

A machine-readable JSON Schema lives at
[cycle-analysis.schema.json](cycle-analysis.schema.json).

---

## Top-level fields

| Field            | Type                | Required | Description                                                                 |
| ---------------- | ------------------- | :------: | --------------------------------------------------------------------------- |
| `path_stages`    | array               |    ✅    | Non-empty list of stage objects (see below).                                |
| `path_name`      | string              |    ⬜    | Human-readable name shown in reports.                                       |
| `loop_rates_khz` | array<int>          |    ⬜    | Loop rates (positive integers) for the CPU budget table.                    |
| `target`         | string              |    ⬜    | Overridden by `--target`.                                                   |
| `build_config`   | string              |    ⬜    | Overridden by `--build-config`.                                             |
| `clock_mhz`      | integer             |    ⬜    | Overridden by `--clock-mhz`.                                                |
| `cortex`         | enum                |    ⬜    | One of `m0`, `m4`, `m7`, `m33`. Overridden by `--cortex`.                   |

---

## Stage object

Each entry of `path_stages` is one of two shapes.

### 1. Pattern stage

Matches all functions whose demangled name matches **any** of the regex
patterns in `patterns`.

```json
{
  "label": "ADC Read",
  "patterns": ["^adc_read$", "^adc_read_v2$"],
  "entry": "^adc_read$",
  "required": true
}
```

| Field      | Type            | Required | Description                                                                                          |
| ---------- | --------------- | :------: | ---------------------------------------------------------------------------------------------------- |
| `label`    | string          |    ✅    | Display name in reports.                                                                             |
| `patterns` | array<string>   |    ✅    | Function-name regexes (Python `re` syntax).                                                          |
| `entry`    | string          |    ⬜    | Regex selecting the **call-graph entry** for this stage. When set, the analyzer walks all callees.   |
| `required` | bool            |    ⬜    | When `false`, a stage that matches nothing does not fail strict mode. Default: `true`.               |

### 2. Architectural stage

Charges per-variant exception overhead (no patterns needed).

```json
{ "label": "ISR Entry", "type": "exception_entry" }
{ "label": "ISR Exit",  "type": "exception_exit"  }
```

| `type` value        | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `exception_entry`   | Adds `EXCEPTION_OVERHEAD[cortex].entry_{min,max}` cycles |
| `exception_exit`    | Adds `EXCEPTION_OVERHEAD[cortex].exit_{min,max}` cycles  |

See [timing-model.md](timing-model.md) for the per-variant values.

---

## Examples

### Minimal pattern-only

```json
{
  "path_name": "PID Loop",
  "loop_rates_khz": [20],
  "path_stages": [
    {"label": "Compute", "patterns": ["^pid_compute$"]}
  ]
}
```

### Call-graph walk

When `entry` is provided, the analyzer attributes cycles for **every** callee
reachable from the entry, not just functions matching `patterns`.

```json
{
  "path_name": "FOC Step",
  "path_stages": [
    {
      "label": "FOC math",
      "entry": "^foc_step$",
      "patterns": ["^foc_step$"]
    }
  ]
}
```

### ISR with architectural overhead

```json
{
  "loop_rates_khz": [10],
  "path_stages": [
    {"label": "Entry",  "type": "exception_entry"},
    {"label": "Handler","entry": "^my_isr$", "patterns": ["^my_isr$"]},
    {"label": "Exit",   "type": "exception_exit"}
  ]
}
```

---

## Validation

The CLI calls `validate_config()` before analysis. Errors include:

- Missing or empty `path_stages`.
- Stage with neither `type` nor `patterns`.
- Invalid `type` value.
- Unparseable `patterns` or `entry` regex.
- Non-positive `loop_rates_khz` entries.
- `cortex` not in `{m0, m4, m7, m33}`.
- `clock_mhz <= 0`.

All errors are aggregated and raised as a single `ConfigError`.
