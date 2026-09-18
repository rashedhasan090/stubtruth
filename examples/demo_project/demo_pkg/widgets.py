"""Mixed implementations for stubtruth demo."""


def render_widget(name: str) -> str:
    """Real implementation."""
    return f"<div class='widget'>{name}</div>"


class WidgetCache:
    """Real cache with a tiny body."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def put(self, key: str, value: str) -> None:
        self._store[key] = value


def export_pdf(path: str) -> None:
    """Claimed in README but not actually implemented."""
    raise NotImplementedError("not implemented")


def ping_health() -> None:
    # TODO: wire up health endpoint
    pass
