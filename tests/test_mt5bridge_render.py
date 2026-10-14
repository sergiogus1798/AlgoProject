"""Known answers for the Verificar table's helpers: the state cell and the missing result."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.desktop.mt5bridge.render import no_result, short


def main() -> None:
    """A long or multi-line state is cut to one line; a failure is said, escaped."""
    assert short("hecha") == "hecha"
    assert short("fallida: a\nb") == "fallida: a…"
    assert short("x" * 80) == "x" * 70 + "…"
    said = no_result({"error": "a <b>\nc"})
    assert "falló" in said and "a &lt;b&gt;<br>c" in said
    assert "En marcha" in no_result({})
    print("test_mt5bridge_render: ok")


if __name__ == "__main__":
    main()
