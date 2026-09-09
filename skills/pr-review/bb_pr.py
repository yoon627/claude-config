#!/usr/bin/env python3
"""Bitbucket Cloud PR 리뷰 보조 CLI — fetch(메타·diff) → post(초안 검증·인라인 댓글 게시) → undo."""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeGuard

API_HOST = "api.bitbucket.org"
API_BASE = f"https://{API_HOST}/2.0"
SCHEMA_VERSION = 1
PR_JSON = "pr.json"
PR_DIFF = "pr.diff"
DRAFT_JSON = "review-draft.json"
DEFAULT_LOG_DIR = Path.home() / ".claude" / "logs"
MAX_ERROR_BODY = 300
REVIEW_ACTIONS = ("approve", "request-changes")

PR_URL_RE = re.compile(
    r"^https://bitbucket\.org/(?P<workspace>[^/]+)/(?P<repo>[^/]+)/pull-requests/(?P<id>\d+)(?:[/?#].*)?$"
)
HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)
GIT_ESCAPES = {"n": b"\n", "t": b"\t", "r": b"\r", "a": b"\a", "b": b"\b", "f": b"\f", "v": b"\v"}


class BitbucketError(RuntimeError):
    """Bitbucket 작업 실패 — 메시지에 자격증명을 담지 않는다."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class ConfigError(BitbucketError):
    """로컬 설정 누락·오류."""


@dataclass(frozen=True)
class PrRef:
    workspace: str
    repo: str
    pr_id: int

    @property
    def path(self) -> str:
        return f"/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}"

    @property
    def slug(self) -> str:
        return f"{self.workspace}-{self.repo}-{self.pr_id}"


@dataclass(frozen=True)
class BitbucketConfig:
    email: str = field(repr=False)
    token: str = field(repr=False)
    timeout: float = 15.0


@dataclass(frozen=True)
class PlannedComment:
    index: int
    path: str
    line: int
    body: str
    severity: str = ""


@dataclass
class PublishResult:
    posted: list[tuple[int, int]] = field(default_factory=list)
    failed_index: int | None = None
    error: str | None = None


@dataclass
class UndoResult:
    deleted: list[int] = field(default_factory=list)
    review_state_cleared: str | None = None
    error: str | None = None


def _is_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


# --- URL / 설정 ---------------------------------------------------------------


def parse_pr_url(url: str) -> PrRef:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise BitbucketError(
            "PR URL 형식이 아닙니다 — https://bitbucket.org/<workspace>/<repo>/pull-requests/<id> 만 지원"
        )
    return PrRef(match["workspace"], match["repo"], int(match["id"]))


def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _find_upwards(name: str, start: Path) -> Path | None:
    for directory in [start, *start.parents]:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def _read_env(path: Path) -> dict[str, str]:
    try:
        return parse_env(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"{path.name} 읽기 실패: {exc}") from None


def load_settings(
    start_dir: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
    global_dir: Path | None = None,
) -> dict[str, str]:
    """env → project .env → ~/.jira-kit/.env 순. 이메일만 JIRA_EMAIL 폴백, 토큰은 폴백 없음."""
    environ = dict(os.environ) if environ is None else dict(environ)
    start = (start_dir or Path.cwd()).resolve()
    home = global_dir if global_dir is not None else Path.home() / ".jira-kit"

    project_env_path = _find_upwards(".env", start)
    project_env = _read_env(project_env_path) if project_env_path else {}
    global_env = _read_env(home / ".env") if (home / ".env").is_file() else {}
    sources = (environ, project_env, global_env)

    values: dict[str, str] = {}
    for key in ("BITBUCKET_EMAIL", "BITBUCKET_API_TOKEN"):
        for source in sources:
            if source.get(key):
                values[key] = source[key]
                break
    if "BITBUCKET_EMAIL" not in values:
        for source in sources:
            if source.get("JIRA_EMAIL"):
                values["BITBUCKET_EMAIL"] = source["JIRA_EMAIL"]
                break
    return values


def make_config(settings: dict[str, str], *, timeout: float = 15.0) -> BitbucketConfig:
    missing = [key for key in ("BITBUCKET_EMAIL", "BITBUCKET_API_TOKEN") if not settings.get(key)]
    if missing:
        raise ConfigError(
            f"설정 누락: {', '.join(missing)} — ~/.jira-kit/.env 에 추가하세요 "
            "(Atlassian API 토큰, scope: read:repository:bitbucket read:pullrequest:bitbucket "
            "write:pullrequest:bitbucket)"
        )
    return BitbucketConfig(settings["BITBUCKET_EMAIL"], settings["BITBUCKET_API_TOKEN"], timeout)


# --- HTTP ---------------------------------------------------------------------


def _check_api_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").casefold()
    try:
        port_ok = parsed.port in (None, 443)
    except ValueError:
        port_ok = False
    has_userinfo = parsed.username is not None or parsed.password is not None
    if parsed.scheme != "https" or host != API_HOST or not port_ok or has_userinfo:
        raise BitbucketError(f"허용되지 않은 호스트로의 요청을 중단했습니다: {host[:100] or '(없음)'}")
    return url


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """리다이렉트 대상이 API 호스트가 아니면 따라가지 않는다 — 기본 handler 는 Authorization 을 그대로 복사한다."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        _check_api_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _build_opener(*handlers: Any) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_SafeRedirectHandler, *handlers)


