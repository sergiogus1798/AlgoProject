# mt5/winside — code that runs under the Windows Python in the MT5 Wine prefix

The `MetaTrader5` package exists only for Windows, so what talks to the terminal runs inside the
prefix (`bin/mt5-install.sh` installs Python 3.12 at `C:\Python`). Standard library and
`MetaTrader5` only: no project imports, it cannot see them.

| file | what it does | run it | in → out |
|---|---|---|---|
| `query.py` | Read-only verbs against the running terminal: account, terminal, symbols, symbol, bars, ticks, positions, orders, history. Never calls a trading function | `mt5/live.py` runs it as `wine C:\Python\python.exe query.py <verb> <json>` | verb + args → one JSON line, or a CSV |
