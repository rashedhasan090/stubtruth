"""Format stubtruth scan results."""

from __future__ import annotations

from dataclasses import dataclass

from .claims import Claim
from .stubs import SymbolHit


@dataclass
class ClaimResult:
    claim: Claim
    status: str  # implemented | stub | missing | ambiguous
    hits: list[SymbolHit]


@dataclass
class ScanReport:
    results: list[ClaimResult]
    root: str

    @property
    def implemented(self) -> int:
        return sum(1 for r in self.results if r.status == "implemented")

    @property
    def stubs(self) -> int:
        return sum(1 for r in self.results if r.status == "stub")

    @property
    def missing(self) -> int:
        return sum(1 for r in self.results if r.status == "missing")

    @property
    def ambiguous(self) -> int:
        return sum(1 for r in self.results if r.status == "ambiguous")

    @property
    def total(self) -> int:
        return len(self.results)

    def coverage(self) -> float:
        if not self.results:
            return 1.0
        return self.implemented / self.total


def render_text(report: ScanReport) -> str:
    lines: list[str] = []
    lines.append(f"stubtruth scan: {report.root}")
    lines.append(
        f"claims={report.total}  implemented={report.implemented}  "
        f"stub={report.stubs}  missing={report.missing}  "
        f"ambiguous={report.ambiguous}  "
        f"coverage={report.coverage():.0%}"
    )
    lines.append("")

    order = {"stub": 0, "missing": 1, "ambiguous": 2, "implemented": 3}
    for r in sorted(report.results, key=lambda x: (order.get(x.status, 9), x.claim.line)):
        c = r.claim
        head = f"[{r.status.upper():11}] `{c.token}`  (README:{c.line}, {c.kind})"
        lines.append(head)
        lines.append(f"  claim: {c.context}")
        if r.hits:
            for h in r.hits:
                lines.append(
                    f"  hit: {h.path}:{h.line}  {h.kind} {h.name}  "
                    f"({h.status}: {h.evidence})"
                )
        else:
            lines.append("  hit: (none)")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(report: ScanReport) -> str:
    import json

    payload = {
        "root": report.root,
        "summary": {
            "claims": report.total,
            "implemented": report.implemented,
            "stub": report.stubs,
            "missing": report.missing,
            "ambiguous": report.ambiguous,
            "coverage": round(report.coverage(), 4),
        },
        "results": [
            {
                "token": r.claim.token,
                "line": r.claim.line,
                "kind": r.claim.kind,
                "context": r.claim.context,
                "status": r.status,
                "hits": [
                    {
                        "path": h.path,
                        "line": h.line,
                        "name": h.name,
                        "kind": h.kind,
                        "status": h.status,
                        "evidence": h.evidence,
                    }
                    for h in r.hits
                ],
            }
            for r in report.results
        ],
    }
    return json.dumps(payload, indent=2) + "\n"
