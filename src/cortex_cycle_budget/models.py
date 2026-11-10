"""Data structures and exception types for cycle analysis."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Instruction:
    """A single decoded instruction with cycle estimates."""

    address: int
    raw_bytes: str
    mnemonic: str
    operands: str
    size: int
    min_cycles: int = 1
    max_cycles: int = 1


@dataclass
class Function:
    """A disassembled function with aggregate cycle / instruction-mix metrics."""

    name: str
    demangled: str
    start_addr: int
    end_addr: int = 0
    instructions: list[Instruction] = field(default_factory=list)
    total_min_cycles: int = 0
    total_max_cycles: int = 0
    instruction_count: int = 0
    code_size: int = 0
    calls: list[str] = field(default_factory=list)
    fpu_ops: int = 0
    load_store_ops: int = 0
    branch_ops: int = 0
    alu_ops: int = 0
    mul_div_ops: int = 0


@dataclass(frozen=True)
class FunctionPath:
    """Best and worst path through one function, directly called functions included."""

    function: str
    start_addr: int
    min_cycles: int = 0
    max_cycles: int = 0
    own_min_cycles: int = 0  # best path, this function's instructions only
    own_max_cycles: int = 0  # worst path, this function's instructions only
    addresses: tuple[int, ...] = ()  # instructions on the worst path, in order
    callees: tuple[tuple[int, int], ...] = ()  # (start address, calls) on the worst path
    min_callees: tuple[tuple[int, int], ...] = ()  # (start address, calls) on the best path
    indirect_calls: int = 0  # calls through a register on the worst path, not followed
    unbounded_loops: int = 0  # loops on the worst path counted for one iteration
    loop_bound: int | None = None  # iterations charged to the loops on the worst path
    whole_body: bool = False  # control flow not resolved: every instruction counted


@dataclass(frozen=True)
class FunctionShare:
    """What one function contributes to a stage's worst path."""

    function: str
    start_addr: int
    calls: int
    max_cycles: int  # own instructions on the worst path, times calls
    instructions: int
    code_size: int
    fpu_ops: int
    addresses: frozenset[int] = frozenset()


@dataclass
class PathStage:
    """One stage in the configured critical path."""

    label: str
    functions: list[str] = field(default_factory=list)
    min_cycles: int = 0
    max_cycles: int = 0
    instruction_count: int = 0  # instructions on the worst path
    code_size: int = 0
    fpu_ops: int = 0  # FPU instructions on the worst path
    is_overhead: bool = False  # True for ISR entry/exit (no disasm)
    breakdown: list[FunctionShare] = field(default_factory=list)
    indirect_calls: int = 0
    notes: list[str] = field(default_factory=list)


class StageMatchError(RuntimeError):
    """Raised when a path stage matches no functions in the binary."""


class ConfigError(RuntimeError):
    """Raised when the configuration file is invalid."""
