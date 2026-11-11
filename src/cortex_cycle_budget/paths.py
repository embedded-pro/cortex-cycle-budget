"""Worst-case path analysis.

Each function becomes a control-flow graph with one node per instruction. The
cost of a function is the longest path from its first instruction to a return,
with the cost of every directly called function added at its call site. A loop
body is counted once unless the configuration gives the function a loop bound,
which every loop in it then runs: nested loops multiply.
"""

from __future__ import annotations

import bisect
import heapq
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace

from cortex_cycle_budget.models import Function, FunctionPath, Instruction
from cortex_cycle_budget.timing_model import COND_SUFFIXES, is_data

# A conditional branch that is not taken, or an instruction an IT block skips.
NOT_TAKEN_CYCLES = (1, 1)

# Calls to these never return, so a path that makes one is not an iteration of
# the analysed loop.
NORETURN_FUNCTIONS: tuple[str, ...] = (
    r"^abort$",
    r"^_?exit$",
    r"^__assert_func$",
    r"^__stack_chk_fail$",
    r"^__cxa_pure_virtual$",
    r"^std::terminate\(\)$",
    r"^__aeabi_[il]div0$",
)

_EXIT = -1
_CONDITIONS = frozenset(COND_SUFFIXES) - {"al"}
_BRANCH = re.compile(rf"^(blx|bl|bx|b)({'|'.join(sorted(_CONDITIONS))})?$")
_TARGET = re.compile(r"(?:^|,\s*)([0-9a-fA-F]+)\s+<")
_TABLE_INDEX = re.compile(r"\[pc,\s*(\w+)")
_COMPARE = re.compile(r"^(\w+),\s*#(\d+)")
_RETURNING_LOADS = ("pop", "ldm", "ldr")
_TABLE_SCAN = 6


@dataclass(frozen=True)
class PathOptions:
    """Analysis settings taken from the configuration."""

    loop_bounds: Mapping[str, int] = field(default_factory=dict)
    cold_calls: Sequence[str] = ()


@dataclass(frozen=True)
class _Flow:
    kind: str  # next | jump | call | return | indirect | table | stop
    conditional: bool = False
    target: int | None = None


@dataclass(frozen=True)
class _Edge:
    dest: int
    min_cycles: int
    max_cycles: int
    callee: int | None = None
    after: int = 0  # cycles spent once after the edge, outside any loop bound


@dataclass
class _Graph:
    edges: list[list[_Edge]]
    indirect: set[int]
    unresolved: bool = False


# (address) -> (min cycles, max cycles, start address of the callee that was costed)
_CalleeCost = Callable[[int | None], tuple[int, int, int | None]]
_Choice = tuple[int, _Edge | None, int | None]


def _stem(mnemonic: str) -> str:
    m = mnemonic.lower().strip()
    for width in (".w", ".n"):
        if m.endswith(width):
            return m[: -len(width)]
    return m


def _conditional(stem: str, base: str) -> bool:
    return stem[len(base):] in _CONDITIONS


def _target(operands: str) -> int | None:
    match = _TARGET.search(operands)
    return int(match.group(1), 16) if match else None


def _without_comment(operands: str) -> str:
    """Operands without the ``@ ...`` / ``; ...`` annotation objdump appends."""
    for marker in ("@", ";"):
        operands = operands.split(marker, 1)[0]
    return operands.strip().lower()


