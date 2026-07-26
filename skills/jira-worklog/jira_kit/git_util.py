"""git worktree 조회 (stdlib subprocess).

worklog·standup·task-sync 가 공유하는 git 접근 계층. 순수 파싱(parse_worktree_porcelain)은
subprocess 없이 테스트한다.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    """git 명령 실패 (미설치·repo 밖·깨진 worktree 등)."""


@dataclass(frozen=True)
class Worktree:
    path: str
    branch: str | None


def run_git(args: list[str], cwd: str | None = None) -> str:
    # encoding 을 UTF-8 로 고정한다 — git 출력(한글 커밋 메시지 등)은 UTF-8 인데
    # Windows 기본 로케일(cp1252)로 디코드하면 UnicodeDecodeError 가 난다.
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        raise GitError("git 실행 파일을 찾을 수 없습니다") from None
    except subprocess.CalledProcessError as exc:
        raise GitError(f"git {' '.join(args)} 실패: {exc.stderr.strip()}") from None
    return result.stdout.strip()


def parse_worktree_porcelain(text: str) -> list[Worktree]:
    """`git worktree list --porcelain` 출력에서 (path, branch) 를 뽑는다."""
    worktrees: list[Worktree] = []
    path: str | None = None
    branch: str | None = None
    for line in text.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree ") :]
            branch = None
        elif line.startswith("branch "):
            branch = line[len("branch ") :].removeprefix("refs/heads/")
        elif not line.strip() and path is not None:
            worktrees.append(Worktree(path, branch))
            path = branch = None
    if path is not None:
        worktrees.append(Worktree(path, branch))
    return worktrees


def list_worktrees(cwd: str | None = None) -> list[Worktree]:
    return parse_worktree_porcelain(run_git(["worktree", "list", "--porcelain"], cwd))


def current_worktree(cwd: str | None = None) -> Worktree | None:
    """cwd 가 속한 worktree(최상위 일치)를 반환한다. 못 찾으면 None."""
    top = Path(run_git(["rev-parse", "--show-toplevel"], cwd))
    for worktree in list_worktrees(cwd):
        if Path(worktree.path) == top:
            return worktree
    return None
