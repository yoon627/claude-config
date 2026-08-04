"""(ticket, date, worktree) worklog 의 upsert 오케스트레이션 (jira_client + markers 위, 순수 조립).

worklog 는 (ticket, date, worktree) 마커로 그 worktree 의 그날 항목을 찾아 **없으면 생성,
있으면 시간 갱신**한다(insert-once 아님) — sync/중간 등록 시 그날 늘어난 시간이 반영되도록.
같은 티켓의 다른 worktree 는 마커가 달라 서로 건드리지 않고, 티켓 총 작업시간은 Jira 가
worklog 항목을 합산한다. 마커가 actor 를 구분하지 못하므로 **현재 사용자(accountId)가 author 인
worklog 만** 대상으로 삼아 타인의 worklog 를 덮지 않는다(get_myself 로 accountId 확보).
갱신은 기존 comment 를 그대로 재전송해 마커·수동편집을 보존한다.
"""

from __future__ import annotations

from dataclasses import dataclass

from .jira_client import JiraConfig, JiraError, add_worklog, update_worklog
from .markers import adf_lines, find_worklogs_by_marker, legacy_worklog_marker, worklog_marker
from .worklog_core import DayWorklog


def _mine(worklogs: list[dict], marker: str, my_account_id: str) -> list[dict]:
    return [
        w for w in find_worklogs_by_marker(worklogs, marker)
        if isinstance(w.get("author"), dict) and w["author"].get("accountId") == my_account_id
    ]


MIN_SECONDS = 60  # Jira 최소 기록 단위 — 비교는 이 하한을 적용한 뒤에 한다


@dataclass(frozen=True)
class PlannedChange:
    """등록 전에 계산한 변경 1건. mutation 없이 diff·게이트 판정에 쓴다."""

    day: DayWorklog
    action: str  # created | updated | unchanged
    new_seconds: int
    old_seconds: int | None = None
    worklog_id: str | None = None
    rival_worktrees: tuple[str, ...] = ()  # 같은 (ticket,날짜)의 내 **다른** worktree 마커

    @property
    def delta(self) -> int:
        return self.new_seconds - (self.old_seconds or 0)


def _rival_worktrees(worklogs: list[dict], ticket: str, day, worktree: str, me: str) -> tuple[str, ...]:
    """같은 (ticket, 날짜)에 달린 **내** worklog 중 다른 worktree 마커의 이름들.

    worktree 를 rename 하면 마커가 안 잡혀 `created` 로 새 항목이 생기고, old 가 없으니 감소
    게이트도 침묵한다 — 결과는 조용한 이중계상이다. 그 신호가 이 목록이다.
    """
    prefix = legacy_worklog_marker(ticket, day) + " ("
    mine_marker = worklog_marker(ticket, day, worktree)
    found = []
    for w in worklogs:
        if not (isinstance(w.get("author"), dict) and w["author"].get("accountId") == me):
            continue
        if w.get("comment") is None:
            continue
        for line in adf_lines(w["comment"]):
            line = line.strip()
            if line.startswith(prefix) and line.endswith(")") and line != mine_marker:
                found.append(line[len(prefix):-1])
    return tuple(sorted(set(found)))


def plan_worklog_changes(
    ticket: str,
    worktree: str,
    days: list[DayWorklog],
    existing_worklogs: list[dict],
    my_account_id: str | None,
) -> list[PlannedChange]:
    """전 날짜의 변경을 **먼저 전부** 계산한다(mutation 없음).

    날짜 루프 안에서 곧바로 upsert 하면 뒷 날짜가 게이트에 걸려도 앞 날짜는 이미 Jira 에 반영된
    채 중단된다 — Jira 쓰기는 코드 revert 로 되돌릴 수 없으므로 all-or-nothing 이어야 한다.
    """
    if not my_account_id:
        raise JiraError("현재 사용자 accountId 확인 불가 — 등록 계획 중단(오귀속 방지)")
    plans = []
    for day in days:
        marker = worklog_marker(ticket, day.day, worktree)
        # upsert 의 사전 검사를 **여기서 먼저** 한다. mutation 단계에서 처음 터지면 앞 날짜는
        # 이미 Jira 에 쓰인 뒤라 all-or-nothing 이 깨지고, diff 도 그 날짜를 created 로 잘못 보인다.
        legacy = _mine(existing_worklogs, legacy_worklog_marker(ticket, day.day), my_account_id)
        if legacy:
            ids = ", ".join(str(w.get("id")) for w in legacy)
            raise JiraError(
                f"worktree 없는 구 형식 worklog {len(legacy)}건 ({ticket} {day.day}: {ids}) — "
                f'귀속 worktree 를 알 수 없어 중단. 마커 줄을 정확히 "{marker}" 로 바꾸면 이 '
                f"worktree 항목으로 흡수된다(시간은 이번 계산값으로 치환)"
            )
        mine = _mine(existing_worklogs, marker, my_account_id)
        if len(mine) > 1:
            ids = ", ".join(str(w.get("id")) for w in mine)
            raise JiraError(
                f"worklog 마커 중복 {len(mine)}건 ({ticket} {day.day} {worktree}: {ids}) — 수동 정리 필요"
            )
        seconds = max(day.seconds, MIN_SECONDS)
        rivals = _rival_worktrees(existing_worklogs, ticket, day.day, worktree, my_account_id)
        if not mine:
            plans.append(PlannedChange(day, "created", seconds, rival_worktrees=rivals))
            continue
        old = mine[0].get("timeSpentSeconds")
        worklog_id = mine[0].get("id")
        # upsert 는 시간 비교 **전에** id 를 본다. 조건을 다르게 두면(예: 갱신이 필요할 때만 검사)
        # plan 은 unchanged 로 통과시키고 mutation 에서 처음 터져 앞 날짜가 이미 쓰인다.
        if not worklog_id:
            raise JiraError(f"worklog id 없음 ({ticket} {day.day}) — 갱신 불가")
        action = "unchanged" if old == seconds else "updated"
        plans.append(PlannedChange(day, action, seconds, old, worklog_id, rivals))
    return plans


