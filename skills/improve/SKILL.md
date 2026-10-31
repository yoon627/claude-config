---
name: improve
description: The analysis axis of the dlc self-improvement loop — an orchestration that reads mechanical checks of operating-asset consistency together with the workflow failure signals hooks accumulate automatically (telemetry), the wiki workflow-failures page and feedback memory, and presents improvement candidates ranked by evidence and frequency. In `deep`, it also runs an axis that periodically (45 days) re-judges overlap between features Claude Code absorbed natively and the home-grown harness. Findings stop at reporting and proposals; fixes happen only after user approval, through wt→dlc (no self-modification of operating assets §1 — no automatic fixes). Use on an explicit `/improve` call. Not for simple questions or code changes.
---

# improve — the analysis axis of the self-improvement loop (assets read-only, ranking, proposals)

`/improve` analyzes 1) operating-asset consistency (successor of the old `/audit`) and 2) the signals hooks accumulate automatically (telemetry) together, and presents **improvement candidates as a ranking**. Relation to the other axes of the loop: **collection** is automatic by hooks (`scripts/dlc-signal.js` — early-stop, guard, doc-drift, router and plan signals), **analysis and proposals** are this skill, **applying** is a separate task through `wt→dlc` after user approval, and **checking the effect** is the signal trend at the next `/improve`. Like c/e, the main agent runs it directly (not delegated to a subagent).

## When to use
- On an explicit `/improve` call. After adding or renaming assets, when workflow friction feels repetitive, or when you want to check the effect of an improvement.
- Not for simple questions, exploration or code changes.

## Role boundaries (avoiding overlap — important)
- **README ↔ surface drift** → the area of the `dlc-doc-drift` hook (Stop warning during the session). improve **does not re-judge it**; it only **aggregates after the fact** the `doc-drift-*` signals the hook emitted.
- **Internal integrity of the wiki** (orphans, dead links, contradictions) → the area of `/wiki lint`. improve only checks the index↔pages counts of the shared wiki (`~/.claude/wiki` clone, path override `CLAUDE_IMPROVE_WIKI`) and recommends lint. Check 6 also reports an error if this repo tracks `wiki/` (the shared wiki is a private repo — a CI gate).
- **Updating the ledger** (recording native-overlap judgments in the wiki) → the area of `/wiki ingest`. improve goes **up to a draft judgment**; the write is done by ingest after approval (§6 boundary).
- Unique to improve: cross-references between assets (settings↔scripts, MEMORY↔memory, docs↔agents, dead-script candidates) + **combined analysis of signal and failure history and the ranking of improvement candidates** + **re-judging overlap with what was absorbed natively** (§6) — the part no other mechanism does.

## Behavior (4 basic steps + 2 `deep` axes + wrap-up)

### 1. Mechanical checks + signal aggregation — `improve.sh`
Run `bash skills/improve/improve.sh` **once** from the repo root (read-only). Output:
- Checks 1–6 (successors of the old audit): `[error]` broken execution path (settings→scripts missing — an absolute path in an exec-form `args` is checked as that exact path, and `~` or `$HOME` is an error; CLAUDE.md→agent missing; skill or agent frontmatter format violations — YAML errors, outside the allowed format, missing name/description, `scripts/frontmatter-lint.js`) / `[warn]` unregistered or missing on one side (MEMORY index, wiki counts) / `[info]` dead-script *candidates* (not conclusive) / `[ok]`.
- Check 8 = **plan-lint** (all tracked plans, always): `scripts/plan-lint.js` checks the §10 plan format and integrity (mandatory frontmatter keys, mandatory H1 sections, Tasks checkboxes and dates, **broken Acceptance references**); violations are `[warn]`. Skip if there are no tracked plans. (The shell has no active-plan concept, so it checks all of them — only /c and /e target the active plan.)
- Check 7 (new): aggregates `~/.claude/telemetry/dlc-signals.jsonl` — per kind, `sessions` (unique), `raw` and the time span. It shows the **failure axis** (early-stop-verify, early-stop-plan-drift, doc-drift-*, guard-worktree-deny, main-edit-ask, plan-blocked) and the **activity axis** (router-*, review-disposition, early-stop-wait-shell — not failures; activity volume and waiting turns) separately. The canonical kind list is `KINDS` in `scripts/dlc-signal.js`. Judge effects by sessions (unique) first — raw can be dominated by repeated firing in the same session.
- Check 9 = **freshness of the native-overlap ledger** (periodic gate): if the `checked` date in `~/.claude/wiki/pages/decision/native-overlap-ledger.md` (path override `CLAUDE_IMPROVE_LEDGER`) is older than the threshold (45 days, `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`), recommend the §6 re-judgment. **It emits only `[info]`** — it is a reminder, not a consistency violation, so it does not pollute the err/warn counters or the severity axis of the ranking. A missing ledger, bad frontmatter, a bad date or a future date are only stated as facts and skipped (keeping `exit 0`). The judgment logic is `scripts/native-overlap-lint.js` (pure functions + CLI, with tests).

