#!/usr/bin/env python3
"""Worktree 생성 시 submodule self-heal init — wt 스킬이 bootstrap 전에 호출한다.

새 worktree 는 submodule 을 worktree 별로(`.git/worktrees/<wt>/modules/<name>`)
새로 clone 하는데, 이 clone 이 중단되면 objects 가 불완전한 채 남아 다음
`git submodule update --init` 이 "Unable to find current revision" 으로 실패하고
스스로 복구하지 못한다(수동 deinit 필요).

이 스크립트는 update 실패 시 submodule 을 리셋(deinit + module dir 삭제)하고 1회
재clone 해 자동 복구한다. `deinit -f` 는 module dir(objects)를 보존하므로 corrupt
를 비우려면 module dir 직접 삭제가 필요하다(gitsubmodules(7)).

데이터 손실 방지: work tree 에 (`.git` 파일 외) 파일이 남은 submodule 은 리셋하지
않고 중단한다. corrupt 상태에선 `git status` 가 rc=128 로 죽어 dirty 를 못 잡지만
사용자 파일은 디스크에 남으므로, status 가 아니라 실제 파일 존재로 판정한다.

`.gitmodules` 없는 레포에서는 no-op 이라 어느 프로젝트에서 돌려도 무해하다.
git 만 호출하므로 stdlib 외 의존성이 없다.

Usage (worktree cwd 에서):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/heal_submodules.py"
"""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# Windows 콘솔 기본 인코딩(cp1252 등)에서 한글 로그 출력 시 UnicodeEncodeError
# 가 나는 걸 막기 위해 stdout/stderr 를 utf-8 로 강제.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")


def log(msg: str) -> None:
    print(f"[heal-submodules] {msg}", flush=True)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def try_capture(cmd: list[str]) -> str | None:
    """run 과 같지만 non-zero 종료 시 None 반환."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _submodule_entries(repo_root: Path) -> list[tuple[str, str]] | None:
    """.gitmodules 의 (name, path) 목록. name 은 git 이 module 디렉터리
    (.git/modules/<name>)를 만들 때 쓰는 식별자라 path 와 다를 수 있다.
    항목이 없거나 파일이 없으면 [], 파일을 믿을 수 없으면(문법 오류·값 없는 path) None.
    `-z` 레코드는 `key\\nvalue\\0` 이고 name·값에 공백·개행이 들어갈 수 있어 첫 `\\n` 에서만 나눈다.
    bytes 로 받아 직접 디코드한다 — text 모드는 `\\r` 을 `\\n` 으로 바꿔 name 을 잘라 버린다."""
    result = subprocess.run(
        [
            "git",
            "config",
            "-z",
            "-f",
            str(repo_root / ".gitmodules"),
            "--get-regexp",
            r"^submodule\..*\.path$",
        ],
        capture_output=True,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        return None
    entries: list[tuple[str, str]] = []
    for record in result.stdout.decode("utf-8", errors="surrogateescape").split("\0"):
        if not record:
            continue
        key, sep, path = record.partition("\n")
        if not sep or not path:
            return None
        entries.append((key.removeprefix("submodule.").removesuffix(".path"), path))
    return entries


def _git_path(repo_root: Path, rel: str) -> str | None:
    """`git rev-parse --git-path` 결과. 끝 줄바꿈만 떼고 공백·`\\r` 은 남긴다 — strip 하거나
    text 모드로 받으면 name `sub ` 나 `sub\\r` 이 형제 `sub` 의 module dir 로 풀린다."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-path", rel],
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="surrogateescape").removesuffix("\n")


def _module_dir(name: str, repo_root: Path) -> Path | None:
    """name 의 module 디렉터리(삭제 대상)를 resolve 해 돌려준다. 그 경로가 이 worktree 의
    modules 디렉터리 밖이면 None. linked worktree 에선 modules 가 <main>/.git/worktrees/<wt>/
    아래라 `../` 몇 개로 main 의 objects 까지 닿으므로, repo·.git 이 아니라 modules 를 경계로 삼는다.
    `..` 구성요소 거부는 git 자신의 submodule name 검사와 같은 기준이다."""
    parts = name.replace("\\", "/").split("/")
    if not name or Path(name).is_absolute() or name.startswith("/") or ".." in parts:
        return None
    base = _git_path(repo_root, "modules")
    target = _git_path(repo_root, f"modules/{name}")
    if not base or not target:
        return None
    base_dir = (repo_root / base).resolve()
    module_dir = (repo_root / target).resolve()
    if module_dir == base_dir or not module_dir.is_relative_to(base_dir):
        return None
    return module_dir


def _submodule_worktree_has_files(worktree: Path) -> bool:
    """work tree 에 (.git gitlink 파일 외) 항목이 하나라도 있으면 True.
    self-heal 은 work tree 가 빈 submodule(=clone 중단, checkout 전)만 리셋하고,
    파일이 남아 있으면(사용자 편집·정상 checkout·partial checkout) 거부한다. corrupt
    objects 상태에서는 `git status` 가 rc=128 로 죽어 dirty 를 못 잡지만 work tree
    파일은 디스크에 멀쩡히 남으므로, status 가 아니라 실제 파일 존재로 판정해야
    deinit 이 사용자 파일을 말없이 날리는 사고를 막을 수 있다.
    `.git` 은 gitlink 파일일 때만 제외한다 — `.git` 이 디렉터리(미흡수 submodule,
    objects 내장)면 고유 데이터일 수 있어 '파일 있음'으로 보아 리셋을 거부한다."""
    if not worktree.is_dir():
        return False
    return any(
        not (child.name == ".git" and child.is_file()) for child in worktree.iterdir()
    )


