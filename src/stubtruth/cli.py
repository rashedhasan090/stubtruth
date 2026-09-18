"""Command-line entry for stubtruth."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import scan
from .report import render_json, render_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stubtruth",
        description=(
            "Map README feature claims to code symbols and report stubs "
            "vs real implementations (offline, CI-friendly)."
        ),
    )
    p.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to scan (default: .)",
    )
    p.add_argument(
        "--readme",
        type=Path,
        default=None,
        help="Path to README (default: README.md under root)",
    )
    p.add_argument(
        "--doc",
        action="append",
        default=[],
        type=Path,
        help="Extra Markdown doc to mine for claims (repeatable)",
    )
    p.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-stub",
        action="store_true",
        help="Exit 2 if any claimed symbol is a stub/empty body",
    )
    p.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit 3 if any claimed token has no matching def",
    )
    p.add_argument(
        "--min-coverage",
        type=float,
        default=None,
        metavar="RATIO",
        help="Exit 4 if implemented/claims coverage is below RATIO (0-1)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"stubtruth: not a directory: {root}", file=sys.stderr)
        return 1

    report = scan(root, readme=args.readme, extra_docs=list(args.doc) or None)
    out = render_json(report) if args.format == "json" else render_text(report)
    sys.stdout.write(out)

    if args.fail_on_stub and report.stubs:
        return 2
    if args.fail_on_missing and report.missing:
        return 3
    if args.min_coverage is not None and report.coverage() < args.min_coverage:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