def classify_flow(instr: Instruction) -> _Flow:
    """How control leaves *instr*."""
    stem = _stem(instr.mnemonic)
    operands = _without_comment(instr.operands)

    if stem in ("cbz", "cbnz"):
        return _Flow("jump", True, _target(instr.operands))
    if stem in ("tbb", "tbh"):
        return _Flow("table")
    if stem == "udf":
        return _Flow("stop")

    branch = _BRANCH.match(stem)
    if branch:
        base, conditional = branch.group(1), branch.group(2) is not None
        target = _target(instr.operands)
        if base == "b":
            return _Flow("jump", conditional, target)
        if base == "bx":
            return _Flow("return" if operands == "lr" else "indirect", conditional)
        return _Flow("call", conditional, target)

    if stem.startswith(_RETURNING_LOADS):
        base = next(b for b in _RETURNING_LOADS if stem.startswith(b))
        loads_pc = "pc" in operands if "{" in operands else operands.startswith("pc,")
        if loads_pc:
            suffix = stem[len(base):].lstrip("iadb")
            return _Flow("return", suffix in _CONDITIONS)
    if stem.startswith(("mov", "add")) and operands.startswith("pc,"):
        returns = stem.startswith("mov") and operands.replace(" ", "") == "pc,lr"
        return _Flow("return" if returns else "indirect", _conditional(stem, stem[:3]))
    return _Flow("next")


def _table_targets(fn: Function, index: int, code: Mapping[int, int]) -> list[int]:
    """Node indices a ``tbb``/``tbh`` at *index* can branch to."""
    instr = fn.instructions[index]
    wide = _stem(instr.mnemonic) == "tbh"
    data = bytearray()
    for follower in fn.instructions[index + 1:]:
        if not is_data(follower.mnemonic):
            break
        width = {".byte": 1, ".short": 2, ".word": 4}.get(follower.mnemonic.lower())
        try:
            value = int(follower.operands.split()[0], 16)
        except (IndexError, ValueError):
            break
        if width is None:
            break
        data += value.to_bytes(width, "little")

    step = 2 if wide else 1
    entries = [int.from_bytes(data[i:i + step], "little") for i in range(0, len(data) - step + 1, step)]

    register = _TABLE_INDEX.search(_without_comment(instr.operands))
    if register:
        for earlier in reversed(fn.instructions[max(0, index - _TABLE_SCAN):index]):
            compare = _COMPARE.match(_without_comment(earlier.operands))
            if _stem(earlier.mnemonic) == "cmp" and compare and compare.group(1) == register.group(1):
                entries = entries[: int(compare.group(2)) + 1]
                break

    base = instr.address + 4
    targets: list[int] = []
    for entry in entries:
        node = code.get(base + 2 * entry)
        if node is None:
            break
        targets.append(node)
    return targets


def _build_graph(fn: Function, cold: Sequence[re.Pattern[str]], name_at: Mapping[int, str]) -> _Graph:
    instructions = fn.instructions
    code = {i.address: n for n, i in enumerate(instructions) if not is_data(i.mnemonic)}
    graph = _Graph(edges=[[] for _ in instructions], indirect=set())

    for n, instr in enumerate(instructions):
        if is_data(instr.mnemonic):
            continue
        flow = classify_flow(instr)
        cost = (instr.min_cycles, instr.max_cycles)
        out = graph.edges[n]
        after = n + 1 if n + 1 < len(instructions) and not is_data(instructions[n + 1].mnemonic) else None
        skips_cold = flow.target is not None and _matches(cold, name_at.get(flow.target, ""))

        if flow.conditional and after is not None:
            out.append(_Edge(after, *NOT_TAKEN_CYCLES))

        if flow.kind == "next":
            if after is not None:
                out.append(_Edge(after, *cost))
        elif flow.kind in ("return", "indirect"):
            if flow.kind == "indirect":
                graph.indirect.add(n)
            out.append(_Edge(_EXIT, *cost))
        elif flow.kind == "jump":
            inside = code.get(flow.target) if flow.target is not None else None
            if inside is not None:
                out.append(_Edge(inside, *cost))
            elif not skips_cold:
                out.append(_Edge(_EXIT, *cost, callee=flow.target))
        elif flow.kind == "call":
            if flow.target is None:
                graph.indirect.add(n)
            if after is not None and not skips_cold:
                out.append(_Edge(after, *cost, callee=flow.target))
        elif flow.kind == "table":
            targets = _table_targets(fn, n, code)
            graph.unresolved = graph.unresolved or not targets
            out.extend(_Edge(t, *cost) for t in targets)
    return graph


