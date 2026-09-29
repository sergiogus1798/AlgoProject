---
name: firm-onboard
description: Add a prop firm to the funding studies by the owner's admission protocol — register it as a candidate, check the admission gates on the firm's own pages (self-built EAs on MT5, Spain served, track record, modelable rules, EA traps), build its catalogue reader or typed catalogue, seed its rules file, find its offer surfaces, record its MT5 facts, and hand the owner an admission sheet; only the owner makes a firm active. Also re-runs the gates on a firm whose rules changed. Use when the owner names a prop firm to add, follow, evaluate or compare, or asks whether a firm is worth adding.
---

# /firm-onboard

The protocol (owner, 2026-09-29) that takes a prop firm from a name to a firm the studies use. The
register is `AlgoData/funding/firms.yaml` (`portfolio/funded/catalog/firms.py`); read
`portfolio/funded/catalog/README.md` and `portfolio/funded/deals/README.md` first. A firm moves
**candidate → active** only by the owner's word; you never set `active`. A candidate is followed —
catalogue weekly, deals daily — but it is not in the buying universe, the notifications or the
studies (encargos 33 and 34).

## Ask first — hard rule 11

Stop and ask, never pick, when a gate's answer depends on reading: "third-party EAs are not
allowed" (is an SQX-generated EA third-party?), a fee whose amount is not published, a rule the
firm's pages and the third parties state differently. Put the question in the admission sheet and
leave the gate open; the owner asks the firm's support or decides.

## 1 · Register it

Add an entry to `AlgoData/funding/firms.yaml` — `firm` (lower-case id, no spaces), `name`,
`status: candidate`, `catalogue` (decided in step 3), `code_check`, `added_on`, `admitted_by: ''`,
`notes` in double quotes. Nothing else happens to the studies yet.

## 2 · The admission gates

Each gate is answered **from the firm's own current pages** (site, help centre, terms), with the URL.
A third party only points to where to look. Record each answer as a rule in step 4.

| gate | passes when | why |
|---|---|---|
| G1 EAs | self-built EAs may trade on MT5 in the owner's sizes (today ≤ 10k USD), challenge and funded; any EA fee is stated with its amount | the whole project trades SQX EAs |
| G2 MT5 | MT5 is offered for those plans | the EAs and step 26 (encargo 34) run on MT5 |
| G3 Spain | Spanish residents may buy and be paid (no country ban; a payout method the owner uses) | a plan he cannot buy is not a plan |
| G4 track record | years operating, payouts verifiably made, no recent wave of denied payouts or retroactive rule changes — list the evidence, do not score it | the account is worthless if the firm does not pay |
| G5 modelable rules | targets, daily loss (and its reference and reset hour), max loss and its mode, min days, consistency, refund, payout cycle are all stated | encargo 33 cannot price what it cannot model |
| G6 EA traps | listed, not judged: identical trades across accounts, max allocation per EA, "customise your EA", HFT/latency/tick-scalping bans, max open risk, news windows, overnight/weekend holding, inactivity | each one can rule out a strategy or a portfolio for that firm |

## 3 · The catalogue

- **Auto** when the firm's own site serves its plans in a machine-readable way to a plain request —
  a public JSON its page loads (Hantec), a data object inline in the page (FTMO, FundedNext). Write
  `portfolio/funded/catalog/<firm>.py` with `SOURCE`, `fetch()`, `normalise(raw)` (same schema as the
  others), add it to `refresh.ADAPTERS`, and a knowhow card saying where the data sits.
- **Manual** when the site blocks automated reading (a bot checkpoint, Cloudflare, a login).
  **Never try to get past a protection** — no headless browser to beat a challenge, no spoofed
  cookies. Type `AlgoData/funding/manual/<firm>.yaml` (format: `fundingpips.yaml`) from the best
  public sources, every value unconfirmed, `confirmed: false`, and ask the owner to check the prices
  and rules on the firm's site himself.
- Then `python3 -m portfolio.funded.catalog.refresh <firm>` and `show <firm>`: every plan in the
  owner's sizes present, prices as the site shows them (list price, not a sale), eas_allowed right
  per size.

## 4 · The rules file

`AlgoData/funding/rules/<firm>.yaml`, the format of `hantec.yaml`. At least these keys, each with its
source and status (`confirmed` only from the firm's own page): `eas_allowed` (and any `ea_fee`),
`daily_loss_basis`, `trailing_lock` where the loss trails, `min_days`, `consistency_formula`,
`fee_refund` (and whether it is per account), `reward_share_base`, `payout_cycle`, `payout_min`,
`news_window`, `weekend_holding`, `overnight_holding`, `max_risk`, `forbidden_practices`,
`identical_trades`, `max_allocation`, `inactivity`, `country_ban`, and anything that pays before
funding (FundedNext's challenge reward). Map a value onto a column (`field`, `stage`) only when it is
a number or flag the tables hold; a rule that depends on size goes in the adapter, with a comment.

## 5 · The offers

Find where the firm shows discounts: a sale price in its catalogue (FTMO, FundedNext), a banner
(Hantec), a code check its purchase page calls (Hantec's `CheckDiscount`). Add a function to
`portfolio/funded/deals/sources.py` and a line to `scan.py`; set `code_check` in the register. A
firm with no check gets its codes as `unverified` through `deals.add`.

## 6 · MT5

What step 26 needs: the server name, the symbols the owner trades and their suffixes, commission and
swap, the server's time zone (the daily-loss day), and whether a free trial or demo exists to
backtest on the firm's feed. Record them in the rules file (`mt5_server`, `mt5_symbols`,
`server_timezone`, `mt5_trial`); read-only through the `mt5` MCP if an account already exists.

## 7 · The admission sheet — and stop

Write `docs/AgentPDFs/fondeo-admision-<firm>-<date>.md` in Spanish for the owner: each gate
passed / failed / open with its evidence and URL, the questions only he or the firm's support can
answer, the catalogue's source and how trustworthy it is, the EA traps, and what in its rules
matters for the expected value (refund, fees, payout cycle, rewards before funding). End it with
«¿La doy de alta como activa?». Update the firm's `notes` in the register. Run
`python3 tools/depmap.py && python3 tools/checks.py`, list the files changed, and stop.

## When the owner says yes

Set `status: active` and `admitted_by: owner, <date>` in the register — the only edit you make to it
on his word. The weekly `fundingWatcher`, the daily `dealHunter`, the buying universe and the studies
take it from there. When he says no: `status: rejected` and the reason in `notes`.

## Re-running the gates

When the weekly watcher reports a change to a gate rule of an active firm (EA policy, country ban,
refund, a payout scandal it finds), run steps 2 and 7 again for that firm and hand the owner a new
sheet; the firm stays active until he says otherwise.
