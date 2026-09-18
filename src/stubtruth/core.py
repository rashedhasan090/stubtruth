"""Orchestrate claim extraction and stub classification."""

from __future__ import annotations

from pathlib import Path

from .claims import Claim, extract_claims
from .report import ClaimResult, ScanReport
from .stubs import SymbolHit, find_symbols


def _pick_status(hits: list[SymbolHit]) -> str:
    if not hits:
        return "missing"
    statuses = {h.status for h in hits}
    # Prefer worst signal when mixed.
    if "stub" in statuses or "empty" in statuses:
        if statuses <= {"stub", "empty"}:
            return "stub"
        return "ambiguous"
    if statuses == {"implemented"}:
        return "implemented"
    return "ambiguous"


def scan(
    root: Path,
    readme: Path | None = None,
    *,
    extra_docs: list[Path] | None = None,
) -> ScanReport:
    """Scan a project root for README claim <-> stub fidelity."""
    root = root.resolve()
    doc_paths: list[Path] = []
    if readme is not None:
        doc_paths.append(readme)
    else:
        for name in ("README.md", "README.rst", "README.txt", "README"):
            candidate = root / name
            if candidate.is_file():
                doc_paths.append(candidate)
                break
    if extra_docs:
        doc_paths.extend(extra_docs)

    claims: list[Claim] = []
    for doc in doc_paths:
        text = doc.read_text(encoding="utf-8", errors="replace")
        claims.extend(extract_claims(text))

    # Dedupe by token (keep first / lowest line).
    by_tok: dict[str, Claim] = {}
    for c in claims:
        key = c.token.lower()
        if key not in by_tok or c.line < by_tok[key].line:
            by_tok[key] = c
    unique = list(by_tok.values())

    hits_map = find_symbols(root, [c.token for c in unique]) if unique else {}

    results: list[ClaimResult] = []
    for c in sorted(unique, key=lambda x: x.line):
        hits = hits_map.get(c.token.lower(), [])
        status = _pick_status(hits)
        results.append(ClaimResult(claim=c, status=status, hits=hits))

    return ScanReport(results=results, root=str(root))
