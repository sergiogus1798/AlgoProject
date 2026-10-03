---
q: How do I call the ui daemon's HTTP API from a script, and why is my request or my launcher run answered 403 or refused?
kw: 403 petición rechazada host origin token; X-Algo-Token; AlgoData/ui/token-<port>; core.uitoken; ALGO_UI_PORT; curl to 8765 refused; «esta confirmación no existe o ya se usó»; «el plan cambió desde que lo viste»; nonce; launch/run advance/run mt5bridge/verify without preflight; CSRF; DNS rebinding; close-terminal cross-origin; uiwalk exits 1 with no output
tag: 🔬  date: 2026-10-03  see: ui/stale-ui-daemon
---
# The daemon serves only a caller with its session token, and a launcher only with its preflight's nonce
Every route but `GET /api/health` wants header `X-Algo-Token` = `core.uitoken.read(port)` (file
`AlgoData/ui/token-<port>`, 0600, new at each daemon start), `Host` `127.0.0.1:<port>` or
`localhost:<port>`, and no `Origin` but the daemon's own — else 403 `petición rechazada: host|origin|token`.
From Python: `ui.desktop.client.get/post` after `client.aim(port)`. Never copy the token anywhere.
`POST /api/launch/run`, `/api/advance/run` and `/api/mt5bridge/verify` also need the `nonce` their
preflight returned — one use, 10 minutes, bound to the confirmation text: preflight, then run with it.
Code importing `ui.daemon` functions (autopilot, `mt5.verify`) passes neither. → `ui/daemon/README.md`

## Evidence
Scratch daemon on 8757, 2026-10-03: `GET /api/jobs` and `POST /api/jobs/x/cancel` → 403 without the
token, 200 with it, 403 with the token plus `Origin: http://evil.example` or `Host: evil.example:8757`;
`/api/health` 200 without; a second `serve --port 8757` exits 1 and leaves the token as it was.
`tests/test_ui_gate.py` holds the same as known answers, plus the nonce's five refusals per launcher.
Before this, any local process could `POST /api/launch/run` (only `/api/launch/chain` compared a plan),
and a web page could fire the two body-less POSTs (`close-terminal`, `jobs/<id>/cancel`) cross-origin.
`uiwalk.py` exiting 1 with nothing printed is not the gate: its `sys.excepthook` swallows an exception
raised in `walk` itself (2026-10-03: a `QTabBar` of Estrategia deleted while `drive` iterated).