### 2. Comparison with accumulated history
- Read the tracking table (failure, count, status) of `~/.claude/wiki/pages/decision/workflow-failures.md` — compare it with the signals to find **failures whose count update was missed**.
- The `MEMORY.md` index (feedback behavior instructions) — whether they were actually applied in recent work, and whether there are dead rules.
- `# Workflow Findings` and `# Deferred` of the current/recent plan logs (`<slug>-log.md`; the body for an old-format plan) — repeated items that exist only in the plan log (or old plan body) and were not promoted to the wiki.

### 3. Semantic checks — LLM judgment (what machines cannot catch)
- Contradictions between documents (rule conflicts between CLAUDE.md ↔ SKILL.md), duplicate skills on the same trigger, dead rules (items no longer valid).
- Read the related files and judge from evidence (no guessing §1).

### 4. Improvement candidate ranking + disposition proposals (no fixes)
- Each candidate = `what is wrong · evidence (signal numbers/file:line) · proposed change (which file, how) · expected effect (which signal should drop)`.
- Ranking criteria: unique-session frequency of failure signals × severity (broken execution path > repeated friction > inventory) × cost of fixing (smaller ranks higher).
- **Effect check**: report the trend of whether the signals of items previously handled as `fixed` actually dropped (if not, they go back to being improvement candidates).
- **Disposition**: if the user approves, the fix is **a separate task (wt→dlc)** — changing operating assets is a file change, so a worktree is mandatory. It joins the same path as dlc's rule "propose a fix when the same failure repeats 2+ times" (wiki workflow-failures). With 0 errors and no meaningful signal, report "no improvement candidates".

