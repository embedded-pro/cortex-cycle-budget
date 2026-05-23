"""ARM disassembly parser — objdump output → :class:`Function` list."""

from __future__ import annotations

import re

from cortex_cycle_budget.models import Function, Instruction
from cortex_cycle_budget.timing_model import classify_instruction, get_timing

_FN_PATTERN = re.compile(r"^([0-9a-fA-F]+)\s+<(.+?)>:$")
_INSTR_PATTERN = re.compile(
    r"^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F ]+?)\s{2,}(\S+)\s*(.*?)$"
)
_CALL_TARGET = re.compile(r"<(.+?)>")


def parse_disassembly(
    objdump_output: str,
    timing: dict[str, tuple[int, int]] | None = None,
) -> list[Function]:
    """Parse ``arm-none-eabi-objdump -d -C`` output into a list of functions.

    Args:
        objdump_output: Raw stdout from objdump.
        timing: Optional per-variant timing table from
            :func:`cortex_cycle_budget.timing_model.resolve_timing_table`.
            If ``None`` the default Cortex-M4 table is used.
    """
    functions: list[Function] = []
    current_fn: Function | None = None

    for line in objdump_output.splitlines():
        fn_match = _FN_PATTERN.match(line)
        if fn_match:
            if current_fn is not None:
                _finalize(current_fn)
                functions.append(current_fn)
            addr = int(fn_match.group(1), 16)
            name = fn_match.group(2)
            current_fn = Function(name=name, demangled=name, start_addr=addr)
            continue

        if current_fn is None:
            continue

        instr_match = _INSTR_PATTERN.match(line)
        if instr_match:
            addr = int(instr_match.group(1), 16)
            raw_bytes = instr_match.group(2).strip()
            mnemonic = instr_match.group(3).strip()
            operands = instr_match.group(4).strip()
            byte_count = len(raw_bytes.replace(" ", "")) // 2
            min_c, max_c = get_timing(mnemonic, timing)

            instr = Instruction(
                address=addr,
                raw_bytes=raw_bytes,
                mnemonic=mnemonic,
                operands=operands,
                size=byte_count,
                min_cycles=min_c,
                max_cycles=max_c,
            )
            current_fn.instructions.append(instr)

            ml = mnemonic.lower()
            if ml in ("bl", "blx", "b", "bx") or ml.startswith("bl"):
                ct = _CALL_TARGET.search(operands)
                if ct:
                    current_fn.calls.append(ct.group(1))

    if current_fn is not None:
        _finalize(current_fn)
        functions.append(current_fn)

    return functions


def _finalize(fn: Function) -> None:
    fn.instruction_count = len(fn.instructions)
    fn.total_min_cycles = sum(i.min_cycles for i in fn.instructions)
    fn.total_max_cycles = sum(i.max_cycles for i in fn.instructions)
    fn.code_size = sum(i.size for i in fn.instructions)
    if fn.instructions:
        fn.end_addr = fn.instructions[-1].address + fn.instructions[-1].size
    for instr in fn.instructions:
        cat = classify_instruction(instr.mnemonic)
        if cat == "fpu":
            fn.fpu_ops += 1
        elif cat == "load_store":
            fn.load_store_ops += 1
        elif cat == "branch":
            fn.branch_ops += 1
        elif cat == "mul_div":
            fn.mul_div_ops += 1
        else:
            fn.alu_ops += 1
