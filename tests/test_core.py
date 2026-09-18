from pathlib import Path

from stubtruth.core import scan

DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo_project"


def test_demo_project_scan():
    report = scan(DEMO)
    by = {r.claim.token.lower(): r.status for r in report.results}
    assert by.get("render_widget") == "implemented"
    assert by.get("widgetcache") == "implemented"
    assert by.get("export_pdf") == "stub"
    assert by.get("ping_health") in {"stub", "empty"} or by.get("ping_health") == "stub"
