"""(ticket, date) worklog 의 upsert 오케스트레이션 (jira_client + markers 위, 순수 조립).

worklog 는 (ticket,date) 마커로 그날 항목을 찾아 **없으면 생성, 있으면 시간 갱신**한다
(insert-once 아님) — sync/중간 등록 시 그날 늘어난 시간이 반영되도록. 마커가 actor 를
구분하지 못하므로 **현재 사용자(accountId)가 author 인 worklog 만** 대상으로 삼아 타인의
worklog 를 덮지 않는다(get_myself 로 accountId 확보). 갱신은 기존 comment 를 그대로
재전송해 마커·수동편집을 보존한다.
"""

from __future__ import annotations

from .jira_client import JiraConfig, JiraError, add_worklog, update_worklog
from .markers import find_worklogs_by_marker, worklog_marker
from .worklog_core import DayWorklog


def upsert_worklog(
    config_jira: JiraConfig,
    ticket: str,
    day: DayWorklog,
    existing_worklogs: list[dict],
    my_account_id: str | None,
    note_parts: tuple[str | None, ...] = (),
) -> str:
    """그날 worklog 를 현재 사용자 것만 골라 upsert. 반환 'created'|'updated'|'unchanged'.

    내 것 0개→생성, 1개→시간 다르면 갱신·같으면 unchanged, **2개+→중복이라 JiraError 로 중단**
    (첫 개만 갱신하면 나머지 dup 이 이중계상). 타 사용자 worklog(같은 마커·다른 author)는 무시.

    my_account_id 가 falsy 면(get_myself 응답 이상) author 대조가 무력화되어 타인 worklog 갱신·
    중복 생성 위험이 있으므로 중단한다(billable 이중계상/hijack 방지).
    """
    if not my_account_id:
        raise JiraError(
            f"현재 사용자 accountId 확인 불가 ({ticket} {day.day}) — worklog upsert 중단(오귀속 방지)"
        )
    marker = worklog_marker(ticket, day.day)
    mine = [
        w for w in find_worklogs_by_marker(existing_worklogs, marker)
        if isinstance(w.get("author"), dict) and w["author"].get("accountId") == my_account_id
    ]
    seconds = max(day.seconds, 60)

    if len(mine) > 1:
        ids = ", ".join(str(w.get("id")) for w in mine)
        raise JiraError(f"worklog 마커 중복 {len(mine)}건 ({ticket} {day.day}: {ids}) — 수동 정리 필요")

    if not mine:
        comment = "\n".join([*(p for p in note_parts if p), marker])
        add_worklog(config_jira, ticket, seconds, day.started, comment=comment)
        return "created"

    existing = mine[0]
    worklog_id = existing.get("id")
    if not worklog_id:
        raise JiraError(f"worklog id 없음 ({ticket} {day.day}) — 갱신 불가")
    if existing.get("timeSpentSeconds") == seconds:
        return "unchanged"
    # 기존 comment 를 그대로 재전송해 마커·수동편집·타툴 코멘트를 보존(시간만 갱신).
    update_worklog(config_jira, ticket, worklog_id, seconds, day.started,
                   comment_adf=existing.get("comment"))
    return "updated"
