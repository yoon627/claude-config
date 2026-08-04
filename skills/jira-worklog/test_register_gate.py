#!/usr/bin/env python3
"""등록 게이트 단위 테스트 (stdlib unittest, Jira 호출 없음).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_register_gate.py

점검 대상 불변식: Jira 쓰기는 코드 revert 로 되돌릴 수 없다. 그래서
① 전 날짜를 먼저 계산해 부분 등록이 남지 않게 하고(all-or-nothing),
② 큰 폭 변동은 **증가·감소 양쪽** 다 막고(매핑 버그의 대표 증상은 과다 흡수),
③ worktree rename 으로 마커를 놓쳐 새 항목이 생기는 사각지대를 막는다.
"""

from __future__ import annotations

import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit.jira_client import JiraError  # noqa: E402
from jira_kit.markers import worklog_marker  # noqa: E402
from jira_kit.worklog_core import DayWorklog  # noqa: E402
from jira_kit.worklog_register import (  # noqa: E402
    gate_reasons,
    plan_worklog_changes,
)

ME = "acct-me"
TICKET = "CSTP1-1234"
WT = "CSTP1-1234-alpha"
DAY = date(2026, 8, 4)


def day_worklog(seconds: int, when: date = DAY) -> DayWorklog:
    return DayWorklog(day=when, seconds=seconds, started=datetime(2026, 8, 4, 9, tzinfo=timezone.utc))


def worklog(marker: str, seconds: int, author: str = ME, wid: str = "1") -> dict:
    return {
        "id": wid,
        "timeSpentSeconds": seconds,
        "author": {"accountId": author},
        "comment": {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": marker}]}],
        },
    }


class PlanTest(unittest.TestCase):
    def test_no_existing_is_created(self):
        [p] = plan_worklog_changes(TICKET, WT, [day_worklog(600)], [], ME)
        self.assertEqual(p.action, "created")
        self.assertIsNone(p.old_seconds)

    def test_existing_same_seconds_is_unchanged(self):
        existing = [worklog(worklog_marker(TICKET, DAY, WT), 600)]
        [p] = plan_worklog_changes(TICKET, WT, [day_worklog(600)], existing, ME)
        self.assertEqual(p.action, "unchanged")

    def test_existing_different_is_updated_with_old_value(self):
        existing = [worklog(worklog_marker(TICKET, DAY, WT), 600)]
        [p] = plan_worklog_changes(TICKET, WT, [day_worklog(1200)], existing, ME)
        self.assertEqual((p.action, p.old_seconds, p.new_seconds), ("updated", 600, 1200))
        self.assertEqual(p.worklog_id, "1")

    def test_seconds_floor_applied_before_compare(self):
        # 60초 하한을 비교 전에 적용하지 않으면 유령 diff 가 난다.
        existing = [worklog(worklog_marker(TICKET, DAY, WT), 60)]
        [p] = plan_worklog_changes(TICKET, WT, [day_worklog(5)], existing, ME)
        self.assertEqual(p.action, "unchanged")

    def test_other_author_is_ignored(self):
        existing = [worklog(worklog_marker(TICKET, DAY, WT), 600, author="someone-else")]
        [p] = plan_worklog_changes(TICKET, WT, [day_worklog(600)], existing, ME)
        self.assertEqual(p.action, "created")  # 남의 것은 건드리지 않는다

    def test_missing_account_id_aborts(self):
        with self.assertRaises(JiraError):
            plan_worklog_changes(TICKET, WT, [day_worklog(600)], [], None)

    def test_rival_worktree_marker_is_collected(self):
        existing = [worklog(worklog_marker(TICKET, DAY, "CSTP1-1234-beta"), 600)]
        [p] = plan_worklog_changes(TICKET, WT, [day_worklog(600)], existing, ME)
        self.assertEqual(p.rival_worktrees, ("CSTP1-1234-beta",))


