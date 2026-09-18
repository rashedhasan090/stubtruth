from stubtruth.claims import extract_claims


def test_extracts_backticks_and_feature_bullets():
    md = """# Tool

## Features

- Provides `alpha_fn` for sorting
- Implements BetaThing for grouping
- Supports plain text only

Also see `gamma_helper` in the API.
"""
    claims = extract_claims(md)
    tokens = {c.token.lower() for c in claims}
    assert "alpha_fn" in tokens
    assert "betathing" in tokens
    assert "gamma_helper" in tokens
