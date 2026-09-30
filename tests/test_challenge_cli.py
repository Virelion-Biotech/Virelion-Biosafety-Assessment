"""Public CLI integration: persisted scenarios, errors, audits, and evaluation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from challenge_platform.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "challenge"


def invoke(*args):
    return subprocess.run([sys.executable, "-m", "challenge_platform", *map(str, args)],
                          text=True, capture_output=True, timeout=15)


def test_demo_is_explicitly_synthetic_and_reproducible():
    a, b = invoke(), invoke("generate")
    assert a.returncode == b.returncode == 0
    assert a.stdout == b.stdout
    data = json.loads(a.stdout)
    assert data["evidence_level"] == "synthetic"
    assert data["provenance"]["parent"]["evidence_level"] == "synthetic"
    assert data["provenance"]["seed"] == 42
    assert data["held_out"] is False


@pytest.mark.parametrize("args", [
    ["--magnitude", "nan"], ["--magnitude", "-0.1"], ["--scenario-id", " "],
    ["--seed", "bad"], ["validate", "/does/not/exist.json"],
])
def test_invalid_inputs_exit_two_without_traceback(args):
    result = invoke(*args)
    assert result.returncode == 2
    assert "error:" in result.stderr and "Traceback" not in result.stderr
    assert not result.stdout


def test_generate_validate_audit_roundtrip_and_tamper_detection(tmp_path):
    output, audit = tmp_path / "scenario.json", tmp_path / "audit.json"
    result = invoke("generate", "--reference", EXAMPLES / "baseline.json", "--output", output,
                    "--audit", audit, "--dataset-version", "synthetic-fixture-v1")
    assert result.returncode == 0, result.stderr
    assert invoke("validate", output).returncode == 0
    verified = invoke("verify-audit", audit)
    assert verified.returncode == 0
    assert json.loads(verified.stdout)["valid"] is True
    data = json.loads(audit.read_text())
    data["outputs"]["phenotype"]["inflammation"] = 0.999
    audit.write_text(json.dumps(data))
    rejected = invoke("verify-audit", audit)
    assert rejected.returncode == 2
    assert "verification failed" in rejected.stderr


def test_cli_rejects_input_output_collision_and_unversioned_audit(tmp_path):
    source = tmp_path / "scenario.json"
    source.write_text(invoke().stdout)
    before = source.read_bytes()
    assert invoke("generate", "--reference", source, "--output", source).returncode == 2
    assert source.read_bytes() == before
    assert invoke("generate", "--audit", tmp_path / "audit.json").returncode == 2
    assert not (tmp_path / "audit.json").exists()


def test_novelty_rescue_and_benchmark_examples_run():
    novelty = invoke("novelty", EXAMPLES / "challenged.json", "--references", EXAMPLES / "registry.json")
    assert novelty.returncode == 0, novelty.stderr
    assert json.loads(novelty.stdout)["is_novel"] is True
    rescue = invoke("rescue", "--baseline", EXAMPLES / "baseline.json",
                    "--challenged", EXAMPLES / "challenged.json", "--treated", EXAMPLES / "treated.json")
    assert rescue.returncode == 0, rescue.stderr
    assert json.loads(rescue.stdout)["overall"] > 0.5
    benchmark = invoke("benchmark", EXAMPLES / "benchmark.json")
    assert benchmark.returncode == 0, benchmark.stderr
    assert json.loads(benchmark.stdout)["metrics"]["accuracy"] == 1


def test_main_accepts_argv(capsys):
    assert main(["generate", "--seed", "12"]) == 0
    assert json.loads(capsys.readouterr().out)["provenance"]["seed"] == 12


def test_installed_console_entry_points():
    # Resolve alongside this interpreter: test the wheel/venv under test, not a global CLI.
    bindir = Path(sys.executable).parent
    for command in ("virelion-challenge", "virelion-bsa"):
        executable = bindir / command
        assert executable.exists(), f"install the package before running this test: {executable}"
        result = subprocess.run([str(executable), "--help"], capture_output=True, text=True, timeout=15)
        assert result.returncode == 0 and "usage:" in result.stdout
