# stubtruth

**Offline CLI that checks whether README feature claims match real code — or just stubs.**

Agent-written and fast-shipped repos often advertise APIs in the README while the matching functions still `pass`, `...`, or `raise NotImplementedError`. `stubtruth` extracts claimed tokens from Markdown, finds matching Python defs, and classifies each hit as **implemented**, **stub**, **missing**, or **ambiguous**. CI exit codes make it a cheap gate.

## Why this is novel

Most doc linters check formatting. Citation tools (like claimcite) check research claims against footnotes. Prompt linters score agent instructions. **stubtruth** is different: it treats README capability claims as a contract against the AST of your code, and fails when the contract is a stub.

It is **not** a fork or thin wrapper of an existing project.

Distinct from: sandclock, tokpack, hushdiff, runseal, toolflow, hedgescope, diffintent, promptfence, aegispath, rippleguard, shardroom, claimcite, citationcheckertool.

## Install

```bash
pip install -e .
# or
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Usage

```bash
# Scan the current project (looks for README.md)
stubtruth .

# Point at a demo tree
stubtruth examples/demo_project

# JSON for tooling
stubtruth examples/demo_project --format json

# CI gates
stubtruth . --fail-on-stub --fail-on-missing --min-coverage 0.8
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | OK (or no failing gates requested) |
| 1 | Bad args / missing directory |
| 2 | `--fail-on-stub` and at least one stub/empty claim |
| 3 | `--fail-on-missing` and at least one unmatched claim |
| 4 | `--min-coverage` not met |

## Demo

The bundled `examples/demo_project` README claims four APIs. Two are real (`render_widget`, `WidgetCache`); two are stubs (`export_pdf`, `ping_health`):

```bash
stubtruth examples/demo_project --fail-on-stub
# exit 2 — stubs detected
```

## How it works

1. Parse README (and optional `--doc` files) for backticked identifiers and Features-section bullets.
2. Walk Python files under the project root (skipping venvs and caches).
3. Match `def` / `async def` / `class` names (case-insensitive).
4. Classify bodies: `pass`, `...`, `NotImplementedError`, short TODO-only bodies → **stub**; otherwise **implemented**.
5. Report and optionally gate.

## Limitations

- Python AST only (v0.1).
- Claim extraction is heuristic (backticks + feature verbs); it will miss prose-only claims.
- Name collisions across modules are marked **ambiguous** when stub and real both exist.

## License

MIT
