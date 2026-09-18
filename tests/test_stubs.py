from pathlib import Path

from stubtruth.stubs import find_symbols


def test_classifies_stub_and_real(tmp_path: Path):
    src = tmp_path / "mod.py"
    src.write_text(
        '''
def real_one(x):
    return x + 1

def stub_one():
    raise NotImplementedError("not implemented")

def empty_one():
    pass

class RealClass:
    def method(self):
        return 42
''',
        encoding="utf-8",
    )
    hits = find_symbols(tmp_path, ["real_one", "stub_one", "empty_one", "RealClass"])
    assert hits["real_one"][0].status == "implemented"
    assert hits["stub_one"][0].status == "stub"
    assert hits["empty_one"][0].status in {"stub", "empty"}
    assert hits["realclass"][0].status == "implemented"
