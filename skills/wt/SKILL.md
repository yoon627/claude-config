---
name: wt
description: Quick Git worktree management — list/switch/create+dlc/remove. `/wt <N>` or an existing worktree name switches to that worktree; any other text (a request) picks a slug without confirmation, creates a new worktree and works inside it with `dlc`. The `?` prefix (`/wt ? <vague description>`) is question mode — it refines the requirement with AskUserQuestion, then joins the same creation path. Use when the user calls `/wt`, `/wt <N>`, `/wt <existing name>`, `/wt <request>`, `/wt ? <vague description>` or `/wt rm <name>`, or when dlc starts a file-changing task outside a worktree and creates a worktree.
---

# wt — Git worktree management

## Arguments

Interpret `args` by these rules:

| Input | Action |
|---|---|
| (empty) | list |
| `<integer N>` | switch to the Nth worktree |
| `rm <name>` | remove |
| **exact match** with an existing worktree branch | switch to that worktree |
| `?` prefix (`? <vague description>`) | question mode — refine the requirement with AskUserQuestion, then join the "request" path |
| any other text (a request) | derive a slug → create the worktree (no confirmation) → work inside it with `dlc` |

- **Interpretation order** (evaluate from the top, **settle at the first match** and do not look at later rules — this order, not the table row order, is the single source of precedence): 1) empty → list. 2) first token `rm` → remove (do not use `rm` as a worktree name). 2.5) first non-space character is `?` → **question mode** (Question mode section — the rest after removing `?` is the seed to refine, then join request). If the first character is `?`, as in `?rm foo` or `?123`, it is question mode regardless of tokens, integers or exact matches. 3) the whole argument is an integer → switch (if out of range, notice + list). 4) the whole argument exactly matches an existing worktree branch → switch. 5) everything else → treated as **a request** (request section).
- A malformed form, such as a missing argument after `rm` → print the table above and stop (`rm` with no argument also prints the list — rm step 1).
- **There is no plain creation without dlc (creating only an empty worktree)** — text that does not match exactly is always handled as a request.

> **Note**: when the user only wants the plain list, the shell `gwl` function (`scripts/gwl.ps1` for PowerShell, `scripts/gwl.zsh` for zsh) is much faster (no model round trip). `/wt` only when processed output or a follow-up action is needed.

## Common rules

- The worktree path is always `.claude/worktrees/<name>`.
- Branch name = worktree name (1:1).
- **When calling EnterWorktree, always use only the `path` argument**. Never use the `name` argument (it attaches a prefix automatically).
- Before running, check that you are in a git repo (`git rev-parse --show-toplevel`).
- Name (slug, rm target) validation: `^[a-zA-Z0-9._/-]+$`. The request text itself is not validated; the slug derived or entered from it must match this pattern.

## list

Print `git worktree list` as `<path>  <sha>  [<branch>]` with an index (1-based). Put a `→` marker before the row matching the current cwd.

## switch

First **resolve the target worktree** (2 ways):
1. `/wt <N>` (integer) — the Nth worktree of the list. If out of range, notice + list.
2. `/wt <existing name>` — the one worktree whose branch name in `git worktree list` is an **exact match**. With 0 exact matches, fall back to **request** (request → create + dlc).

No partial or fuzzy matching. Exact match only.

### How to move — branch on whether the target is main
Inside a worktree session, `EnterWorktree` only accepts targets under `.claude/worktrees/` (it cannot enter main = the repo root). So the tool depends on where the target is:

- **Main detection = by path** (not by branch name — regardless of main/master): target path == the first `worktree <path>` of `git worktree list --porcelain` (= the main checkout). Both `/wt 1` (integer 1) and `/wt <main branch name>` (exact match) go through this detection.
- **If the target is main**:
  - If the cwd is already main (= `git rev-parse --show-toplevel` matches the first porcelain worktree path above) → report "already on main" without calling `ExitWorktree`.
  - Otherwise → return the session to its original (main) location with **`ExitWorktree(action: keep)`**. If the return is a successful return to main, done. If it returns a "no active worktree session" no-op and the cwd is still the worktree (the session started inside the worktree, not via `/wt`/EnterWorktree) → tell the user automatic return is impossible (open a new session or move manually). Do not guess the session history; **judge by the tool's return**.
- **If the target is anything else (a worktree below)** → `EnterWorktree(path: <abs>)`.

