"""AI 세션 작업시간 측정 (Claude·Codex 세션 로그 기반, stdlib only).

Claude·Codex 모두 cwd(worktree 포함)별로 세션 로그를 남긴다(Claude 는 slug 디렉토리
``~/.claude/projects/<slug>/``, Codex 는 ``~/.codex/sessions`` 아래 rollout 파일의
``session_meta.cwd``). 그래서 **worktree 에서 실행하면 그 worktree 세션들만** 잡혀 worktree↔
티켓 매핑이 자동으로 된다(worktree 이름/브랜치명에서 티켓 추출). ``discover_sessions`` 가 두 소스를 한 번에
발견하고, 시간은 union 한다. 소스별 파싱은 Claude 는 이 모듈, Codex 는 ``codex_session`` 이 담당한다.

각 세션의 user/assistant 메시지 timestamp 로 '실제 AI 가 작업한 구간'을 뽑는다:
연속 이벤트 gap 중 **진짜 사용자 입력 직전 gap(대기)** 과 **max_gap 초과 gap(중단)** 은 제외한다.
남은 구간들을 (여러 세션에 걸쳐) union 으로 병합해 겹침을 제거하고, 자정 기준으로 날짜별
분할해 합산한다(날짜 단위 Jira worklog).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from enum import Enum
from pathlib import Path, PurePath

from ._sessionio import iter_jsonl_timestamped, mtime
from .codex_session import codex_events, find_codex_session_files
from .worklog_core import DayWorklog

_Interval = tuple[datetime, datetime]

# worktree 는 `<root>/.claude/worktrees/<name>` 에 만들어진다(skills/wt/SKILL.md).
# 삭제된 worktree 는 `git worktree list` 에 없으므로 이 규약으로 이름을 되살린다.
_WORKTREES_SEGMENTS = (".claude", "worktrees")


class BucketKind(Enum):
    """cwd 가 귀속되는 단위."""

    LIVE = "live"  # 현존하는 worktree
    DEAD = "dead"  # 삭제됐지만 경로 규약으로 이름을 복원한 worktree
    MAIN = "main"  # repo 루트 (어떤 worktree 에도 속하지 않음)
    UNMATCHED = "unmatched"  # repo 밖 (타 repo·홈 등)


@dataclass(frozen=True)
class Bucket:
    """귀속 단위. ``kind`` 로 등록 가능 여부를 판정한다(이름만으로 구분하면 샌다)."""

    kind: BucketKind
    name: str | None = None

    @property
    def registrable(self) -> bool:
        return self.kind is BucketKind.LIVE


_UNMATCHED = Bucket(BucketKind.UNMATCHED)


def _normalized(path: str | Path) -> PurePath:
    """비교용 정규화: 절대경로 + 플랫폼별 대소문자 정규화.

    ``resolve()`` 로 symlink(``/tmp`` → ``/private/tmp``)를, ``normcase`` 로 Windows·APFS
    의 대소문자 차이를 흡수한다. 존재하지 않는 경로도 다뤄야 하므로 strict 는 쓰지 않는다.
    """
    return PurePath(os.path.normcase(str(Path(path).resolve())))


def _dead_worktree_name(cwd: PurePath, root: PurePath) -> str | None:
    """`<root>/.claude/worktrees/<name>` 규약에서 worktree 이름을 복원한다.

    중첩 worktree 가 있으므로 **마지막** 출현을 기준으로 삼는다 — 그래야 하위 worktree 가
    상위 이름으로 잘못 복원되지 않는다.
    """
    parts = cwd.relative_to(root).parts
    last = None
    for i in range(len(parts) - len(_WORKTREES_SEGMENTS)):
        if parts[i:i + len(_WORKTREES_SEGMENTS)] == _WORKTREES_SEGMENTS:
            last = i + len(_WORKTREES_SEGMENTS)
    if last is None or last >= len(parts):
        return None
    return parts[last]


def classify_cwd(cwd: str | Path | None, root: str | Path, live_worktrees) -> Bucket:
    """세션 줄의 cwd 를 귀속 bucket 으로 분류한다.

    조상 폴백을 하지 않는 것이 핵심이다. main 은 모든 worktree 의 조상이면서 자신도
    worktree 목록에 있으므로, 매칭 실패를 조상으로 흘려보내면 삭제된 worktree 의 시간이
    통째로 main 에 흡수된다(실측 3.5배 과다).
    """
    if cwd is None:
        return _UNMATCHED
    target = _normalized(cwd)
    repo_root = _normalized(root)
    if not target.is_relative_to(repo_root):
        return _UNMATCHED

    deepest = max(
        (
            candidate
            for worktree in live_worktrees
            if (candidate := _normalized(worktree)) != repo_root
            and target.is_relative_to(candidate)
        ),
        key=lambda p: len(p.parts),
        default=None,
    )
    dead_name = _dead_worktree_name(target, repo_root)
    if dead_name is not None and (deepest is None or deepest.name != dead_name):
        return Bucket(BucketKind.DEAD, dead_name)
    if deepest is not None:
        return Bucket(BucketKind.LIVE, deepest.name)
    return Bucket(BucketKind.MAIN)


@dataclass(frozen=True)
class SessionFiles:
    """한 worktree 에 대해 발견한 소스별 세션 파일 묶음."""

    claude: list[Path]
    codex: list[Path]


def discover_sessions(cwd: str | Path, home: Path | None = None) -> SessionFiles:
    """worktree cwd 에 해당하는 Claude·Codex 세션 파일을 한 번에 발견한다.

    통합 함수가 이 묶음을 받아 시간·토큰을 각각 산출하므로, CLI 한 실행에서 세션 트리를
    두 번 스캔하지 않는다.
    """
    return SessionFiles(
        claude=find_session_files(cwd, home),
        codex=find_codex_session_files(cwd, home),
    )


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
    events: list[tuple[datetime, str]] = []
    for obj, moment in iter_jsonl_timestamped(jsonl_text, tz):
        role = _message_role(obj)
        if role is None:
            continue
        events.append((moment, role))
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


def ai_worklog_by_date(
    session_files: SessionFiles, tz: tzinfo, max_gap_minutes: int = 60
) -> list[DayWorklog]:
    """Claude·Codex 세션의 AI 작업구간을 union·자정분할해 날짜별 DayWorklog 로 반환한다."""
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
    merged = merge_intervals(intervals)
    by_day = _split_by_date(merged)
    return [
        DayWorklog(day=day, seconds=int(by_day[day][0]), started=by_day[day][1])
        for day in sorted(by_day)
    ]


def find_session_files(cwd: str | Path, home: Path | None = None) -> list[Path]:
    """cwd 의 세션 디렉토리에서 세션 jsonl 파일 목록(수정시각 오름차순, stat 실패 방어)."""
    directory = sessions_dir(cwd, home)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.jsonl"), key=mtime)
