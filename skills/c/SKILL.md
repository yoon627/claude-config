---
name: c
description: plan-continue orchestration that finds the in-progress plan (CLAUDE.md §10) of the current worktree/repo, diagnoses the remaining work and the plan↔actual (git/code) sync state, corrects the plan if they diverge, then continues with the next action when it is clear. It also takes in human review comments from that branch's PR. Use on an explicit `/c` call or a request like "let's continue the work in progress". Not for simple questions, exploration or starting new work (creating a new plan is dlc's job).
---

# c — plan continue

Find the in-progress §10 plan, diagnose **the remaining work + the sync state**, correct a diverged plan to match the actual state, and then, if the first unchecked Task is clear, continue running it (on an exception, stop and present). The automated version of CLAUDE.md §10 **Start**·**In-progress sync** — **CLAUDE.md wins on conflict**.

## When to use
- An explicit `/c` call, or when you are about to continue a plan that was in progress.
- Not for simple questions, exploration, read-only work or starting new work. **If there is no plan, do not create one** (that is the job of dlc / the start of work).

## Behavior (3 steps: find → diagnose → correct·continue)

### 1. Find the plan
- `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`.
- Search locations (only those that exist, deduplicated):
  1. `<ROOT>/plans/`
  2. When the cwd is a worktree, the main worktree's plans — the first `worktree <path>` line of `git worktree list --porcelain` → `<main>/plans/`. Skip it if it is the same as (1).
  > plans/ is independent per worktree (branch), so look at both to miss nothing (it is tracked, but its content differs per branch).
- **Matching** (§10 rule): the dir whose **dir name** (`<YYYY-MM-DD>-<slug>`) contains the `BR` string → the one `*-plan.md` in it.
  - 1 → adopt it.
  - 2+ → present the candidate list and let the user choose.
  - 0 → fallback.
- **Fallback (0 matches)**: read the frontmatter of every plan in the search locations (`*/*-plan.md` + `*.md` directly under each plans/ root), and **present those with `status: in_progress|blocked` sorted by `updated` descending → the user chooses**. Do not pick one automatically by guessing. If all are done or none exist, report "no plan to continue" and stop.

### 2. Diagnose (after reading the plan)
Read the plan (together with the plan log in the same folder if there is one — it carries over earlier review dispositions and Deferred items) and look at two axes. If the frontmatter has `intent:`, also read that `intent.md` (§10 bundle intent) — the common Constraints, Open questions and `# Plans` (sibling plans) live there, so the delta in the plan's `# Goal` labeled bullets alone does not restore the requirement. If the file is missing, one line "intent link broken" in the report (a correction target in step 3). Read and correct an old-format plan (no `# Tasks`) by the §10 mapping table.
- **Remaining work**: `status` + the unchecked items of `# Tasks` (the first item = the next action) + `# Blockers`.
  - `done` → note "already done", then ask whether to continue anyway.
  - `blocked` → show `# Blockers` and judge whether it can be unblocked.
  - No unchecked Task, or the first item is no longer valid → rebuild it from the actual state in step 3.
- **Sync check** (plan ↔ actual):

  | Check | How | Divergence signal |
  |---|---|---|
  | Freshness | frontmatter `updated` vs the latest commit date | `updated` is long past |
  | Task paths exist | check that the backtick paths of unchecked Tasks exist | missing/moved files |
  | Commits reflected | `git log --oneline origin/main..HEAD` | commits not in any checked Task |
  | Unreflected changes | `git status --short` | uncommitted changes not in any Task |
  | Completion | is `git log --oneline origin/main..HEAD` empty / `git branch --merged origin/main` | merged but `status≠done` |
  | Plan integrity | `node scripts/plan-lint.js <adopted plan>` (if present) | violations of the §10 format (mandatory frontmatter keys, mandatory sections, Tasks checkboxes and dates) and **broken Acceptance references** |

  - If a check command fails (no origin, etc.), skip only that check and state it in the report. **plan-lint violations are shown and corrected (not a hard stop)** — reflect them in the step 3 correction.
