"""A helper's SystemExit must reach FastMCP as an Exception, not kill the stdio server."""
import pytest

from mt5 import server


def test_systemexit_becomes_runtimeerror(monkeypatch: pytest.MonkeyPatch) -> None:
    """A tool whose helper exits returns a RuntimeError."""
    def boom(*a, **k) -> None:
        """Stands in for a helper that exits."""
        raise SystemExit("terminal abierto")
    monkeypatch.setattr(server.metaeditor, "sqx_indicators", boom)
    with pytest.raises(RuntimeError, match="terminal abierto"):
        server.mt5_install_sqx_indicators()
