"""Locate definitions and classify stub vs real implementation."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".tox",
}

_STUB_RAISE = re.compile(
    r"(?i)raise\s+(NotImplementedError|Exception|RuntimeError)\s*\(\s*"
    r"[\"'](?:not\s+implemented|todo|stub|pass)[^\"']*[\"']\s*\)"
)
_TODO_LINE = re.compile(r"(?i)\b(?:TODO|FIXME|XXX|HACK|STUB)\b")


@dataclass(frozen=True)
class SymbolHit:
    path: str
    line: int
    name: str
    kind: str  # function | async_function | class | method
    status: str  # implemented | stub | empty
    evidence: str


def _body_status(node: ast.AST, source: str) -> tuple[str, str]:
    """Classify a function/class body as stub / empty / implemented."""
    body: list[ast.stmt]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        body = list(node.body)
        # Skip docstring.
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]
    elif isinstance(node, ast.ClassDef):
        body = list(node.body)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]
    else:
        return "implemented", "non-def"

    if not body:
        return "empty", "empty body"

    # Single-statement stubs.
    if len(body) == 1:
        stmt = body[0]
        if isinstance(stmt, ast.Pass):
            return "stub", "pass"
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if stmt.value.value is Ellipsis:
                return "stub", "ellipsis"
        if isinstance(stmt, ast.Raise):
            seg = ast.get_source_segment(source, stmt) or ""
            if "NotImplementedError" in seg or _STUB_RAISE.search(seg):
                return "stub", "NotImplementedError"
            return "stub", "raise-only"
        if isinstance(stmt, ast.Return) and stmt.value is None:
            return "empty", "return None only"

    # Multi-line but dominated by TODO / stub raises.
    snippet = ast.get_source_segment(source, node) or ""
    if _STUB_RAISE.search(snippet) and len(body) <= 3:
        return "stub", "stub raise in body"
    if _TODO_LINE.search(snippet) and len(body) <= 2:
        # Very short TODO-only bodies.
        nontrivial = [
            s
            for s in body
            if not (
                isinstance(s, ast.Pass)
                or (
                    isinstance(s, ast.Expr)
                    and isinstance(getattr(s, "value", None), ast.Constant)
                )
            )
        ]
        if not nontrivial or (
            len(nontrivial) == 1 and isinstance(nontrivial[0], ast.Raise)
        ):
            return "stub", "TODO marker"

    return "implemented", "has body"


class _Collector(ast.NodeVisitor):
    def __init__(self, path: str, source: str, want: set[str]) -> None:
        self.path = path
        self.source = source
        self.want = {w.lower() for w in want}
        self.hits: list[SymbolHit] = []
        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name.lower() in self.want:
            status, evidence = _body_status(node, self.source)
            self.hits.append(
                SymbolHit(
                    path=self.path,
                    line=node.lineno,
                    name=node.name,
                    kind="class",
                    status=status,
                    evidence=evidence,
                )
            )
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_fn(node, "method" if self._class_stack else "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_fn(node, "method" if self._class_stack else "async_function")

    def _visit_fn(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, kind: str
    ) -> None:
        if node.name.lower() in self.want:
            status, evidence = _body_status(node, self.source)
            self.hits.append(
                SymbolHit(
                    path=self.path,
                    line=node.lineno,
                    name=node.name,
                    kind=kind,
                    status=status,
                    evidence=evidence,
                )
            )
        self.generic_visit(node)


def iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        files.append(p)
    return sorted(files)


def find_symbols(root: Path, tokens: list[str]) -> dict[str, list[SymbolHit]]:
    """Map lowercase token -> symbol hits under root."""
    want = {t for t in tokens}
    by_token: dict[str, list[SymbolHit]] = {t.lower(): [] for t in tokens}

    for path in iter_python_files(root):
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, OSError):
            continue
        rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        coll = _Collector(rel, source, want)
        coll.visit(tree)
        for hit in coll.hits:
            by_token.setdefault(hit.name.lower(), []).append(hit)

    return by_token