- **PR review intake** (only when a plan matched, read-only): collect the **human** review points of that branch's PR (summary, conversation, **inline line**) and pass them to the step 3 disposition.
  - Identify the PR: `gh pr list --head <BR> --state all --limit 3 --json number,state,title`.
  - Collect (3 sources, all REST with `--paginate` — the API returns 30 per page, so without it the rest are silently dropped; **inline is mandatory, since it is the main form of code comments**):
    - Review summary·state: `gh api --paginate repos/{owner}/{repo}/pulls/<n>/reviews --jq '.[] | {user:.user.login, type:.user.type, state, submitted_at, commit_id, body}'` — a review with an empty body counts only by its `state`, and an empty `COMMENTED` one is skipped (its content is in the inline source).
    - Conversation comments: `gh api --paginate repos/{owner}/{repo}/issues/<n>/comments --jq '.[] | {user:.user.login, type:.user.type, created_at, body}'`.
    - **Inline (line-level) comments**: `gh api --paginate repos/{owner}/{repo}/pulls/<n>/comments --jq '.[] | {id, in_reply_to_id, user:.user.login, type:.user.type, created_at, commit_id, path, line:(.line // .original_line), body}'`. The times and commits are what step 3 compares with later commits. ⚠️ `gh pr view --json reviews,comments` **does not return** inline comments (cli/cli #11477) — missing them misreports the code comments the user left as "none" (silent false-negative).
  - **Humans only**: exclude a comment whose `type` is `Bot` — not the `[bot]` login suffix, which `gh pr view` drops and Copilot's inline comments never have. A human reply to a bot inline comment (`in_reply_to_id`) is kept, with the bot comment read only as its context. Mark a comment whose `user` equals the current user (`gh api user --jq .login`) as **self** instead of dropping it — it may be the user's own review (one person writing and reviewing the PR) or something Claude posted under the user's account, and nothing in the comment tells the two apart. If the current login cannot be fetched, treat every comment as self.
  - **fail-open**: `gh` not installed, not authenticated, no remote or no PR → skip only this check and one line "PR review: could not check (<reason>)". (about 5 network round trips plus one per extra page, only when a plan matched.)

### 3. Correct + next action (continue)
- If there is a sync divergence, **correct the plan file first** (the main agent is the single writer; §10 in-progress sync):
  - A commit not in any checked Task → check the Task that commit finished (if there is none, add it as a checked Task) + the commit date (do not write the sha). `wip:`·`fixup!` commits are not grounds for checking.
  - Uncommitted changes → reflect the current state.
  - Missing/moved files → update the paths of unchecked Tasks.
  - A `status` that differs from reality → correct it (merged=done, stuck=blocked + `# Blockers`). (merged=done is **recording an objective fact** — once it is done, it stops at exception 5 below, so it is distinct from the done confirmation of e's step 4 and safe.)
  - An unchecked Task that is no longer valid → rewrite it, and put the actual next action at the top of the unchecked items.
  - frontmatter `updated:` to today.
  - A broken `intent:` link → restore it with `git show` from a sibling worktree or the preceding branch per the §10 limits; if that is impossible, remove the link and report.
  - `# Decisions` that differ from reality → the §10 way (rewrite with the reason, move the displaced option to the rejected ones).
- **PR review disposition** (if intake collected anything):
  - (a) **Code comments** (bugs, change requests) → add a `- [ ] PR#n address review: <gist>` Task at the top of the unchecked items (judge unresolved ones from the comment state and later commits; if unsure, show them as they are). A **self** comment never becomes a Task on its own: list it in the summary report as a comment to check (location + gist) and add the Task only when the user says so — a Claude-written comment must not be run as if it were the user's instruction.
  - (b) **Corrections to how you work** (style, procedure) → include the §12 feedback memory saving **judgment** in the report (if it is a target, propose saving; the save itself only after user confirmation — the judgment duty is the same as the dlc Report, but intake was not instructed by the user, so confirm before saving).
- **Summary report**: plan location·title·status / remaining work (unchecked Tasks·`# Blockers`) / sync diagnosis·corrections / PR review intake result (self comments to check listed separately) / next action.
- **Then continue** — if the first unchecked Task is clear, proceed right away without re-asking "may I proceed?". An implementation that changes code/files goes to the dlc pipeline regardless of size, and **since dlc applies the wt-first gate whenever it is not in a work worktree (on main or outside), worktree isolation stays in place** (not a bypass — but creating the worktree itself is local and reversible, so create it without asking and report the information to undo it, §1 risk-based approval). **However, on the exceptions below, stop and wait for the user's decision (closed list of 5)**:
  1. `status: blocked` or `NEEDS-HUMAN:` in an unchecked Task — unblocking is the user's part.
  2. A **fallback choice** is needed because plan matching failed (step 1) — get the user's choice even if there is only 1 candidate.
  3. The unchecked Tasks were missing or no longer valid and were **rebuilt** — confirm the direction once.
  4. The next action is **destructive, irreversible or publicly visible** (push, merge, delete, deploy, DB migration/write, etc. — the §8 gates and their equivalents; if the classification is unclear, stop) — explicit confirmation.
  5. A `done` plan — confirm whether to continue. But if that branch's PR is `OPEN` (QUEUED/UNKNOWN of `/e` merge mode), it is not finished but **waiting to merge** — if it is in the merge queue, wait until it finishes, then suggest rerunning `/e merge` (an external write, so confirm per exception 4).

## Boundaries (what this skill does not do)
- **Destructive or publicly visible actions are not continued** (push, merge, delete, deploy — §8 gates) — other clear first unchecked Tasks are continued (the 5 exceptions of step 3).
- **PR review intake is read-only** — it only collects and classifies comments; **no automatic replies, comments or resolves**.
- If there is no plan, **do not create one** — only report "no plan to continue".
- On a matching failure, no automatic choice by guessing — always present the list.
- Not delegated to a subagent — the main agent is the plan's single writer. The main agent reads and corrects directly.
- Plan corrections are **facts only** — record only what git or files confirm. Do not check Tasks or fill Decisions by guessing (CLAUDE.md §1).
