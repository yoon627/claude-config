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
        is_current = cwd_norm == path_norm or cwd_norm.startswith(path_norm + "/")
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
        parsed.append((is_current, name, sha, label))

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
    return parsed


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("prompt") != "gwl":
        return 0

    cwd = data.get("cwd") or os.getcwd()
    cwd_norm = normalize(cwd)

    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        reason = "git: command not found"
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
