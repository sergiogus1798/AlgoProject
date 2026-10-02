---
q: is the SQX command API authenticated; listens on 0.0.0.0; firewall ports; drive worker over LAN
tag: 🔬  date: 2026-09-21  see: sqx-drive/three-install-topology
---
# The SQX command API listens on 0.0.0.0 with no authentication
Anyone on the network can send `-project action=start` or `-databank action=clear`.
Closed since 2026-10-02: `ufw` on, default deny, allowing only `tailscale0`, 22/tcp and 3389/tcp; before that 5050 answered from the internet. No SQX setting binds it to localhost — the firewall is the only fix. Changing `ufw` is the owner's (sudo); he enters through Tailscale (server `100.113.159.40`).
Upside (unused): a worker on another machine is drivable over LAN without a daemon of its own.

## Evidence
`ss -ltnp`:
```
LISTEN 0.0.0.0:5050   users:(("StrategyQuantX",pid=3385011))
LISTEN 0.0.0.0:8080   users:(("StrategyQuantX",pid=3385011))
```
Machines are used independently, so multi-machine driving is not being built.

2026-10-02, portchecker.io against the public IP — before `ufw enable`: `5050 true, 3389 true`; after: `5050 false, 5051 false, 5060 false, 5070 false, 8080 false, 3389 true`, while `127.0.0.1:5050` still connects.
