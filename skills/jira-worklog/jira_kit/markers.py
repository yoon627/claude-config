"""worklog upsert 를 위한 결정론적 마커 (idempotency).

Jira worklog POST 는 비멱등이라, worklog comment 에 (ticket,date) 마커를 심어 그날 항목을
다시 찾을 수 있게 한다. CLI 는 등록 전 기존 worklog 를 조회해 마커로 그날 **본인** 항목을
찾고(``find_worklogs_by_marker``), 없으면 생성·있으면 시간만 갱신한다(upsert, ``worklog_register``).
"""

from __future__ import annotations

from datetime import date
from typing import Any

_PREFIX = "[jira-kit]"


def worklog_marker(ticket: str, day: date) -> str:
    """(ticket, 날짜) 조합의 결정론적 worklog 마커 문자열."""
    return f"{_PREFIX} worklog {ticket} {day.isoformat()}"


def adf_to_text(node: Any) -> str:
    """ADF 문서/노드에서 모든 text 를 이어붙여 추출한다(마커 검색용)."""
    if isinstance(node, dict):
        parts: list[str] = []
        if node.get("type") == "text" and isinstance(node.get("text"), str):
            parts.append(node["text"])
        children = node.get("content")
        if isinstance(children, list):
            parts.extend(adf_to_text(child) for child in children)
        return "".join(parts)
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    return ""


def find_worklogs_by_marker(worklogs: list[dict[str, Any]], marker: str) -> list[dict[str, Any]]:
    """comment 에 marker 가 있는 worklog 를 **전부** 반환한다(0개면 []).

    upsert 가 author-scoping(내 것만)·중복 판정(2개+ 이면 중단)에 쓰므로 첫 매치가 아니라
    모두 돌려준다.
    """
    return [
        w for w in worklogs
        if w.get("comment") is not None and marker in adf_to_text(w["comment"])
    ]
