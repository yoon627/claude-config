#!/usr/bin/env python3
"""Preview or upsert a work summary in a Jira Cloud issue description."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, tzinfo
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import tomllib
except (
    ModuleNotFoundError
):  # pragma: no cover - Python 3.10 fallback is not supported by CI.
    tomllib = None  # type: ignore[assignment]


DEFAULT_TICKET_PATTERN = r"[A-Z][A-Z0-9]+-\d+"
MARKER_PREFIX = "[jira-task]"
DESCRIPTION_HEADING = "작업 내용"
MAX_SUMMARY_LENGTH = 12_000
SECRET_PATTERNS = (
    re.compile(r"(?i)JIRA_API_TOKEN\s*="),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,})\b"),
)


class JiraTaskError(RuntimeError):
    """Jira task note operation failed without exposing credentials."""


class ConfigError(JiraTaskError):
    """Local Jira configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    values: dict[str, str] = field(repr=False)

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.values.get(key) or default


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str = field(repr=False)
    token: str = field(repr=False)
    api_base: str = ""

    def rest_base(self) -> str:
        return (self.api_base or self.base_url).rstrip("/")


@dataclass(frozen=True)
class TaskContext:
    ticket: str
    worktree: str
    task_date: str
    session: str


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


def _flatten_toml(data: dict[str, Any]) -> dict[str, str]:
    jira = data.get("jira", {}) if isinstance(data.get("jira"), dict) else {}
    worklog = data.get("worklog", {}) if isinstance(data.get("worklog"), dict) else {}
    raw = {
        "JIRA_BASE_URL": jira.get("base_url"),
        "JIRA_EMAIL": jira.get("email"),
        "JIRA_CLOUD_ID": jira.get("cloud_id"),
        "JIRA_TIMEZONE": worklog.get("timezone"),
        "JIRA_TICKET_PATTERN": worklog.get("ticket_pattern"),
    }
    return {key: str(value) for key, value in raw.items() if value is not None}


def _read_toml(path: Path) -> dict[str, str]:
    if tomllib is None:  # pragma: no cover
        return {}
    try:
        return _flatten_toml(tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path.name} 파싱 실패: {exc}") from None
    except OSError as exc:
        raise ConfigError(f"{path.name} 읽기 실패: {exc}") from None


def load_settings(
    start_dir: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
    global_dir: Path | None = None,
) -> Settings:
    """Load non-secret settings and credentials using jira-worklog's locations."""
    environ = dict(os.environ) if environ is None else dict(environ)
    start = (start_dir or Path.cwd()).resolve()
    home = global_dir if global_dir is not None else Path.home() / ".jira-kit"

    global_env = _read_env(home / ".env") if (home / ".env").is_file() else {}
    project_env_path = _find_upwards(".env", start)
    project_env = _read_env(project_env_path) if project_env_path else {}

    toml_path = _find_upwards("jira-kit.toml", start)
    if toml_path is None and (home / "jira-kit.toml").is_file():
        toml_path = home / "jira-kit.toml"
    toml_values = _read_toml(toml_path) if toml_path else {}

    values: dict[str, str] = {}
    keys = (
        "JIRA_BASE_URL",
        "JIRA_EMAIL",
        "JIRA_CLOUD_ID",
        "JIRA_TIMEZONE",
        "JIRA_TICKET_PATTERN",
        "JIRA_TASK_SESSION",
    )
    for key in keys:
        for source in (environ, project_env, global_env, toml_values):
            if source.get(key):
                values[key] = source[key]
                break
    for source in (environ, project_env, global_env):
        if source.get("JIRA_API_TOKEN"):
            values["JIRA_API_TOKEN"] = source["JIRA_API_TOKEN"]
            break
    return Settings(values)


def _redact(text: str, config: JiraConfig) -> str:
    redacted = text
    for secret in (config.token, config.email):
        if secret:
            redacted = redacted.replace(secret, "[redacted]")
    return redacted[:500]


def _auth_header(config: JiraConfig) -> str:
    encoded = base64.b64encode(f"{config.email}:{config.token}".encode()).decode(
        "ascii"
    )
    return f"Basic {encoded}"


