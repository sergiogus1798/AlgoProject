---
q: is the SQX command API authenticated; listens on 0.0.0.0; firewall ports; drive worker over LAN
tag: 🔬  date: 2026-09-21  see: sqx-drive/three-install-topology
---
# The SQX command API listens on 0.0.0.0 with no authentication
Anyone on the network can send `-project action=start` or `-databank action=clear`.
On an untrusted network close 5050/5051/5060/5061/5070/5071/8080/8081/8082 at the firewall (needs sudo — owner's job).
Upside (unused): a worker on another machine is drivable over LAN without a daemon of its own.

## Evidence
`ss -ltnp`:
```
LISTEN 0.0.0.0:5050   users:(("StrategyQuantX",pid=3385011))
LISTEN 0.0.0.0:8080   users:(("StrategyQuantX",pid=3385011))
```
Machines are used independently, so multi-machine driving is not being built.