_opener: urllib.request.OpenerDirector | None = None


def _default_opener() -> urllib.request.OpenerDirector:
    global _opener
    if _opener is None:
        _opener = _build_opener()
    return _opener


def _auth_value(config: BitbucketConfig) -> str:
    return base64.b64encode(f"{config.email}:{config.token}".encode()).decode("ascii")


def _redact(text: str, config: BitbucketConfig) -> str:
    redacted = text
    for secret in (config.token, config.email, _auth_value(config)):
        if secret:
            redacted = redacted.replace(secret, "[redacted]")
    return redacted[:MAX_ERROR_BODY]


def _request(
    config: BitbucketConfig,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    what: str,
    accept: str = "application/json",
    expected: tuple[int, ...] = (200, 201, 204),
    opener: urllib.request.OpenerDirector | None = None,
) -> tuple[int, bytes]:
    url = _check_api_url(path if path.startswith("https://") else f"{API_BASE}{path}")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Basic {_auth_value(config)}")
    request.add_header("Accept", accept)
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with (opener or _default_opener()).open(request, timeout=config.timeout) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")
        except (OSError, http.client.HTTPException):
            detail = "(본문 읽기 실패)"
        raise BitbucketError(f"{what} 실패 ({exc.code}): {_redact(detail, config)}", exc.code) from None
    except urllib.error.URLError as exc:
        raise BitbucketError(f"Bitbucket 연결 실패 ({what}): {_redact(str(exc.reason), config)}") from None
    except (OSError, http.client.HTTPException) as exc:
        raise BitbucketError(f"Bitbucket 요청 실패 ({what}): {_redact(str(exc), config)}") from None

    if status not in expected:
        raise BitbucketError(f"{what} 실패: 예상 {expected}, 받음 {status}", status)
    return status, raw


