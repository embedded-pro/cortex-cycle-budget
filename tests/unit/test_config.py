"""Tests for the public config validator."""

from __future__ import annotations

import pytest

from cortex_cycle_budget import ConfigError, validate_config


class TestValidateConfig:
    def test_minimal_valid(self) -> None:
        validate_config({"path_stages": [{"label": "s", "patterns": ["foo"]}]})

    def test_missing_path_stages(self) -> None:
        with pytest.raises(ConfigError, match="path_stages"):
            validate_config({})

    def test_path_stages_must_be_non_empty_list(self) -> None:
        with pytest.raises(ConfigError, match="non-empty"):
            validate_config({"path_stages": []})

    def test_path_stages_must_be_list(self) -> None:
        with pytest.raises(ConfigError, match="non-empty"):
            validate_config({"path_stages": "not a list"})

    def test_stage_missing_label(self) -> None:
        with pytest.raises(ConfigError, match="missing 'label'"):
            validate_config({"path_stages": [{"patterns": ["foo"]}]})

    def test_stage_without_type_or_patterns(self) -> None:
        with pytest.raises(ConfigError, match="type.*patterns"):
            validate_config({"path_stages": [{"label": "s"}]})

    def test_unknown_stage_type(self) -> None:
        with pytest.raises(ConfigError, match="unknown type"):
            validate_config({
                "path_stages": [{"label": "s", "type": "garbage"}],
            })

    def test_exception_entry_type_ok_without_patterns(self) -> None:
        validate_config({
            "path_stages": [{"label": "e", "type": "exception_entry"}],
        })

    def test_invalid_regex(self) -> None:
        with pytest.raises(ConfigError, match="not valid regex"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["[unclosed"]}],
            })

    def test_invalid_entry_regex(self) -> None:
        with pytest.raises(ConfigError, match="entry.*not valid regex"):
            validate_config({
                "path_stages": [{
                    "label": "s",
                    "patterns": ["foo"],
                    "entry": "(unclosed",
                }],
            })

    def test_negative_loop_rate(self) -> None:
        with pytest.raises(ConfigError, match="loop_rates_khz"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["x"]}],
                "loop_rates_khz": [-1],
            })

    def test_string_loop_rate(self) -> None:
        with pytest.raises(ConfigError, match="loop_rates_khz"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["x"]}],
                "loop_rates_khz": ["20"],
            })

    def test_invalid_cortex_variant(self) -> None:
        with pytest.raises(ConfigError, match="cortex"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["x"]}],
                "cortex": "m99",
            })

    def test_valid_cortex_variants(self) -> None:
        for v in ("m0", "m4", "m7", "m33"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["x"]}],
                "cortex": v,
            })

    def test_invalid_clock_mhz(self) -> None:
        with pytest.raises(ConfigError, match="clock_mhz"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["x"]}],
                "clock_mhz": 0,
            })

    def test_combine_accepts_sum_and_max(self) -> None:
        for combine in ("sum", "max"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["foo"], "combine": combine}],
            })

    def test_unknown_combine(self) -> None:
        with pytest.raises(ConfigError, match="unknown combine"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["foo"], "combine": "average"}],
            })

    def test_loop_bounds_ok(self) -> None:
        validate_config({
            "path_stages": [{"label": "s", "patterns": ["foo"]}],
            "loop_bounds": {"^drain$": 6},
        })

    def test_loop_bounds_per_loop_ok(self) -> None:
        validate_config({
            "path_stages": [{"label": "s", "patterns": ["foo"]}],
            "loop_bounds": {"^update$": [3, 3, 9]},
        })

    @pytest.mark.parametrize("bounds", [
        {"^drain$": 0}, {"^drain$": "6"}, {"^drain$": True}, ["x"],
        {"^drain$": []}, {"^drain$": [3, 0]}, {"^drain$": [3, "9"]}, {"^drain$": [True]},
    ])
    def test_invalid_loop_bounds(self, bounds: object) -> None:
        with pytest.raises(ConfigError, match="loop_bounds"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["foo"]}],
                "loop_bounds": bounds,
            })

    def test_loop_bounds_key_must_be_a_regex(self) -> None:
        with pytest.raises(ConfigError, match="loop_bounds.*not valid regex"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["foo"]}],
                "loop_bounds": {"(": 2},
            })

    def test_cold_calls_ok(self) -> None:
        validate_config({
            "path_stages": [{"label": "s", "patterns": ["foo"]}],
            "cold_calls": ["^trip$"],
        })

    @pytest.mark.parametrize("cold", ["^trip$", [1], ["("]])
    def test_invalid_cold_calls(self, cold: object) -> None:
        with pytest.raises(ConfigError, match="cold_calls"):
            validate_config({
                "path_stages": [{"label": "s", "patterns": ["foo"]}],
                "cold_calls": cold,
            })

    def test_multiple_errors_reported(self) -> None:
        with pytest.raises(ConfigError) as exc:
            validate_config({
                "path_stages": [{"label": "s"}],
                "loop_rates_khz": [-1],
                "cortex": "m99",
            })
        msg = str(exc.value)
        assert "type" in msg
        assert "loop_rates_khz" in msg
        assert "cortex" in msg
