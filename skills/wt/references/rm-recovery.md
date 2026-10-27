# rm-recovery — details of wt's creation git sequence · rm failure recovery branches (reference)

This holds the **details of `wt`'s worktree creation git sequence** (§3.1~3.3, and the reasons for the §3.6 self-heal/bootstrap) and the **recovery branches by stderr when `rm` fails** (§6). The SKILL body keeps only the procedure steps and safety gates; the mechanics and fallbacks are here.

> This file is not loaded automatically — `wt` Reads it **when creating a worktree (§3 base ref, `--no-track`, the self-heal judgment)** or **when `rm` branches on a `git worktree remove` failure**. The safety gates (no `--force`/`-D`/remote deletion without confirmation, branch deletion only after remove succeeded) have the SKILL body (`## Cautions`, rm §6) as their single source; this file covers only the "why/how".

## A. Creation git sequence details (§3.1~3.3)
- **`<default>`**: the name from `git symbolic-ref --short refs/remotes/origin/HEAD` with `origin/` removed (`main` on failure). The base ref is `origin/<default>`.
- `git fetch origin <default>` (only a warning on failure).
- `git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default>`.
  - **Why `--no-track`**: it blocks the automatic upstream setting of the new branch → on the first `git push`, the global `push.autoSetupRemote=true` sets it to `origin/<slug>` (= a remote branch with its own name). With track, it would wrongly point to origin/<default>.

## B. Environment setup order · self-heal (§3.6 heal/bootstrap)
In order, in the new cwd. Whatever fails, keep the worktree and report the error as is (the user decides on a manual rerun).
1. **submodule self-heal init**: `uv run --no-project python "${CLAUDE_SKILL_DIR}/heal_submodules.py"`. Automatically repairs an interrupted submodule clone (incomplete objects → "Unable to find current revision"), then inits. A no-op (harmless) in a repo without `.gitmodules`.
   - **Why it runs before bootstrap**: it keeps bootstrap's submodule update from dying on an interrupted, corrupt submodule and stopping the later steps (uv sync etc.).
   - **When it refuses the automatic repair and stops with exit 1** (judged before any deinit or deletion): when a path in `.gitmodules` cannot be read (syntax error, a path without a value, no entries), when the module dir of a submodule name points outside this worktree's `modules` directory (a `..` component or an absolute path — in a linked worktree it reaches as far as `<main>/.git/objects`), or when files to keep remain in the work tree (`.git` is left out of the count only when it is a gitlink file starting with `gitdir: ` — a directory or other content counts as a file to keep). This is so as not to trust the `.gitmodules` set by the cloned repo as a deletion path. After it stops, check the cause and repair manually.
2. If `tools/bootstrap/bootstrap.py` exists, `uv run tools/bootstrap/bootstrap.py` (skip if absent — no effect on other projects).

## C. rm failure stderr branch — file held (§6)
When `git worktree remove <path>` fails, SKILL body §6 branches on stderr. **The safety gates and the branch deletion order (no `--force`/`-D`/remote deletion without confirmation, branch deletion only after remove succeeded) have the SKILL body (`## Cautions`, rm §6) as their single source** — here only the reason for the "file held" branch:
- **File held type** (OS deletion failures such as "Access is denied"·"being used by another process"·"Directory not empty"·Windows "Invalid argument"): a live process holds files of the worktree (`.venv` etc.). `wt rm` **does not stop it automatically; it tells the user** — it is a path the user calls directly, so it cannot know whether the session that started the holding process is this session, and a path filter alone cannot tell it apart from a user server (`/e` step 7 can reclaim processes the same session started — `~/.claude/wiki/docs/worktree-lifecycle.md` §C). (`--force` works at the git level and cannot release an OS file hold.)
- **Partial success** (registration removed but the directory left) is a branch separate from the hold — the check and `prune` procedure are in `~/.claude/wiki/docs/worktree-lifecycle.md` §C.
