#!/usr/bin/env python3
"""Preview or upsert a work summary in a Jira Cloud issue description."""

from __future__ import annotations

import argparse
import base64
import hashlib
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
ITEM_PREFIX_RE = re.compile(r"^(?:[-*•]|\d{1,2}[.)])(?:\s+|$)")
DATE_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEGACY_MARKER_DATE_RE = re.compile(r"\sdate=(\S+)")
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
    task_date: str


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
        return _adf_node_text(node.get("content"))
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


def _summary_items(summary: str) -> list[str]:
    heading_prefix = f"{DESCRIPTION_HEADING}:"
    items: list[str] = []
    for raw in summary.splitlines():
        line = ITEM_PREFIX_RE.sub("", raw.strip(), count=1).strip()
        if line.startswith(heading_prefix):
            line = line[len(heading_prefix) :].strip()
        line = ITEM_PREFIX_RE.sub("", line, count=1).strip()
        if line:
            items.append(line)
    return items


def _description_entry_lines(summary: str, task_date: str) -> list[str]:
    return [task_date, *(f"- {item}" for item in _summary_items(summary))]


def _description_entry(summary: str, task_date: str) -> dict[str, Any]:
    lines = _description_entry_lines(summary, task_date)
    content: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if index == 0:
            content.append(
                {"type": "text", "text": line, "marks": [{"type": "strong"}]}
            )
        else:
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


def _heading_level(block: dict[str, Any]) -> int | None:
    if block.get("type") != "heading":
        return None
    attrs = block.get("attrs")
    level = attrs.get("level") if isinstance(attrs, dict) else None
    return level if isinstance(level, int) else 6


def _section_range(content: list[dict[str, Any]]) -> tuple[int, int] | None:
    """`작업 내용` heading 다음 블록부터 같은 레벨 이하의 다음 heading 직전까지."""
    for start, block in enumerate(content):
        level = _heading_level(block)
        if level is None or _adf_node_text(block).strip() != DESCRIPTION_HEADING:
            continue
        for end in range(start + 1, len(content)):
            other = _heading_level(content[end])
            if other is not None and other <= level:
                return start + 1, end
        return start + 1, len(content)
    return None


def _first_line(block: dict[str, Any]) -> str:
    return _adf_node_text(block).split("\n", 1)[0].strip()


def _legacy_marker_date(block: dict[str, Any]) -> str | None:
    for line in _adf_node_text(block).split("\n"):
        line = line.strip()
        if line.startswith(MARKER_PREFIX):
            match = LEGACY_MARKER_DATE_RE.search(line)
            if match:
                return match.group(1)
    return None


def _date_block_indices(content: list[dict[str, Any]], task_date: str) -> list[int]:
    """섹션 안에서 그 날짜에 속한 블록 위치.

    날짜 줄 블록부터 다음 날짜 줄·옛 marker 블록·하위 heading 직전까지와, 그 날짜의 옛 marker 블록.
    """
    section = _section_range(content)
    if section is None:
        return []
    indices: list[int] = []
    in_date = False
    for index in range(*section):
        block = content[index]
        first = _first_line(block)
        legacy_date = _legacy_marker_date(block)
        if _heading_level(block) is not None:
            in_date = False
        elif DATE_LINE_RE.match(first):
            in_date = first == task_date
        elif legacy_date is not None:
            in_date = False
        if in_date or legacy_date == task_date:
            indices.append(index)
    return indices


def existing_entry_text(description: dict[str, Any] | None, task_date: str) -> str:
    content = _description_content(description)
    return "\n".join(
        _adf_node_text(content[index])
        for index in _date_block_indices(content, task_date)
    )


def entry_fingerprint(description: dict[str, Any] | None, task_date: str) -> str:
    text = existing_entry_text(description, task_date)
    if not text:
        return "none"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _description_matches(
    description: dict[str, Any] | None, summary: str, task_date: str
) -> bool:
    content = _description_content(description)
    indices = _date_block_indices(content, task_date)
    if len(indices) != 1:
        return False
    return _adf_node_text(content[indices[0]]) == "\n".join(
        _description_entry_lines(summary, task_date)
    )


def upsert_description_body(
    description: dict[str, Any] | None, summary: str, task_date: str
) -> tuple[dict[str, Any], str]:
    """기존 ADF 본문을 보존하고 그 날짜 항목을 새 요약 하나로 추가·교체한다."""
    if description is None:
        result: dict[str, Any] = {"type": "doc", "version": 1, "content": []}
    else:
        result = json.loads(json.dumps(description, ensure_ascii=False))
        if result.get("type") != "doc":
            raise JiraTaskError("Jira description의 ADF type이 doc이 아닙니다")
        if not isinstance(result.get("version"), int):
            raise JiraTaskError("Jira description의 ADF version이 없습니다")

    content = _description_content(result)
    entry = _description_entry(summary, task_date)
    indices = _date_block_indices(content, task_date)
    if indices:
        if len(indices) == 1 and _adf_node_text(content[indices[0]]) == _adf_node_text(
            entry
        ):
            return result, "unchanged"
        content[indices[0]] = entry
        for index in reversed(indices[1:]):
            del content[index]
        return result, "updated"

    section = _section_range(content)
    if section is None:
        content.extend([_description_heading(), entry])
    else:
        content.insert(section[1], entry)
    return result, "added"


