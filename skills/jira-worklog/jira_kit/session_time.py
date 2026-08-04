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
from collections.abc import Iterable, Sequence
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


def _resolved(path: str | Path) -> Path:
    """절대경로화 + symlink 해소(``/tmp`` → ``/private/tmp``).

    존재하지 않는 경로(삭제된 worktree)도 다뤄야 하므로 strict 는 쓰지 않는다.
    """
    return Path(path).resolve()


def _compared(path: Path) -> PurePath:
    """비교 전용 정규화.

    ``normcase`` 는 **Windows 에서만** 의미가 있다(구분자 통일 + 소문자화). POSIX 에선
    항등이라 macOS 의 대소문자 무시 파일시스템은 덮지 못한다 — 대소문자만 다른 cwd 는
    매칭에 실패한다. 소문자화된 결과는 비교에만 쓰고 표시·티켓 추출에는 원본을 쓴다
    (worktree 이름이 소문자가 되면 ``extract_ticket`` 의 대문자 패턴이 어긋난다).
    """
    return PurePath(os.path.normcase(str(path)))


# (비교용 경로, 표시용 이름)
_Candidate = tuple[PurePath, str]


class WorktreeIndex:
    """cwd → bucket 분류기. 정규화를 한 번만 하고 cwd 문자열 단위로 캐시한다.

    이벤트마다 root 와 live worktree 전부를 ``resolve()`` 하면 O(이벤트 × worktree) 의
    syscall 이 된다(실측 live 20개 × 2만 이벤트 = 5.8s — ``--all`` 5초 기준을 분류 단독으로
    넘긴다). 실코퍼스는 2.6만 이벤트에 distinct cwd 가 77개뿐이라 캐시가 잘 듣는다.
    """

    def __init__(self, root: str | Path, live_worktrees: Iterable[str | Path]) -> None:
        self._root = _resolved(root)
        self._root_key = _compared(self._root)
        self._live: list[_Candidate] = []
        for worktree in live_worktrees:
            path = _resolved(worktree)
            key = _compared(path)
            if key != self._root_key:  # root 자신은 폴백 대상이지 후보가 아니다
                self._live.append((key, path.name))
        self._cache: dict[str, Bucket] = {}

    def classify(self, cwd: str | Path | None) -> Bucket:
        if cwd is None:
            return _UNMATCHED
        key = str(cwd)
        bucket = self._cache.get(key)
        if bucket is None:
            bucket = self._cache[key] = self._classify(key)
        return bucket

    def _classify(self, cwd: str) -> Bucket:
        try:
            resolved = _resolved(cwd)
        except (OSError, ValueError):
            # cwd 는 로그에서 온 외부 입력이라 신뢰하지 않는다. 한 줄이 전체 집계를 죽이면 안 된다.
            return _UNMATCHED
        target = _compared(resolved)

        live = max(
            (c for c in self._live if target.is_relative_to(c[0])),
            key=lambda c: len(c[0].parts),
            default=None,
        )
        dead = self._dead_candidate(resolved, target)
        # 더 깊은 쪽이 이긴다. 이름이 아니라 경로로 비교해야 상위 live 와 이름이 같은
        # 중첩 dead worktree 가 상위로 흡수되지 않는다(흡수되면 등록 가능으로 오판).
        if dead is not None and (live is None or len(dead[0].parts) > len(live[0].parts)):
            return Bucket(BucketKind.DEAD, dead[1])
        if live is not None:
            return Bucket(BucketKind.LIVE, live[1])
        if target.is_relative_to(self._root_key):
            return Bucket(BucketKind.MAIN)
        return _UNMATCHED

    def _dead_candidate(self, resolved: Path, target: PurePath) -> _Candidate | None:
        """`<root>/.claude/worktrees/<name>` 규약으로 삭제된 worktree 를 복원한다.

        중첩이 있으므로 **이름이 뒤따르는 마지막 출현**을 쓴다. 표시용 이름은 정규화 이전
        경로에서 뽑아 대소문자를 보존한다.
        """
        if not target.is_relative_to(self._root_key):
            return None
        parts = target.parts
        display = resolved.parts
        width = len(_WORKTREES_SEGMENTS)
        found = None
        for i in range(len(self._root_key.parts), len(parts) - width + 1):
            if parts[i:i + width] == _WORKTREES_SEGMENTS and i + width < len(parts):
                found = i + width
        if found is None:
            return None
        return PurePath(*parts[:found + 1]), display[found]


