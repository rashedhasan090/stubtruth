"""Extract feature/capability claims from README-style Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Backticked identifiers that look like APIs / CLIs / modules.
_BACKTICK = re.compile(r"`([A-Za-z_][\w.\-]{1,63})`")

# Bullet or numbered list lines under Features-like sections, or standalone.
_FEATURE_VERB = re.compile(
    r"(?i)\b(?:supports?|provides?|implements?|includes?|offers?|"
    r"enables?|ships?|exposes?|handles?|detects?|scores?|maps?|"
    r"classifies?|audits?|checks?|validates?)\b"
)

_SECTION_HEADERS = re.compile(
    r"(?i)^#{1,3}\s+(features?|capabilities?|what (?:it|this) does|"
    r"usage|cli|commands?|api)\s*$"
)

_SKIP_TOKENS = {
    "python",
    "pip",
    "mit",
    "cli",
    "api",
    "json",
    "yaml",
    "md",
    "readme",
    "license",
    "pytest",
    "github",
    "bash",
    "shell",
    "ubuntu",
    "macos",
    "windows",
    "http",
    "https",
    "url",
    "ci",
    "cd",
}


@dataclass(frozen=True)
class Claim:
    """A claimed capability token extracted from docs."""

    token: str
    line: int
    context: str
    kind: str  # backtick | verb_phrase | heading_bullet


def _normalize_token(raw: str) -> str | None:
    t = raw.strip().strip(".,;:!?")
    if not t or len(t) < 2:
        return None
    # Prefer the last dotted/segmented piece for matching defs.
    base = t.split(".")[-1]
    base = base.replace("-", "_")
    if base.lower() in _SKIP_TOKENS:
        return None
    if not re.match(r"^[A-Za-z_][\w]*$", base):
        return None
    return base


def extract_claims(text: str) -> list[Claim]:
    """Pull claim tokens from Markdown text."""
    claims: list[Claim] = []
    seen: set[tuple[str, int]] = set()
    in_feature_section = False

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        if _SECTION_HEADERS.match(line.strip()):
            in_feature_section = True
            continue
        if line.startswith("#") and not _SECTION_HEADERS.match(line.strip()):
            in_feature_section = False

        stripped = line.strip()
        is_bullet = bool(re.match(r"^[-*+]\s+|^\d+\.\s+", stripped))

        for m in _BACKTICK.finditer(line):
            token = _normalize_token(m.group(1))
            if not token:
                continue
            key = (token.lower(), i)
            if key in seen:
                continue
            seen.add(key)
            claims.append(
                Claim(
                    token=token,
                    line=i,
                    context=stripped[:160],
                    kind="backtick",
                )
            )

        # Verb-heavy bullets in Features sections (or any bullet with a verb).
        if is_bullet and (in_feature_section or _FEATURE_VERB.search(stripped)):
            # Prefer backticked tokens already captured; also grab Camel/snake words.
            for m in re.finditer(r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+|[a-z]+_[a-z0-9_]+)\b", stripped):
                token = _normalize_token(m.group(1))
                if not token:
                    continue
                key = (token.lower(), i)
                if key in seen:
                    continue
                seen.add(key)
                claims.append(
                    Claim(
                        token=token,
                        line=i,
                        context=stripped[:160],
                        kind="heading_bullet" if in_feature_section else "verb_phrase",
                    )
                )

    return claims
