"""UserPromptSubmit hook: intercept exact `gwl` and show annotated git worktree list."""
import json
import os
import subprocess
import sys


def normalize(p: str) -> str:
    return p.replace("\\", "/").rstrip("/")


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
            ["git", "worktree", "list"],
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
            parsed = []
            for raw in proc.stdout.splitlines():
                parts = raw.split(None, 2)
                if len(parts) < 3:
                    continue
                path_token, sha, rest = parts
                path_norm = normalize(path_token)
                name = os.path.basename(path_norm) or path_norm
                is_current = cwd_norm == path_norm or cwd_norm.startswith(path_norm + "/")
                parsed.append((is_current, name, sha, rest))
            if not parsed:
                reason = "(no worktrees)"
            else:
                name_w = max(len(p[1]) for p in parsed)
                rendered = [
                    f"{'→' if cur else ' '} {nm:<{name_w}}  {sha}  {rest}"
                    for cur, nm, sha, rest in parsed
                ]
                reason = "\n".join(rendered)

    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
