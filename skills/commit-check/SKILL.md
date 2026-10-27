---
name: commit-check
description: Checks whether the current branch's not-yet-published (unpushed) commits are each "one reviewable purpose", builds a proposal table of folds (fixup), splits (by file), reordering and message fixes, and once the user approves, restructures only the commit boundaries while keeping the code content unchanged. Called at dlc wrap-up (after the step 16 commit) and from `/e merge` (before push, when there are uncleaned commits), and also used for an explicit `/commit-check` call or requests like "clean up my commits / split this commit / fold these commits". It does not push.
---

# commit-check — check and restructure commit units

A commit is one reviewable purpose. This skill looks at the branch's **unpublished** commits by that standard, and when something needs fixing it goes propose → approve → restructure. The model judges; `commit_units.py` collects, validates and restructures (the script enforces every safety condition — do not bypass it by composing git commands yourself).

## Judgment criteria

- **Fold (fixup)**: follow-up fixes to the same work — review fixes, corrections of typos and simple mistakes, polishing the same file after a draft, `wip:`·`fixup!` commits. Fold them into the earlier commit with the same purpose. For a `fixup!` commit, the default proposal is to fold it into `fixup_of` (the in-range target that approximates the target selection of git `rebase --autosquash` — ref names and `HEAD~n` are not resolved) (no `show` check needed). This default takes precedence over the `plan-only` default below — a `fixup!` holding only plan files is folded into its target too. When a `/e` WIP commit spans several units, make one `{"from": [unit, WIP], "paths": [that unit's paths]}` entry per unit to split the WIP by path and fold each part. `squash!`·`amend!` also point to a target through `fixup_of`, but folding them carries a message meaning (squash = combine the bodies, amend = replace the message), so state `message` in the plan entry. If `fixup_of` is null, write "target unconfirmed/out of range" (a typo in the title, or the target is already published, on the default branch, on another branch or tagged) and do not fold. When several units changed the same file, folding into an earlier unit can conflict and make apply refuse — then leave it unapplied and put the reason in the proposal table. For other follow-up fixes, `overlaps` (a later commit changes an earlier commit's file again) is the first signal; check with `show` whether the purpose is really the same.
- **Split**: a commit that mixes two or more purposes — fixes for different problems, a refactor or config change unrelated to the feature. Split it when the purposes separate by file. If the purposes are mixed inside one file (by hunk), do not split automatically; only write "manual split needed" in the proposal table.
- **Fix the message**: when the title differs from the repo's convention. The canonical convention is the commit section of that repo's AGENTS.md·CLAUDE.md; without one, read it from `convention_samples` (recent titles on the default branch). The title says what changed, the body says why.
- **Leave as is**: if it is already one purpose in one commit, do not touch it. A plan-only commit (`plan-only`) serves a different purpose (keeping a record), so the default is not to fold it (but for a `fixup!` with a `fixup_of`, the fold default above wins).
- **Out of range**: published commits (reachable from a remote), tagged commits and commits on another local branch drop out at the collection step (`excluded`). If a signed commit or a merge commit is in the range, do not restructure.

## Procedure

1. **Collect** — from the repo root:
   ```
   uv run --no-project python "${CLAUDE_SKILL_DIR}/commit_units.py" collect
   ```
   On failure (detached HEAD, a merge commit in the range, no base branch), report the reason and stop. If `on_default_branch` is true, it is the default branch, so do not restructure (report only).
2. **Fast path** — with 0 commits in the range, end without a question with one line "no unpublished commits to check". Even with 1, judge it — end with one line "no issues" only when the file list looks like one purpose (no unrelated areas mixed), there are no flags and the title fits the convention.
3. **Judge** — look at each commit's `files`·`flags`·`overlaps`, and check the patch only of the commits that need it with `commit_units.py show <sha>` (do not run raw `git log/show`).
4. **Proposal table** — if nothing needs changing, end with "no issues" (no question). Otherwise, with a `current commit → proposal → reason` table, write the following only when applicable:
   - Intermediate commits unverified — intermediate commits made by the restructuring are combinations that never went through hooks or builds (the final tree is the same as the original).
   - Removing a commit together with its revert by folding them (drop) is not supported.
   - Manual split needed (by hunk).
   - The number of commits excluded because this branch already pushed them (`excluded.published`) and excluded by tags (`excluded.tags`).
5. **Approve** — ask apply / leave unapplied with `AskUserQuestion`. It is unpublished local history and can be undone, but approval before restructuring is a rule the user set (2026-09-24). In a flow that cannot ask the user (unattended), do not apply; leave only the proposal table in the report.
6. **Apply** — write the plan JSON to a scratch file with `Write`, then:
   ```
   uv run --no-project python "${CLAUDE_SKILL_DIR}/commit_units.py" apply <plan file>
   ```
   On success you get `new_head`, `commits` (sha, title and files per commit), `backup_ref` and `rollback`. On failure the branch, index and work tree are as they were before the call (except side effects the repo's commit-msg hook caused itself) — report the error text as is, then fix the plan and retry or leave it unapplied.
7. **Report** — check that the files per commit in `commits` match the proposal table (reordering can cancel one commit's change against a later commit and drop a file — even if the final tree is the same, if it differs from the proposal, tell the user how to undo it (`rollback`)). Put the new commit sha list, the backup ref and the undo command (`rollback`) in the report. Do not write to the caller's record files (plan etc.).

## When called from `/e merge`

Before push, `/e merge` finds, among the commits going into the PR, the `wip`·`fixup` (including `squash!`·`amend!`) flag commits with `commit_units.py pending origin/<default>`, and sorts each into `rewritable` (within this skill's range) / `published` (reached by a remote-tracking ref) / `held` (not on the remote, held by another local branch or tag) / `blocked` (the range cannot be restructured — `range_error`: merge commits, signed commits, the default branch, etc.; `pending` checks in advance the conditions apply would refuse). Only when there is a `rewritable` one does it call this skill, **narrowed to cleaning up the `wip`·`fixup` flag commits** (`review-followup`·`plan-only` flags are not targets). In that case:
- For each `wip`·`fixup` flag commit, propose either a fold (into `fixup_of` or an earlier commit with the same purpose) or a reword to a proper title (`{"from": [sha], "message": ...}`) — if the target is out of range (`fixup_of` null — e.g. a `fixup!` for an already published unit), reword is the answer. Reword also when the first commit of the range is a `wip` and there is no earlier commit to fold into.
- For a flag commit you propose to fold, also write "reword on conflict: `<title>`" in the proposal table, so one approval covers both. If apply refuses with a conflict (`merge-tree --write-tree 실패`), do not leave it unapplied; switch only that commit to the reword written in the table and apply once more — a `fixup!` after several units changed the same file is this case, and leaving it unapplied makes `/e merge` stop at the same spot even when rerun. If you need to change to a plan that was not in the table, ask again.
- Split, reorder and message proposals unrelated to the flags go in the table only for reference and not into the plan (if they were left unapplied, the whole merge would stop).
- Follow-up handling when the plan is left unapplied or apply fails is done by `/e` (this skill only returns the result).

## Plan JSON

Send back the `base`·`head` that `collect` gave unchanged (if the branch moved in between, apply refuses). `commits` is **the order of the new history**.

```json
{
  "schema": 1,
  "base": "<collect.base>",
  "head": "<collect.head>",
  "commits": [
    {"from": ["<A>", "<C>"]},
    {"from": ["<B>"], "message": "feat: new title\n\nbody\n"},
    {"from": ["<D>"], "paths": ["src/a.py"], "message": "fix: fix a\n"},
    {"from": ["<D>"], "paths": ["docs/b.md"], "message": "docs: update b\n"}
  ]
}
```

- `from`: the original commits to put into this new commit (in their original order). Several means a fold — the first commit is the target, and the new commit takes its author and message. The trailers of the rest (`Co-Authored-By` etc.) are merged without duplicates.
- `paths`: only when splitting by file. Only these paths of those commits' changes go in. A split entry requires a `message`, and every file of the original commit must be assigned to the entries with nothing missing and nothing overlapping. For a rename, put the old and new paths in the same entry.
- `message`: the new message. If omitted, the target commit's message. When the plan gives a message, or trailer merging makes the resulting message differ from the original, it goes through the repo's `commit-msg` hook (if the hook refuses, the whole apply is refused; a message the hook changed is used as is). Folding commits that carry trailers that differ per session (`Claude-Session` etc.) almost always runs the hook.
- The canonical plan format is `validate_plan` in `commit_units.py`.

## What it does not do

- push or force-push — published commits never enter the range, so there is no case that needs it.
- Restructuring the default branch (main, master, etc.), restructuring a range with a signed commit or merge commit, splitting by hunk, drop.
- Bypassing what the script refused by running git commands directly.
