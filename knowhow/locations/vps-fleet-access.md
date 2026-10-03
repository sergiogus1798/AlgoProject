---
q: How do I reach the Windows VPS fleet machine?
kw: how to reach the Windows VPS; ssh vps; Tailscale; live MT5 terminals; fleet; run PowerShell remotely; VPS specs RAM OS; ports open to the internet
tag: 🔬  date: 2026-10-02  see: sqx-drive/api-no-auth, locations/live-ea-magic-numbers
---
# The Windows VPS is reached with `ssh vps`, over Tailscale only
`ssh vps` (alias in `~/.ssh/config`, key `~/.ssh/id_ed25519_vps`, no passphrase so cron can use it) logs in as `administrator`; host, IP and terminal folders are in `config/machine.yaml` under `fleet.vps`. Its sshd rule admits `100.64.0.0/10` only, so port 22 is closed from the internet.
The remote shell is `cmd`: a quoted one-liner breaks. Pipe the script instead — `ssh vps 'powershell -NoProfile -Command "$input | Out-String | Invoke-Expression"' <<'EOF'` … `EOF`. (`-Command -` reads the script line by line: it stops, silently and with exit 0, at the first multi-line `{ }` block.) Files travel with `scp`; there is no `rsync` and no Python on the VPS.
It is **Windows Server 2022 Datacenter** (build 20348), not the Windows 10 encargo 35 assumed — supported until 2031; patched by the owner on 2026-10-02 (build 20348.169 → 20348.5622, nothing pending), after five years without updates. 6 cores, 12 GB.
The terminals are **not portable**: each keeps its data in `%APPDATA%\MetaQuotes\Terminal\<hash>\` (`origin.txt` names the install), and all share `…\Terminal\Common\Files\`. Eight data folders exist (Hantec, FTMO, MetaQuotes, Five Percent ×2, Infinox ×2, IC Markets EU); only the first three run. No terminal has anything in `MQL5\Services`, and there is no scheduled task of ours.
The old key `~/.ssh/id_ed25519` has a passphrase the owner does not remember; do not use it for anything unattended.
Still open to the internet on the VPS's public IP: 3389 (RDP) and 5986 (WinRM HTTPS). The owner left them open (2026-10-02: his PC is not on Tailscale and for now the VPS only holds funded-challenge accounts) — not a finding to re-report; offer again only when real money goes there. RDP is under brute force (1,816 failed logons in 27 min, no lockout threshold).
Both Tailscale node keys expire 2027-03-31 unless expiry is disabled in the admin console.

## Evidence
2026-10-02, `ssh vps "whoami & hostname & ver"` → `vmd182013\administrator`, `Microsoft Windows [Version 10.0.20348.169]`.
Three `terminal64.exe` running: FTMO 390 MB, Hantec 588 MB, MetaQuotes 391 MB; 5.8 GB of 12 free; C: 164 GB free.
`tailscale ping 100.112.93.53` → direct, 98 ms. From this server, public IP: 22 closed, 3389 open, 5986 open, 5985 and 445 closed.
2026-10-02 (late), listing: terminal builds Hantec 6230, MetaQuotes 6230, FTMO 5833; the three run in session 2 (the RDP desktop), started 2026-10-02 23:53-23:55. A heredoc with a multi-line `ForEach-Object { }` under `-Command -` printed its first section and nothing else.
2026-10-02 23:54, after the update and reboot: build `20348.5622`, 0 updates pending, `sshd` and `Tailscale` running with automatic start, SSH rule still `100.64.0.0/10`.
