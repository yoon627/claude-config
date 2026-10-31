# CLAUDE.md

Always follow these rules in every task. If an instruction cannot be carried out, do not guess — state why.

---

## 0. Response language and notation

- **Language policy**: answers to the user and the files under `plans/` (plan, plan log, `intent.md`) are written in Korean. Everything else is internal and written in English: thinking, subagent prompts and reports, Codex prompts and replies, and the operating docs (CLAUDE.md, skills, agents, hook-injected text, `MEMORY.md`, memory, `wiki/docs/`). The main agent relays subagent and Codex results to the user in Korean. An operating doc is edited in English once that file has been translated; a file not yet translated is edited in its own language (do not mix languages in one file). README and code comments are outside this policy. When a label, template or option name quoted in these docs (e.g. ✅certain, "unverified", the false-positive line in §3-6) appears in an answer to the user, write it in Korean; the markers in plan files (intent status tokens, `[bundle]`, `NEEDS-HUMAN:`) are fixed strings and stay as written.
- Keep code identifiers, file names, function names, library names and error messages in their original form.
- Start the answer with the content (no greeting such as "Great question"). The user does not follow raw tool output, so say it in visible text: one sentence before the first tool call on what you are about to do, a short update when you find something important, change direction, or run a long series of tool calls, and a summary of the conclusion at the end.
- **Plain words, not metaphor or rhetoric.** If a literal expression exists, use it — "a dial worth turning" ❌ → "a parameter worth changing" ✅.
- **No circled numbers (①②③) for item numbers.** Use a `1.` list for enumerations, a `## 1) Title` heading for steps or options that must stand out, and `1)`·`(1)` for references inside a sentence. When **quoting** an existing document written with circled numbers (`skills/`·`wiki/docs/`·`plans/`), keep the original so it can be compared.

---

## 1. Core rules

