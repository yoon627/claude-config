"""worklog upsert 를 위한 결정론적 마커 (idempotency).

Jira worklog POST 는 비멱등이라, worklog comment 에 (ticket, date, worktree) 마커를 심어
그 항목을 다시 찾을 수 있게 한다. CLI 는 등록 전 기존 worklog 를 조회해 마커로 **본인** 항목을
찾고(``find_worklogs_by_marker``), 없으면 생성·있으면 시간만 갱신한다(upsert, ``worklog_register``).

같은 티켓을 여러 worktree 에서 작업하면(``CSTP1-1234-abc``/``-def``) 마커에 worktree 가 없을 때
두 worktree 가 같은 항목을 자기 것으로 잡아 나중 등록이 이전 시간을 덮는다. 그래서 마커는
worktree 까지 포함하고, 티켓 총합은 Jira 의 worklog 합계에 맡긴다.

매칭은 **줄 정확일치**다. 부분문자열로 찾으면 사용자 ``--comment`` 본문이나 Jira UI 수동 편집
텍스트가 마커를 품고 있을 때 그 항목을 자기 것으로 오인하고, 문단이 구분자 없이 이어붙으면
두 문단에 걸쳐 마커가 우연히 합성되기도 한다.

반대로 정확일치는 마커를 **놓치는** 쪽이 위험하다 — 못 찾으면 새 항목을 만들어 그날 시간이
이중계상되는데, 오매치와 달리 조용하다. 그래서 줄 추출은 Jira UI 편집으로 생기는 변형
(``hardBreak``·``codeBlock``·``heading``·앞뒤 공백)까지 흡수한다.
"""

from __future__ import annotations

from datetime import date
from typing import Any

_PREFIX = "[jira-kit]"

# 자식 text 가 한 줄(들)을 이루는 블록. 그 외 노드는 자식으로 재귀한다(blockquote·listItem 등).
_TEXT_BLOCKS = ("paragraph", "heading", "codeBlock")


def legacy_worklog_marker(ticket: str, day: date) -> str:
    """worktree 도입 전 형식의 마커. 새로 쓰지 않고 **기존 항목 탐지에만** 쓴다."""
    return f"{_PREFIX} worklog {ticket} {day.isoformat()}"


def worklog_marker(ticket: str, day: date, worktree: str) -> str:
    """(ticket, 날짜, worktree) 조합의 결정론적 worklog 마커 문자열.

    빈 이름은 구 형식과 구별되지 않아 legacy 검사에 자기가 걸리고, 개행은 마커를 두 줄로 쪼개
    영영 못 찾게 만든다 — 둘 다 조용한 이중계상으로 이어지므로 여기서 막는다.
    """
    if not worktree:
        raise ValueError("worklog 마커에 빈 worktree 이름을 쓸 수 없습니다 (구 형식과 충돌)")
    if "\n" in worktree or "\r" in worktree:
        raise ValueError(f"worklog 마커에 개행이 든 worktree 이름을 쓸 수 없습니다: {worktree!r}")
    return f"{legacy_worklog_marker(ticket, day)} ({worktree})"


def _inline_text(node: Any) -> str:
    """블록 안의 text 를 이어붙인다. ``hardBreak`` 는 줄바꿈으로 되살린다.

    mark(bold 등)로 조각난 text 노드도 원래 문자열로 복원된다.
    """
    if isinstance(node, dict):
        if node.get("type") == "hardBreak":
            return "\n"
        text = node.get("text")
        own = text if node.get("type") == "text" and isinstance(text, str) else ""
        return own + _inline_text(node.get("content"))
    if isinstance(node, list):
        return "".join(_inline_text(n) for n in node)
    return ""


def adf_lines(node: Any) -> list[str]:
    """ADF 문서에서 텍스트 블록을 줄 목록으로 뽑는다(마커 정확일치 검색용)."""
    if isinstance(node, list):
        return [line for child in node for line in adf_lines(child)]
    if not isinstance(node, dict):
        return []
    if node.get("type") in _TEXT_BLOCKS:
        return _inline_text(node.get("content")).split("\n")
    return adf_lines(node.get("content"))


def find_worklogs_by_marker(worklogs: list[dict[str, Any]], marker: str) -> list[dict[str, Any]]:
    """comment 에 marker 줄이 있는 worklog 를 **전부** 반환한다(0개면 []).

    upsert 가 author-scoping(내 것만)·중복 판정(2개+ 이면 중단)에 쓰므로 첫 매치가 아니라
    모두 돌려준다. 비교 전 줄 양끝 공백을 떼어 Jira 의 정규화·UI 편집 흔적을 흡수한다.
    """
    return [
        w for w in worklogs
        if w.get("comment") is not None
        and any(line.strip() == marker for line in adf_lines(w["comment"]))
    ]