def upsert_description(
    config: JiraConfig,
    issue_key: str,
    summary: str,
    task_date: str,
    expected_fingerprint: str,
    *,
    timeout: float = 15.0,
) -> tuple[str, dict[str, Any]]:
    current = get_issue_description(config, issue_key, timeout=timeout)
    actual = entry_fingerprint(current, task_date)
    if actual != expected_fingerprint:
        raise JiraTaskError(
            f"{task_date} 기존 항목 지문이 다릅니다(기대 {expected_fingerprint}, 현재 {actual}) — "
            "preview를 다시 실행해 기존 항목을 읽고 요약을 다시 쓰세요"
        )
    planned, action = upsert_description_body(current, summary, task_date)
    if action == "unchanged":
        return action, current or planned

    update_issue_description(config, issue_key, planned, timeout=timeout)
    saved = get_issue_description(config, issue_key, timeout=timeout)
    if not _description_matches(saved, summary, task_date):
        raise JiraTaskError(
            f"task 본문 갱신 후 저장값 확인 불일치 {issue_key}: {task_date} 항목을 찾지 못했습니다"
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
    return TaskContext(ticket, task_date)


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
    if not _summary_items(summary):
        raise JiraTaskError(
            "적을 작업 항목이 없습니다 — --summary 또는 --summary-file에 항목을 한 줄씩 적으세요"
        )
    if len(summary) > MAX_SUMMARY_LENGTH:
        raise JiraTaskError(f"summary가 너무 깁니다(최대 {MAX_SUMMARY_LENGTH}자)")
    if any(pattern.search(summary) for pattern in SECRET_PATTERNS):
        raise JiraTaskError(
            "summary에 credential/private key로 보이는 값이 있어 게시를 중단합니다"
        )
    if any(line.strip().startswith(MARKER_PREFIX) for line in summary.splitlines()):
        raise JiraTaskError("summary에 예약된 [jira-task] marker를 직접 넣지 마세요")
    return summary


def build_description_entry(summary: str, task_date: str) -> str:
    return "\n".join(_description_entry_lines(summary, task_date))


def _preview_existing(
    settings: Settings, ticket: str, task_date: str, timeout: float
) -> tuple[str, str]:
    """그 날짜의 기존 항목과 지문. 읽지 못하면 사유와 `unknown`."""
    try:
        config = make_jira_config(settings, timeout=timeout)
        current = get_issue_description(config, ticket, timeout=timeout)
        existing = existing_entry_text(current, task_date)
        fingerprint = entry_fingerprint(current, task_date)
    except (ConfigError, JiraTaskError) as exc:
        return f"(확인 불가: {exc})", "unknown"
    return existing or "(없음)", fingerprint


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jira task 본문에 Claude·Codex 작업내용 기록"
    )
    parser.add_argument(
        "--ticket",
        help="Jira issue key (예: ABC-1234). 생략 시 worktree/branch에서 추출",
    )
    parser.add_argument("--worktree", help="티켓 추출에 쓸 worktree 이름")
    parser.add_argument(
        "--date", help="작업일(YYYY-MM-DD), 기본은 JIRA_TIMEZONE 기준 오늘"
    )
    parser.add_argument(
        "--expect-existing",
        help="--post 필수: preview가 출력한 그 날짜 기존 항목 지문(없으면 none)",
    )
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
        entry = build_description_entry(summary, context.task_date)
        if args.post and not args.expect_existing:
            raise JiraTaskError(
                "--post에는 --expect-existing <preview의 기존 항목 지문>이 필요합니다"
            )
        print(f"티켓: {context.ticket}")
        print(f"날짜: {context.task_date}")
        if not args.post:
            print("동작: task description 갱신 (미리보기; 외부 변경 없음)")
            existing, fingerprint = _preview_existing(
                settings, context.ticket, context.task_date, args.timeout
            )
            print("--- 그 날짜 기존 항목 (교체됨) ---")
            print(existing)
            print(f"--- 기존 항목 지문: {fingerprint} ---")
            print("--- 교체 후 ---")
            print(entry)
            print("--- end ---")
            return 0

        print("동작: task description 갱신 (Jira 반영)")
        config = make_jira_config(settings, timeout=args.timeout)
        action, _ = upsert_description(
            config,
            context.ticket,
            summary,
            context.task_date,
            args.expect_existing,
            timeout=args.timeout,
        )
        print(f"Jira task description {action}: {context.ticket}")
        return 0
    except (ConfigError, JiraTaskError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
