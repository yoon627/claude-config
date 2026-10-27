# env-copy — automatic copy mechanics when wt creates a worktree (reference)

This holds the **candidate selection and exclusion rules** of the automatic copy (no opt-out) in §3.4 worktree creation of the `wt` request path. There are two kinds of target — `.env` (secrets) and `.claude/settings.local.json` (the permission allowlist). The SKILL body keeps only "copy from main, skip if it already exists, a failure is only a warning"; the details are here.

> The file name is the same as in the `.env` days (README and the wiki inventory quote it) — the content covers both targets.

> This file is not loaded automatically — `wt` Reads it **when it creates a new worktree (request §3.4 `.env` copy)**. The behavior skeleton "copy, do not overwrite, keep the worktree even on failure" has the SKILL body as its single source; this file covers only "which files are picked as candidates or excluded".

## Candidate selection
- **source = the main worktree path** = the first `worktree <path>` line of `git worktree list --porcelain`. **Always based on main**, even when the current cwd is inside a worktree.
- **Candidate list = `git -C <main> ls-files --others --ignored --exclude-standard`** (lists only ignored files). Pick from this list with the two predicates below.
  - **A. `.env`** — rows whose basename is exactly `.env`. (A `.env` inside a cache ignored as a whole directory is not put in the listing by git, so it is excluded automatically.)
  - **B. Permission allowlist** — the row whose repo-relative path is **exactly `.claude/settings.local.json`** (anchored match, no basename matching).

### Why B is an anchored exact match
Claude Code reads the local settings file at one repo-relative path only: `.claude/settings.local.json` ([settings](https://code.claude.com/docs/en/settings) "Where Claude Code keeps the local file in a git repository"). Since 2.1.211, inside a git repo it uses the file at the repo root, and a worktree session uses the file at the main checkout root — so, apart from the exceptions below, main's permission rules apply even without the copy (measured on 2.1.288 macOS). In the exceptions (Windows, the repo root is the home directory, outside git, the owner of the repo root or its `.git`·`.claude` is not the current user) it reads the file in the session's working directory (including where `EnterWorktree` or `/cd` moved it), so without the copy the worktree session starts with **0 allowed permissions** (CLAUDE.md §8 enforces worktree work, so every real path falls here) — these exceptions are why the copy is needed. Otherwise the copy is a supplement. The docs say that a file an old version left in the start directory is also read together with the root file and both sets of permission rules apply — for a session started directly in the worktree, the copy's rules are added too, and since the copy is from when it was made, an allow later deleted on main also stays. Whether a session entered with `EnterWorktree` also reads the copy is not in the docs and was not measured.

Widening to basename or prefix matching actually drags in the wrong files — in this repo's measurement the same listing shows `.claude/settings.local.json.bak` (a backup) and `settings.local.json` (at the repo root — only for sessions whose cwd is `$HOME`, unrelated to worktrees). Nested worktree copies (`.claude/worktrees/<other>/.claude/settings.local.json`) are excluded for the same reason.

### Why B is narrowed to one target
The other ignored files under `.claude/` are of a different nature — `.credentials.json` (credentials; copying widens the exposure) · `history.jsonl` (session history) · `*.lock` (locks) · `*.bak` (backups) · `worktrees/` (recursion). Widening gains nothing and only adds risk.

### That the candidate list is ignored files is itself a safeguard
If a repo keeps `.claude/settings.local.json` tracked, it is never a candidate (the worktree checkout already has it then), and if it is untracked but not ignored it is not picked either, so **files at risk of being committed are not pushed into the worktree**.

## Extra exclusions (regex, matching at any segment)
`(^|/)(\.venv|node_modules|__pycache__|\.uv-cache|\.cache|dist|build)/` — a safety net for pattern ignores that are not by directory.

## Copy
- Copy each candidate to **the same relative path** inside `.claude/worktrees/<slug>/`. mkdir the parent directory if it is missing.
- **If a file already exists at the same path, skip (do not overwrite).**
- A copy failure (permissions, etc.) only prints a warning, and the worktree stays.
- Report: `.env: N copied, M skipped` · `settings.local: N copied, M skipped` (omit each when both are 0).
