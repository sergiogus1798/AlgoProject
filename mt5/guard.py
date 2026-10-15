"""Keep the verification terminal off the owner's real accounts (funded, in a phase, live)."""

from core.paths import MT5_REAL_LOGINS, MT5_VERIFY_LOGINS

WHY = "sin cuenta de verificación (cuenta fondeada protegida)"


class Protected(SystemExit):
    """A real account was about to be logged into for a backtest or a read."""


def is_protected(account: dict | None) -> bool:
    """True when `account["login"]` is a real account of `fleet.vps.accounts` that the owner
    has not listed in `mt5_verify_logins` of config/machine.yaml. None (the terminal's last
    account) is not judged here: the tester's ini then names no login at all."""
    login = int((account or {}).get("login") or 0)
    return login in MT5_REAL_LOGINS and login not in MT5_VERIFY_LOGINS


def refuse(account: dict | None) -> None:
    """Raise Protected, before any terminal is launched, when the account is a protected one."""
    if account and is_protected(account):
        raise Protected(
            f"{WHY}: el login {account['login']} está en fleet.vps.accounts de "
            "config/machine.yaml y no se toca desde el verificador (dueño, 2026-10-15)"
        )