def _force_rmtree(path: Path) -> None:
    """Windows 는 git pack 파일이 read-only 라 shutil.rmtree 가 PermissionError 를
    낸다 — 먼저 하위 파일의 read-only 를 풀고 삭제한다. 경로가 없으면 no-op. 다른
    프로세스가 파일을 점유(WinError 32)하면 OSError 가 나며 호출부가 안내·surface 한다."""
    if not path.is_dir():
        return
    for child in path.rglob("*"):
        if child.is_file():
            os.chmod(child, stat.S_IWRITE)
    shutil.rmtree(path)


def _reset_submodule(name: str, path: str) -> None:
    """submodule 을 깨끗한 재clone 가능 상태로 리셋. deinit 은 work tree+config 만
    지우고 module dir(objects)는 보존하므로, corrupt objects 를 비우려면 module dir
    까지 삭제해야 한다 (gitsubmodules(7): "manually delete $GIT_DIR/modules/<name>").
    호출 전에 init_submodules 가 전 항목을 검증하지만, 삭제 직전에 경계를 한 번 더 본다."""
    git_dir = _module_dir(name, Path.cwd())
    if git_dir is None:
        log(f"module dir 을 확인할 수 없거나 modules 밖을 가리켜 삭제하지 않음: {name}")
        sys.exit(1)
    # deinit 은 빈 work tree+config 정리용. 미초기화 submodule 등에서 실패해도
    # 이어지는 module dir 삭제+재clone 으로 복구되므로 best-effort 로 무시한다.
    try:
        run(["git", "submodule", "deinit", "-f", "--", path])
    except subprocess.CalledProcessError:
        log(f"deinit 실패(미초기화 가능) — module dir 삭제로 진행: {path}")
    try:
        _force_rmtree(git_dir)
    except OSError as exc:
        # 다른 프로세스(에디터·git GUI·백신)가 pack 을 점유하면 chmod 로도 못 풀어
        # 일부만 지워질 수 있다. bare traceback 대신 조치 방법을 안내하고 surface.
        log(
            f"module dir 삭제 실패({exc}) — 점유 프로세스 종료 후 수동 삭제 필요: "
            f"{git_dir}"
        )
        raise


def init_submodules(repo_root: Path) -> None:
    if not (repo_root / ".gitmodules").is_file():
        return
    log("git submodule update --init --recursive")
    try:
        run(["git", "submodule", "update", "--init", "--recursive"])
        return
    except subprocess.CalledProcessError:
        log("submodule update 실패 — 중단된 clone 으로 보고 자가복구 판정")

    # 어떤 deinit·삭제보다 먼저 전 항목을 검증한다 — .gitmodules 는 clone 한 repo 가 정하는 입력이다.
    entries = _submodule_entries(repo_root)
    if not entries:
        log(".gitmodules 의 submodule path 를 읽을 수 없어 자동 복구를 중단(문법 오류·값 없는 path·항목 없음)")
        sys.exit(1)
    dirs = [_module_dir(name, repo_root) for name, _ in entries]
    escaping = [name for (name, _), d in zip(entries, dirs) if d is None]
    if escaping:
        log(f"module dir 을 확인할 수 없거나 modules 밖을 가리키는 submodule name 이 있어 자동 복구를 중단: {', '.join(escaping)}")
        sys.exit(1)
    # 한 module dir 이 다른 것과 같거나 그 안이면(`a` 와 `a/objects`) 리셋이 형제의 object DB 를 지운다.
    overlapping = [
        name
        for i, (name, _) in enumerate(entries)
        if any(j != i and (dirs[i] == o or dirs[i].is_relative_to(o)) for j, o in enumerate(dirs))
    ]
    if overlapping:
        log(f"module dir 이 다른 submodule 과 겹치는 name 이 있어 자동 복구를 중단: {', '.join(overlapping)}")
        sys.exit(1)

    # work tree 에 파일이 남은 submodule 은 절대 자동 리셋하지 않는다(데이터 손실 방지).
    unsafe = [
        path for _, path in entries if _submodule_worktree_has_files(repo_root / path)
    ]
    if unsafe:
        log(f"work tree 에 보존할 파일이 있어 자동 복구를 중단: {', '.join(unsafe)}")
        log(
            "수동 복구(필요한 파일 백업 후): git submodule deinit -f <path> && "
            "rm -rf <module dir> && git submodule update --init --recursive"
        )
        sys.exit(1)

    for name, path in entries:
        _reset_submodule(name, path)

    log("git submodule update --init --recursive (자가복구 재clone)")
    try:
        run(["git", "submodule", "update", "--init", "--recursive"])
    except subprocess.CalledProcessError:
        log("자가복구 후에도 submodule update 실패 — 네트워크/인증/권한 확인 필요")
        raise


def main() -> int:
    repo_root_str = try_capture(["git", "rev-parse", "--show-toplevel"])
    if not repo_root_str:
        log("git 저장소가 아님 — skip")
        return 0
    repo_root = Path(repo_root_str)
    os.chdir(repo_root)
    init_submodules(repo_root)  # .gitmodules 없으면 내부에서 no-op
    return 0


if __name__ == "__main__":
    sys.exit(main())