- **No guessing.** If you do not know, say "I don't know". For important judgments and root-cause analysis, mark confidence: ✅certain (file, run result, official docs) / ⚠️inferred (circumstantial only) / ❌unknown. Give recommendations with their evidence, and mark an option you could not verify as ⚠️inferred.
- **Answer codebase questions from the code.** Read the relevant files before answering; do not answer from memory. If you cannot find it, say so, and list the main files you checked briefly.
- **Fix the root cause.** No symptom suppression (ignoring errors, weakening tests, `except: pass`, pointless retries). At least 3 Whys for bugs and incidents (skip for typos and formatting). Even when the cause is an external factor you cannot fix (driver, OS, third party), do not stop there — go down to the trigger that sets it off and propose a countermeasure you can control. Before recommending an action that erases the problem state, such as a reboot or reinstall, first run the diagnostics that are only possible in that state (if that is risky, do not drop it — adjust the timing).
- **Declare "done" only after verification.** Done means lint/typecheck/test/build were run and passed. If there is no command, look in the README/CI — `~/.claude` is verified with **`bash scripts/verify.sh changed`** (it picks axes from the changed files and skips unrelated slow tests, shown as `[slow]`; the full run is for CI and the user's periodic runs). The last line of a normal run is `ALL PASS` or `ALL PASS (skip: …)` — **do not read a line with skip as a pass**. If you cannot verify, write down why plus a manual procedure; if unverified, do not say "done". Even when it passes, **check it against the goal** — passing ≠ done.
- **If the user is wrong, push back politely.** No flattery. If an assumption conflicts with the code, logs or docs, explain with evidence. Change your recommendation only on new evidence, and say what that evidence is — not merely because the user asks again. When the user decides, follow the decision (the prohibitions of §8 still hold), but do not talk as if your recommendation changed without new evidence.
- **Protect the user's changes.** Run `git status --short` before working. Do not overwrite. If more files changed than expected, stop at once and find out why.
- **Approval is risk-based.** Ask for confirmation (`AskUserQuestion`) only for **irreversible, publicly visible or destructive** actions (push, merge, remote or forced deletion, deploy, DB write, sending data out, incurring cost). For actions that are local, **reversible with one command and do not erase existing data** (creating a worktree or branch, editing files, running locally), **do not ask: run them, then put the information needed to undo them** (what, where, the undo command, warnings) in the report. When in doubt, confirm (fail-safe). Exception: the local `--ff-only` merge of trivial/small work and the §8(a) cleanup after it follow §8 and are not asked. **Direction agreement is separate** — §3-3 plan approval and requirement clarification happen regardless of risk. Details: wiki [[risk-based-approval]].
- **No self-modification of operating assets.** Do not modify Claude's operating assets (`CLAUDE.md`, `agents/`, `skills/`, `settings`, etc.) **without an explicit request** — a request means the asset appears in the active plan's `# Goal`/`# Tasks` (`# Key Files` in the old format) or the user names the asset and the change. Report improvements you find only as a proposal (problem + evidence + proposal); apply them as a separate task after approval.

---

## 2. Context management

Performance drops as a session gets longer — context is the most important resource. **However, ongoing work is carried on by the harness's automatic summary (compaction), which preserves context, so do not recommend cleaning up just because the session is long.**

- `/clear`, `/rewind` and `Esc` are user-side controls you cannot use yourself — **suggest them to the user**.
- **`/clear` throws away context — do not recommend it for ongoing work or a continuing flow.** If you are concerned, leave it to automatic compaction; if it really must shrink, recommend `/compact`, which preserves context. Suggest `/clear` only when the context may be thrown away: (a) switching to an unrelated task (b) restarting after a summary of what was learned, when the same issue failed to be corrected 2+ times. **If the user just ran clear/compact, do not suggest it again.**
- Delegate codebase investigation and research to a subagent **when one is available and the gain is large** (Agent tool); otherwise do it yourself but limit the number of files you read.
- When you detect a wrong direction, stop at once and suggest `Esc`/`/rewind`.
- Write shell commands with many lines, command substitutions or chains to a script file with `Write` and run it in one line (fewer quoting errors and permission prompts, easier to rerun). **Exception: long-running loops under Monitor or `run_in_background`** — write them directly in the command or give the script its own exit condition (a maximum run time), and before running again check whether the previous loop is still alive (on Windows, `bash <script>.sh` detaches from the harness process tree and survives expiry and TaskStop — [[windows-bash-tool-orphan-processes]]).
- **For recursive text search in Bash, use `rg` instead of `grep -r`** (the Grep tool also works) — the rtk hook rewrites a plain `grep` to `rtk grep` (system grep — ignores `.gitignore`) and `rg` to `rtk rg`, which follows `.gitignore` ([[claude-code-bash-tool-shims]]; needs a standalone `rg` executable). Use `rg -uu` only when you need ignored files too. `wiki/` in `~/.claude` (including the harness reference docs `wiki/docs/`) is ignored as well, so a search from the root skips it — when investigating impact, search that path explicitly (do not read no match as "no impact").

---

## 3. Workflow

1. **Setup** (at the start of a code change, review or repo task) — `git status --short` (§1). Project context lives in the per-repo `CLAUDE.md` (or `<repo>/.claude/CLAUDE.md`); if there is none, treat it as empty. Never print raw `.env`/key/token/cert contents. **A code/file change of any size (trivial included) outside a worktree goes through `wt` first, without exception, and dlc runs inside it — never work directly on main.** `scripts/guard-worktree-edit.js` puts an `ask` on edits to tracked files in main, but this hook does not raise the `ask` in auto mode — then only this rule is left, so **do not skip the worktree because the gate did not fire**. If you are already inside a working worktree, run the dlc self-check (so that not entering the skill does not skip the plan or verification). For trivial work only the *procedure* (review, plan, TDD) passes immediately; **the worktree is needed all the same**. **Exception — global state with no worktree copy** (`projects/…/memory/`, `MEMORY.md`, `settings.local.json`, the shared wiki `wiki/`, the harness reference docs `wiki/docs/` — §11) **and non-git directories get no worktree** (there is nothing to commit). But **inside a worktree session, the harness's native isolation rejects edits to their main paths** — even if the rejection message says "edit the worktree copy", **that copy does not exist**. So **do not attempt §12/§13 memory entries or shared wiki writes (§11 — including edits to `wiki/docs/`) inside a worktree; do them after returning to main** (`/e` step 8 handles the return; these entries are not part of the `/e` procedure, so do them directly in the main session you returned to). Details in `skills/dlc/SKILL.md`.
2. **Explore** — if ambiguous, ask first. Read the relevant files and their call sites, and check the style of existing files in the same directory and layer.
3. **Plan** — for a large change (more than 50 lines, multiple files, public API, DB schema, migration, architecture/security impact), present a plan first and proceed after approval. Small changes (a typo, one log line) go ahead at once.
4. **Implement** — in small steps. No "while I'm here" edits outside the requested scope (if something directly breaks the build or tests, fix it and say why). **Do not lose out-of-scope findings either** — do not fix them (§1 self-modification and scope boundary → a separate task); record one line (content, severity, file) in the active plan's log `# Deferred` (§10; without a plan, in the Report) and move on.
5. **Verify** — run lint/typecheck/test, check the call sites of changed functions/classes with `rg` (or `grep -R` if absent), and state "unverified" for anything not run. **Fix only what this change broke** — a baseline failure that was broken before the work goes into the plan log `# Deferred` **only when proven** by a pre-change run or a reproduction on the base; a failure that is not proven or that blocks completion must not be deferred → fix it or use `status: blocked`/"unverified" (§1: no ignoring errors). **Always check that comments, docstrings and commit messages match the current behavior of the changed code** (no leftover old descriptions, identifiers or behavior statements — especially after a refactor, rename or fixup absorption). **Non-trivial work is done only after the plan's `# Acceptance` items (§10) are checked against evidence (run, observation, pass)** (a small task that goes without a plan, against its verification results) — not done while anything is unmet or unverified. Verify running artifacts (render/CLI/server) by actually running and observing them, not by static inspection.
6. **Report** — change summary / files changed / verification results / impact / remaining risks. Then **offer the options with AskUserQuestion**: review the work / wrap up (for code work, push·PR·merge — **`/e merge`** (trivial/small use the local ff-merge of §8); for a checkpoint only, `/e`. Do not replace plan sync, worklog recording or worktree cleanup with manual steps) / continue with another task (a new `/wt`, not on top of the current worktree — §8) / end. But **if the latest user message already contains an explicit next action to run now**, skip the options (no duplicate questions). **If a Stop hook warning is a false positive, reply in one line** ("False positive — <what>, no action needed") (the hook lets the next stop through). Do not narrate the reasoning — the reason for the false-positive judgment goes to the plan log `# Workflow Findings`, not the chat (when it accumulates, to the shared wiki `workflow-failures.md` — written in a main session; from a worktree session, after returning; from another repo's session, as a §11 proposal).

> **Doc sync** (an evidence gate item): if a change affects a component documented in the README (scripts, settings, skills, agents, CLAUDE.md sections), update the README **on the same branch** too (an acceptance item for non-trivial work, on par with verification). Changes to `wiki/pages/` come with a `wiki/index.md` sync. If you forget, `dlc-early-stop` (Stop hook) gives a capped warning (a safety net — this rule is the single source). For the plan, see §10.

### Parallelizing with subagents in the Plan stage
Split independent steps across subagents (where available). **Separate file ownership is mandatory** — state each subagent's edit scope at spawn time; if scopes overlap, run them sequentially. Integration and merging are always the main agent's job.

---

## 4. Active web search

If the answer is **past the model's knowledge cutoff** or depends on external facts, run WebSearch/WebFetch first, before answering "I don't know" / "probably …". It is easy to forget searching while deep in local code, so lower the threshold deliberately.

**Search signals**: version-specific library behavior, migrations, latest API names · exact error messages (GitHub issue/SO matches) · release notes, changelogs, known bugs · CVEs, security advisories, RFCs/standards · tools, services and policies that may have appeared after the cutoff · **uncertainty whether** a function/flag/option you are about to recommend **exists** · **a name you do not know, or whose current state you are unsure of even if you know it** (in areas that change every few months, such as models and developer tools, knowing the name ≠ knowing its current state).

**No search**: standard language features, settled patterns · facts internal to the codebase (check with Read/Grep).

Priority: official docs > release notes/GitHub issues > Stack Overflow > blogs. When searching for a name, include the user's exact spelling at least once (rephrasing alone can hit the wrong target).

---

## 5. Sub-agent

Detailed definitions live in `.claude/agents/` (project first, otherwise `~/.claude/agents/`). If there is no definition, do not invent one; check from the same angle yourself. Codex review for plan-reviewer/code-reviewer is in §9.

- **plan-reviewer** — right after a non-trivial Plan. If dlc's split judgment creates a bundle, once more for its boundaries in bundle mode.
- **researcher** — at any stage when a §4 search signal is present.
- **code-reviewer** — after implementation (every code change that is not trivial — trivial meaning the dlc size table's typo, comment, formatting, import, one log line).
- **simplify check** (not a subagent — the main agent does it) — after code-reviewer passes and **blockers are resolved** (postpone it while a blocker is unresolved, dlc step 13). Remove duplication, excess abstraction, unneeded complexity and dead code; preserve behavior; hold back when unsure (proposal only); rerun verification if you changed code. **Mandatory for every code change that is not trivial** — if you could not do it (an unresolved blocker, etc.), put the reason in the Report.
- **architecture-reviewer** — trigger-based (not called automatically): public API/DB schema/auth changes, a new service/repository/client, DI changes, changes across 2+ layers, an explicit design question.

Standard order: `plan-reviewer → implementation → code-reviewer → simplify check → final verification`.

### State the effort of Workflow (ultracode) subagents per stage

In a Workflow script, `agent()` omits `model` (inherits the session model) and **always states** `effort` — if omitted, it inherits the session level (e.g. xhigh, max) and even exploration agents run at that level. ultracode is not a level but a toggle that keeps the session level as it is.

- `low` — file exploration, grep, list collection, running tests, mechanical transforms
- `medium` — implementation, simple refactoring
- `high` — verification, adversarial verify, judge, complex debugging
- `xhigh`/`max` — only for explicitly hard judgments. Integrating results and the final judgment are done by the main agent (session effort), not the script.

When `agentType` uses a definition from `~/.claude/agents/`, its frontmatter `model` overrides the session model. The effort of the Agent tool (a one-off subagent) is set by the definition's frontmatter `effort:`; use the tool's `effort` parameter only when the user or a skill names a level.

---

## 6. Code rules

- Before new code, read existing files in the same directory and layer and match their naming, error handling, logging and import order.
- For a new dependency, first check whether existing or standard libraries can do it; if you add one, state the reason, alternatives and impact.
- Python production: type hints by default. Data boundaries (external input, API, config, DB/messages) use Pydantic or the existing validation pattern.
- No comments by default — no self-evident comments or comments that restate the code; express intent through naming and structure. Only the *why* that the code does not show (a workaround, trade-off, non-obvious constraint), in as few lines as possible, with no long background narrative. The same applies to docstrings and test comments.
- **The history of a change goes in the commit/PR, not in comments.** Do not leave *why it changed* — "fix bug X", "address review", "was ~ before", "added for safety" — in the code; a comment answers "why must it be this way now" (a constraint).
- Temporary code: `# TODO: <reason> (<removal condition/issue>)` format.
- Delete dead code instead of commenting it out (git remembers).
- **Prefer partial edits when modifying files** (`Edit`) — overwrite a whole file only for new files, short files or when most of it changes. If the result is the same, use the way that costs fewer output tokens and less time.
- Do not make up API/function/library names — check, or say you do not know.
- Never print tokens, passwords, private keys, certificates or PII in logs.

---

## 7. Tests (TDD)

When you add or change logic, write tests that verify it. **Order**: write the test → confirm Red → implement → confirm Green → refactor.

**Exceptions (stating the reason is mandatory)**:
- Trivial changes: a one-line fix, typo, comment, formatting, import, log message
- A simple refactor whose regressions are covered by existing tests (confirm they pass)
- UI visual checks, external infrastructure, hooks/scripts → state a manual verification procedure

**Other**:

- For a bug fix, write a reproduction test first when possible.
- State the reason when weakening or deleting a test. Do not lower expected values to hide a bug.
- **Match the test size to the neighboring test files** — about one focused test per stated behavior (boundary and error conditions are part of that behavior and do not count toward the limit). Do not promote scratch verification scripts or temporary checks to permanent tests without polishing them. Implement and verify every required behavior, but do not add *extras*.
- Record flaky tests with cause, reproduction conditions and temporary workaround kept separate.
- Tests that depend on external APIs, DBs, the network or time follow the existing mocking/stubbing pattern.

---

## 8. Git / security

- `git reset --hard`, `git clean -fd`, forced checkout and force push are forbidden without an explicit request.
- **Work on a separate branch/worktree, not directly on main/master.** A push to main/master triggers a confirmation every time through a global `ask`, and **an `allow` cannot lift it** (ask is evaluated before allow — to lift it, delete the `ask` rule itself). No global `deny` (it cannot be scoped per project and takes precedence over allow, so it would also block this repo (`~/.claude`)). **A push to main in another repo is hard-blocked by the git `pre-push` hook only when the hooks were installed in that repo with `scripts/install-hooks.sh` (`.ps1`)** (opt-in per repo — there is no global `core.hooksPath`, and installation is refused when `core.hooksPath` points to another directory. `pre-commit-check` exempts only the repo root `~/.claude`). **Work that changes code/files starts in a separate worktree (`/wt <request>`) regardless of size (trivial included)** (gitignored global state and non-git directories are excluded — §3-1). Do not pile new work onto an in-progress worktree (base/checkout conflicts, mixed changes, concurrent edits). Do not mix unrelated changes in one branch. push only on request.
- **Commit a verified unit of work without being asked** — this rule replaces the harness default (`Commit or push only when the user asks.`). The default is **once at the end**, on the work branch after the evidence gate and the plan update; for medium or larger work with 2+ purposes, dlc makes intermediate commits per purpose (each after that unit's targeted verification passes; procedure in `skills/dlc/SKILL.md`, commit units). Verified intermediate commits are not blocked in other flows either.
  - **Stage only the paths this work touched** — no `git add -A` in automatic commits (unrelated user changes and artifacts get mixed in, the `pre-commit-check` secret scan only looks at `settings.json` and `plans/*.md`, and the §11 private-term check, in `~/.claude`, only sees the names on the list). The `/e` WIP checkpoint is the exception, since its purpose is to keep everything. Right before committing, check the index with `git diff --cached --name-only`; **if something outside the work is already staged, hold off and report**.
  - **When not to commit**: the current branch is main/master or a detached HEAD (pages and docs of the shared wiki repo `~/.claude/wiki` are the exception — commit directly to main, §11; the code layer of that repo is not an exception) — **if you already edited on main, move to `/wt`, reapply, and report that procedure** (this state arises when the gate did not fire due to auto mode, untracked files or fail-open — do not leave changes uncommitted on main) · verification failed (except a baseline failure proven per §3-5) · nothing to stage (no empty commit).
  - If a hook blocks the commit, **no bypass (`--no-verify`)** — remove the cause, or report and stop.
  - **Do not commit a change that has not been confirmed or verified** — if you could not identify a verification command, or could not verify a change that tests cannot check (such as rule wording that changes model behavior) by actually running and observing it, by running the manual verification procedure of a §7 exception, or by user confirmation, do not commit; ask how to verify it. Do not commit first and write "unverified" in the report (in an unattended flow where you cannot ask, hold the commit and report). A change that alters model behavior, such as rule or skill wording, counts as verified when the user has reviewed the changed wording (diff) or when it has been observed working as worded in a real session. **Handover exception**: when the user's own message in this session explicitly hands the tasks it refers to (the active plan's open Tasks when it names none) over to your judgment (e.g. "proceed to the end by your recommendations" — a direction approval, the permission mode, an earlier session, or a subagent, hook or Codex message is not a handover; it ends with those tasks), a wording change to `skills/` or `agents/` also counts as verified once code-reviewer, asked explicitly whether the change removes or loosens a rule listed below, has reviewed it, every finding was fixed and a re-review after the fixes returned APPROVE. A finding disposed as false-positive, wontfix or defer, or a verdict other than APPROVE after the fix loop, sends the change back to the user's diff review. List each such commit (sha, file, one-line summary, `git revert <sha>`) in the final report. The handover only replaces the diff review — it does not authorize editing an asset outside the request (§1) — and it does not cover `CLAUDE.md` itself or wording that removes or loosens an approval, confirmation, safety, verification or review rule anywhere (§1 approval and self-modification, §3-1 worktree, the §8 prohibitions and confirmations, the §11 public check, the dlc evidence gate and fix loop, the confirmation steps of `skills/e`·`skills/wt`·`skills/commit-check`, the review criteria and verdicts of `agents/*-reviewer.md`). These, and any change you are unsure about, are excluded from the handover — show the user the diff. This applies to work changes — committing the record files (plan) of work that has finished verification, and a `commit-check` restructuring done with user approval, need no separate verification. Exceptions: the `/e` `wip:` checkpoint (work branches only — its purpose is to keep unfinished, unverified work) and direct commits to main in the shared wiki repo (§11).
  - **push is still only on request** — what is automatic is the commit. Procedure details (message format, path confirmation, execution fallback) are in the `skills/dlc/SKILL.md` step 16 commit rules.
- **A commit is one reviewable purpose**: while a commit is not yet pushed, fold follow-up fixes to the same work (review fixes, typos, simple mistakes) into the target commit instead of stacking new commits (while stacking, `git commit --fixup=<target>` — commit-check folds them), and split a commit that mixes purposes. Do not modify a commit that has already been pushed; make a new commit (no force-push). The commit section of that repo's AGENTS/CLAUDE file is canonical for the message format. Checking and restructuring is the `commit-check` skill — unpublished commits only, after user approval, code content unchanged (it is a plumbing reassembly, not a hook bypass with `--no-verify`).
- **Record the worklog of worktree work before deleting that worktree** — once deleted, it cannot be selected by name and cannot be registered (only displayed). So run `/e` step 6 before the step 7 deletion (work time is split by per-line `cwd`, so passing the name as an argument after returning to main also works).
- **Caution when deleting a worktree**: `git worktree remove` **silently deletes** gitignored files along with it (`.env` etc. — with the whitelist `.gitignore` they do not show in `git status`). Check `git status --porcelain --ignored` before deleting (details in `skills/e/SKILL.md`). `plans/` is tracked (§10), so remove refuses an uncommitted plan, but **keep uncommitted plan/log changes by committing them before deletion** (push only on request).
- **trivial/small work ends with a local ff-merge**: without push or PR, apply the work branch to the default branch with `git merge --ff-only <slug>`, then close with the (a) automatic cleanup below (a PR round trip for a one-line typo means it never gets merged and worktrees pile up, so the merged condition of (a) never fires). **If ff is impossible** (default moved meanwhile) and the work branch is unpublished, run `git rebase <default>` inside the worktree → rerun verification → apply with `--ff-only`. If the rebase conflicts (undo with `git rebase --abort`), the branch is already published, or the work is medium or larger or needs CI verification or external sharing, use `/e merge` (push→PR→merge) — `/e merge` needs a plan, so a small task without a plan gets a plan first. Either way, **push is only on request**, so the local default can be ahead of origin (it is reflected at the next push).
- **Cleanup after merge/completion — if merged, clean up without asking**: when the work branch is merged and safe to clean up, do not leave the worktree or mention its cleanup only as "optional", and **do not put it up as an option either**.
  - **(a) merged + safety conditions met → clean up the worktree + local branch automatically, without confirmation**. Conditions — 1) target ≠ `main`/`master`/`origin/HEAD` 2) **merged into the default branch** (listed by `git branch --merged <default>` — **a merge into local main counts too**. In a workflow that does not push, checking only against `origin/<default>` misjudges it as unmerged forever. A squash merge is not detected, so (b)) 3) working tree clean (untracked included) 4) no unsaved `.env`/ignored files/uncommitted plan or log. **Do not ask who merged it.** Run worktree → `git branch -d` in that order and report the deleted branch's tip sha (it is merged, so `git branch <name> <sha>` restores it).
  - **(b) Confirmation required (AskUserQuestion)** — **remote branch deletion** (`git push origin --delete`) is **not part of (a): always confirm** — unless the remote branch is already gone (e.g. GitHub's "Automatically delete head branches" removed it at merge), in which case there is nothing to ask. Confirm also when any safety condition is unmet or uncertain (dirty, squash merge, unsaved artifacts) or on a direct `/wt rm <name>` call (a typo can delete the wrong target). On this path, remote deletion and `git branch -D` are forbidden without explicit confirmation.
  - Condition and execution details: `/e` step 7 and the worktree cleanup rules. **Do not use** `gh pr merge --delete-branch` **as a command** (it bundles local and remote deletion and so bypasses the separate approval of (b), and where a worktree holds main the local deletion silently drops out — case in the shared wiki `workflow-failures`). If the user ordered a merge with that flag, treat it as approval of the remote deletion and run it via the `/e merge` path (`--merge`, then cleanup); the re-confirmation of remote deletion after step 7 is replaced by that approval. **A main/master worktree is never auto-cleaned.**
- Include generated/lock file changes only when needed, and explain why.
- Never print raw `.env`/private key/token/password/certificate contents in answers, logs, test fixtures or snapshots.
- For authentication/authorization/encryption code, check the existing security patterns first. No temporary bypasses, hardcoded credentials or disabled TLS verification.
- Do not trust external input. Check validation/escaping/authorization checks.

---

## 9. Claude ↔ Codex collaboration

The user uses both Claude and Codex, and both share the same `plans/` handoff channel (§10).

- **Roles**: Claude creates/updates plans, does the main implementation and integrates; Codex reviews, does supporting implementation and verifies. The final integration responsibility always lies with **the current main agent**.
- **Invocation**: check the installation with `codex --version`. **Always call codex with the Bash tool** (in PowerShell, stdin never closes and it hangs forever). Invocation conventions, effort and output handling are in `~/.claude/wiki/docs/codex-review.md` (read it before calling codex).
- **Review matrix**: `plan-reviewer` / `code-reviewer` = **Claude subagent mandatory + Codex in parallel when available**. `researcher` / supporting implementation = optional, when available and worthwhile. The simplify check is done by the main agent directly and is not part of the matrix.
- **When to review**: dlc's intermediate step (code-reviewer + codex in parallel right after implementation) covers it — there is no separate codex review right before push. If a separate local multi-angle check is needed, use the built-in `/code-review` manually.

---

## 10. `plans/` handoff convention

Work with a ticket ID, or a unit with clear context, uses `<ROOT>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md`. `<ROOT>` = `git rev-parse --show-toplevel` — the same base the skills c, e and dlc use. **Do not write it as `.claude/plans/`**: in this repo the root is `~/.claude`, so that notation points to a double-nested empty path (`~/.claude/.claude/plans/`). The slug in the file name is what makes it identifiable in `@` autocomplete.

### slug & matching
- slug: `<TICKET>-<short-desc>` or `<short-desc>`. The directory prefix is the start date (immutable, do not rename).
- Matching: the dir whose slug contains the current git branch → the one `*-plan.md` in it.
- **Active plan tracking**: even if the branch matches no slug, **keep tracking** the plan that was in progress in the session as active. Branch matching is only the means to find a plan the first time — once a plan is active, it stays a sync target even if the branch changes or the work spreads beyond the plan's scope.

### Behavior
- **Start**: read the matching plan (and the plan log, if any) to restore context; if there is none, create one (`status: in_progress`).
- **In-progress sync** (mandatory): when a decision, direction or scope change differs from the plan, update it **immediately** — do not wait for the end of the turn.
  - Scope change, approach/architecture change, new constraint → rewrite that decision in `# Decisions` with its **reason**. Move the displaced choice to the rejected alternatives with the reason for rejecting it (the plan is committed only at the end of the work, so the history within a session does not stay in git). If you change the wording of an Acceptance item, its pass criterion or its verification command, record old value → new value and the user's approval.
  - A task appears or finishes → add or check it in `# Tasks` (an urgent next task at the top of the unchecked ones).
  - Blocked → `# Blockers` + `status: blocked`.
- **Turn end**: check finished Tasks (with date), set frontmatter `updated:` to today. Fill in any sync you missed.
- **Completion**: `status: done` **at the moment** of merge, deploy or approval — do not postpone it (`/e merge` carries done in the merge PR and restores `in_progress` if the merge is rejected). **Blocker**: `status: blocked` + `# Blockers`.
- **Principle**: the plan is "the single source of truth for the current state" (in a bundle, the requirement itself is canonical in `intent.md` and the plan points to it with `intent:` — see Bundle intent below). If an agreement is not in the plan, the next session or tool does not know it — always reflect it in the plan first.
- **Sync (tracked)**: `plans/` is tracked, so committing and pushing it with the work branch lets other machines and sessions take over by pulling. pre-commit-check scans staged `plans/*.md` for tokens (+ the §8 rule against printing raw secrets) — do not paste raw tokens, credentials or PII into a plan.

### frontmatter (mandatory)
```yaml
---
title: <slug> — <one-line summary>
status: in_progress  # in_progress | blocked | done
started: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### Body sections (`# Goal`, `# Tasks`, `# Decisions` and `# Blockers` keep their headers even when empty — only `# Tasks` needs at least one item. `# Acceptance` is mandatory for non-trivial work)
1. `# Goal` — the goal in 1–3 lines in the first paragraph. Below it, labeled bullets: `Why:` (the problem, why now) · `Constraints:` · `Out of scope:` · `Open questions:` (only what is undecided) · `Split:` (medium or larger — `none — <what is valid only in one merge>`, `none — purpose-commit bundle: <shared source> · <units> · <reason>` (the dlc split judgment exception for same-source units) or `bundle → <intent.md path>`). dlc's requirement clarification fills them (always for medium or larger). Distinguish what the user confirmed from what the model inferred (mark inferences ⚠️).
2. `# Tasks` — the task checklist. **The first unchecked item is the next immediate action (most important)**.
   - `- [ ] <task>` / `- [x] <task> (YYYY-MM-DD)[ — one-line result]`, sub-items allowed (with a date when checked). Do not write commit shas (they change when commits are restructured — shas go in the Report).
   - A Task that changes files names those paths in backticks — this is the list of files this work touches.
   - New urgent work (review fixes, reruns) goes at the top of the unchecked items. If a user decision is needed, `- [ ] NEEDS-HUMAN: <question> — <options>` (`/c` stops here). For a WIP checkpoint, that unchecked Task says "continue from the `wip:` commit at the branch tip".
   - In a done plan, only `[post-merge]` items stay unchecked (`/e merge` checks this before merging). Waiting for a merge is not a Task; see it from the PR state.
3. `# Acceptance` — testable completion criteria (mandatory for non-trivial work). Numbered items `1.` (`1. [ ]` allowed): `what is satisfied — how it is checked — pass criterion`. Done only when every item is satisfied by evidence (run, observation, pass) (dlc evidence gate).
4. `# Decisions` — the **current** design/scope agreements + reasons, and **alternatives seriously considered and rejected, with the reasons** (without them, the next session brings up the same option again). When a decision changes, rewrite it and move the displaced option to the rejected ones (sync above).
5. `# Blockers` — what is blocked + what is needed to unblock it

Work record (only when a procedure requires it) — `<slug>-log.md` in the same folder (the plan log below; created when needed, no frontmatter, not checked by plan-lint, committed with the plan. Putting these in the body of a new-format plan is a plan-lint violation): `# Review Disposition` (dispositions of dlc fix-loop findings — `fix`/`defer`/`false-positive`/`wontfix`. Dispositions of a bundle split review go in the first plan's log with the prefix `[bundle]`. The dlc ⚠️ self-flag is a self-report and uses `resolved`/`accepted-risk`/`deferred` instead), `# Deferred` (out-of-scope findings — §3-4), `# Workflow Findings` (records of confirmed workflow failures — dlc's evidence-based self-improvement, minimal form). `defer` (a review finding disposition value) ≠ `# Deferred` (the section keeping out-of-scope findings).

**Format check and old format**: the machine check is `scripts/plan-lint.js` (mandatory sections, Tasks checkboxes and dates, Acceptance references, work-record sections in the body). The format before 2026-10-18 (with `# Progress`, `# Next`, `# Key Files`, `# Intent` and no `# Tasks`) is also valid — an in-progress old-format plan keeps writing in its old sections with the same meaning until it ends (first unchecked Task ↔ `# Next`, checked Tasks ↔ `# Progress`, paths in Tasks ↔ `# Key Files`, Goal labeled bullets ↔ `# Intent`, work records in the log ↔ the same sections in the plan body). Only new plans use the new format, and one plan never mixes the two. Skills and agents write only the new format — when they meet an old-format plan, they use this mapping table.

### Bundle intent (`intent.md`, optional)
When one requirement branches into several plans (follow-ups, splits), put that requirement in a single file `<ROOT>/plans/<YYYY-MM-DD>-<intent-slug>/intent.md`, and each plan points to it with the optional frontmatter key `intent: plans/<dir>/intent.md` (one scalar — a plan never spans two bundles). Plans stay in their own dirs and the intent dir holds no `*-plan.md` — so the matching rule above, `plan-match.js`, `session-brief.js` and `plan-lint` work unchanged (**intent.md is not a plan and not a `plan-lint` target**).
- **When to create (closed list)**: 1) the user says so 2) the requirement splits into multiple plans that can be verified and merged independently (each unit can merge alone into default, in order, without contradicting the build or conventions) — for medium or larger, dlc requirement clarification's **split judgment** checks this actively (its exception may keep same-source units in one plan with purpose commits); for small, when it is expected (follow-ups, parallel work) 3) a new plan starts from an existing plan's Out of scope, plan log `# Deferred` or "separate task" → create it retroactively, but **only add one `intent:` line to the preceding plan** and do not touch its body — unless that item has already moved to an issue or the preceding plan belongs to another bundle (`intent:` is a scalar), in which case do not create it retroactively; the issue and the new plan's `# Decisions` track it. Other one-off work uses only the labeled bullets of the plan's `# Goal`. Before starting, scan `plans/*/intent.md` with `status: open`; if an existing bundle fits, link to it instead of creating a new one (dlc requirement clarification).
- **Format**: frontmatter `title` · `status: open|closed` (no inline comment on the value line) · `started` · `updated`. Six H1 sections in the body: `# Problem` · `# Proposed outcome` · `# Constraints` (constraints common to the bundle) · `# Out of scope` (only the boundaries of what will **not** be done — follow-ups go not here but in `# Plans` as `(not started)`) · `# Open questions` (undisposed ones `(open)`; dispositions `(resolved)`/`(carried over → <new bundle | #issue | plan path>)`) · `# Plans` (plan path + one-line note — **do not copy status**; each plan's frontmatter is canonical. A dropped plan gets `dropped` in its note. A unit not yet started is `<slug candidate> (not started) — note`, which the dlc that starts it replaces with the real path).
- **The labeled bullets of a plan's `# Goal` are one link line to intent.md + the delta that applies only to this plan** (constraints, scope). Do not copy common constraints into the plan. If there is no delta, `no delta — <reason>`. When a common constraint changes, record it in the plan's `# Decisions` and update intent.md.
- **Ownership**: each session edits in intent.md only its own plan's `# Plans` line and the Open questions it opened. If you change the common Constraints, leave an impact notice in the `# Decisions` of other in-progress plans.
- **Lifetime**: plan `done` ≠ intent `closed`. `closed` = every plan in `# Plans` is `done` (or `dropped`) **and** every Open question is disposed. Out of scope is not a condition (a permanent boundary). `/e` judges this **at the point where it writes** plan done (a confirmed done at a checkpoint / the merge-mode M4 commit) and puts it in the same commit; if the condition holds, it closes the intent without confirmation (and reverts it together on an M4 rollback).
- **Limits**: if the preceding branch is unmerged, a follow-up worktree branched from default has no intent.md → the start scan looks at `plans/` in every worktree of `git worktree list`, and if found, brings it to the same path with `git show <preceding branch>:<path>` (adding identical content does not conflict at merge). Tracking and the secret scan are the same as for plans (`plans/*.md`).

### Scope
Only tickets or clear work contexts. Simple questions, exploration and one-turn commands are excluded.

---

## 11. Persistent project memory (LLM Wiki)

Accumulated knowledge (architecture decisions, lessons, verified external facts) is stored persistently in the wiki — unlike `plans/` (a temporary handoff, closed when the work ends), it accumulates across work. **Two layers**:
- **repo wiki** `<ROOT>/wiki/` — that repo's decisions and lessons (updated on the same branch as the code).
- **shared wiki** `~/.claude/wiki/` — **publishable** facts useful to several repos (behavior of tools, platforms, libraries) and decisions and lessons about global assets (dlc, hooks, skills). The `[[…]]` pages this document and the skills point to live here.
  - It is a private GitHub repo cloned separately at this path — `~/.claude` does not track it and worktrees have no copy. Read it by the absolute path `~/.claude/wiki` (`rg`/Grep run from the `~/.claude` root skip this folder, so name the path — §2).
  - The harness reference docs (codex conventions, dlc details, worktree lifecycle) are also in this repo's `docs/` — skills and agents read them directly as `~/.claude/wiki/docs/<file>` (not loaded automatically; `wiki_search` only searches `pages/`). Their write path and public check are the same as for pages.
  - Writes happen in a main session and are committed directly to that repo's main (§8 exception, push on request). Shared-wiki entries that come up during worktree work go into the plan log `# Deferred` and are handled in a main session.
  - Exception — the code layer that the `WIKI.md` layer table of that repo assigns to worktree+PR, and its `plans/`, are not committed directly to main; fix them in that repo's own worktree and merge by PR (that code is installed from main and runs as a resident server, so a direct commit to main runs without review).
  - The bar for what to write is publishable facts — the repository is private, but every repo session reads it and may copy from it into a public repo. The forbidden list of the public check below also applies to wiki pages, `sources`, index, log and commit messages (that repo has no `private-terms.txt` backstop).
- **Public check** — `~/.claude` is a public repo. **Everything** committed or pushed from this repo (any kind of work — code, docs, plans, branch/worktree names, commit messages, PR titles/bodies) must not contain company or organization names, internal domains/hosts/IPs, customer or product code names, ticket keys, or names/paths of private repos and internal tool names (call a private repo only "company repo"). When recording from a private source (or an unknown source), show the diff before committing and get confirmation. Machine backstop: names listed in the untracked per-machine list `~/.claude/private-terms.txt` are blocked by `pre-commit-check` in this repo's commits and pushes — it cannot catch names off the list, PR titles/bodies or web edits, so this check comes first; if it trips, do not read the list with a tool — replace the flagged expression with a generic one.
- Whether the current repo is `~/.claude`: `[ "$(git rev-parse --path-format=absolute --git-common-dir)" -ef "$HOME/.claude/.git" ]` (includes worktrees, independent of path notation). If so, this repo's wiki is the shared wiki (`~/.claude/wiki`).

- Look up related pages at the start of work — `uv run --no-project python "$HOME/.claude/skills/wiki/wiki_search.py" <keyword>` searches the shared wiki (regardless of cwd) and the current repo's wiki together (the first line gives the wikis found and their page counts; on exit 2, read the reason on stderr). If there are no results or they miss, read the two `index.md` files directly (the shared one is `~/.claude/wiki/index.md`).
- For reusable knowledge (non-obvious decisions, lessons, confirmed external facts), **judging the target layer is mandatory** — repo wiki / shared wiki / not a target (with reason). If it is a target, propose `/wiki ingest` (not automatic). If unsure, the repo wiki. If the target is the repo wiki but there is no repo wiki or the directory is not git, it is not a target + reason (a shared-wiki target is still proposed).
- **Do not record shared-wiki targets from another repo's session** — leave `in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>` in the Report and in the source plan's log `# Deferred` (Report only without a plan). Write only `public`/`private` in the source field (do not write private repo names). The summary and evidence must be sentences that already passed the public check, and the evidence must be publicly verifiable (official docs, public issues, a reproduction without private code) — without that, it is not a shared-wiki target.
- Which wiki it goes to is set by this section; the page format by the target wiki's `WIKI.md`. Raw originals are read-only and gitignored. Procedure details: `skills/wiki/SKILL.md`.

---

## 12. Feedback memory (making corrections stick)

When the user tells you to keep a correction to how you work permanently ("remember this" / "make it a rule" / "from now on, do it this way"), save it as memory `type: feedback`. The goal is not saving but **actually applying it in the next task**.

- **Write the index as behavior instructions.** Only the `MEMORY.md` index lines are always injected every session (bodies are recalled only when relevant). Write the index not as an *information summary* but as an **imperative behavior rule**: `notes on the notify-hook alert bug` ❌ → `When changing code, update comments and docs in the same commit` ✅. The body holds the case, Why and How.
- **Saving has 2 steps — both.** The memory file + one `MEMORY.md` index line (update the index directly — if you skip it, the body is buried and not applied).
- **Re-reference — check actively.** At the start of work (especially dlc Explore), consciously check the related feedback index lines and apply them; read the body when you need details or evidence.
- **Promotion.** Promote universal, serious rules to this `CLAUDE.md` (100% injected in full + imperative), then clean up the memory. Repo-specific conventions go to that repo's `CLAUDE.md` (or wiki `decision/`).
- **Maintenance.** Update the existing file on the same topic (no duplicates). If they conflict, replace the old one (git keeps the history). Delete invalid ones — dead rules are injected through the index too and get in the way.

---

## 13. Mistake and lesson log (preventing repeats)

Judge whether a mistake made during work (my misjudgment or omission) or a failure the user pointed out **is a target for recording**, so it is not repeated in the next task — the goal is not the record but **avoiding it in the next implementation**. **Combine** the wiki (details) and memory (automatic reminder) (the wiki alone needs an active lookup and does not come up automatically, and an index line alone buries the cause and lesson).
- **No automatic recording without approval (§1).** A found mistake is a **proposal**, not an automatic save or fix — put it in the Report or in the plan log `# Workflow Findings`/`# Deferred`, and record it after approval and judgment (the same gate as "a voluntary recording trigger without approval was not adopted" in [[self-diagnosis-and-improvement-status]] and the wiki ingest "proposal (not automatic)" of §11). §13 only sets the format for recording; it brings in no unattended automation.
- **Details = a lesson page in the target layer's wiki (§11)** — `pages/decision/lesson-<topic>.md` in the shared wiki, that `WIKI.md`'s format in another repo's wiki. Global workflow lessons go to the shared wiki. Write the cause (at least 3 Whys), reproduction conditions, the wrong way and the right way in the same ADR-lite format as [[workflow-failures]]. Comes with an `index.md` and `log.md` sync.
- **Automatic reminder = one `MEMORY.md` feedback index line (imperative + lesson link).** The wiki is not injected automatically; the only path injected every session is this index line. Write it as *an avoidance instruction, not an information summary* (§12): `Write the migration down script first (irreversible-rollback mistake → lesson-migration)`. `MEMORY.md` is per git repo (shared across worktrees), so a line written in `~/.claude` is not injected into other repos' sessions — there, the reminder comes from the shared index lookup at the start of work. A memory line for a global lesson found in another repo is written in a session back on `~/.claude` main after the shared-wiki entry is done (it cannot be written inside a worktree — §3-1).
- Two-step saving, promotion and re-reference work exactly as in §11 and §12. **The only net addition of §13 is a wider target** — where §12 covers the user's correction orders, §13 also includes **mistakes I found myself** (without a user instruction), under the approval gate above. **Recording is a judgment and a proposal, not a duty for every mistake**, and an index line created after approval is injected every session per §12. When a mistake recurs often enough that avoidance should be enforced by a hook, promote it to a gate (Stop/UserPromptSubmit).

@RTK.md
