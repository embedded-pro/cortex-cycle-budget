"""End-to-end integration test: compile → analyze → assert."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from cortex_cycle_budget.cli_multi import main as cli_multi_main
from cortex_cycle_budget.cli_single import main as cli_single_main

GCC = shutil.which("arm-none-eabi-gcc")
OBJDUMP = shutil.which("arm-none-eabi-objdump") or "arm-none-eabi-objdump"
SIZE = shutil.which("arm-none-eabi-size") or "arm-none-eabi-size"

requires_arm_gcc = pytest.mark.skipif(
    GCC is None,
    reason="arm-none-eabi-gcc not available",
)


C_SOURCE = """
__attribute__((noinline)) int helper(int x) { return x * 3 + 7; }
__attribute__((noinline)) int critical(int x) {
    int acc = 0;
    for (int i = 0; i < 4; ++i) acc += helper(i + x);
    return acc;
}
int _start(void) { return critical(42); }
"""


CPU_FLAGS = {
    "m4": ["-mcpu=cortex-m4", "-mthumb"],
    "m7": ["-mcpu=cortex-m7", "-mthumb"],
    "m33": ["-mcpu=cortex-m33", "-mthumb"],
}


def _compile(tmp_path: Path, cortex: str) -> Path:
    src = tmp_path / "tiny.c"
    src.write_text(C_SOURCE)
    elf = tmp_path / f"tiny_{cortex}.elf"
    cmd = [
        GCC, *CPU_FLAGS[cortex],
        "-Os", "-nostdlib", "-ffreestanding",
        "-Wl,-Ttext=0x0", "-Wl,--entry=_start",
        str(src), "-o", str(elf),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return elf


def _write_config(tmp_path: Path, cortex: str) -> Path:
    cfg = {
        "path_name": "Tiny Critical",
        "loop_rates_khz": [20],
        "path_stages": [
            {"label": "Critical", "patterns": ["^critical$"]},
            {"label": "Helper", "patterns": ["^helper$"]},
        ],
    }
    p = tmp_path / f"cfg_{cortex}.json"
    p.write_text(json.dumps(cfg))
    return p


@pytest.mark.integration
@requires_arm_gcc
@pytest.mark.parametrize("cortex", ["m4", "m7", "m33"])
def test_end_to_end_single_mode(tmp_path: Path, cortex: str) -> None:
    elf = _compile(tmp_path, cortex)
    cfg = _write_config(tmp_path, cortex)
    out = tmp_path / f"out_{cortex}"

    rc = cli_single_main([
        str(cfg),
        "--elf", str(elf),
        "--target", f"test-{cortex}",
        "--build-config", "Release",
        "--clock-mhz", "100",
        "--cortex", cortex,
        "--output-dir", str(out),
        "--objdump", OBJDUMP,
        "--size-tool", SIZE,
    ])
    assert rc == 0

    metrics_path = out / "cycle_metrics.json"
    assert metrics_path.is_file()
    m = json.loads(metrics_path.read_text())
    assert m["cortex"] == cortex
    assert m["summary"]["estimated_max_cycles"] > 0
    # Both stages must have matched at least one function
    labels = {s["label"]: s for s in m["stages"]}
    assert labels["Critical"]["functions"] == ["critical"]
    assert labels["Helper"]["functions"] == ["helper"]


@pytest.mark.integration
@requires_arm_gcc
def test_end_to_end_multi_mode(tmp_path: Path) -> None:
    elf = _compile(tmp_path, "m4")
    cfg = _write_config(tmp_path, "m4")

    out_a = tmp_path / "mode_a"
    out_b = tmp_path / "mode_b"
    analyses = [
        {"label": "Mode A", "elf_path": str(elf),
         "config_path": str(cfg), "output_dir": str(out_a)},
        {"label": "Mode B", "elf_path": str(elf),
         "config_path": str(cfg), "output_dir": str(out_b)},
    ]
    analyses_path = tmp_path / "analyses.json"
    analyses_path.write_text(json.dumps(analyses))
    combined = tmp_path / "combined"

    rc = cli_multi_main([
        str(analyses_path),
        "--target", "multi-board",
        "--build-config", "Release",
        "--clock-mhz", "100",
        "--cortex", "m4",
        "--output-dir", str(combined),
        "--objdump", OBJDUMP,
        "--size-tool", SIZE,
    ])
    assert rc == 0

    pr_comment = (combined / "combined_pr_comment.md").read_text()
    assert "Mode A" in pr_comment
    assert "Mode B" in pr_comment
    assert "<!-- cortex-cycle-budget-comment -->" in pr_comment

    combined_metrics = json.loads((combined / "combined_metrics.json").read_text())
    assert len(combined_metrics["modes"]) == 2
    assert combined_metrics["overall_max_cycles"] > 0
