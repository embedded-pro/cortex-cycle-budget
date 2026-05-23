"""Tests for the single-mode CLI (cortex-cycle-budget)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cortex_cycle_budget.cli_single import main

SAMPLE_DISASM = """\

example.elf:     file format elf32-littlearm


Disassembly of section .text:

00000100 <foo>:
     100:	b500      	push	{lr}
     102:	2001      	movs	r0, #1
     104:	bd00      	pop	{pc}

00000110 <bar>:
     110:	4770      	bx	lr
"""


@pytest.fixture
def workspace(tmp_path: Path) -> dict[str, Path]:
    config = {
        "path_name": "Test Path",
        "loop_rates_khz": [20],
        "path_stages": [
            {"label": "Foo Stage", "patterns": ["^foo$"]},
            {"label": "Bar Stage", "patterns": ["^bar$"]},
        ],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    disasm_path = tmp_path / "sample.disasm"
    disasm_path.write_text(SAMPLE_DISASM)

    out_dir = tmp_path / "out"
    return {
        "config": config_path,
        "disasm": disasm_path,
        "out": out_dir,
        "elf": tmp_path / "ignored.elf",  # not read in --disasm-file mode
    }


def _run(ws: dict[str, Path], extra: list[str] | None = None) -> int:
    args = [
        str(ws["config"]),
        "--elf", str(ws["elf"]),
        "--disasm-file", str(ws["disasm"]),
        "--target", "test-board",
        "--build-config", "Release",
        "--clock-mhz", "100",
        "--cortex", "m4",
        "--output-dir", str(ws["out"]),
    ]
    if extra:
        args += extra
    return main(args)


class TestCliSingle:
    def test_happy_path_produces_outputs(self, workspace: dict[str, Path]) -> None:
        rc = _run(workspace)
        assert rc == 0
        out = workspace["out"]
        for fname in (
            "full_disassembly.txt",
            "cycle_estimation_report.md",
            "cpu_budget.md",
            "pr_comment.md",
            "annotated_disassembly.md",
            "cycle_metrics.json",
        ):
            assert (out / fname).is_file(), f"missing {fname}"

    def test_metrics_round_trip(self, workspace: dict[str, Path]) -> None:
        _run(workspace)
        m = json.loads((workspace["out"] / "cycle_metrics.json").read_text())
        assert m["target"] == "test-board"
        assert m["cortex"] == "m4"
        assert m["summary"]["path_stages"] == 2

    def test_missing_config_fails(self, tmp_path: Path) -> None:
        rc = main([
            str(tmp_path / "nope.json"),
            "--elf", str(tmp_path / "x.elf"),
            "--target", "t", "--build-config", "Release",
            "--clock-mhz", "1", "--cortex", "m4",
        ])
        assert rc == 1

    def test_invalid_cortex_rejected_by_argparse(self) -> None:
        with pytest.raises(SystemExit):
            main([
                "x", "--elf", "y", "--target", "t",
                "--build-config", "Release",
                "--clock-mhz", "1", "--cortex", "m99",
            ])

    def test_threshold_violation_returns_nonzero(self, workspace: dict[str, Path]) -> None:
        # Force a tiny threshold so the run exceeds it.
        rc = _run(workspace, extra=["--fail-over-max-cycles", "0"])
        assert rc == 2

    def test_threshold_pass_returns_zero(self, workspace: dict[str, Path]) -> None:
        rc = _run(workspace, extra=["--fail-over-max-cycles", "1000000"])
        assert rc == 0

    def test_no_strict_allows_unmatched_stage(
        self, workspace: dict[str, Path], tmp_path: Path,
    ) -> None:
        cfg = {
            "path_name": "Test",
            "path_stages": [{"label": "Missing", "patterns": ["^never$"]}],
        }
        (tmp_path / "config2.json").write_text(json.dumps(cfg))
        ws = dict(workspace)
        ws["config"] = tmp_path / "config2.json"
        rc = _run(ws, extra=["--no-strict"])
        assert rc == 0

    def test_cortex_m7_changes_vsqrt_timing(
        self, tmp_path: Path, workspace: dict[str, Path],
    ) -> None:
        # Replace disasm with one that uses vsqrt.f32
        disasm = """\

example.elf:     file format elf32-littlearm


Disassembly of section .text:

00000100 <foo>:
     100:	eeb1 0bc1 	vsqrt.f32	s0, s2
     104:	4770      	bx	lr
"""
        disasm_path = tmp_path / "m7.disasm"
        disasm_path.write_text(disasm)
        cfg = {"path_stages": [{"label": "S", "patterns": ["^foo$"]}]}
        cfg_path = tmp_path / "m7cfg.json"
        cfg_path.write_text(json.dumps(cfg))

        out_m4 = tmp_path / "out_m4"
        out_m7 = tmp_path / "out_m7"

        for cortex, out in (("m4", out_m4), ("m7", out_m7)):
            rc = main([
                str(cfg_path),
                "--elf", "ignored",
                "--disasm-file", str(disasm_path),
                "--target", "t",
                "--build-config", "Release",
                "--clock-mhz", "100",
                "--cortex", cortex,
                "--output-dir", str(out),
            ])
            assert rc == 0

        m4_metrics = json.loads((out_m4 / "cycle_metrics.json").read_text())
        m7_metrics = json.loads((out_m7 / "cycle_metrics.json").read_text())
        # vsqrt.f32 = 14 on M4 vs 7 on M7
        assert m4_metrics["summary"]["estimated_max_cycles"] > m7_metrics["summary"]["estimated_max_cycles"]