def gate_reasons(
    changes: list[PlannedChange], *, ratio: float = 0.5, floor_seconds: int = 1800
) -> list[str]:
    """등록을 막아야 할 이유들(빈 리스트면 통과). **순수 함수** — 네트워크·상태 없음.

    ① 큰 폭 변동은 **증가·감소 양쪽** 모두 막는다. 이번 변경의 정상 방향은 과다분 감소지만,
       매핑 버그의 대표 증상도 과다 흡수라 방향만으로는 구분되지 않는다. billable 에서는 과다
       등록이 과소보다 위험하다.
    ② rename 으로 마커를 놓쳐 새 항목을 만드는 경우 — old 가 없어 ①이 침묵하는 사각지대다.
    비율과 절대값을 **둘 다** 넘을 때만 막는다(작은 값의 큰 비율 변동으로 매번 걸리지 않게).
    """
    reasons = []
    for c in changes:
        if c.action == "updated" and c.old_seconds:
            delta = abs(c.delta)
            if delta >= floor_seconds and delta / c.old_seconds > ratio:
                direction = "증가" if c.delta > 0 else "감소"
                reasons.append(
                    f"{c.day.day}: {c.old_seconds // 60}m → {c.new_seconds // 60}m "
                    f"({direction} {delta // 60}m)"
                )
        if c.action == "created" and c.rival_worktrees:
            reasons.append(
                f"{c.day.day}: 같은 날 내 다른 worktree 항목({', '.join(c.rival_worktrees)})이 "
                f"있는데 이 worktree 마커는 없음. worktree rename 이면 새로 만들 때 이중계상되고, "
                f"두 worktree 를 같은 날 병렬로 돌린 정상 상황이면 그대로 진행하면 된다 "
                f"(둘을 구분할 근거가 없어 사람에게 넘긴다)"
            )
    return reasons


def upsert_worklog(
    config_jira: JiraConfig,
    ticket: str,
    day: DayWorklog,
    existing_worklogs: list[dict],
    my_account_id: str | None,
    *,
    worktree: str,
    note_parts: tuple[str | None, ...] = (),
) -> str:
    """그 worktree 의 그날 worklog 를 현재 사용자 것만 골라 upsert.

    반환 'created'|'updated'|'unchanged'. 내 것 0개→생성, 1개→시간 다르면 갱신·같으면 unchanged,
    **2개+→중복이라 JiraError 로 중단**(첫 개만 갱신하면 나머지 dup 이 이중계상). 타 사용자
    worklog(같은 마커·다른 author)는 무시.

    my_account_id 가 falsy 면(get_myself 응답 이상) author 대조가 무력화되어 타인 worklog 갱신·
    중복 생성 위험이 있으므로 중단한다(billable 이중계상/hijack 방지).

    worktree 없는 구 형식 마커의 **본인** 항목이 남아 있으면 중단한다 — 그 항목이 어느 worktree
    것인지 알 수 없어, 새로 만들면 이중계상되고 흡수하면 그 worktree 시간이 부풀기 때문이다.
    """
    if not my_account_id:
        raise JiraError(
            f"현재 사용자 accountId 확인 불가 ({ticket} {day.day}) — worklog upsert 중단(오귀속 방지)"
        )
    marker = worklog_marker(ticket, day.day, worktree)
    legacy = _mine(existing_worklogs, legacy_worklog_marker(ticket, day.day), my_account_id)
    if legacy:
        ids = ", ".join(str(w.get("id")) for w in legacy)
        raise JiraError(
            f"worktree 없는 구 형식 worklog {len(legacy)}건 ({ticket} {day.day}: {ids}) — "
            f"귀속 worktree 를 알 수 없어 중단. Jira 에서 그 항목의 마커 줄을 정확히 "
            f'"{marker}" 로 바꾸면 이 worktree 항목으로 흡수된다(단 시간이 이번 계산값으로 '
            f"치환되니 다른 worktree 몫이 섞여 있으면 먼저 나눠라). 항목을 지우면 그 시간은 "
            f"사라진다. 어중간하게 덧붙이면 어느 마커와도 일치하지 않아 새 항목이 생겨 "
            f"이중계상된다"
        )
    mine = _mine(existing_worklogs, marker, my_account_id)
    seconds = max(day.seconds, MIN_SECONDS)

    if len(mine) > 1:
        ids = ", ".join(str(w.get("id")) for w in mine)
        raise JiraError(
            f"worklog 마커 중복 {len(mine)}건 ({ticket} {day.day} {worktree}: {ids}) — 수동 정리 필요"
        )

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
