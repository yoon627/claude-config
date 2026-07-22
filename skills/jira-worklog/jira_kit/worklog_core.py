"""worklog 공용 자료구조 + 티켓 추출 (순수 로직, stdlib only).

작업시간 측정은 session_time(Claude·Codex 세션 로그 기반)이 담당한다. 이 모듈은
그 결과를 담는 ``DayWorklog`` 와, 이름 문자열(worktree 디렉토리·브랜치)에서 Jira 티켓을
뽑는 ``extract_ticket`` 만 둔다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

_DEFAULT_TICKET_PATTERN = r"CSTP1-\d+"


@dataclass(frozen=True)
class DayWorklog:
    """하루 단위로 묶은 작업시간."""

    day: date
    seconds: int
    started: datetime


def extract_ticket(
    name: str, pattern: str = _DEFAULT_TICKET_PATTERN, *, anchored: bool = False
) -> str | None:
    """이름 문자열(worktree 디렉토리·브랜치)에서 Jira 티켓 키를 추출한다. 매치 없으면 None.

    ``anchored=True`` 면 맨 앞(prefix)에서만 매치한다. worktree 디렉토리는 ``CSTP1-<id>-<slug>``
    prefix 규약이라, 이름 중간에 박힌 다른 티켓(예: ``backport-CSTP1-1-to-2``)을 잡아 billable
    worklog 를 오귀속하는 걸 막는다. 기본(브랜치 등)은 부분일치(search).
    """
    match = re.match(pattern, name) if anchored else re.search(pattern, name)
    return match.group(0) if match else None


def format_duration(seconds: int) -> str:
    """초를 사람이 읽는 소요시간으로. 예: 5400 → '1h 30m'."""
    hours, minutes = divmod(round(seconds / 60), 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    return f"{hours}h" if hours else f"{minutes}m"