def direct_callees(fn: Function, functions: Sequence[Function]) -> list[Function]:
    """Functions *fn* calls or tail-calls by address, anywhere in its body."""
    ordered = sorted(functions, key=lambda f: f.start_addr)
    starts = [f.start_addr for f in ordered]
    found: dict[int, Function] = {}
    for instr in fn.instructions:
        if is_data(instr.mnemonic):
            continue
        flow = classify_flow(instr)
        if flow.kind not in ("call", "jump") or flow.target is None:
            continue
        if fn.start_addr <= flow.target < fn.end_addr:
            continue
        position = bisect.bisect_right(starts, flow.target) - 1
        if position >= 0 and flow.target < max(ordered[position].end_addr, starts[position] + 1):
            found[starts[position]] = ordered[position]
    return list(found.values())


def _matches(patterns: Iterable[re.Pattern[str]], name: str) -> bool:
    return any(p.search(name) for p in patterns)


def _depth_first(edges: Sequence[Sequence[_Edge]], start: int) -> tuple[list[int], set[tuple[int, int]]]:
    """Post-order of the nodes reachable from *start* and the edges that close a loop."""
    order: list[int] = []
    back: set[tuple[int, int]] = set()
    state = {start: 1}
    stack = [(start, iter(edges[start]))]
    while stack:
        node, pending = stack[-1]
        for edge in pending:
            if edge.dest == _EXIT:
                continue
            seen = state.get(edge.dest, 0)
            if seen == 1:
                back.add((node, edge.dest))
            elif seen == 0:
                state[edge.dest] = 1
                stack.append((edge.dest, iter(edges[edge.dest])))
                break
        else:
            state[node] = 2
            order.append(node)
            stack.pop()
    return order, back


def _loop_bodies(edges: Sequence[Sequence[_Edge]], reachable: Sequence[int],
                 back: set[tuple[int, int]]) -> dict[int, set[int]]:
    """The nodes of each loop, by loop header."""
    bodies: dict[int, set[int]] = {}
    if not back:
        return bodies
    predecessors: dict[int, list[int]] = {n: [] for n in reachable}
    for node in reachable:
        for edge in edges[node]:
            if edge.dest != _EXIT:
                predecessors[edge.dest].append(node)
    for latch, header in back:
        body = bodies.setdefault(header, {header})
        work = [latch]
        while work:
            node = work.pop()
            if node not in body:
                body.add(node)
                work.extend(predecessors[node])
    return bodies


def _way_out(header: int, body: set[int], forward: Sequence[Sequence[_Edge]],
             callee_cost: _CalleeCost) -> tuple[int, int] | None:
    """Cheapest way out of a loop from its header: (max cycles, node reached), or None."""
    reached = {header: 0}
    queue = [(0, header)]
    found: tuple[int, int] | None = None
    while queue:
        spent, node = heapq.heappop(queue)
        if spent > reached[node] or (found is not None and spent >= found[0]):
            continue
        for edge in forward[node]:
            total = spent + edge.max_cycles + callee_cost(edge.callee)[1]
            if edge.dest == _EXIT or edge.dest not in body:
                if found is None or total < found[0]:
                    found = (total, edge.dest)
            elif total < reached.get(edge.dest, total + 1):
                reached[edge.dest] = total
                heapq.heappush(queue, (total, edge.dest))
    return found


def _acyclic(edges: Sequence[Sequence[_Edge]], first: int,
             callee_cost: _CalleeCost) -> tuple[list[list[_Edge]], dict[int, set[int]]]:
    """Edges of the worst-path search, with every loop opened, and the loop bodies.

    The edge that closes a loop is dropped and its branch is charged as taken.
    Where that leaves the latch no way on (the body ends in a jump back to the
    test), it gets an edge that leaves the loop by the cheapest way from the
    loop header. A path therefore runs each loop body once.
    """
    order, back = _depth_first(edges, first)
    bodies = _loop_bodies(edges, order, back)
    forward = [[e for e in out if (n, e.dest) not in back] for n, out in enumerate(edges)]
    opened = [list(out) for out in forward]
    for latch, header in sorted(back):
        taken = max(e.max_cycles for e in edges[latch] if e.dest == header)
        if forward[latch]:
            opened[latch] = [replace(e, max_cycles=max(e.max_cycles, taken)) for e in opened[latch]]
            continue
        way_out = _way_out(header, bodies[header], forward, callee_cost)
        if way_out is not None:
            opened[latch].append(_Edge(way_out[1], 0, taken, after=way_out[0]))
    _, residual = _depth_first(opened, first)
    if residual:
        opened = [[e for e in out if (n, e.dest) not in residual] for n, out in enumerate(opened)]
    return opened, bodies