## request (request → create + dlc)

**All text** that is not an integer, not `rm` and not an exact match with an existing worktree branch is handled as a request. The request text is passed unchanged as the `dlc` task after the worktree is created.

### 1. Derive the slug
- Make a short kebab-case slug from the request: ASCII lowercase/digits/`-`, ≤ ~30 characters, matching `^[a-zA-Z0-9._/-]+$`.
- For a Korean or other non-ASCII request, summarize the core meaning in English for the slug (e.g. "로그인 리다이렉트 버그 수정" → `login-redirect-fix`).
- Keep it short, centered on verb+object, without filler words.

### 2. Collision check
- If the branch (`git rev-parse --verify --quiet refs/heads/<slug>`) or the directory (`.claude/worktrees/<slug>`) exists → adopt the first free candidate among `<slug>-2`, `<slug>-3` … automatically, and show the collision in the §4 report.

### 3. Create (without confirmation — risk-based approval, CLAUDE.md §1)
Creating a worktree is local and non-destructive and is undone with one `/wt rm <slug>`, so **do not ask for slug approval**. Instead put the information needed to undo it in the §4 report.
0. **Check whether main is dirty**: look at the main worktree's uncommitted changes with `git status --porcelain`. If a requested target file is dirty, the new worktree is based on `origin/<default>` and **will not contain that edit**, so report it before creating (§1 protect the user's changes — editing an old version unknowingly conflicts at merge or silently reverts the user's edit).
1. `<default>` = the name from `git symbolic-ref --short refs/remotes/origin/HEAD` with `origin/` removed (`main` on failure). The base ref is `origin/<default>`.
2. `git fetch origin <default>` (only a warning on failure — but **expose a fetch failure as a stale base in the §4 report**). After the fetch, **capture the base sha** with `git rev-parse --short origin/<default>` (the §4 report value — which base it was created on is the basis for judging an undo).
3. `git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default>`. (The reason for `--no-track` and the first push's autoSetupRemote are in `references/rm-recovery.md` §A.)
4. **Automatic copy of ignored settings** (no opt-out): from the **main worktree**, copy 1) files whose basename is exactly `.env` and 2) the file whose repo-relative path is exactly `.claude/settings.local.json` to **the same relative path** inside `.claude/worktrees/<slug>/`. **If it already exists, skip (do not overwrite)**; a copy failure (permissions, etc.) is only a warning and the worktree stays. The reason for copying 2): where the file at the repo root is not used, such as Windows (list in `references/env-copy.md`), local settings are read from the session's working directory (the worktree entered with `EnterWorktree`), so without it the worktree session starts with **0 allowed permissions** (§8 enforces worktree work, so every real path falls here). Otherwise, since 2.1.211, worktree sessions also read the main checkout's file, and the copy is a supplement. The candidate predicates, exclusion rules and why an anchored match is needed are also in `references/env-copy.md`.
5. `EnterWorktree(path: <repo-root>/.claude/worktrees/<slug>)`.
6. Environment setup in the new cwd (in order): **submodule self-heal** (`heal_submodules.py`) → **bootstrap** (`tools/bootstrap/bootstrap.py` if present, otherwise skip). Heal **before bootstrap** (keeps an interrupted, corrupt submodule from killing the later steps). Whatever fails, **keep the worktree and report the error as is** (the user decides on a manual rerun). Self-heal/bootstrap details are in `references/rm-recovery.md` §B.

### 4. Report + dlc work
- After creating and entering, **invoke the `dlc` Skill with the request text as the argument** in the new worktree (the current cwd) (Skill tool, `skill: dlc`, `args: <request text>`). From there dlc proceeds from the size gate through the pipeline.
- **Report right before dlc starts (the safety net of creating without confirmation — it gives the information to undo instead of approval)**: "Created: `<slug>` (base `origin/<default>@<short-sha>`) — undo with `/wt rm <slug>`" + append only when applicable:
  - `.env: N copied, M skipped` · `settings.local: N copied, M skipped` (omit each when both are 0)
  - a **stale base** used because `git fetch` failed / heal or bootstrap skipped or failed (§3.6 keeps the worktree even on failure — always expose what failed)
  - a collision suffix adopted (`<slug>` already existed, so created as `<slug>-2`)
  - **Near-miss note** (guards against creating by typo — create without asking, but point to the way back): judge it **only when the request text has no spaces**. Normalize = lowercase + remove `-`/`_`/`.`. Collect the candidates whose normalized existing worktree branch — other than the one just created — **equals the normalized request or is within Levenshtein distance ≤2**. **Only when there is exactly 1 candidate**, add one line to the report: "If you meant the existing `<name>`, `/wt rm <created slug>`, then `/wt <name>`" (the created slug carries any collision suffix). With 0 candidates stay silent; **with 2 or more, list only the candidate names** and attach no undo command (so as not to mislead by pointing at the wrong candidate).
