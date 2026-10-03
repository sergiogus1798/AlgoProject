---
name: sync
description: Put the project's current state on GitHub and keep it there — check what changed, refuse to commit data or machine-specific files, run the mechanical checks, propose the commits grouped by theme and make them only after the owner's yes, and push master. Also bootstraps the remote the first time. Use when the owner asks to push, sync, back up or publish the project, to commit pending work, before cloning it on another machine, or asks whether GitHub is up to date.
---

# /sync

Keeps the GitHub copy equal to what is on this machine, so cloning it elsewhere gives a working
project. It commits and pushes code and documentation. **It never pushes data** — that is what the
data root is for, and `.gitignore` enforces it.

It is safe to run at any time: it touches no SQX install, starts no worker and reads no databank.

## The daily proposal: propose → the owner's «sí» → apply

Every morning (05:45, `bin/nightly-commit-proposal.sh`) an agent that cannot run `git add`, `commit` or
`push` writes `AlgoData/audit/<date>-commit.md` (for the owner, in Spanish) and `<date>-commit.json`
(groups of `{message, body, paths}`, plus `en_curso` and `paradas`). **Do not redo the grouping by hand
when the owner says «aplica la propuesta de commit», «commitea lo de la noche» or similar.** Run:

```bash
python3 -m tools.commit_apply --dry-run          # read the summary to him if he did not see the .md
python3 -m tools.commit_apply --trailer "<the attribution line this session gives>"
```

Options: `[YYYY-MM-DD]` another day · `--only 1,3` some groups · `--no-push` · `--force` (a proposal older
than 12 h, or groups whose files changed after it — only if he says the tree did not move). It stages
and commits only each group's own paths, pushes once with the gh credential helper (plain `git push`
fails from a non-interactive shell) and prints in Spanish what was committed, skipped and left. Show him
that summary. If there is no proposal for today, or it is stale, run the steps below instead.
Never apply a proposal without his yes: the commit is his decision (hard rule 12).

## Step 1 — is there a remote at all?

```bash
git remote -v
```

**If there is one**, go to step 2.

**If there is none**, bootstrap it. The repository must be **private**: it holds the owner's
strategy research. Never create it public, and never ask him to confirm that choice — private is
the answer.

```bash
gh auth status                       # must say "Logged in to github.com"
gh repo create AlgoProject --private --source=. --remote=origin
```

`gh` lives in `~/.local/bin/gh`; it is not installed system-wide. If `gh auth status` says logged
out, **stop and ask the owner to run `gh auth login` himself** in his own terminal — the flow needs
a browser and a one-time code, and no session can do it on his behalf.

## Step 2 — read what changed before touching anything

```bash
git status --porcelain -uall
git diff --stat
git log --oneline -5
```

Then check the three things that must never be committed. Each is a stop, not a warning:

```bash
# 1. Nothing machine-specific. machine.yaml is the ONLY file allowed to differ between
#    computers, and it is gitignored. If it appears staged, .gitignore has been broken.
git status --porcelain | grep -E 'config/machine\.yaml' && echo "STOP"

# 2. No data, and no strategies. Heavy data belongs in ~/Desktop/AlgoData (hard rule 7);
#    the one legal .sqx is the golden-test fixture.
git status --porcelain -uall | grep -E '\.(csv|parquet|sqx|db|h2\.db)"?$' \
  | grep -v 'tests/fixtures/' && echo "STOP"

# 3. No secrets.
git diff --cached -U0 | grep -inE '(api[_-]?key|secret|password|token)\s*[:=]\s*.{16,}' && echo "STOP"
```

And size — a repository that has to be cloned over a phone tether stays small:

```bash
du -sh .git; git status --porcelain -uall | grep '^??' | sed 's/^?? //' | tr -d '"' \
  | while read -r f; do du -k "$f"; done | sort -rn | head -10
```

Anything above about 2 MB that is not a manual screenshot: ask before committing it. Anything that
looks like exported data: it goes to the data root instead.

## Step 3 — the mechanical checks must be green first

A broken commit on GitHub is worse than an uncommitted one, because the next clone starts from it.

```bash
python3 tools/depmap.py && python3 tools/checks.py
python3 tests/test_cfx.py && python3 tests/test_sqxfile.py
```

`depmap.py` rewrites `docs/DEPENDENCIES.md`, so run it **before** staging — otherwise the file it
regenerates is left dirty after the commit. If `checks.py` reports anything, fix it or stop; never
push over it.

## Step 4 — group by theme, then ask

One commit per concern, never one giant "update". The owner reads every line of history, and a
commit message that says *why* is the only thing that survives the session that wrote it. The
owner commits (hard rule 12): this step ends with a question, not a commit.

List each group with its message and its files, then ask **¿Quieres hacer el commit?**. Only after
a yes, per group, stage only the files named in the group, by name — never a blanket add of the
whole tree, because other sessions leave their own changes in it:

```bash
git add <the group's files> && git commit -m "core: <what changed>" -m "<the attribution lines the session gives>"
```

`python3 -m tools.commit_apply` does exactly this from a proposal (see above); by hand, the same rule.

The themes that recur here: `core:` shared readers · `sqx:` exporters, inspection, curation ·
`tasks:` population analysis · `strategies:` single-strategy studies · `portfolio:` ·
`docs:` manual pages · `knowhow:` findings · `claude:` skills and permissions ·
`tools:` checks and depmap.

Rules for the message:

- First line under 72 characters, no trailing period, imperative or a `prefix:` label.
- A body whenever the change is not self-evident: what was wrong, what it is now, and how it was
  verified. Numbers beat adjectives.
- Never invent verification. If it was not run, the message does not claim it.

## Step 5 — push master

There is one branch, `master` (rule 12). Push it, and the tags — only once the commits of step 4
exist, i.e. after the owner's yes.

```bash
git push -u origin master
git push origin --tags
```

Then confirm the remote actually has it, rather than trusting that the push said so:

```bash
git status -sb                       # should show ...origin/master with no ahead/behind
gh repo view --web --json url -q .url
```

## Step 6 — report, in Spanish

Tell him: which commits went up, the clone URL, and **anything
left uncommitted and why**. If something was deliberately not pushed, say so — silence about it is
the failure mode that matters.

## What this skill does NOT do

- **It does not create, switch or merge branches.** One folder, one branch, `master` (rule 12).
- **It does not rewrite history.** No amend of a pushed commit, no rebase, no force push. If a
  pushed commit is wrong, the fix is another commit.
- **It does not delete anything.** Not a branch, not a remote, not a file.
- **It does not commit work it does not understand.** A half-finished refactor from another session
  — files changed with callers that no longer match, `checks.py` red — gets reported to the owner,
  not committed on his behalf.

## Cloning on another machine

What the clone lacks (`config/machine.yaml`, the data root, `AlgoData/manual-fuentes/`) and the
steps to set it up are in the owner's chapter `AlgoData/manual-fuentes/10-github.md` (PDF in
`docs/manual/`). Afterwards `python3 tools/checks.py` must be green. On Windows, only the analysis
half runs — see the Windows section of `README.md`.
