"""UserPromptSubmit hook: intercept exact `gwl` and show annotated git worktree list."""
import json
import os
import subprocess
import sys


def normalize(p: str) -> str:
    return p.replace("\\", "/").rstrip("/")


def parse_porcelain(out: str, cwd_norm: str):
    """Parse `git worktree list --porcelain` into (is_current, name, sha, label).

    Porcelain emits one record per worktree (fields one-per-line, records
    separated by a blank line), so worktree paths containing spaces are
    preserved verbatim and bare/detached entries are explicit — unlike the
    human format, which is whitespace-ambiguous.
    """
    parsed = []
    rec = {}

    def flush():
        wt = rec.get("worktree")
        if not wt:
            return
        path_norm = normalize(wt)
        name = os.path.basename(path_norm) or path_norm
        if "bare" in rec:
            sha, label = "", "(bare)"
        elif "detached" in rec:
            sha, label = rec.get("HEAD", "")[:7], "(detached HEAD)"
        else:
            sha = rec.get("HEAD", "")[:7]
            branch = rec.get("branch", "")
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
            label = f"[{branch}]" if branch else "[?]"
        for ann in ("locked", "prunable"):
            if ann in rec:
                label += f" ({ann})"
        parsed.append((path_norm, name, sha, label))

    for raw in out.splitlines():
        if not raw:
            flush()
            rec = {}
            continue
        key, _, val = raw.partition(" ")
        if key in ("worktree", "HEAD", "branch"):
            rec[key] = val
        elif key in ("bare", "detached", "locked", "prunable"):
            rec[key] = True
    flush()
    # Worktrees can nest under the main checkout (.claude/worktrees/<n>); only the longest matching path is current.
    matches = [p for p, *_ in parsed if cwd_norm == p or cwd_norm.startswith(p + "/")]
    current = max(matches, key=len) if matches else None
    return [(p == current, name, sha, label) for p, name, sha, label in parsed]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("prompt") != "gwl":
        return 0

    cwd = data.get("cwd") or os.getcwd()
    cwd_norm = normalize(cwd)
    # git's own toplevel, like gwl.zsh: `git worktree list` prints the same physical path, so a
    # symlinked cwd still matches. Outside a work tree the raw cwd is kept (the list call reports why).
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, check=False)
        if top.returncode == 0 and top.stdout.strip():
            cwd_norm = normalize(top.stdout.strip())
    except (FileNotFoundError, NotADirectoryError):
        pass

    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        # On Windows a missing executable reports filename=None; only a missing cwd names the cwd.
        reason = str(exc) if exc.filename == cwd else "git: command not found"
    else:
        if proc.returncode != 0:
            reason = (proc.stderr or proc.stdout).strip() or f"git exited {proc.returncode}"
        else:
            parsed = parse_porcelain(proc.stdout, cwd_norm)
            if not parsed:
                reason = "(no worktrees)"
            else:
                name_w = max(len(p[1]) for p in parsed)
                sha_w = max(len(p[2]) for p in parsed)
                rendered = [
                    f"{'→' if cur else ' '} {nm:<{name_w}}  {sha:<{sha_w}}  {rest}"
                    for cur, nm, sha, rest in parsed
                ]
                reason = "\n".join(rendered)

    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