- Last line: "→ dlc start: <request>".

## Question mode (`?` prefix → refine → request)

When a request is too vague to fix into a slug yet, the `?` prefix **narrows the requirement in conversation first**, then joins the request path. A `?` suffix is not used (it would clash with ordinary question-form requests, so only the prefix triggers).

### 1. Extract the seed
- The seed (vague description) is `args` with the leading `?` and the spaces after it removed. The seed may be empty, as in `/wt ?`.

### 2. Refine (AskUserQuestion)
- Based on the seed, ask questions that narrow **what / where / with what result** to finish. If the seed is empty, start with "what you want to do".
- If one round does not narrow it, ask more to settle the scope, target and completion criteria. Adding `?` is itself a sign of "I want to narrow it in conversation", so ask at least once.
- If the user cancels or refuses, create nothing and stop.
- If asking more still does not settle the scope, target and completion criteria, do not hand it to request — ask more or stop (handing it to §3 while vague makes the slug and the dlc task weak).

### 3. Join request
- Use the settled requirement **as the request text** and run the request section §1 (derive the slug) → §4 (report + dlc) as is. Question mode only adds this front step (settling the requirement); the slug, collision check, creation, `.env` copy and dlc logic are reused.

## rm `<name>`

1. `<name>` missing → print the Arguments table (usage) + list and stop.
2. Matching: if an integer, the Nth of the list; otherwise the one **exact match** of the branch name.
3. 0 → notice + list. (Exact match only, so there is no 2+ ambiguous case.)
4. Safety checks:
   - Refuse the main worktree.
   - If the cwd is under the target, refuse + suggest switching to another worktree.
   - If `git status --porcelain` in the target is not empty, warn.
   - If there are unpushed commits, warn (`git log origin/<branch>..<branch>`, or without an upstream `git log <branch> --not --remotes`).
   - **Gitignored artifact check (mandatory)** — `git worktree remove` **deletes gitignored files along with it without a warning**. This repo has a whitelist `.gitignore`, so `.env` and `.claude/settings.local.json` are ignored → the `git status --porcelain` above does not catch them. Collect the inventory with `git -C <target worktree path> status --porcelain --ignored` (unlike `/e`, the target may not be the cwd, so `-C <target>` is mandatory), and if there are `.env` files, secret candidates or other unsaved artifacts, **state** the list that will be deleted in the step 5 AskUserQuestion body (default keep). `plans/` is tracked (§10), so uncommitted plans and logs are caught by the `git status --porcelain` above and remove refuses — commit them, then delete.
   - **Unmerged detection (the basis for the option 3 remote deletion judgment)**: if the target branch is not in `git branch --merged origin/<default>` or `git log origin/<default>..<branch>` is not empty, it is **unmerged** — but if it is in `git branch --merged <default>` (the local default branch), write it not as unmerged but as **"merged only into the local default (not reflected in origin)"** (the commits remain in the local default, so the loss risk is low, but if the remote branch is deleted, those commits have no remote copy until the default is pushed). Remote deletion (option 3) carries a data-loss risk, so state this in the option 3 warning (e blocks it with its step 7 condition 4 (merged) gate, but wt is manual, so it is the user's judgment; if the merge state cannot be determined, the premise is not to delete). `<default>` = the name from `git symbolic-ref --short refs/remotes/origin/HEAD` with `origin/` removed (`main` on failure).
   - **Worklog preview** — the AI work time of a deleted worktree cannot be selected by name and so cannot be registered in Jira (only displayed). If all refusal checks above passed and `~/.claude/skills/jira-worklog/` exists (same as the `/e` step 6 preview — the preview runs without credentials), preview with the target's **directory name** settled in step 2: POSIX `bash "$HOME/.claude/skills/jira-worklog/run_worklog.sh" <name>`, Windows PowerShell `& "$HOME/.claude/skills/jira-worklog/run_worklog.ps1" <name>` (in an isolated worktree session, the absolute path with `$HOME` expanded — `skills/e/SKILL.md` step 2). In the output, read only the block whose header is `[<name>]` — one name can also match another worktree's branch, and a list of deleted worktrees follows.
     - If the header has a ticket (`ticket=<key>`) and a total (`합계 <duration>`), write in the step 5 body "if this time (<total>) is not registered, it cannot be registered after deletion — first rerun the preview command above with `--register` (an upsert, so rerunning makes no duplicates; if registration is blocked (`등록 차단`), check the reason and add `--allow-large-change`)".
     - Do not write it for `ticket=(없음)` or `[<name>] 세션 활동 없음`.
     - If there is neither the target header nor a "세션 활동 없음" line (including a non-zero exit — on Windows it is unknown whether a non-zero exit is visible, #190), write it in the body as a preview failure.
     - Do not register on the user's behalf — it is a consent separate from the deletion confirmation.
5. AskUserQuestion (option 1: worktree only / option 2: worktree + local branch / option 3: worktree + local and remote branch / option 4: cancel). State the warnings (especially unpushed, unmerged and unregistered worklog time) in the question body — remote deletion (option 3) only when the user who saw that warning chooses it.
6. Run: `git worktree remove <path>`. On failure, branch on the stderr cause:
   - **"modified or untracked files"/"use --force" type** (changes or untracked files left): apply `--force` **only after a separate AskUserQuestion** (never force without asking).
   - **File held type** (OS deletion failure — "Access is denied"·"being used"·"Directory not empty"·Windows "Invalid argument"·git `failed to delete` "Permission denied"·`rmdir` of the leftover directory "Device or resource busy"): a live process holds files of that worktree (`.venv` etc.) — though on Linux·macOS "Permission denied" can also be a real permission problem (root-owned files left by docker or sudo), so if no process holds the files, check their owner. `wt rm` is a path the user calls directly, so it cannot know whether the holding process belongs to this session; **do not stop it automatically**, tell the user the holding process and suggest retrying after its owner stops it (`--force` has no effect on an OS hold). Checking for a partial success (registration removed, directory left) and `prune` are in `~/.claude/wiki/docs/worktree-lifecycle.md` §C.
   - Options 2·3 (local branch deletion): `git branch -D <branch>` **only after remove succeeded** (keep the branch when remove fails or is refused).
   - Option 3 (remote deletion too): after the local deletion, `git push origin --delete <branch>` (if the remote ref is absent: a no-op with only a warning).
7. One-line report.

## Cautions

- `git worktree remove --force`, `git branch -D` and remote branch deletion (`git push origin --delete`) are forbidden without the user's explicit confirmation. (`wt rm <name>` is the path where the user names the target directly = CLAUDE.md §8(b) — **a typo can delete the wrong worktree, so always confirm**. The automatic cleanup without asking when merged is §8(a) — the `/e` and right-after-merge flow, not `wt rm`.)
- Text that does not match exactly is treated as a request and creates a new worktree. **Do not ask for confirmation before creating** (risk-based approval — CLAUDE.md §1): a wrong creation from a name typo is undone not by approval but by the §4 near-miss report + `/wt rm <slug>`. Deletion (the first bullet above) is irreversible and keeps confirmation — **within this skill, creation without confirmation and deletion with confirmation** is the result of applying the risk-based standard.
- The request path runs `dlc` automatically after creation. For simple questions, exploration or read-only work that needs no worktree, handle it in the current worktree instead of `/wt`.
- After EnterWorktree, follow-up commands are relative to the new cwd.
- **The automatic copy only covers the new-creation path**. A worktree not made through that path may lack `.claude/settings.local.json` — where the file at the repo root is not used, such as Windows (`references/env-copy.md`), that worktree session's permission allowlist is empty, so copy it once from main if needed (otherwise, 2.1.211+ reads main's file and it is not needed): `cp <main worktree>/.claude/settings.local.json <worktree>/.claude/settings.local.json` (`<main worktree>` = the first line path of `git worktree list`). No bulk retroactive copy (it could revive files the user deliberately deleted, and `wt` is a skill for creating, moving and deleting, not a sync tool).
