#!/usr/bin/env python3
"""브랜치 커밋 단위 점검·재구성 — commit-check 스킬이 호출한다.

  collect         현재 브랜치의 재작성 대상 커밋(다른 로컬 브랜치·원격·태그에서 도달 불가)을
                  JSON 으로 낸다. 커밋별 파일·플래그·overlap·관례 샘플 포함.
  show <sha>      판정용 커밋 패치(모델이 raw git 을 치지 않게).
  apply <plan>    모델이 만든 계획(JSON 파일, '-' 면 stdin)대로 커밋 경계를 재구성한다.

재구성은 plumbing(`merge-tree --write-tree` + `commit-tree`)으로만 하고 사용자 index·작업트리는
건드리지 않는다. 모든 검증(최종 tree 동일·커밋별 파일)을 통과한 뒤에만 백업 ref 생성·오래된 백업
정리·브랜치 이동을 `update-ref --stdin` 트랜잭션 하나로 수행한다 — 실패하면 만든 객체를 버릴 뿐
ref 는 그대로다(예외: repo 의 commit-msg hook 이 스스로 일으킨 부작용). push 는 하지 않는다.
게시(원격 도달) 커밋은 범위에서 빠지므로 force-push 가 필요한 경우가 없다.

Usage (repo 안에서):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/commit_units.py" collect
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = 1
MIN_GIT = (2, 40)  # merge-tree --merge-base
BACKUP_NS = "refs/commit-check"
KEEP_BACKUPS = 5
STAMP = re.compile(r"^\d{8}T\d{6,}Z$")
IN_PROGRESS = ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "sequencer")
SINGLE_VALUE_TRAILERS = {"change-id"}

_FLAG_PATTERNS = (
    ("wip", re.compile(r"^wip\b", re.I)),
    ("fixup", re.compile(r"^(fixup|squash|amend)!")),
    ("review-followup", re.compile(
        r"리뷰\s*(반영|지적)|address(ed)?\s+review|review\s+(fix|feedback|comments?)|\bnits?\b|오타|\btypo", re.I)),
)


class CommitCheckError(Exception):
    pass


class Git:
    def __init__(self, cwd: Path | str, env: dict[str, str] | None = None) -> None:
        self.cwd = Path(cwd)
        self.env = env

    def run(self, *args: str, input: bytes | None = None, env_extra: dict[str, str] | None = None) -> bytes:
        env = dict(self.env if self.env is not None else os.environ)
        env["GIT_LITERAL_PATHSPECS"] = "1"
        if env_extra:
            env.update(env_extra)
        r = subprocess.run(["git", *args], cwd=self.cwd, env=env, input=input, capture_output=True)
        if r.returncode != 0:
            detail = (r.stderr or r.stdout).decode("utf-8", "replace").strip()[:800]
            raise CommitCheckError(f"git {' '.join(args[:2])} 실패(exit {r.returncode}): {detail}")
        return r.stdout


def _text(b: bytes) -> str:
    return b.decode("utf-8", "replace")


def _lines(b: bytes) -> list[str]:
    return [x for x in _text(b).splitlines() if x]


def _nul_fields(b: bytes) -> list[str]:
    return [_text(x) for x in b.split(b"\0") if x]


def _rev_list(git: Git, include: list[str], exclude: list[str], *opts: str) -> list[str]:
    """제외 ref 가 많아도 argv 길이 제한에 걸리지 않게 stdin 으로 넘긴다."""
    spec = "\n".join([*include, "--not", *exclude]) + "\n"
    return _lines(git.run("rev-list", *opts, "--stdin", input=spec.encode("utf-8")))


def current_branch(git: Git) -> str:
    try:
        ref = _text(git.run("symbolic-ref", "HEAD")).strip()
    except CommitCheckError:
        raise CommitCheckError("detached HEAD 에서는 점검할 브랜치가 없다") from None
    return ref.removeprefix("refs/heads/")


def _refs(git: Git, *prefixes: str) -> list[tuple[str, str]]:
    return [tuple(x.split(" ", 1)) for x in _lines(git.run("for-each-ref", "--format=%(refname) %(objectname)", *prefixes))]  # type: ignore[misc]


def _default_ref(git: Git) -> str | None:
    try:
        ref = _text(git.run("symbolic-ref", "-q", "refs/remotes/origin/HEAD")).strip()
        if ref:
            return ref
    except CommitCheckError:
        pass
    for name in ("refs/heads/main", "refs/heads/master"):
        if _refs(git, name):
            return name
    return None


def _default_branch_name(default: str | None) -> set[str]:
    names = {"main", "master"}
    if default:
        names.add(re.sub(r"^refs/(heads|remotes/[^/]+)/", "", default))
    return names


def commit_files(git: Git, sha: str) -> list[dict]:
    out = git.run("diff-tree", "-r", "-z", "--no-commit-id", "--name-status", "-M", sha).split(b"\0")
    files, i = [], 0
    while i < len(out) and out[i]:
        status = _text(out[i])
        if status[:1] in ("R", "C"):
            files.append({"status": status[:1], "old_path": _text(out[i + 1]), "path": _text(out[i + 2])})
            i += 3
        else:
            files.append({"status": status[:1], "path": _text(out[i + 1])})
            i += 2
    return files


def _paths(files: list[dict]) -> set[str]:
    out = set()
    for f in files:
        out.add(f["path"])
        if f.get("old_path") and f["status"] == "R":
            out.add(f["old_path"])
    return out


def _changes(git: Git, sha: str) -> tuple[int, int]:
    added = deleted = 0
    for line in _lines(git.run("diff-tree", "-r", "--no-commit-id", "--numstat", "-M", sha)):
        a, d, _ = line.split("\t", 2)
        added += int(a) if a.isdigit() else 0
        deleted += int(d) if d.isdigit() else 0
    return added, deleted


def _meta(git: Git, sha: str) -> dict:
    subject, body, name, email, date = _text(
        git.run("log", "-1", "--format=%s%x00%B%x00%an%x00%ae%x00%ad", "--date=raw", sha)
    ).split("\0")
    return {"subject": subject, "message": body.rstrip("\n") + "\n", "author_name": name,
            "author_email": email, "author_date": date.strip()}


def _signed(git: Git, sha: str) -> bool:
    header = _text(git.run("cat-file", "commit", sha)).split("\n\n", 1)[0]
    return any(line.startswith("gpgsig") for line in header.splitlines())


def _flags(subject: str, files: list[dict]) -> list[str]:
    flags = [name for name, pat in _FLAG_PATTERNS if pat.search(subject)]
    if not files:
        flags.append("empty")
    elif all(f["path"].startswith("plans/") for f in files):
        flags.append("plan-only")
    return flags


def resolve_range(git: Git) -> dict:
    branch = current_branch(git)
    head = _text(git.run("rev-parse", "HEAD")).strip()
    heads = [r for r, _ in _refs(git, "refs/heads/") if r != f"refs/heads/{branch}"]
    tags = [r for r, _ in _refs(git, "refs/tags/")]
    remotes = [r for r, _ in _refs(git, "refs/remotes/")]
    exclude = heads + tags + remotes
    commits = _rev_list(git, ["HEAD"], exclude, "--reverse", "--topo-order")
    if _rev_list(git, ["HEAD"], exclude, "--merges"):
        raise CommitCheckError("재작성 범위에 merge 커밋이 있다 — 선형 이력만 지원")
    base = head
    if commits:
        parents = _text(git.run("rev-list", "--parents", "-n", "1", commits[0])).split()[1:]
        if not parents:
            raise CommitCheckError("범위가 루트 커밋까지 내려간다 — 기준 브랜치(main 등)·원격·태그가 없는 repo 다. "
                                   "기준 브랜치에서 분기한 작업 브랜치에서 실행한다")
        if len(parents) != 1:
            raise CommitCheckError("범위 첫 커밋이 merge 커밋이다 — 선형 이력만 지원")
        base = parents[0]
    default = _default_ref(git)
    published = len(_rev_list(git, ["HEAD"], heads + tags + ([default] if default else []))) - len(commits)
    tagged = len(_rev_list(git, ["HEAD"], heads + remotes)) - len(commits)
    return {"branch": branch, "head": head, "base": base, "commits": commits, "default_ref": default,
            "on_default": branch in _default_branch_name(default), "upstreams": _branch_upstreams(git, branch),
            "excluded": {"published": published, "tags": tagged}}


def _branch_upstreams(git: Git, branch: str) -> list[tuple[str, str | None]]:
    """각 remote 의 `refs/remotes/<remote>/<branch>` 와 현재 값(없으면 None).

    collect 와 ref 이동 사이에 이 브랜치가 push 되면(처음 push 포함) 트랜잭션 verify 가 막는다.
    무관한 원격 ref·symref(`origin/HEAD`)는 넣지 않는다 — 넣으면 fetch 마다 실패하거나 symref 이중 갱신으로 거부된다.
    """
    out = []
    for remote in _lines(git.run("remote")):
        ref = f"refs/remotes/{remote}/{branch}"
        found = _refs(git, ref)
        out.append((ref, found[0][1] if found else None))
    return out


def collect(git: Git, rng: dict | None = None) -> dict:
    rng = rng or resolve_range(git)
    commits = []
    for sha in rng["commits"]:
        meta = _meta(git, sha)
        files = commit_files(git, sha)
        added, deleted = _changes(git, sha)
        commits.append({"sha": sha, **meta, "files": files, "added": added, "deleted": deleted,
                        "flags": _flags(meta["subject"], files)})
    overlaps = []
    for i, later in enumerate(commits):
        mine = {p for p in _paths(later["files"]) if not p.startswith("plans/")}
        for earlier in commits[:i]:
            shared = mine & _paths(earlier["files"])
            if shared:
                overlaps.append({"commit": later["sha"], "earlier": earlier["sha"], "files": sorted(shared)})
    default = rng["default_ref"]
    samples = _lines(git.run("log", "-20", "--no-merges", "--format=%s", default)) if default else []
    return {
        "schema": SCHEMA, "branch": rng["branch"], "on_default_branch": rng["on_default"],
        "base": rng["base"], "head": rng["head"], "commits": commits, "overlaps": overlaps,
        "excluded": rng["excluded"], "default_ref": default, "convention_samples": samples,
        "signed": any(_signed(git, c["sha"]) for c in commits),
    }


def _nested_conflict(cov: set[str], paths: set[str]) -> str | None:
    """파일↔디렉토리 전환(f 삭제 + f/z 추가)은 한 항목에 있어야 합성 tree 가 성립한다."""
    for q in paths:
        parts = q.split("/")
        for i in range(1, len(parts)):
            p = "/".join(parts[:i])
            if p in paths and ((p in cov) != (q in cov)):
                return f"{p} ↔ {q}"
    return None


def validate_plan(plan: dict, data: dict) -> list[dict]:
    """계획 스키마의 정본. 각 범위 커밋의 파일을 항목들이 빠짐없이·겹침 없이 나눠 가져야 한다."""
    if not isinstance(plan, dict):
        raise CommitCheckError("계획은 JSON 객체여야 한다")
    if plan.get("schema") != SCHEMA:
        raise CommitCheckError(f"계획 schema 는 {SCHEMA} 이어야 한다")
    if plan.get("base") != data["base"] or plan.get("head") != data["head"]:
        raise CommitCheckError("수집 이후 브랜치가 바뀌었다(base/head 불일치) — collect 부터 다시")
    order = {c["sha"]: i for i, c in enumerate(data["commits"])}
    files = {c["sha"]: c["files"] for c in data["commits"]}
    entries = plan.get("commits")
    if not isinstance(entries, list) or (data["commits"] and not entries):
        raise CommitCheckError("계획 commits 는 비어 있지 않은 목록이어야 한다")
    coverage: dict[str, list[set[str]]] = {}
    out = []
    for n, e in enumerate(entries, 1):
        if not isinstance(e, dict):
            raise CommitCheckError(f"{n}번 항목은 객체여야 한다")
        src = e.get("from")
        if not isinstance(src, list) or not src or not all(isinstance(s, str) and s in order for s in src):
            raise CommitCheckError(f"{n}번 항목: from 은 범위 커밋 sha 목록이어야 한다")
        if len(set(src)) != len(src) or src != sorted(src, key=order.__getitem__):
            raise CommitCheckError(f"{n}번 항목: from 은 중복 없이 원래 순서대로")
        paths = e.get("paths")
        message = e.get("message")
        if message is not None and (not isinstance(message, str) or not message.strip()):
            raise CommitCheckError(f"{n}번 항목: message 는 비어 있지 않은 문자열")
        if paths is not None:
            if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
                raise CommitCheckError(f"{n}번 항목: paths 는 비어 있지 않은 경로 목록")
            if message is None:
                raise CommitCheckError(f"{n}번 항목: 경로로 나눈 항목은 message 가 필요하다")
            if set(paths) - set().union(*(_paths(files[s]) for s in src)):
                raise CommitCheckError(f"{n}번 항목: from 커밋에 없는 경로가 있다")
        covs = {}
        for s in src:
            cov = _paths(files[s]) if paths is None else _paths(files[s]) & set(paths)
            if paths is not None:
                if not cov:
                    raise CommitCheckError(f"{n}번 항목: {s[:8]} 는 이 경로들을 바꾸지 않는다")
                for f in files[s]:
                    if f["status"] == "R" and ((f["old_path"] in cov) != (f["path"] in cov)):
                        raise CommitCheckError(f"{n}번 항목: rename 쌍({f['old_path']} → {f['path']})은 같은 항목이어야 한다")
                nested = _nested_conflict(cov, _paths(files[s]))
                if nested:
                    raise CommitCheckError(f"{n}번 항목: 파일↔디렉토리 전환({nested})은 같은 항목이어야 한다")
            coverage.setdefault(s, []).append(cov)
            covs[s] = cov
        out.append({"from": src, "paths": paths, "message": message, "cover": covs})
    for sha in order:
        covs = coverage.get(sha)
        if not covs:
            raise CommitCheckError(f"{sha[:8]} 가 계획에 없다")
        union = set().union(*covs)
        if union != _paths(files[sha]) or sum(len(c) for c in covs) != len(union) or (not union and len(covs) != 1):
            raise CommitCheckError(f"{sha[:8]} 의 파일이 항목들에 빠짐없이·겹침 없이 나뉘지 않았다")
    return out


def _parent(git: Git, sha: str) -> str:
    return _text(git.run("rev-parse", f"{sha}^")).strip()


def _tree(git: Git, rev: str) -> str:
    return _text(git.run("rev-parse", f"{rev}^{{tree}}")).strip()


def _commit_tree(git: Git, tree: str, parent: str, message: str, author: dict | None = None) -> str:
    env = None
    if author:
        epoch, tz = author["author_date"].split()
        env = {"GIT_AUTHOR_NAME": author["author_name"], "GIT_AUTHOR_EMAIL": author["author_email"],
               "GIT_AUTHOR_DATE": f"@{epoch} {tz}"}
    out = git.run("commit-tree", tree, "-p", parent, "--no-gpg-sign", "-F", "-",
                  input=message.encode("utf-8"), env_extra=env)
    return _text(out).strip()


def _path_limited(git: Git, sha: str, paths: set[str]) -> str:
    """부모 tree 에 `paths` 만 sha 의 상태로 바꾼 합성 커밋(부모는 sha 의 부모).

    경로는 전부 repo 루트 기준 `--index-info` 레코드로 넣는다(삭제는 mode 0) — cwd 가 하위 디렉토리여도
    같은 결과가 나오게.
    """
    parent = _parent(git, sha)
    zero = "0" * len(parent)
    fd, index = tempfile.mkstemp(prefix="commit-check-index-")
    os.close(fd)
    os.unlink(index)
    env = {"GIT_INDEX_FILE": index}
    try:
        git.run("read-tree", parent, env_extra=env)
        listed = git.run("ls-tree", "-z", "--full-tree", sha, "--", *sorted(paths)).split(b"\0")
        present = set()
        info = b""
        for rec in filter(None, listed):
            head, path = rec.split(b"\t", 1)
            mode, _type, obj = head.split(b" ")
            present.add(_text(path))
            info += mode + b" " + obj + b"\t" + path + b"\0"
        for gone in sorted(paths - present):
            info += f"0 {zero}\t{gone}".encode("utf-8") + b"\0"
        git.run("update-index", "-z", "--index-info", input=info, env_extra=env)
        tree = _text(git.run("write-tree", env_extra=env)).strip()
    finally:
        for leftover in (index, index + ".lock"):
            if os.path.exists(leftover):
                os.unlink(leftover)
    return _commit_tree(git, tree, parent, "commit-check path-limited\n")


def _trailers(git: Git, message: str) -> list[str]:
    return _lines(git.run("interpret-trailers", "--parse", "--no-divider", input=message.encode("utf-8")))


def _trailer_key(trailer: str) -> str:
    return trailer.split(":", 1)[0].strip().lower()


def _merge_trailers(git: Git, message: str, sources: list[str]) -> str:
    have = _trailers(git, message)
    keys = {_trailer_key(t) for t in have}
    extra: list[str] = []
    for src in sources:
        for t in _trailers(git, src):
            key = _trailer_key(t)
            if t in have or t in extra or (key in SINGLE_VALUE_TRAILERS and key in keys):
                continue
            extra.append(t)
            keys.add(key)
    if not extra:
        return message
    sep = "\n" if have else "\n\n"
    return message.rstrip("\n") + sep + "\n".join(extra) + "\n"


def _run_commit_msg_hook(git: Git, message: str) -> str:
    fd, path = tempfile.mkstemp(prefix="commit-check-msg-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(message)
        git.run("hook", "run", "--ignore-missing", "commit-msg", "--", path,
                env_extra={"GIT_LITERAL_PATHSPECS": "0"})
        return Path(path).read_text(encoding="utf-8")
    finally:
        os.unlink(path)


def _entry_tree(git: Git, tip: str, entry: dict) -> str:
    cur = tip
    tree = _tree(git, tip)
    for i, s in enumerate(entry["from"]):
        src = s if entry["paths"] is None else _path_limited(git, s, entry["cover"][s])
        tree = _lines(git.run("merge-tree", "--write-tree", f"--merge-base={_parent(git, s)}", cur, src))[0]
        if i < len(entry["from"]) - 1:
            cur = _commit_tree(git, tree, cur, "commit-check intermediate\n")
    return tree


def _entry_message(git: Git, entry: dict, metas: dict) -> str:
    target = metas[entry["from"][0]]
    message = entry["message"] if entry["message"] is not None else target["message"]
    if not message.endswith("\n"):
        message += "\n"
    message = _merge_trailers(git, message, [metas[s]["message"] for s in entry["from"]])
    if entry["message"] is not None or message != target["message"]:
        message = _run_commit_msg_hook(git, message)
    return message


def rebuild(git: Git, data: dict, entries: list[dict]) -> list[dict]:
    metas = {c["sha"]: c for c in data["commits"]}
    tip = data["base"]
    made = []
    for n, e in enumerate(entries, 1):
        tree = _entry_tree(git, tip, e)
        originally_empty = all("empty" in metas[s]["flags"] for s in e["from"])
        if tree == _tree(git, tip) and not originally_empty:
            raise CommitCheckError(f"{n}번 항목이 빈 커밋이 된다(되돌림끼리 합치는 drop 은 미지원)")
        message = _entry_message(git, e, metas)
        new = _commit_tree(git, tree, tip, message, author=metas[e["from"][0]])
        actual = set(_nul_fields(git.run("diff-tree", "-r", "-z", "--no-commit-id", "--name-only", "--no-renames", new)))
        expected = set().union(*e["cover"].values())
        if not actual <= expected:
            raise CommitCheckError(f"{n}번 항목 결과에 계획 밖 파일이 섞였다: {sorted(actual - expected)}")
        made.append({"sha": new, "subject": message.splitlines()[0], "files": sorted(actual)})
        tip = new
    if _tree(git, tip) != _tree(git, data["head"]):
        raise CommitCheckError("재구성 결과의 최종 tree 가 원래 HEAD 와 다르다")
    return made


def _git_version_ok(git: Git) -> bool:
    m = re.search(r"(\d+)\.(\d+)", _text(git.run("version")))
    return bool(m) and (int(m.group(1)), int(m.group(2))) >= MIN_GIT


def _in_progress(git: Git) -> list[str]:
    found = []
    for name in IN_PROGRESS:
        p = Path(_text(git.run("rev-parse", "--git-path", name)).strip())
        if not p.is_absolute():
            p = git.cwd / p
        if p.exists():
            found.append(name)
    return found


def _stale_backups(git: Git, branch: str) -> list[tuple[str, str]]:
    """이 브랜치 직속 백업(`<ns>/<branch>/<stamp>`)만 — `<branch>/x/...` 같은 다른 브랜치 백업은 건드리지 않는다."""
    prefix = f"{BACKUP_NS}/{branch}/"
    own = sorted((r, o) for r, o in _refs(git, prefix) if STAMP.match(r[len(prefix):]))
    excess = len(own) + 1 - KEEP_BACKUPS
    return own[:excess] if excess > 0 else []


def apply(git: Git, plan: dict) -> dict:
    if not _git_version_ok(git):
        raise CommitCheckError(f"git {MIN_GIT[0]}.{MIN_GIT[1]} 이상이 필요하다(merge-tree --merge-base)")
    busy = _in_progress(git)
    if busy:
        raise CommitCheckError(f"진행 중인 git 작업이 있다: {', '.join(busy)}")
    rng = resolve_range(git)
    if rng["on_default"]:
        raise CommitCheckError(f"기본 브랜치({rng['branch']})는 재구성하지 않는다 — 작업 브랜치에서 실행")
    data = collect(git, rng)
    if data["signed"]:
        raise CommitCheckError("범위에 서명된 커밋이 있다 — 재구성하면 서명을 잃으므로 지원하지 않는다")
    entries = validate_plan(plan, data)
    head, branch = data["head"], data["branch"]
    if not data["commits"]:
        return {"changed": False, "new_head": head}
    made = rebuild(git, data, entries)
    new = made[-1]["sha"]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = f"{BACKUP_NS}/{branch}/{stamp}"
    tx = ["start"]
    zero = "0" * len(head)
    tx += [f"verify {ref} {oid or zero}" for ref, oid in rng["upstreams"]]
    tx += [f"delete {ref} {oid}" for ref, oid in _stale_backups(git, branch)]
    tx += [f"create {backup} {head}", f"update refs/heads/{branch} {new} {head}", "commit"]
    git.run("update-ref", "-m", "commit-check", "--stdin", input=("\n".join(tx) + "\n").encode("utf-8"))
    return {"changed": True, "old_head": head, "new_head": new, "commits": made, "backup_ref": backup,
            "rollback": ["git", "update-ref", f"refs/heads/{branch}", head, new]}


def show(git: Git, sha: str) -> str:
    if sha.startswith("-"):
        raise CommitCheckError("show 인자는 커밋이어야 한다")
    oid = _text(git.run("rev-parse", "--verify", "--end-of-options", f"{sha}^{{commit}}")).strip()
    return _text(git.run("show", "--stat", "--patch", "--format=fuller", oid))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="commit_units.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collect")
    p_show = sub.add_parser("show")
    p_show.add_argument("sha")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("plan", help="계획 JSON 파일 경로, '-' 면 stdin")
    args = ap.parse_args(argv)
    git = Git(Path.cwd())
    try:
        if args.cmd == "collect":
            print(json.dumps(collect(git), ensure_ascii=False, indent=1))
        elif args.cmd == "show":
            sys.stdout.write(show(git, args.sha))
        else:
            raw = sys.stdin.read() if args.plan == "-" else Path(args.plan).read_text(encoding="utf-8")
            print(json.dumps(apply(git, json.loads(raw)), ensure_ascii=False, indent=1))
    except (CommitCheckError, json.JSONDecodeError, OSError) as exc:
        print(f"commit-check: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