### 5. Wide observation — `improve.sh deep` (opt-in)
When the 4 basic steps are not enough, or for a periodic check, `bash skills/improve/improve.sh deep` adds 3 more sections (still read-only, no secrets printed):
- Check 10 **size of the injected and loaded surface** (`wc -c`): bytes of CLAUDE.md, skills/*/SKILL.md and agents/*.md + total — quantitative evidence of the token pressure on every session and task (slimming candidates).
- Check 11 **usage counts** (`scripts/usage-count.js`): transcript-based frequency of skill, subagent and codex calls (counts and slugs only, no raw text or file names) — identifies rarely used assets (dead candidates) vs high-frequency friction points.
- Check 12 **MCP server inventory** (names only from `~/.claude.json`): the registered MCP servers — unused or duplicate candidates.

In deep, check 9 also gets one more line — it prints the **delta window** (the ledger's `checked_version` → the installed `claude --version`), telling §6 where to start reading the changelog.

deep is **only a wider observation** — the judgment, proposal and disposition path is the same as the 4 steps (measure→judge→propose, no fixes, the main agent directly). If an external lookup (ecosystem, versions) is needed, the main agent judges it with a separate researcher, but **does not put local transcript, MCP or telemetry contents into the web prompt**.

### 6. Native overlap check — deep only, periodic (cleanup in the other direction)

Re-judges whether the home-grown harness **is holding on to features Claude Code absorbed natively**. Where 1–5 look at "do the assets disagree with each other", this axis looks at "is the asset **still needed**" — the only axis that takes the outside (native) as its reference.

**When**: when check 9 reports that the threshold has passed, or right after a large native release. It does not run in a basic (non-deep) run (web lookup cost).

**Procedure**:
1. **Read the ledger** — the existing judgments and `checked_version` in `~/.claude/wiki/pages/decision/native-overlap-ledger.md`.
2. **Look up the delta** — download the raw `CHANGELOG.md` whole (`https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`) into a fresh scratch directory and read the entries **only after `checked_version`** locally; not WebFetch, which summarizes a large document so its tail is cut and version attribution shifts. The docs page (`https://code.claude.com/docs/en/changelog`) is only a cross-check. A full lookup only when there is no ledger or no `checked_version`. This lookup falls under the "external lookup" rule above — **do not put local transcript, MCP or telemetry contents into the web prompt**.
3. **Draft re-judgments** — **do not modify files.** Present the existing rows that now have grounds to be overturned, and the components that newly overlap in the delta, **as a draft table**. Values are `keep`/`watch`/`retire` (defined in the ledger). **No judgment without evidence** (§1) — each row is backed by `vX.Y.Z + date` or a local file path.
4. **Join the ranking** — this axis's candidates have 0 telemetry signals, so they are always at the bottom of step 4's "unique-session frequency" axis. **Substitute score: degree of overlap (`retire` > `watch`) × upkeep cost (check 10 surface bytes, whether always injected) × removal cost.**
5. **Disposition** — as in step 4, **up to proposals**. See the boundary below.

**Boundary (important)**: `/improve` **does not write the ledger.** Judgments are presented as drafts, and updating the ledger, `index.md` and `log.md` is done by **`/wiki ingest` after user approval**. Even with a `retire` judgment, it does not remove the home-grown component — it only puts it up as a ranking candidate, and the actual removal is a separate task through `wt→dlc` after approval (§1 no self-modification of operating assets, §11 ingest is a proposal, §13 no recording without approval).

**Limits**: if the installed version lags behind the latest release, the delta window cannot cover the latest absorptions — **"no version change ≠ no overlap"**. This is especially true of installs with automatic updates turned off.

### 7. Wrap-up — update the `last-improve` marker (basic and deep alike)
Once the ranking and disposition proposals (or "no improvement candidates") are settled, run `node ~/.claude/scripts/dlc-signal.js mark` once **right before printing the final report**, and put its result in the report. The SessionStart notice "/improve recommended — failure signals accumulated in N sessions (since the marker)" counts only sessions after this marker time — without the update, a threshold once crossed never comes back down, and the recommendation loses its meaning as a signal.
- If you did not actually see the signals, **do not run it** — when `improve.sh` ended non-zero, check 7 printed `신호 집계 실행 실패`, or you stopped before the report. Running it anyway would also drop signals you never saw from the count. A check **finding** an `[error]` is not a run failure.
- Why the path is fixed to `~/.claude/scripts/`: this SKILL is loaded at user level (main checkout), and calling it by a cwd-relative path can run an old script without this feature in a worktree session.
- If the output has no `last-improve 마커 갱신:` line or ends non-zero, it failed — put one line in the report (the recommendation keeps showing in the next session too).

## Boundaries (what it does not do)
- **No fixes** — up to checks, aggregation, ranking and proposals. No self-modification of operating assets (§1). improve.sh has no modifying or destructive commands (read-only). The only write is the step 7 marker (`<signalDir>/last-improve` — default `~/.claude/telemetry`, overridden by `CLAUDE_DLC_SIGNAL_DIR`; gitignored local state, not an operating asset). **The wiki ledger is no exception** — the §6 judgment is a draft and the write is `/wiki ingest` after approval.
- **No re-judging of signals** — telemetry is the after-the-fact aggregation of hook judgments. README drift and wiki internals are the hook's and `/wiki lint`'s areas respectively.
- **No concluding or deleting dead scripts** — info candidates only; the actual judgment is a person's.
- Not delegated to a subagent — the main agent runs, judges and reports directly.