def _request(
    config: JiraConfig,
    method: str,
    path: str,
    body: dict[str, Any] | None,
    *,
    expected_status: int,
    what: str,
    timeout: float = 15.0,
    allow_empty_response: bool = False,
) -> dict[str, Any]:
    data = (
        json.dumps(body, ensure_ascii=False).encode("utf-8")
        if body is not None
        else None
    )
    request = urllib.request.Request(
        f"{config.rest_base()}{path}", data=data, method=method
    )
    request.add_header("Authorization", _auth_header(config))
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = _redact(exc.read().decode("utf-8", "replace"), config)
        raise JiraTaskError(f"{what} 실패 ({exc.code}): {detail}") from None
    except urllib.error.URLError as exc:
        raise JiraTaskError(f"Jira 연결 실패 ({what}): {exc.reason}") from None
    except OSError as exc:
        raise JiraTaskError(f"Jira 요청 실패 ({what}): {exc}") from None

    if status != expected_status:
        raise JiraTaskError(f"{what} 실패: 예상 {expected_status}, 받음 {status}")
    if not raw and allow_empty_response:
        return {}
    if not raw:
        raise JiraTaskError(f"{what} 실패: 빈 응답 (status {status})")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise JiraTaskError(f"{what} 응답 파싱 실패: 비-JSON 응답") from None
    if not isinstance(result, dict):
        raise JiraTaskError(f"{what} 응답 파싱 실패: object가 아님")
    return result