class PreconditionTest(unittest.TestCase):
    """upsert 가 던지는 조건은 **계획 단계에서** 잡아야 한다.

    mutation 루프에서 처음 터지면 앞 날짜는 이미 Jira 에 쓰인 뒤라 부분 등록이 남는다.
    """

    def test_legacy_marker_aborts_before_any_write(self):
        from jira_kit.markers import legacy_worklog_marker

        existing = [worklog(legacy_worklog_marker(TICKET, DAY), 600)]
        with self.assertRaises(JiraError):
            plan_worklog_changes(TICKET, WT, [day_worklog(600)], existing, ME)

    def test_duplicate_marker_aborts(self):
        marker = worklog_marker(TICKET, DAY, WT)
        existing = [worklog(marker, 600, wid="1"), worklog(marker, 900, wid="2")]
        with self.assertRaises(JiraError):
            plan_worklog_changes(TICKET, WT, [day_worklog(600)], existing, ME)

    def test_missing_worklog_id_aborts_when_update_needed(self):
        existing = [worklog(worklog_marker(TICKET, DAY, WT), 600, wid="1")]
        del existing[0]["id"]
        with self.assertRaises(JiraError):
            plan_worklog_changes(TICKET, WT, [day_worklog(1200)], existing, ME)

    def test_later_day_precondition_blocks_earlier_day_too(self):
        # 핵심: 2일차가 막히면 1일차도 쓰이지 않아야 한다.
        from jira_kit.markers import legacy_worklog_marker

        d1, d2 = date(2026, 8, 3), date(2026, 8, 4)
        existing = [
            worklog(worklog_marker(TICKET, d1, WT), 600, wid="1"),
            worklog(legacy_worklog_marker(TICKET, d2), 600, wid="2"),
        ]
        with self.assertRaises(JiraError):
            plan_worklog_changes(
                TICKET, WT, [day_worklog(700, d1), day_worklog(700, d2)], existing, ME
            )


class GateTest(unittest.TestCase):
    def existing_update(self, old: int, new: int):
        existing = [worklog(worklog_marker(TICKET, DAY, WT), old)]
        return plan_worklog_changes(TICKET, WT, [day_worklog(new)], existing, ME)

    def test_small_change_passes(self):
        self.assertEqual(gate_reasons(self.existing_update(3600, 4200)), [])

    def test_large_decrease_blocks(self):
        reasons = gate_reasons(self.existing_update(7200, 1800))
        self.assertEqual(len(reasons), 1)
        self.assertIn("감소", reasons[0])

    def test_large_increase_blocks_too(self):
        # 매핑 버그의 대표 증상은 과다 흡수다 — 방향만으로 안전을 판단할 수 없다.
        reasons = gate_reasons(self.existing_update(1800, 7200))
        self.assertEqual(len(reasons), 1)
        self.assertIn("증가", reasons[0])

    def test_big_ratio_but_tiny_absolute_passes(self):
        # 5분 → 15분은 비율은 크지만 절대값이 작다. 매번 걸리면 게이트가 무시된다.
        self.assertEqual(gate_reasons(self.existing_update(300, 900)), [])

    def test_created_with_rival_worktree_blocks(self):
        existing = [worklog(worklog_marker(TICKET, DAY, "CSTP1-1234-beta"), 600)]
        plans = plan_worklog_changes(TICKET, WT, [day_worklog(600)], existing, ME)
        reasons = gate_reasons(plans)
        self.assertEqual(len(reasons), 1)
        self.assertIn("beta", reasons[0])

    def test_created_without_rival_passes(self):
        self.assertEqual(gate_reasons(plan_worklog_changes(TICKET, WT, [day_worklog(600)], [], ME)), [])

    def test_gate_sees_all_days_before_any_write(self):
        # 마지막 날짜만 임계를 넘겨도 전체가 막혀야 한다(부분 등록 방지).
        d1, d2 = date(2026, 8, 3), date(2026, 8, 4)
        existing = [
            worklog(worklog_marker(TICKET, d1, WT), 3600, wid="1"),
            worklog(worklog_marker(TICKET, d2, WT), 7200, wid="2"),
        ]
        plans = plan_worklog_changes(
            TICKET, WT, [day_worklog(3700, d1), day_worklog(600, d2)], existing, ME
        )
        self.assertEqual(len(plans), 2)
        self.assertTrue(gate_reasons(plans))


if __name__ == "__main__":
    unittest.main(verbosity=2)
