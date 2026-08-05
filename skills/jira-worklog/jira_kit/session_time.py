"""AI 세션 작업시간 측정 (Claude·Codex 세션 로그 기반, stdlib only).

Claude 세션 파일은 ``~/.claude/projects/<slug>/`` 아래에서 현재 cwd를 따라 이동할 수 있어,
파일 위치만으로 worktree를 정하면 한 세션의 시간이 마지막 위치에 몰린다. Claude는 각 작업
이벤트의 top-level ``cwd``로 나누고, Codex는 ``~/.codex/sessions`` rollout 첫 줄의
``session_meta.cwd``로 파일 단위 귀속한다. ``discover_sessions``가 저장소의 관련 파일을
한 번 발견하고, 시간은 worktree별로 union 한다.

각 세션의 user/assistant 메시지 timestamp 로 '실제 AI 가 작업한 구간'을 뽑는다:
연속 이벤트 gap 중 **진짜 사용자 입력 직전 gap(대기)** 과 **max_gap 초과 gap(중단)** 은 제외한다.
남은 구간들을 (여러 세션에 걸쳐) union 으로 병합해 겹침을 제거하고, 자정 기준으로 날짜별
분할해 합산한다(날짜 단위 Jira worklog).
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from pathlib import Path

from ._sessionio import iter_jsonl_timestamped, mtime
from .codex_session import (
    codex_events,
    find_codex_session_files_for_worktrees,
    session_cwd,
)
from .git_util import GitError, list_worktrees
from .worklog_core import DayWorklog

_Interval = tuple[datetime, datetime]
_AttributedEvent = tuple[datetime, str, str | None]


@dataclass(frozen=True)
class SessionFiles:
    """한 저장소의 관련 Claude·Codex 세션 파일 묶음."""

    claude: list[Path]
    codex: list[Path]
    target: str | None = None
    worktree_paths: tuple[str, ...] = ()


def discover_sessions(
    cwd: str | Path,
    home: Path | None = None,
    *,
    worktree_paths: Iterable[str | Path] | None = None,
) -> SessionFiles:
    """저장소의 worktree들에 관련된 Claude·Codex 세션 파일을 한 번에 발견한다.

    Claude 세션은 한 파일 안에서 cwd가 이동할 수 있으므로 현재 worktree의 프로젝트 폴더만
    보지 않는다. CLI 한 실행에서 이 묶음을 한 번만 읽어 worktree별로 나눈다.
    """
    resolved_paths = resolve_worktree_paths(cwd, worktree_paths)
    return SessionFiles(
        claude=find_session_files(cwd, home, worktree_paths=resolved_paths),
        codex=find_codex_session_files_for_worktrees(resolved_paths, home),
        target=worktree_key(cwd),
        worktree_paths=tuple(resolved_paths),
    )


def resolve_worktree_paths(
    cwd: str | Path, worktree_paths: Iterable[str | Path] | None = None
) -> list[str]:
    """cwd가 속한 저장소의 worktree 경로를 중복 없이 반환한다.

    테스트·호출자가 경로를 직접 주면 git 조회를 생략한다. 경로를 주지 않은 경우에는 현재
    저장소의 전체 worktree를 조회하고, git 조회가 불가능한 일반 세션 로그 fixture에서는
    cwd 하나만 fallback으로 사용한다.
    """
    if worktree_paths is not None:
        paths = [str(path) for path in worktree_paths]
    else:
        try:
            paths = [worktree.path for worktree in list_worktrees(str(cwd))]
        except GitError:
            paths = [str(cwd)]
    if not paths:
        paths = [str(cwd)]

    result: list[str] = []
    seen: set[str] = set()
    for path in paths:
        key = worktree_key(path)
        if key not in seen:
            result.append(str(Path(path).resolve()))
            seen.add(key)
    return result


def worktree_key(path: str | Path) -> str:
    """worktree 경로를 결과 매핑의 안정적인 키로 정규화한다."""
    return str(Path(path).resolve())


def _match_key(path: str | Path) -> str:
    return os.path.normcase(os.path.normpath(str(Path(path).resolve())))


def _worktree_for_cwd(cwd: str | None, worktree_paths: list[str]) -> str | None:
    """cwd를 포함하는 가장 긴 worktree path의 결과 키를 반환한다."""
    if not cwd:
        return None
    candidate = _match_key(cwd)
    matches = [
        path for path in worktree_paths
        if candidate == _match_key(path)
        or candidate.startswith(_match_key(path) + os.sep)
    ]
    if not matches:
        return None
    return worktree_key(max(matches, key=lambda path: len(_match_key(path))))


def project_slug(path: str | Path) -> str:
    """절대경로를 Claude Code projects slug 로 변환한다(비영숫자 → ``-``).

    예: ``C:\\Users\\me\\Repos\\app\\.claude\\worktrees\\x``
        → ``C--Users-me-Repos-app--claude-worktrees-x``
    """
    return re.sub(r"[^a-zA-Z0-9]", "-", str(Path(path).resolve()))


def sessions_dir(cwd: str | Path, home: Path | None = None) -> Path:
    """cwd 에 해당하는 Claude Code 세션 디렉토리(``~/.claude/projects/<slug>``)."""
    base = (home or Path.home()) / ".claude" / "projects"
    return base / project_slug(cwd)


def _message_role(obj: dict) -> str | None:
    """메시지 role 정규화: 진짜 사용자 입력만 'user', assistant·도구결과는 'assistant'.

    Claude Code 는 tool_result 를 ``type=user`` 로 기록한다. 이를 사용자 입력으로 보면
    도구 실행 구간(assistant tool_use → user tool_result)이 '대기'로 잘못 제외되어 AI
    작업시간이 과소된다. 따라서 tool_result 는 AI 작업 흐름('assistant')으로 분류한다.
    """
    kind = obj.get("type")
    if kind == "assistant":
        return "assistant"
    if kind == "user":
        message = obj.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list) and any(
            isinstance(c, dict) and c.get("type") == "tool_result" for c in content
        ):
            return "assistant"
        return "user"
    return None


def parse_message_events(jsonl_text: str, tz: tzinfo) -> list[tuple[datetime, str]]:
    """세션 jsonl 텍스트에서 (시각, role) 이벤트를 시간순으로 뽑는다.

    role 은 'user'(진짜 사용자 입력) / 'assistant'(AI 응답 + 도구결과)로 정규화한다.
    """
    return [
        (moment, role)
        for moment, role, _ in parse_message_events_with_cwd(jsonl_text, tz)
    ]


def parse_message_events_with_cwd(
    jsonl_text: str, tz: tzinfo
) -> list[_AttributedEvent]:
    """세션 jsonl에서 (시각, role, cwd) 이벤트를 시간순으로 뽑는다.

    Claude의 메타데이터 줄에는 cwd가 없을 수 있지만, 작업 이벤트는 top-level cwd를 가진다.
    cwd가 없는 작업 이벤트는 오귀속을 막기 위해 ``None``으로 남긴다.
    """
    events: list[_AttributedEvent] = []
    for obj, moment in iter_jsonl_timestamped(jsonl_text, tz):
        role = _message_role(obj)
        if role is None:
            continue
        raw_cwd = obj.get("cwd")
        cwd = raw_cwd if isinstance(raw_cwd, str) and raw_cwd else None
        events.append((moment, role, cwd))
    events.sort(key=lambda e: e[0])
    return events


def ai_intervals(events: list[tuple[datetime, str]], max_gap_minutes: int = 60) -> list[_Interval]:
    """이벤트에서 'AI 작업 구간' [prev, cur] 목록을 뽑는다.

    gap 이 max_gap 초과면 중단, 진짜 사용자 입력 직전(assistant→user)이면 대기 → 둘 다 제외.
    """
    max_gap = max_gap_minutes * 60
    intervals: list[_Interval] = []
    for i in range(1, len(events)):
        prev_t, prev_role = events[i - 1]
        cur_t, cur_role = events[i]
        gap = (cur_t - prev_t).total_seconds()
        if gap <= 0 or gap > max_gap:
            continue
        if cur_role == "user" and prev_role == "assistant":
            continue
        intervals.append((prev_t, cur_t))
    return intervals


def _ai_intervals_by_worktree(
    events: list[_AttributedEvent],
    worktree_paths: list[str],
    max_gap_minutes: int,
) -> dict[str, list[_Interval]]:
    """cwd 경계를 넘지 않는 AI 작업구간을 worktree별로 나눈다."""
    intervals: dict[str, list[_Interval]] = {worktree_key(path): [] for path in worktree_paths}
    max_gap = max_gap_minutes * 60
    mapped_events = [
        (moment, role, _worktree_for_cwd(cwd, worktree_paths))
        for moment, role, cwd in events
    ]
    for i in range(1, len(events)):
        prev_t, prev_role, prev_worktree = mapped_events[i - 1]
        cur_t, cur_role, cur_worktree = mapped_events[i]
        gap = (cur_t - prev_t).total_seconds()
        if gap <= 0 or gap > max_gap:
            continue
        if cur_role == "user" and prev_role == "assistant":
            continue
        if prev_worktree is None or prev_worktree != cur_worktree:
            continue
        intervals[prev_worktree].append((prev_t, cur_t))
    return intervals


def merge_intervals(intervals: list[_Interval]) -> list[_Interval]:
    """겹치거나 맞닿은 구간을 union 으로 병합한다(여러 세션의 시간 중복 제거)."""
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _split_by_date(intervals: list[_Interval]) -> dict[date, tuple[float, datetime]]:
    """구간들을 자정 기준으로 날짜별로 쪼개 {날짜: (초, 첫시각)} 으로 합산한다."""
    by_day: dict[date, tuple[float, datetime]] = {}
    for start, end in intervals:
        cursor = start
        while cursor < end:
            day = cursor.date()
            next_midnight = datetime.combine(day + timedelta(days=1), time.min, tzinfo=cursor.tzinfo)
            segment_end = min(end, next_midnight)
            seconds = (segment_end - cursor).total_seconds()
            acc_seconds, acc_first = by_day.get(day, (0.0, cursor))
            by_day[day] = (acc_seconds + seconds, min(acc_first, cursor))
            cursor = segment_end
    return by_day


def _day_worklogs(intervals: list[_Interval]) -> list[DayWorklog]:
    by_day = _split_by_date(merge_intervals(intervals))
    return [
        DayWorklog(day=day, seconds=int(by_day[day][0]), started=by_day[day][1])
        for day in sorted(by_day)
    ]


def ai_worklogs_by_worktree(
    session_files: SessionFiles,
    worktree_paths: Iterable[str | Path],
    tz: tzinfo,
    max_gap_minutes: int = 60,
) -> dict[str, list[DayWorklog]]:
    """Claude·Codex 세션 시간을 한 번 읽어 worktree별 날짜 작업시간으로 나눈다.

    Claude는 각 이벤트의 cwd로 interval 양끝을 분류하고, Codex는 rollout 첫 줄의 cwd로
    파일 전체를 분류한다. 각 worktree 안에서만 interval을 merge하므로 서로 다른 worktree의
    시간이 합쳐지거나 이동 구간이 billable 시간으로 들어가지 않는다.
    """
    paths = resolve_worktree_paths(Path.cwd(), worktree_paths)
    intervals: dict[str, list[_Interval]] = {worktree_key(path): [] for path in paths}
    for path in session_files.claude:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        grouped = _ai_intervals_by_worktree(
            parse_message_events_with_cwd(text, tz), paths, max_gap_minutes
        )
        for key, path_intervals in grouped.items():
            intervals[key].extend(path_intervals)

    for path in session_files.codex:
        source_worktree = _worktree_for_cwd(session_cwd(path), paths)
        if source_worktree is None:
            continue
        intervals[source_worktree].extend(
            ai_intervals(codex_events([path], tz), max_gap_minutes)
        )

    return {key: _day_worklogs(path_intervals) for key, path_intervals in intervals.items()}


def ai_worklog_by_date(
    session_files: SessionFiles,
    tz: tzinfo,
    max_gap_minutes: int = 60,
    *,
    cwd: str | Path | None = None,
    worktree_paths: Iterable[str | Path] | None = None,
) -> list[DayWorklog]:
    """한 worktree의 Claude·Codex 세션을 union·자정분할해 날짜별로 반환한다.

    ``cwd``를 주면 Claude 이벤트의 줄 단위 cwd 귀속을 사용한다. 생략한 구버전 호출은 기존
    파일 단위 합산을 유지해 외부 호출자의 호환성을 보존한다.
    """
    target = worktree_key(cwd) if cwd is not None else session_files.target
    if target is not None:
        paths = resolve_worktree_paths(
            cwd or target,
            worktree_paths or session_files.worktree_paths or [target],
        )
        grouped = ai_worklogs_by_worktree(session_files, paths, tz, max_gap_minutes)
        return grouped.get(target, [])

    intervals: list[_Interval] = []
    for path in session_files.claude:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        intervals.extend(ai_intervals(parse_message_events(text, tz), max_gap_minutes))
    for path in session_files.codex:
        # 파일=독립 세션이라 파일별로 interval 을 뽑는다(파일 경계 gap 오염 방지).
        intervals.extend(ai_intervals(codex_events([path], tz), max_gap_minutes))
    return _day_worklogs(intervals)


def find_session_files(
    cwd: str | Path,
    home: Path | None = None,
    *,
    worktree_paths: Iterable[str | Path] | None = None,
) -> list[Path]:
    """관련 Claude 프로젝트 디렉토리의 세션 jsonl 파일을 수정시각 순으로 찾는다."""
    paths = resolve_worktree_paths(cwd, worktree_paths)
    projects = (home or Path.home()) / ".claude" / "projects"
    if not projects.is_dir():
        return []
    slugs = [project_slug(path) for path in paths]
    files: set[Path] = set()
    try:
        directories = projects.iterdir()
        for directory in directories:
            if not directory.is_dir():
                continue
            if not any(
                directory.name == slug or directory.name.startswith(slug + "-")
                for slug in slugs
            ):
                continue
            files.update(directory.glob("*.jsonl"))
    except OSError:
        return []
    return sorted(files, key=mtime)
