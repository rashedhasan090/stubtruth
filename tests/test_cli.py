from pathlib import Path

from stubtruth.cli import main

DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo_project"


def test_cli_text_ok():
    code = main([str(DEMO), "--format", "text"])
    assert code == 0


def test_cli_fail_on_stub():
    code = main([str(DEMO), "--fail-on-stub"])
    assert code == 2