def _request_json(
    config: BitbucketConfig,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    what: str,
    expected: tuple[int, ...] = (200, 201),
) -> dict[str, Any]:
    _, raw = _request(config, method, path, body, what=what, expected=expected)
    if not raw:
        return {}
    try:
        result = json.loads(raw.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        raise BitbucketError(f"{what} 응답 파싱 실패: 비-JSON 응답") from None
    if not isinstance(result, dict):
        raise BitbucketError(f"{what} 응답 파싱 실패: object 가 아님")
    return result


def _get_paged(config: BitbucketConfig, path: str, *, what: str = "목록 조회") -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    url: str | None = f"{API_BASE}{path}?pagelen=100"
    while url:
        page = _request_json(config, "GET", _check_api_url(url), None, what=what)
        values.extend(item for item in page.get("values", []) if isinstance(item, dict))
        url = page.get("next") or None
    return values


# --- 작업 디렉토리 -------------------------------------------------------------


def default_work_dir(ref: PrRef) -> Path:
    return Path(tempfile.gettempdir()) / "bb-pr-review" / ref.slug


def inside_git_work_tree(path: Path) -> bool:
    resolved = path.resolve()
    return any((directory / ".git").exists() for directory in [resolved, *resolved.parents])


def check_work_dir(path: Path) -> Path:
    if inside_git_work_tree(path):
        raise BitbucketError(
            f"작업 디렉토리가 git work tree 안입니다: {path} — PR 소스가 커밋될 수 있어 거부. "
            "--dir 을 생략하거나 repo 밖 경로를 주세요"
        )
    if path.is_symlink():
        raise BitbucketError(f"작업 디렉토리가 심볼릭 링크입니다: {path} — 거부")
    return path


def ensure_work_dir(path: Path) -> Path:
    check_work_dir(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.mkdir(exist_ok=True, mode=0o700)
    if os.name != "nt":
        for directory in (path.parent, path):
            if directory.stat().st_uid != os.getuid():
                raise BitbucketError(f"작업 디렉토리 소유자가 다릅니다: {directory} — 거부")
        os.chmod(path, 0o700)
    return path


def _write_private(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(tmp, flags, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    os.replace(tmp, path)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    _write_private(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _read_json(path: Path, what: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BitbucketError(f"{what} 없음: {path} — 먼저 fetch 를 실행하세요") from None
    except (OSError, json.JSONDecodeError) as exc:
        raise BitbucketError(f"{what} 읽기 실패 ({path.name}): {exc}") from None
    if not isinstance(data, dict):
        raise BitbucketError(f"{what} 형식 오류: object 가 아님 ({path.name})")
    return data


# --- fetch ---------------------------------------------------------------------


def _endpoint(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw or {}
    return {
        "branch": (raw.get("branch") or {}).get("name"),
        "commit": (raw.get("commit") or {}).get("hash"),
        "repo": (raw.get("repository") or {}).get("full_name"),
    }


def fetch_pr(config: BitbucketConfig, ref: PrRef) -> dict[str, Any]:
    raw = _request_json(config, "GET", ref.path, None, what="PR 조회")
    return {
        "workspace": ref.workspace,
        "repo": ref.repo,
        "pr_id": ref.pr_id,
        "url": ((raw.get("links") or {}).get("html") or {}).get("href"),
        "title": raw.get("title"),
        "description": raw.get("description"),
        "author": (raw.get("author") or {}).get("display_name"),
        "state": raw.get("state"),
        "source": _endpoint(raw.get("source")),
        "destination": _endpoint(raw.get("destination")),
    }


def fetch_diff(config: BitbucketConfig, ref: PrRef) -> bytes:
    _, raw = _request(config, "GET", f"{ref.path}/diff", None, what="diff 조회", accept="text/plain")
    return raw


def fetch_inline_comments(config: BitbucketConfig, ref: PrRef) -> list[dict[str, Any]]:
    comments = []
    for item in _get_paged(config, f"{ref.path}/comments", what="댓글 조회"):
        inline = item.get("inline")
        if not inline or item.get("deleted"):
            continue
        comments.append(
            {
                "id": item.get("id"),
                "path": inline.get("path"),
                "to": inline.get("to"),
                "from": inline.get("from"),
                "author": (item.get("user") or {}).get("display_name"),
                "content": ((item.get("content") or {}).get("raw") or "")[:200],
            }
        )
    return comments


def _draft_skeleton(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "workspace": meta["workspace"],
        "repo": meta["repo"],
        "pr_id": meta["pr_id"],
        "source_sha": meta["source"]["commit"],
        "comments": [],
        "notes": [],
    }


def _check_existing_draft(draft_path: Path, ref: PrRef) -> dict[str, Any] | None:
    """다른 PR 의 초안이 남은 디렉토리에는 아무것도 쓰지 않는다 — 덮어쓰면 그 초안으로 undo 할 수 없게 된다."""
    if not draft_path.exists():
        return None
    existing = _read_json(draft_path, "초안")
    if _draft_identity_problems(existing, {"workspace": ref.workspace, "repo": ref.repo, "pr_id": ref.pr_id}):
        raise BitbucketError(
            f"작업 디렉토리에 다른 PR 의 초안이 있습니다: {draft_path} — 다른 --dir 을 쓰거나, "
            "그 초안의 댓글을 undo 한 뒤 지우세요"
        )
    return existing


def fetch_all(config: BitbucketConfig, ref: PrRef, work_dir: Path) -> str:
    ensure_work_dir(work_dir)
    existing_draft = _check_existing_draft(work_dir / DRAFT_JSON, ref)
    meta = fetch_pr(config, ref)
    diff = fetch_diff(config, ref)
    meta["existing_inline_comments"] = fetch_inline_comments(config, ref)
    meta["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    _write_json(work_dir / PR_JSON, meta)
    _write_private(work_dir / PR_DIFF, diff)
    draft_warning = None
    if existing_draft is None:
        _write_json(work_dir / DRAFT_JSON, _draft_skeleton(meta))
    elif existing_draft.get("source_sha") != meta["source"]["commit"]:
        draft_warning = "주의: 기존 초안이 이전 source 커밋 기준 — source_sha 를 갱신하고 라인을 다시 확인해야 검증을 통과한다"

    files = parse_diff_lines(diff.decode("utf-8", "replace"))
    anchorable = sum(1 for lines in files.values() if lines)
    source, destination = meta["source"], meta["destination"]
    lines = [
        f"PR #{ref.pr_id}: {meta.get('title')}  (작성자 {meta.get('author')}, 상태 {meta.get('state')})",
        f"{source.get('repo')}:{source.get('branch')}@{(source.get('commit') or '')[:12]} → "
        f"{destination.get('repo')}:{destination.get('branch')}",
        f"diff {len(diff):,} bytes · 파일 {len(files)}개(앵커 가능 {anchorable}) · 기존 인라인 댓글 {len(meta['existing_inline_comments'])}건",
        f"작업 디렉토리: {work_dir}",
        f"  {PR_JSON} / {PR_DIFF} / {DRAFT_JSON}",
    ]
    if source.get("repo") != destination.get("repo"):
        lines.append("주의: fork PR — 로컬 clone 의 origin 에는 source 브랜치가 없다. diff 만으로 리뷰")
    if draft_warning:
        lines.append(draft_warning)
    return "\n".join(lines)


# --- diff 파서 -----------------------------------------------------------------


def _unquote_git_path(token: str) -> str:
    if not (len(token) >= 2 and token.startswith('"') and token.endswith('"')):
        return token
    inner = token[1:-1]
    out = bytearray()
    i = 0
    while i < len(inner):
        char = inner[i]
        if char != "\\":
            out.extend(char.encode("utf-8"))
            i += 1
            continue
        i += 1
        if i >= len(inner):
            break
        octal = inner[i : i + 3]
        if len(octal) == 3 and all(digit in "01234567" for digit in octal):
            out.append(int(octal, 8))
            i += 3
            continue
        out.extend(GIT_ESCAPES.get(inner[i], inner[i].encode("utf-8")))
        i += 1
    return out.decode("utf-8", "replace")


def _strip_side(path: str) -> str:
    return path[2:] if path.startswith(("a/", "b/")) else path


def _diff_git_target(rest: str) -> str | None:
    """`diff --git a/<x> b/<y>` 의 b 쪽 경로. git 은 공백을 인용하지 않으므로 a==b 인 분할점을 먼저 찾는다."""
    if rest.startswith('"'):
        tokens = re.findall(r'"(?:[^"\\]|\\.)*"', rest)
        return _strip_side(_unquote_git_path(tokens[-1])) if tokens else None
    if rest.startswith("a/"):
        body = rest[2:]
        cut = body.find(" b/")
        while cut != -1:
            if body[:cut] == body[cut + 3 :]:
                return body[cut + 3 :]
            cut = body.find(" b/", cut + 1)
        cut = body.rfind(" b/")
        if cut != -1:
            return body[cut + 3 :]
    tokens = rest.split(" ")
    return _strip_side(tokens[-1]) if len(tokens) >= 2 else None


def _header_path(line: str) -> str | None:
    """`+++ b/<path>` 의 경로. git 은 공백 경로 뒤에 탭을 붙이고, 제어문자·비ASCII 경로는 인용한다."""
    target = line[4:]
    quoted = re.match(r'"(?:[^"\\]|\\.)*"', target)
    if quoted:
        return _strip_side(_unquote_git_path(quoted.group(0)))
    target = target.split("\t", 1)[0]
    return None if target == "/dev/null" else _strip_side(target)


def parse_diff_lines(diff_text: str) -> dict[str, set[int]]:
    """새 파일 기준 앵커 가능 라인(추가+컨텍스트). 삭제·바이너리·rename-only 는 빈 집합.

    hunk 는 header 의 count 로 경계를 정한다 — 본문 줄이 `+++ `/`--- `/`diff` 로 시작해도 header 로 읽지 않는다.
    """
    result: dict[str, set[int]] = {}
    current: str | None = None
    cursor = 0
    remaining_old = remaining_new = 0
    for raw in diff_text.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        if (remaining_old > 0 or remaining_new > 0) and not line.startswith(("+", "-", " ", "\\")) and line != "":
            remaining_old = remaining_new = 0
        if remaining_old > 0 or remaining_new > 0:
            if line.startswith("\\"):
                continue
            if line.startswith("+"):
                remaining_new -= 1
                if current is not None:
                    result[current].add(cursor)
                cursor += 1
            elif line.startswith("-"):
                remaining_old -= 1
            else:
                remaining_old -= 1
                remaining_new -= 1
                if current is not None:
                    result[current].add(cursor)
                cursor += 1
            continue
        if line.startswith("diff --git "):
            current = _diff_git_target(line[len("diff --git ") :])
            if current is not None:
                result.setdefault(current, set())
        elif line.startswith("+++ "):
            current = _header_path(line)
            if current is not None:
                result.setdefault(current, set())
        elif line.startswith("@@"):
            match = HUNK_RE.match(line)
            if match:
                cursor = int(match["new_start"])
                remaining_old = int(match["old_count"]) if match["old_count"] is not None else 1
                remaining_new = int(match["new_count"]) if match["new_count"] is not None else 1
    return result


# --- 초안 검증 / 게시 -----------------------------------------------------------


def _draft_identity_problems(draft: dict[str, Any], meta: dict[str, Any]) -> list[str]:
    problems = []
    version = draft.get("schema_version")
    if not _is_int(version) or version != SCHEMA_VERSION:
        problems.append(f"초안 schema_version {version!r} ≠ {SCHEMA_VERSION}")
    identity = (draft.get("workspace"), draft.get("repo"), draft.get("pr_id"))
    if identity != (meta.get("workspace"), meta.get("repo"), meta.get("pr_id")):
        problems.append(f"초안의 PR 식별자 {identity} 가 pr.json 과 다릅니다")
    return problems


def _draft_binding_problems(draft: dict[str, Any], meta: dict[str, Any]) -> list[str]:
    problems = _draft_identity_problems(draft, meta)
    if draft.get("source_sha") != (meta.get("source") or {}).get("commit"):
        problems.append("초안 source_sha 가 pr.json 과 다릅니다 — 다시 fetch 한 뒤 초안을 갱신하세요")
    return problems


def _summarize_lines(lines: set[int]) -> str:
    ordered = sorted(lines)
    ranges: list[str] = []
    start = prev = ordered[0]
    for value in ordered[1:]:
        if value == prev + 1:
            prev = value
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = value
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(ranges)


def plan_comments(
    draft: dict[str, Any], meta: dict[str, Any], line_map: dict[str, set[int]]
) -> tuple[list[PlannedComment], list[str]]:
    problems = _draft_binding_problems(draft, meta)
    if problems:
        return [], problems

    planned: list[PlannedComment] = []
    items = draft.get("comments")
    if not isinstance(items, list):
        return [], ["초안 comments 가 목록이 아닙니다"]
    for position, item in enumerate(items, start=1):
        tag = f"#{position}"
        if not isinstance(item, dict):
            problems.append(f"{tag}: 항목이 object 가 아닙니다")
            continue
        posted_id = item.get("posted_id")
        if posted_id is not None:
            if _is_int(posted_id) and posted_id > 0:
                continue
            problems.append(f"{tag}: posted_id 가 양의 정수가 아닙니다 ({posted_id!r})")
            continue
        if item.get("state") == "unknown":
            problems.append(
                f"{tag}: 이전 실행의 결과 미확인(unknown) — PR 의 기존 댓글을 확인해 posted_id 를 적거나 항목을 삭제하세요"
            )
            continue
        path, line, body = item.get("path"), item.get("line"), item.get("body")
        if not isinstance(path, str) or not path:
            problems.append(f"{tag}: path 가 없습니다 (인라인 댓글만 지원)")
            continue
        if not _is_int(line) or line < 1:
            problems.append(f"{tag}: line 이 없거나 양의 정수가 아닙니다 ({path})")
            continue
        if not isinstance(body, str) or not body.strip():
            problems.append(f"{tag}: body 가 비었습니다 ({path}:{line})")
            continue
        if path not in line_map:
            problems.append(f"{tag}: diff 에 없는 파일 {path}")
            continue
        anchors = line_map[path]
        if not anchors:
            problems.append(f"{tag}: {path} 는 앵커 가능한 라인이 없습니다(삭제·바이너리·rename-only)")
            continue
        if line not in anchors:
            problems.append(
                f"{tag}: {path}:{line} 은 diff 의 새 파일 기준 라인이 아닙니다 (가능: {_summarize_lines(anchors)})"
            )
            continue
        planned.append(PlannedComment(position, path, line, body.strip(), str(item.get("severity") or "")))
    return planned, problems


def publish_gate_problems(live: dict[str, Any], draft: dict[str, Any]) -> list[str]:
    """게시 직전 재조회한 PR 과 초안의 대조 — 하나라도 걸리면 한 건도 게시하지 않는다."""
    problems = []
    if live.get("state") != "OPEN":
        problems.append(f"PR 상태가 {live.get('state')} 라 게시를 중단합니다 — 다시 fetch 해 확인하세요")
    if (live.get("source") or {}).get("commit") != draft.get("source_sha"):
        problems.append("PR source 커밋이 fetch 이후 바뀌었습니다 — 다시 fetch 하고 초안을 재검토하세요")
    return problems


def render_plan(planned: list[PlannedComment], problems: list[str], *, dry_run: bool) -> str:
    lines = [f"게시 예정 인라인 댓글 {len(planned)}건" + (" (미리보기; 외부 변경 없음)" if dry_run else "")]
    for item in planned:
        first = item.body.splitlines()[0]
        severity = f" [{item.severity}]" if item.severity else ""
        lines.append(f"  #{item.index} {item.path}:{item.line}{severity} {first}")
    if problems:
        lines.append(f"게시 불가 {len(problems)}건 — 하나라도 있으면 게시하지 않는다. 초안을 고친 뒤 다시 실행:")
        lines.extend(f"  {problem}" for problem in problems)
    return "\n".join(lines)


def _append_log(log_path: Path, record: dict[str, Any]) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"경고: 게시 로그 기록 실패 ({log_path}): {exc}", file=sys.stderr)


def default_log_path() -> Path:
    return DEFAULT_LOG_DIR / f"pr-review-{datetime.now().date().isoformat()}.jsonl"


def publish(
    config: BitbucketConfig,
    ref: PrRef,
    planned: list[PlannedComment],
    draft: dict[str, Any],
    draft_path: Path,
    *,
    log_path: Path,
) -> PublishResult:
    """`planned` 는 이 `draft` 인스턴스를 `plan_comments` 로 검증해 얻은 것이어야 한다(위치로 결합)."""
    entries = draft["comments"]
    result = PublishResult()
    for item in planned:
        entry = entries[item.index - 1]
        body = {"content": {"raw": item.body}, "inline": {"path": item.path, "to": item.line}}
        try:
            response = _request_json(config, "POST", f"{ref.path}/comments", body, what=f"댓글 #{item.index} 게시")
        except BitbucketError as exc:
            if not (exc.status is not None and 400 <= exc.status < 500):
                entry["state"] = "unknown"
                _write_json(draft_path, draft)
            result.failed_index, result.error = item.index, str(exc)
            return result
        comment_id = response.get("id")
        if not _is_int(comment_id) or comment_id <= 0:
            entry["state"] = "unknown"
            _write_json(draft_path, draft)
            result.failed_index, result.error = item.index, f"#{item.index} 게시 응답에 id 가 없습니다 — PR 에서 댓글 생성 여부를 확인하세요"
            return result
        entry["posted_id"] = comment_id
        entry.pop("state", None)
        _write_json(draft_path, draft)
        _append_log(
            log_path,
            {
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "pr": f"{ref.workspace}/{ref.repo}#{ref.pr_id}",
                "comment_id": comment_id,
                "path": item.path,
                "line": item.line,
            },
        )
        result.posted.append((item.index, comment_id))
        inline = response.get("inline") or {}
        saved_to = inline.get("to")
        if inline.get("path") != item.path or (saved_to is not None and saved_to != item.line):
            result.failed_index = item.index
            result.error = (
                f"#{item.index} 은 이미 게시됐지만 응답 anchor 가 다릅니다: 요청 {item.path}:{item.line}, "
                f"저장 {inline.get('path')}:{saved_to} (id {comment_id}) — PR 에서 확인하고 필요하면 undo"
            )
            return result
    return result


def set_review_state(config: BitbucketConfig, ref: PrRef, action: str) -> None:
    if action not in REVIEW_ACTIONS:
        raise BitbucketError(f"알 수 없는 리뷰 상태: {action}")
    _request(config, "POST", f"{ref.path}/{action}", None, what=f"PR {action}", expected=(200, 201, 204))


def undo(config: BitbucketConfig, ref: PrRef, draft: dict[str, Any], draft_path: Path) -> UndoResult:
    result = UndoResult()
    identity = _draft_identity_problems(draft, {"workspace": ref.workspace, "repo": ref.repo, "pr_id": ref.pr_id})
    if identity:
        result.error = identity[0] + " — 이 초안으로는 되돌릴 수 없습니다"
        return result
    comments = draft.get("comments")
    if not isinstance(comments, list):
        result.error = "초안 comments 가 목록이 아닙니다"
        return result
    for position, entry in enumerate(comments, start=1):
        if not isinstance(entry, dict) or entry.get("posted_id") is None:
            continue
        comment_id = entry["posted_id"]
        if not _is_int(comment_id) or comment_id <= 0:
            result.error = f"#{position}: posted_id 가 양의 정수가 아닙니다 ({comment_id!r}) — 초안을 확인하세요"
            return result
        try:
            _request(config, "DELETE", f"{ref.path}/comments/{int(comment_id)}", None, what=f"댓글 #{position} 삭제", expected=(204, 200))
        except BitbucketError as exc:
            result.error = str(exc)
            return result
        entry.pop("posted_id", None)
        _write_json(draft_path, draft)
        result.deleted.append(comment_id)
    action = draft.get("review_state")
    if action in REVIEW_ACTIONS:
        try:
            _request(config, "DELETE", f"{ref.path}/{action}", None, what=f"PR {action} 취소", expected=(204, 200))
        except BitbucketError as exc:
            result.error = str(exc)
            return result
        draft.pop("review_state", None)
        _write_json(draft_path, draft)
        result.review_state_cleared = action
    return result


# --- CLI -------------------------------------------------------------------------


def _load_work_dir(work_dir: Path) -> tuple[dict[str, Any], str, dict[str, Any]]:
    check_work_dir(work_dir)
    meta = _read_json(work_dir / PR_JSON, "PR 메타")
    try:
        diff = (work_dir / PR_DIFF).read_bytes().decode("utf-8", "replace")
    except OSError as exc:
        raise BitbucketError(f"diff 읽기 실패: {exc} — 먼저 fetch 를 실행하세요") from None
    draft = _read_json(work_dir / DRAFT_JSON, "초안")
    return meta, diff, draft


def _ref_from_meta(meta: dict[str, Any]) -> PrRef:
    try:
        return PrRef(str(meta["workspace"]), str(meta["repo"]), int(meta["pr_id"]))
    except (KeyError, TypeError, ValueError):
        raise BitbucketError("pr.json 에 PR 식별자가 없습니다 — 다시 fetch 하세요") from None


def cmd_fetch(args: argparse.Namespace) -> int:
    ref = parse_pr_url(args.url)
    work_dir = check_work_dir(Path(args.dir) if args.dir else default_work_dir(ref))
    config = make_config(load_settings(), timeout=args.timeout)
    print(fetch_all(config, ref, work_dir))
    print(f"다음: {DRAFT_JSON} 의 comments 를 채운 뒤 `post --dir \"{work_dir}\"` 로 미리보기")
    return 0


def cmd_post(args: argparse.Namespace) -> int:
    action = "approve" if args.approve else "request-changes" if args.request_changes else None
    if action and not args.post:
        print(f"오류: --{action} 는 --post 와 함께만 쓸 수 있습니다", file=sys.stderr)
        return 2
    work_dir = Path(args.dir)
    meta, diff, draft = _load_work_dir(work_dir)
    planned, problems = plan_comments(draft, meta, parse_diff_lines(diff))
    print(render_plan(planned, problems, dry_run=not args.post))
    if problems:
        return 2
    if not args.post:
        return 0

    ref = _ref_from_meta(meta)
    config = make_config(load_settings(), timeout=args.timeout)
    gate = publish_gate_problems(fetch_pr(config, ref), draft)
    if gate:
        for problem in gate:
            print(f"오류: {problem}", file=sys.stderr)
        return 2
    if not planned and not action:
        print("게시할 항목이 없습니다")
        return 0

    result = publish(config, ref, planned, draft, work_dir / DRAFT_JSON, log_path=default_log_path())
    for index, comment_id in result.posted:
        print(f"게시됨 #{index} → comment {comment_id}")
    if result.failed_index is not None:
        print(f"오류: {result.error}", file=sys.stderr)
        print(f"게시 {len(result.posted)}건 완료, #{result.failed_index} 에서 중단 — 초안의 posted_id/state 확인 후 재실행", file=sys.stderr)
        return 2
    if action:
        draft["review_state"] = action
        _write_json(work_dir / DRAFT_JSON, draft)
        try:
            set_review_state(config, ref, action)
        except BitbucketError as exc:
            if exc.status is not None and 400 <= exc.status < 500:
                draft.pop("review_state", None)
                _write_json(work_dir / DRAFT_JSON, draft)
            raise
        print(f"PR 상태 변경: {action}")
    return 0


def cmd_undo(args: argparse.Namespace) -> int:
    work_dir = Path(args.dir)
    meta, _, draft = _load_work_dir(work_dir)
    identity_problems = _draft_identity_problems(draft, meta)
    if identity_problems:
        for problem in identity_problems:
            print(f"오류: {problem} — 이 초안으로는 되돌릴 수 없습니다", file=sys.stderr)
        return 2
    raw_comments = draft.get("comments")
    comments = raw_comments if isinstance(raw_comments, list) else []
    posted = [
        (position, entry.get("posted_id"))
        for position, entry in enumerate(comments, start=1)
        if isinstance(entry, dict) and entry.get("posted_id") is not None
    ]
    action = draft.get("review_state")
    print(f"삭제 대상 댓글 {len(posted)}건" + (" (미리보기; 외부 변경 없음)" if not args.post else ""))
    for position, comment_id in posted:
        print(f"  #{position} → comment {comment_id}")
    if action:
        print(f"PR 상태 취소 대상: {action}")
    if not args.post:
        return 0
    if not posted and not action:
        print("되돌릴 것이 없습니다")
        return 0
    config = make_config(load_settings(), timeout=args.timeout)
    result = undo(config, _ref_from_meta(meta), draft, work_dir / DRAFT_JSON)
    for comment_id in result.deleted:
        print(f"삭제됨 comment {comment_id}")
    if result.review_state_cleared:
        print(f"PR 상태 취소: {result.review_state_cleared}")
    if result.error:
        print(f"오류: {result.error}", file=sys.stderr)
        return 2
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bitbucket Cloud PR 리뷰 — fetch / post / undo")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout(초)")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="PR 메타·diff 를 작업 디렉토리에 저장하고 초안 골격을 만든다")
    fetch.add_argument("url", help="https://bitbucket.org/<workspace>/<repo>/pull-requests/<id>")
    fetch.add_argument("--dir", help="작업 디렉토리(기본: OS 임시 디렉토리, git work tree 안은 거부)")
    fetch.set_defaults(func=cmd_fetch)

    post = sub.add_parser("post", help="초안을 검증하고(기본 미리보기) --post 시 인라인 댓글을 게시한다")
    post.add_argument("--dir", required=True, help="fetch 가 만든 작업 디렉토리")
    post.add_argument("--post", action="store_true", help="실제로 게시 (외부 변경)")
    state = post.add_mutually_exclusive_group()
    state.add_argument("--approve", action="store_true", help="댓글 게시 후 PR approve (--post 필요)")
    state.add_argument("--request-changes", action="store_true", help="댓글 게시 후 request changes (--post 필요)")
    post.set_defaults(func=cmd_post)

    undo_parser = sub.add_parser("undo", help="이 초안이 게시한 댓글·PR 상태를 되돌린다(기본 미리보기)")
    undo_parser.add_argument("--dir", required=True, help="fetch 가 만든 작업 디렉토리")
    undo_parser.add_argument("--post", action="store_true", help="실제로 삭제 (외부 변경)")
    undo_parser.set_defaults(func=cmd_undo)
    return parser.parse_args(argv)


def _configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _configure_output()
    args = parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, BitbucketError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