def classify_cwd(
    cwd: str | Path | None, root: str | Path, live_worktrees: Iterable[str | Path]
) -> Bucket:
    """단발 분류 편의 함수. 반복 호출은 ``WorktreeIndex`` 를 재사용하라(정규화 비용).

    조상 폴백을 하지 않는 것이 핵심이다. main 은 모든 worktree 의 조상이면서 자신도
    worktree 목록에 있으므로, 매칭 실패를 조상으로 흘려보내면 삭제된 worktree 의 시간이
    통째로 main 에 흡수된다(실측 3.5배 과다).
    """
    return WorktreeIndex(root, live_worktrees).classify(cwd)


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


def parse_message_events(jsonl_text: str, tz: tzinfo) -> list[tuple[datetime, str, str | None]]:
    """세션 jsonl 텍스트에서 (시각, role, cwd) 이벤트를 시간순으로 뽑는다.

    role 은 'user'(진짜 사용자 입력) / 'assistant'(AI 응답 + 도구결과)로 정규화한다.
    cwd 는 귀속 근거다 — 세션 파일은 cwd 를 따라 폴더를 옮겨 다니므로 파일이 놓인 위치가
    아니라 줄마다 기록된 cwd 로 나눠야 한다. 결측이면 앞줄에서 물려받지 않고 ``None`` 이다
    (물려받으면 worktree 경계가 사라져 오귀속이 된다).
    """
    events: list[tuple[datetime, str, str | None]] = []
    for obj, moment in iter_jsonl_timestamped(jsonl_text, tz):
        role = _message_role(obj)
        if role is None:
            continue
        cwd = obj.get("cwd")
        events.append((moment, role, cwd if isinstance(cwd, str) and cwd else None))
    events.sort(key=lambda e: e[0])
    return events


_Event = Sequence  # (시각, role[, cwd|bucket]) — 뒤 요소는 소비자마다 다르다


def _is_work_gap(prev: _Event, cur: _Event, max_gap: float) -> bool:
    """인접 두 이벤트 사이가 'AI 작업 구간'인지.

    gap 이 max_gap 초과면 중단, 진짜 사용자 입력 직전(assistant→user)이면 대기 → 둘 다 아님.
    """
    gap = (cur[0] - prev[0]).total_seconds()
    if gap <= 0 or gap > max_gap:
        return False
    return not (cur[1] == "user" and prev[1] == "assistant")


def ai_intervals(events: Sequence[_Event], max_gap_minutes: int = 60) -> list[_Interval]:
    """이벤트에서 'AI 작업 구간' [prev, cur] 목록을 뽑는다.

    events 는 (시각, role) 또는 (시각, role, cwd) — 3번째 요소는 무시한다. Codex 이벤트는
    cwd 를 줄 단위로 갖지 않아 2-튜플이라 양쪽을 받는다.
    """
    max_gap = max_gap_minutes * 60
    return [
        (events[i - 1][0], events[i][0])
        for i in range(1, len(events))
        if _is_work_gap(events[i - 1], events[i], max_gap)
    ]


@dataclass(frozen=True)
class AttributionStats:
    """귀속 과정에서 버린 양 — dry-run 에 노출해 과소계상을 감시한다."""

    boundary_dropped: int = 0
    boundary_seconds: float = 0.0