def _solve(
    order: Sequence[int],
    edges: Sequence[Sequence[_Edge]],
    instructions: Sequence[Instruction],
    scale: Callable[[int], int],
    callee_cost: _CalleeCost,
    *,
    worst: bool,
    dead_ends_finish: bool,
) -> dict[int, _Choice]:
    """Cycles from each node to the end of the function on the costliest or cheapest path."""
    table: dict[int, _Choice] = {}
    for node in order:
        chosen: _Choice | None = None
        for edge in edges[node]:
            if edge.dest != _EXIT and edge.dest not in table:
                continue
            rest = 0 if edge.dest == _EXIT else table[edge.dest][0]
            callee_min, callee_max, callee = callee_cost(edge.callee)
            if worst:
                total = (edge.max_cycles + callee_max) * scale(node) + edge.after + rest
            else:
                total = edge.min_cycles + callee_min + rest
            if chosen is None or (total > chosen[0] if worst else total < chosen[0]):
                chosen = (total, edge, callee)
        if chosen is None and dead_ends_finish and not edges[node]:
            instr = instructions[node]
            chosen = (instr.max_cycles * scale(node) if worst else instr.min_cycles, None, None)
        if chosen is not None:
            table[node] = chosen
    return table


def _extreme(
    first: int,
    edges: Sequence[Sequence[_Edge]],
    instructions: Sequence[Instruction],
    scale: Callable[[int], int],
    callee_cost: _CalleeCost,
    *,
    worst: bool,
) -> dict[int, _Choice]:
    """:func:`_solve` over paths that return; if none does, over paths that just end."""
    order, _ = _depth_first(edges, first)
    table = _solve(order, edges, instructions, scale, callee_cost, worst=worst, dead_ends_finish=False)
    if first in table:
        return table
    return _solve(order, edges, instructions, scale, callee_cost, worst=worst, dead_ends_finish=True)


def analyze_paths(
    functions: Sequence[Function],
    roots: Iterable[Function],
    options: PathOptions | None = None,
) -> dict[int, FunctionPath]:
    """Worst- and best-case paths of *roots* and of every function they call.

    Returns a mapping from function start address to :class:`FunctionPath`.
    Cycle counts include the directly called functions; calls through a
    register are counted but not followed.
    """
    options = options or PathOptions()
    ordered = sorted(functions, key=lambda f: f.start_addr)
    starts = [f.start_addr for f in ordered]
    name_at = {f.start_addr: f.demangled for f in ordered}
    cold = [re.compile(p) for p in (*NORETURN_FUNCTIONS, *options.cold_calls)]
    bounds = [(re.compile(p), n) for p, n in options.loop_bounds.items()]

    def containing(address: int) -> Function | None:
        position = bisect.bisect_right(starts, address) - 1
        if position < 0:
            return None
        fn = ordered[position]
        return fn if address < max(fn.end_addr, fn.start_addr + 1) else None

    results: dict[int, FunctionPath] = {}
    active: set[int] = set()

    def callee_cost(address: int | None) -> tuple[int, int, int | None]:
        if address is None:
            return 0, 0, None
        callee = containing(address)
        if callee is None or callee.start_addr in active:
            return 0, 0, None
        path = cost(callee)
        return path.min_cycles, path.max_cycles, callee.start_addr

    def cost(fn: Function) -> FunctionPath:
        known = results.get(fn.start_addr)
        if known is not None:
            return known
        active.add(fn.start_addr)
        path = _function_path(fn, _build_graph(fn, cold, name_at), bounds, callee_cost)
        active.discard(fn.start_addr)
        results[fn.start_addr] = path
        return path

    for root in roots:
        cost(root)
    return results


