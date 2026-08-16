import json

from biosafety_assessment.cli import main


def test_cli_non_interactive_exit_code(capsys):
    code = main(
        [
            "--cell-type", "ipsc",
            "--genetic-mod", "none",
            "--vector", "rcv",
            "--scale", "bench",
            "--use", "research",
            "--risk", "none",
            "--no-color",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "BSL-3" in out
    assert "IBC APPROVAL REQUIRED" in out


def test_cli_json_export(tmp_path, capsys):
    out_path = tmp_path / "summary.json"
    code = main(
        [
            "--cell-type", "ipsc",
            "--genetic-mod", "none",
            "--vector", "aav",
            "--scale", "bench",
            "--use", "research",
            "--risk", "none",
            "--json", str(out_path),
            "--quiet",
            "--no-color",
        ]
    )
    assert code == 0
    payload = json.loads(out_path.read_text())
    assert payload["result"]["bsl_label"] == "BSL-2"


def test_cli_requires_all_or_none_fields():
    code = main(["--cell-type", "ipsc"])
    assert code == 2