def bucket_intervals(
    events: list[tuple[datetime, str, Bucket]], max_gap_minutes: int = 60
) -> tuple[dict[Bucket, list[_Interval]], AttributionStats]:
    """bucket 을 단 이벤트에서 bucket 별 작업구간을 뽑는다.

    **인접 쌍의 bucket 이 같을 때만** 구간을 발행한다. bucket 별로 이벤트를 먼저 걸러
    스트림을 만들면, A→B→A 왕복이 max_gap 안에 들어올 때 A 의 두 이벤트가 B 구간을
    가로질러 이어져 이중계상된다. 경계 구간은 '이동' 자체라 어느 쪽 것도 아니므로 버리고,
    버린 양은 통계로 돌려준다.

    호출 측이 **파일별로** 부르는 것을 전제한다(파일 = 독립 세션). 여러 파일 이벤트를 한
    스트림으로 합치면 서로 다른 세션 사이 공백이 작업시간으로 잡힌다.
    """
    max_gap = max_gap_minutes * 60
    buckets: dict[Bucket, list[_Interval]] = {}
    dropped = 0
    dropped_seconds = 0.0
    for i in range(1, len(events)):
        prev, cur = events[i - 1], events[i]
        if not _is_work_gap(prev, cur, max_gap):
            continue
        if prev[2] != cur[2]:
            dropped += 1
            dropped_seconds += (cur[0] - prev[0]).total_seconds()
            continue
        buckets.setdefault(prev[2], []).append((prev[0], cur[0]))
    return buckets, AttributionStats(dropped, dropped_seconds)


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
    return worklog_from_intervals(intervals)


def worklog_from_intervals(intervals: list[_Interval]) -> list[DayWorklog]:
    """작업구간들을 union·자정분할해 날짜별 DayWorklog 로 만든다."""
    by_day = _split_by_date(merge_intervals(intervals))
    return [
        DayWorklog(day=day, seconds=int(by_day[day][0]), started=by_day[day][1])
        for day in sorted(by_day)
    ]


def ai_worklog_by_bucket(
    claude_files: list[Path],
    tz: tzinfo,
    root: str | Path,
    live_worktrees: Iterable[str | Path],
    max_gap_minutes: int = 60,
) -> tuple[dict[Bucket, list[DayWorklog]], AttributionStats]:
    """Claude 세션 파일들을 한 번만 읽어 bucket 별 날짜 worklog 로 나눈다.

    코퍼스를 worktree 마다 다시 읽으면 worktree 수만큼 스캔이 반복된다 — 단일 패스가
    ``--all`` 성능 기준의 전제다. Codex 는 줄 단위 cwd 이동이 없어(rollout 전수에서 cwd 가
    2개 이상인 파일 0건) 파일 단위 귀속을 그대로 쓰므로 여기서 다루지 않는다.
    """
    index = WorktreeIndex(root, live_worktrees)
    per_bucket: dict[Bucket, list[_Interval]] = {}
    dropped = 0
    dropped_seconds = 0.0
    for path in claude_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        events = [
            (moment, role, index.classify(cwd))
            for moment, role, cwd in parse_message_events(text, tz)
        ]
        buckets, stats = bucket_intervals(events, max_gap_minutes)
        for bucket, intervals in buckets.items():
            per_bucket.setdefault(bucket, []).extend(intervals)
        dropped += stats.boundary_dropped
        dropped_seconds += stats.boundary_seconds
    worklogs = {bucket: worklog_from_intervals(iv) for bucket, iv in per_bucket.items()}
    return worklogs, AttributionStats(dropped, dropped_seconds)


def find_session_files(cwd: str | Path, home: Path | None = None) -> list[Path]:
    """cwd 의 세션 디렉토리에서 세션 jsonl 파일 목록(수정시각 오름차순, stat 실패 방어)."""
    directory = sessions_dir(cwd, home)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.jsonl"), key=mtime)