def _function_path(
    fn: Function,
    graph: _Graph,
    bounds: Sequence[tuple[re.Pattern[str], int]],
    callee_cost: _CalleeCost,
) -> FunctionPath:
    instructions = fn.instructions
    first = next((n for n, i in enumerate(instructions) if not is_data(i.mnemonic)), None)
    if first is None:
        return FunctionPath(function=fn.demangled, start_addr=fn.start_addr)
    if graph.unresolved:
        return _whole_body(fn, graph, callee_cost)

    opened, bodies = _acyclic(graph.edges, first, callee_cost)
    depth: dict[int, int] = {}  # node → number of loops it is nested in
    for body in bodies.values():
        for member in body:
            depth[member] = depth.get(member, 0) + 1
    looping = set(depth)
    bound = next((n for pattern, n in bounds if pattern.search(fn.demangled)), None)

    def scale(node: int) -> int:
        return 1 if bound is None else int(bound ** depth.get(node, 0))

    forward = [[e for e in out if e.after == 0] for out in opened]
    worst = _extreme(first, opened, instructions, scale, callee_cost, worst=True)
    best = _extreme(first, forward, instructions, scale, callee_cost, worst=False)
    if first not in worst or first not in best:
        return _whole_body(fn, graph, callee_cost)

    addresses: list[int] = []
    callees: dict[int, int] = {}
    own_max = indirect = 0
    in_loop = False
    step: int | None = first
    while step is not None and step != _EXIT:
        _, taken, callee = worst[step]
        times = scale(step)
        addresses.append(instructions[step].address)
        if taken is None:
            own_max += instructions[step].max_cycles * times
        else:
            own_max += taken.max_cycles * times + taken.after
        if step in graph.indirect:
            indirect += times
        if callee is not None:
            callees[callee] = callees.get(callee, 0) + times
        in_loop = in_loop or step in looping
        step = taken.dest if taken is not None else None

    min_callees: dict[int, int] = {}
    own_min = 0
    step = first
    while step is not None and step != _EXIT:
        _, taken, callee = best[step]
        own_min += taken.min_cycles if taken is not None else instructions[step].min_cycles
        if callee is not None:
            min_callees[callee] = min_callees.get(callee, 0) + 1
        step = taken.dest if taken is not None else None

    return FunctionPath(
        function=fn.demangled,
        start_addr=fn.start_addr,
        min_cycles=best[first][0],
        max_cycles=worst[first][0],
        own_min_cycles=own_min,
        own_max_cycles=own_max,
        addresses=tuple(addresses),
        callees=tuple(sorted(callees.items())),
        min_callees=tuple(sorted(min_callees.items())),
        indirect_calls=indirect,
        unbounded_loops=len(bodies) if in_loop and bound is None else 0,
        loop_bound=bound if in_loop else None,
    )


def _whole_body(fn: Function, graph: _Graph, callee_cost: _CalleeCost) -> FunctionPath:
    """Fallback when the control flow cannot be resolved: every instruction, every call once."""
    callees: dict[int, int] = {}
    low = high = 0
    for out in graph.edges:
        for edge in out:
            callee_min, callee_max, callee = callee_cost(edge.callee)
            if callee is not None and callee not in callees:
                callees[callee] = 1
                low += callee_min
                high += callee_max
    code = [i for i in fn.instructions if not is_data(i.mnemonic)]
    return FunctionPath(
        function=fn.demangled,
        start_addr=fn.start_addr,
        min_cycles=fn.total_min_cycles + low,
        max_cycles=fn.total_max_cycles + high,
        own_min_cycles=fn.total_min_cycles,
        own_max_cycles=fn.total_max_cycles,
        addresses=tuple(i.address for i in code),
        callees=tuple(sorted(callees.items())),
        min_callees=tuple(sorted(callees.items())),
        indirect_calls=len(graph.indirect),
        whole_body=True,
    )
