# Path analysis

A stage is charged the **worst path** through the functions it names, not the
sum of their instructions. This page says what that means and where the
analysis stops.

---

## One function

The disassembly of a function becomes a control-flow graph with one node per
instruction. The cost of the function is the costliest path from its first
instruction to a return.

| Construct                         | How it is charged                                                          |
| --------------------------------- | -------------------------------------------------------------------------- |
| Conditional branch                | Taken: the table cost. Not taken: 1 cycle. The path takes the costlier way. |
| `if`/`else`, `switch`             | Only the costliest arm. `tbb`/`tbh` tables are read from the disassembly.  |
| Direct call (`bl`, tail `b`)      | The callee's own worst path, at every call site on the path.               |
| Call through a register (`blx r3`) | The instruction only. The target is unknown and is **not** followed.       |
| Loop                              | The body once, unless `loop_bounds` gives the function a bound.            |
| Call that never returns (`abort`) | The path ends there and is not a candidate for the worst path.             |
| Literal pools, jump tables        | Data: never on a path, never charged.                                      |

The minimum is the cheapest path to a return, with every branch at its
minimum cost.

A function whose jump table cannot be read falls back to the sum of all its
instructions, and the report says so.

---

## One stage

Every function a stage matches is a **root**, unless another matched function
calls it directly: then it is already on that function's path.

- `"combine": "sum"` (default) — the roots run one after the other; the stage
  is charged all of them.
- `"combine": "max"` — the roots are alternatives, of which one runs; the
  stage is charged the costliest.

```json
{
  "label": "Control mode",
  "combine": "max",
  "patterns": ["^torque_step$", "^speed_step$", "^position_step$"]
}
```

With `entry`, the only root is the function `entry` selects.

### Which stage a function is charged to

A function on a worst path is charged to the stage that names it. A function
no stage names is charged to the stage of its caller.

```json
"path_stages": [
  {"label": "Dispatch", "patterns": ["^isr$"]},
  {"label": "Control",  "patterns": ["^control_step$"]}
]
```

If `isr` calls `control_step` directly, `control_step` and what it calls are
charged to *Control*, and *Dispatch* holds the rest of `isr`. The total is the
same however the stages are cut.

---

## Loops

A loop the analysis cannot bound is charged for one iteration and listed under
*Analysis Notes*. Give the function a bound to charge more:

```json
"loop_bounds": { "^drain_fifo$": 6 }
```

Every loop in a function matching the regex is charged that many iterations,
so nested loops multiply: with a bound of 3, the body of a loop inside a loop
is charged 9 times. A bound larger than the real one keeps the estimate an
upper bound.

### One bound per loop

A function whose loops run different numbers of times takes a list, one bound
per loop:

```json
"loop_bounds": { "^matrix_update$": [3, 3, 9] }
```

The bounds follow the loops in address order, by the first instruction of each
loop. A loop inside another still multiplies: its body is charged its own
bound times the bound of every loop around it. Here the first loop runs 3
times, the second, nested in it, 3 times per pass and so 9 times in all, and
the third 9 times.

The *Loops* table of the full report lists every loop of each charged
function in that order, with its address, its nesting depth, its size and the
iterations it was charged. Read the order and the nesting from there, and
find each loop in the annotated disassembly by its address.

The list is tied to the code the compiler generated. If it names a different
number of bounds than the function has loops, every loop is charged the
largest bound in the list and the report says so. Correct the list after a
change to the function, the compiler or its options.

---

## Paths that are not part of an iteration

A path that calls a function matching `cold_calls` is left out of the worst
path, as are paths that end in a function that never returns.

```json
"cold_calls": ["^trip_over_current$", "^assert_failed$"]
```

Use it for fault handling that stops the loop. Do not use it for work the
loop does on some iterations: that work belongs in the worst case.

---

## What the notes mean

The full report ends with *Analysis Notes*. Each one is something the estimate
does not include or had to assume.

| Note                                                      | What to do                                                       |
| --------------------------------------------------------- | ---------------------------------------------------------------- |
| calls through a register are not followed                 | Name the function it reaches in a stage. Callbacks, virtual calls. |
| loops are charged for one iteration                       | Add the function to `loop_bounds`.                               |
| `loop_bounds` lists a different number of bounds …        | Rewrite the list from the *Loops* table of the report.           |
| alternative … is not charged                              | Expected with `"combine": "max"`.                                |
| … is not on the worst path of …, which calls it           | Its caller's worst path does not reach it. Nothing to do.        |
| … is already charged to stage …                           | Two stages match it. Remove it from one.                         |
| control flow not resolved, every instruction is charged   | A jump table could not be read; the function is over-estimated.  |

---

## Limits

- A loop bound applies to every loop of its function; loops of different
  lengths in one function all take the largest.
- Recursive calls are charged once.
- Indirect calls and jumps are never resolved.
- No cache, flash wait-state, or bus model: see
  [timing-model.md](timing-model.md).

For the cycles a path really takes, measure it on hardware with DWT.