def fetch_cloud_id(site_url: str, *, timeout: float = 10.0) -> str | None:
    try:
        with urllib.request.urlopen(
            f"{site_url.rstrip('/')}/_edge/tenant_info", timeout=timeout
        ) as response:
            data = json.loads(response.read().decode("utf-8", "replace"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    cloud_id = data.get("cloudId") if isinstance(data, dict) else None
    return cloud_id if isinstance(cloud_id, str) and cloud_id else None


def make_jira_config(settings: Settings, *, timeout: float = 10.0) -> JiraConfig:
    base_url = settings.get("JIRA_BASE_URL")
    email = settings.get("JIRA_EMAIL")
    token = settings.get("JIRA_API_TOKEN")
    if not base_url or not email or not token:
        raise ConfigError("JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN 설정이 필요합니다")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ConfigError("JIRA_BASE_URL은 https URL이어야 합니다")
    cloud_id = settings.get("JIRA_CLOUD_ID") or fetch_cloud_id(
        base_url, timeout=timeout
    )
    api_base = (
        f"https://api.atlassian.com/ex/jira/{quote(cloud_id, safe='')}"
        if cloud_id
        else ""
    )
    return JiraConfig(base_url.rstrip("/"), email, token, api_base)


def adf_from_text(text: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": line}]}
            if line
            else {"type": "paragraph", "content": []}
            for line in text.split("\n")
        ],
    }


def _adf_node_text(node: Any) -> str:
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "text":
            return str(node.get("text", ""))
        if node_type == "hardBreak":
            return "\n"
        return "".join(_adf_node_text(child) for child in node.get("content", []))
    if isinstance(node, list):
        return "".join(_adf_node_text(child) for child in node)
    return ""


def adf_lines(body: Any) -> list[str]:
    if not isinstance(body, dict):
        return []
    blocks = body.get("content", [])
    if not isinstance(blocks, list):
        return []
    lines: list[str] = []
    for block in blocks:
        lines.extend(_adf_node_text(block).split("\n"))
    return lines


def _description_content(description: dict[str, Any] | None) -> list[dict[str, Any]]:
    if description is None:
        return []
    if "content" not in description:
        description["content"] = []
    content = description["content"]
    if not isinstance(content, list) or not all(
        isinstance(node, dict) for node in content
    ):
        raise JiraTaskError(
            "Jira description의 ADF content가 올바른 block list가 아닙니다"
        )
    return content


def _description_entry_lines(summary: str, marker: str) -> list[str]:
    summary_lines = summary.splitlines() or [""]
    first = summary_lines[0]
    prefix = f"{DESCRIPTION_HEADING}:"
    if first.startswith(prefix):
        first = first[len(prefix) :].lstrip()
    return [f"{DESCRIPTION_HEADING}: {first}", *summary_lines[1:], marker]


def _description_entry(summary: str, marker: str) -> dict[str, Any]:
    lines = _description_entry_lines(summary, marker)
    content: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        if line:
            content.append({"type": "text", "text": line})
        if index < len(lines) - 1:
            content.append({"type": "hardBreak"})
    return {"type": "paragraph", "content": content}


def _description_heading() -> dict[str, Any]:
    return {
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": DESCRIPTION_HEADING}],
    }


def _marker_block_index(content: list[dict[str, Any]], marker: str) -> int | None:
    for index, block in enumerate(content):
        lines = _adf_node_text(block).split("\n")
        if any(line.strip() == marker for line in lines):
            return index
    return None


def _has_description_heading(content: list[dict[str, Any]]) -> bool:
    return any(
        _adf_node_text(block).strip() == DESCRIPTION_HEADING for block in content
    )


def _description_matches(
    description: dict[str, Any] | None, summary: str, marker: str
) -> bool:
    content = _description_content(description)
    index = _marker_block_index(content, marker)
    if index is None:
        return False
    return _adf_node_text(content[index]) == "\n".join(
        _description_entry_lines(summary, marker)
    )


def upsert_description_body(
    description: dict[str, Any] | None, summary: str, marker: str
) -> tuple[dict[str, Any], str]:
    """기존 ADF 본문을 보존하고 marker 항목을 추가·갱신한다."""
    if description is None:
        result: dict[str, Any] = {"type": "doc", "version": 1, "content": []}
    else:
        result = json.loads(json.dumps(description, ensure_ascii=False))
        if result.get("type") != "doc":
            raise JiraTaskError("Jira description의 ADF type이 doc이 아닙니다")
        if not isinstance(result.get("version"), int):
            raise JiraTaskError("Jira description의 ADF version이 없습니다")

    content = _description_content(result)
    entry = _description_entry(summary, marker)
    index = _marker_block_index(content, marker)
    if index is not None:
        if _adf_node_text(content[index]) == _adf_node_text(entry):
            return result, "unchanged"
        content[index] = entry
        return result, "updated"

    if not _has_description_heading(content):
        content.append(_description_heading())
    content.append(entry)
    return result, "added"


def upsert_description(
    config: JiraConfig,
    issue_key: str,
    summary: str,
    marker: str,
    *,
    timeout: float = 15.0,
) -> tuple[str, dict[str, Any]]:
    current = get_issue_description(config, issue_key, timeout=timeout)
    planned, action = upsert_description_body(current, summary, marker)
    if action == "unchanged":
        return action, current or planned

    update_issue_description(config, issue_key, planned, timeout=timeout)
    saved = get_issue_description(config, issue_key, timeout=timeout)
    if not _description_matches(saved, summary, marker):
        raise JiraTaskError(
            f"task 본문 갱신 후 저장값 확인 불일치 {issue_key}: marker/요약을 찾지 못했습니다"
        )
    return action, saved or planned


def get_issue_description(
    config: JiraConfig, issue_key: str, *, timeout: float = 15.0
) -> dict[str, Any] | None:
    encoded_key = quote(issue_key, safe="")
    result = _request(
        config,
        "GET",
        f"/rest/api/3/issue/{encoded_key}?fields=description",
        None,
        expected_status=200,
        what=f"task 본문 조회 {issue_key}",
        timeout=timeout,
    )
    fields = result.get("fields")
    if not isinstance(fields, dict):
        raise JiraTaskError(f"task 본문 조회 {issue_key} 응답에 fields가 없습니다")
    description = fields.get("description")
    if description is None:
        return None
    if not isinstance(description, dict):
        raise JiraTaskError(
            f"task 본문 조회 {issue_key}의 description이 ADF object가 아닙니다"
        )
    return description


def update_issue_description(
    config: JiraConfig,
    issue_key: str,
    description: dict[str, Any],
    *,
    timeout: float = 15.0,
) -> dict[str, Any]:
    path = f"/rest/api/3/issue/{quote(issue_key, safe='')}"
    return _request(
        config,
        "PUT",
        path,
        {"fields": {"description": description}},
        expected_status=204,
        what=f"task 본문 갱신 {issue_key}",
        timeout=timeout,
        allow_empty_response=True,
    )


def _git_value(*args: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip()


def infer_worktree(cwd: Path | None = None) -> str:
    current = (cwd or Path.cwd()).resolve()
    root = _git_value("rev-parse", "--show-toplevel", cwd=current)
    return Path(root or current).name


def infer_branch(cwd: Path | None = None) -> str:
    return _git_value("branch", "--show-current", cwd=(cwd or Path.cwd()).resolve())


def infer_ticket(worktree: str, branch: str, pattern: str) -> str | None:
    try:
        matcher = re.compile(pattern)
    except re.error as exc:
        raise ConfigError(f"JIRA_TICKET_PATTERN 파싱 실패: {exc}") from None
    match = matcher.match(worktree)
    if match:
        return match.group(0)
    match = matcher.search(branch)
    return match.group(0) if match else None


def _marker_component(value: str, label: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.:@-]+", "_", value.strip())
    if not normalized:
        raise JiraTaskError(f"{label}이(가) 비어 있습니다")
    return normalized[:160]


def make_marker(context: TaskContext) -> str:
    return (
        f"{MARKER_PREFIX} ticket={_marker_component(context.ticket, 'ticket')}"
        f" date={_marker_component(context.task_date, 'date')}"
        f" worktree={_marker_component(context.worktree, 'worktree')}"
        f" session={_marker_component(context.session, 'session')}"
    )


def _resolve_timezone(name: str | None) -> tzinfo:
    if name:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            pass
    return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")


def resolve_context(args: argparse.Namespace, settings: Settings) -> TaskContext:
    worktree = args.worktree or infer_worktree()
    branch = infer_branch()
    pattern = (
        settings.get("JIRA_TICKET_PATTERN", DEFAULT_TICKET_PATTERN)
        or DEFAULT_TICKET_PATTERN
    )
    ticket = args.ticket or infer_ticket(worktree, branch, pattern)
    if not ticket:
        raise JiraTaskError(
            "티켓을 자동 추출하지 못했습니다 — --ticket KEY-123을 지정하세요"
        )
    if "/" in ticket or any(char.isspace() for char in ticket):
        raise JiraTaskError("ticket은 공백·slash를 포함할 수 없습니다")

    timezone = _resolve_timezone(settings.get("JIRA_TIMEZONE"))
    task_date = args.date or datetime.now(timezone).date().isoformat()
    try:
        date.fromisoformat(task_date)
    except ValueError:
        raise JiraTaskError("--date는 YYYY-MM-DD 형식이어야 합니다") from None
    session = (
        args.session_id
        or settings.get("JIRA_TASK_SESSION")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or "manual"
    )
    return TaskContext(ticket, worktree, task_date, session)


def _summary_from_args(args: argparse.Namespace) -> str:
    chunks = [part.strip() for part in args.summary if part.strip()]
    if args.summary_file:
        try:
            content = (
                sys.stdin.read()
                if args.summary_file == "-"
                else Path(args.summary_file).read_text(encoding="utf-8")
            )
        except OSError as exc:
            raise JiraTaskError(f"summary 파일 읽기 실패: {exc}") from None
        if content.strip():
            chunks.append(content.strip())
    summary = "\n".join(chunks).strip()
    if not summary:
        raise JiraTaskError("--summary 또는 --summary-file이 필요합니다")
    if len(summary) > MAX_SUMMARY_LENGTH:
        raise JiraTaskError(f"summary가 너무 깁니다(최대 {MAX_SUMMARY_LENGTH}자)")
    if any(pattern.search(summary) for pattern in SECRET_PATTERNS):
        raise JiraTaskError(
            "summary에 credential/private key로 보이는 값이 있어 게시를 중단합니다"
        )
    if any(line.strip().startswith(MARKER_PREFIX) for line in summary.splitlines()):
        raise JiraTaskError("summary에 예약된 [jira-task] marker를 직접 넣지 마세요")
    return summary


def build_description_entry(summary: str, marker: str) -> str:
    return "\n".join(_description_entry_lines(summary, marker))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jira task 본문에 Claude·Codex 작업내용 기록"
    )
    parser.add_argument(
        "--ticket",
        help="Jira issue key (예: CSTP1-1234). 생략 시 worktree/branch에서 추출",
    )
    parser.add_argument("--worktree", help="marker에 기록할 worktree 이름")
    parser.add_argument(
        "--date", help="작업일(YYYY-MM-DD), 기본은 JIRA_TIMEZONE 기준 오늘"
    )
    parser.add_argument("--session-id", help="marker에 기록할 세션 식별자")
    parser.add_argument(
        "--summary",
        action="append",
        default=[],
        help="작업내용 한 줄 또는 문단. 여러 번 지정 가능",
    )
    parser.add_argument("--summary-file", help="summary 파일 경로; '-'이면 stdin")
    parser.add_argument(
        "--post", action="store_true", help="Jira task description을 실제로 갱신"
    )
    parser.add_argument(
        "--timeout", type=float, default=15.0, help="Jira 요청 timeout(초)"
    )
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
        settings = load_settings()
        context = resolve_context(args, settings)
        summary = _summary_from_args(args)
        marker = make_marker(context)
        entry = build_description_entry(summary, marker)
        print(f"티켓: {context.ticket}")
        print(f"marker: {marker}")
        print(
            "동작: task description 갱신 (미리보기; 외부 변경 없음)"
            if not args.post
            else "동작: task description 갱신 (Jira 반영)"
        )
        print("--- description addition ---")
        print(entry)
        print("--- end description addition ---")
        if not args.post:
            return 0

        config = make_jira_config(settings, timeout=args.timeout)
        action, _ = upsert_description(
            config, context.ticket, summary, marker, timeout=args.timeout
        )
        print(f"Jira task description {action}: {context.ticket}")
        return 0
    except (ConfigError, JiraTaskError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
