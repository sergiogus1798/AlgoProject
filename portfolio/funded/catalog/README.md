# portfolio/funded/catalog — what each prop firm sells, and under which rules

The funding database: every plan (type × size × account currency) of every firm we trade with EAs,
its list price, its rules per stage, its add-ons with their surcharge, **every add-on combination
priced with the rules it leaves in force**, and a compendium of the rules no catalogue carries.
Which firms: the register `AlgoData/funding/firms.yaml` (`firms.py`) — active ones are in the
buying universe and the studies; candidates are followed while the `/firm-onboard` protocol runs.
Today Hantec Trader and FTMO active, FundedNext and FundingPips candidates. Encargo 33 reads it.

Where it lives (`core.paths.funding_dir()`, never in the repo):

| path | what |
|---|---|
| `AlgoData/funding/funding.sqlite` | the database |
| `AlgoData/funding/catalogs/<firm>/<date>.json` | the raw catalogue, kept only when it changed |
| `AlgoData/funding/firms.yaml` | the register: each firm's status (candidate, active, rejected), catalogue kind, code check |
| `AlgoData/funding/manual/<firm>.yaml` | the typed catalogue of a firm whose site blocks automated reading |
| `AlgoData/funding/rules/<firm>.yaml` | the curated rules, edited by hand and by the `fundingWatcher` agent |
| `AlgoData/funding/csv/{combos,plans,rules,changes}.csv` | the current picture for a spreadsheet, rewritten by every refresh — never edit, never read from code |

## Tables

| table | key | holds |
|---|---|---|
| `plans` | `plan_key` = `firm:family:size:ccy` | steps, size, list price and its currency, `eas_allowed` |
| `stages` | `plan_key`, `stage` (`phase1`…`phase3`, `funded`) | target, daily loss, max loss and its mode (`static`, `trailing`, `eod_trailing`), min days, time limit, consistency, reward share, payout days, news and weekend allowed, `filled_from` |
| `options` | `plan_key`, `option_key` | label, effect as the site words it, surcharge in % of the base price |
| `rules` | `firm`, `family`, `rule_key` | the compendium: value, text, source URL, `confirmed` / `unconfirmed` / `conflict`, last checked |
| `combos` | — (rebuilt each refresh) | one row per plan × subset of priced add-ons: price and the rules after them |
| `changes` | — (appended) | every added, removed or changed value, by day |
| `snapshots` | — (appended) | every fetch: when, source, hash, raw file |
| `deals` | `firm`, `kind`, `code`, `plan_key` | the offers found daily, one row per deal × plan — `portfolio/funded/deals/README.md` |

The four first tables are **versioned**: a row is current while `valid_to` is NULL; a change
closes it and opens another, so any past price is a query away. In a numeric rule, **0 means the
rule does not exist, NULL means not known yet**. `filled_from` names the curated rule that set a
value; a trailing `?` says it is unconfirmed. Discounts are ignored: prices are list prices.

## Files

| file | what it does | run it | in → out |
|---|---|---|---|
| `combos.py` | Every add-on combination of every plan, priced, with the rules it leaves in force. | — | rows → combos |
| `firms.py` | The firms register: which prop firms the project follows, and whether each is in the studies (`AlgoData/funding/firms.yaml`). | — | YAML → ids |
| `ftmo.py` | FTMO's catalogue, read from the pricing table embedded in its home page, as normalised rows. | — | HTML → rows |
| `fundednext.py` | FundedNext's CFD catalogue, read from the `packages` its home page carries in the Next.js payload. | — | HTML → rows |
| `hantec.py` | Hantec Trader's catalogue, read from the public JSON its purchase page loads, as normalised rows. | — | JSON → rows |
| `manual.py` | A firm whose site cannot be read by code: its catalogue typed in `AlgoData/funding/manual/<firm>.yaml`, as normalised rows. | — | YAML → rows |
| `overlay.py` | The curated rules file of a firm: loaded as compendium rows and laid over the scraped rows. | — | YAML → rows |
| `refresh.py` | Re-read every firm's site and rules file into the funding database and print what changed. | `python3 -m portfolio.funded.catalog.refresh [firm…]` | sites + rules → db |
| `schema.py` | The funding database's tables, keys and connection — one SQLite file under the data root. | — | → `funding.sqlite` |
| `show.py` | Print a firm's plans, or one plan with chosen add-ons: its price and every rule in force. | `python3 -m portfolio.funded.catalog.show hantec:express:25000:USD MAX_DRAWDOWN PROFIT_TARGET` | db → stdout |
| `store.py` | Write one firm's rows into the versioned tables, logging every added, removed or changed value. | — | rows → tables |

## Adding a firm

The `/firm-onboard` skill (`.claude/skills/firm-onboard/SKILL.md`): register as candidate, admission
gates on the firm's own pages, an adapter in `refresh.ADAPTERS` (with `SOURCE`, `fetch()`,
`normalise(raw)`) or a typed `manual/<firm>.yaml` when the site blocks reading — never forced — the
rules file, the offer surfaces, the MT5 facts, and an admission sheet. Only the owner makes it active.
A new add-on key gets its line in `combos.EFFECTS`; until then the refresh names it `UNMODELLED`.
