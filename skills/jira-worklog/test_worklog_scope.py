#!/usr/bin/env python3
"""worklog upsert 의 worktree scope 격리 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_worklog_scope.py

점검 대상 불변식: 같은 티켓의 worktree 가 여럿이어도 각자 자기 worklog 항목만 만지고
서로의 시간을 덮지 않는다. 마커 매칭은 ADF 문단(줄) 정확일치라 사용자 코멘트에 마커와
같은 문자열이 섞여도 오매치하지 않는다. worktree 없는 구 마커 항목은 귀속이 모호하므로
중단한다.

Jira 는 호출하지 않는다 — ``add_worklog``/``update_worklog`` 를 patch 하고, 기존 worklog
목록은 ``adf_from_text`` 로 만든 **실제 ADF** 를 써서 문단 연결 경로까지 통과시킨다.
"""

from __future__ import annotations

import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit import worklog_register  # noqa: E402
from jira_kit.jira_client import JiraConfig, JiraError, adf_from_text  # noqa: E402
from jira_kit.markers import (  # noqa: E402
    adf_lines,
    find_worklogs_by_marker,
    legacy_worklog_marker,
    worklog_marker,
)
from jira_kit.worklog_core import DayWorklog  # noqa: E402

TICKET = "CSTP1-1234"
DAY = date(2026, 7, 22)
ME = "account-me"
OTHER = "account-other"
CONFIG = JiraConfig(base_url="https://example.atlassian.net", email="me@example.com", token="x")


def day_worklog(hours: float) -> DayWorklog:
    started = datetime(2026, 7, 22, 9, 0, tzinfo=timezone(timedelta(hours=9)))
    return DayWorklog(day=DAY, seconds=int(hours * 3600), started=started)


def worklog(comment_text: str, *, seconds: int, author: str = ME, id_: str = "1") -> dict:
    """Jira 가 돌려주는 worklog 항목 모양(코멘트는 실제 ADF)."""
    return {
        "id": id_,
        "author": {"accountId": author},
        "timeSpentSeconds": seconds,
        "comment": adf_from_text(comment_text),
    }


def entry_for(worktree: str, *, seconds: int, author: str = ME, id_: str = "1",
              note: str | None = None) -> dict:
    """worklog_register 가 만드는 것과 같은 코멘트 구조의 기존 항목."""
    marker = worklog_marker(TICKET, DAY, worktree)
    text = f"{note}\n{marker}" if note else marker
    return worklog(text, seconds=seconds, author=author, id_=id_)


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def doc(*blocks: dict) -> dict:
    return {"type": "doc", "version": 1, "content": list(blocks)}


class AdfLinesTest(unittest.TestCase):
    """Jira UI 편집으로 생기는 ADF 변형에서도 마커 줄을 놓치지 않아야 한다.

    마커를 **놓치면** 새 항목이 생겨 그날 시간이 이중계상된다 — 오매치와 달리 조용하므로
    이 방향의 회귀가 더 위험하다.
    """

    MARKER = worklog_marker(TICKET, DAY, "CSTP1-1234-abc")

    def assert_finds(self, comment: dict) -> None:
        self.assertEqual(
            find_worklogs_by_marker([{"comment": comment}], self.MARKER),
            [{"comment": comment}],
        )

    def test_adf_from_text_roundtrip(self) -> None:
        self.assertEqual(
            adf_lines(adf_from_text(f"메모\n\n{self.MARKER}")), ["메모", "", self.MARKER]
        )

    def test_hard_break_splits_a_paragraph_into_lines(self) -> None:
        """UI 에서 Shift+Enter 로 줄을 더하면 한 문단 안에 hardBreak 이 들어간다."""
        comment = doc({
            "type": "paragraph",
            "content": [text("메모"), {"type": "hardBreak"}, text(self.MARKER)],
        })
        self.assertEqual(adf_lines(comment), ["메모", self.MARKER])
        self.assert_finds(comment)

    def test_code_block_and_heading_are_text_blocks(self) -> None:
        for block_type in ("codeBlock", "heading"):
            with self.subTest(block_type):
                comment = doc({"type": block_type, "content": [text(self.MARKER)]})
                self.assert_finds(comment)

    def test_marker_inside_list_item(self) -> None:
        comment = doc({
            "type": "bulletList",
            "content": [{
                "type": "listItem",
                "content": [{"type": "paragraph", "content": [text(self.MARKER)]}],
            }],
        })
        self.assert_finds(comment)

    def test_marks_split_text_nodes_are_rejoined(self) -> None:
        head, tail = self.MARKER[:10], self.MARKER[10:]
        comment = doc({
            "type": "paragraph",
            "content": [
                {"type": "text", "text": head, "marks": [{"type": "strong"}]},
                text(tail),
            ],
        })
        self.assert_finds(comment)

    def test_surrounding_whitespace_is_ignored(self) -> None:
        self.assert_finds(doc({"type": "paragraph", "content": [text(f"  {self.MARKER} ")]}))

    def test_paragraph_without_content_yields_empty_line(self) -> None:
        self.assertEqual(adf_lines(doc({"type": "paragraph"})), [""])

    def test_non_adf_comment_is_not_matched(self) -> None:
        self.assertEqual(find_worklogs_by_marker([{"comment": self.MARKER}], self.MARKER), [])


class UpsertScopeTest(unittest.TestCase):
    def setUp(self) -> None:
        add = mock.patch.object(worklog_register, "add_worklog")
        update = mock.patch.object(worklog_register, "update_worklog")
        self.add_worklog = add.start()
        self.update_worklog = update.start()
        self.addCleanup(add.stop)
        self.addCleanup(update.stop)

    def upsert(self, worktree: str, day: DayWorklog, existing: list[dict],
               account_id: str | None = ME, **kwargs) -> str:
        return worklog_register.upsert_worklog(
            CONFIG, TICKET, day, existing, account_id, worktree=worktree, **kwargs
        )

    def test_other_worktree_entry_is_not_overwritten(self) -> None:
        """다른 worktree 항목이 있어도 새로 만들 뿐 그 항목을 갱신하지 않는다."""
        existing = [entry_for("CSTP1-1234-abc", seconds=2 * 3600)]

        result = self.upsert("CSTP1-1234-def", day_worklog(3), existing)

        self.assertEqual(result, "created")
        self.add_worklog.assert_called_once()
        self.update_worklog.assert_not_called()

    def test_created_comment_carries_own_scope_marker(self) -> None:
        self.upsert("CSTP1-1234-def", day_worklog(3), [])

        comment = self.add_worklog.call_args.kwargs["comment"]
        self.assertIn(worklog_marker(TICKET, DAY, "CSTP1-1234-def"), comment.splitlines())

    def test_same_worktree_rerun_updates_only_its_entry(self) -> None:
        existing = [
            entry_for("CSTP1-1234-abc", seconds=2 * 3600, id_="abc-1"),
            entry_for("CSTP1-1234-def", seconds=1 * 3600, id_="def-1"),
        ]

        result = self.upsert("CSTP1-1234-def", day_worklog(3), existing)

        self.assertEqual(result, "updated")
        self.add_worklog.assert_not_called()
        self.assertEqual(self.update_worklog.call_args.args[2], "def-1")

    def test_same_worktree_same_seconds_is_unchanged(self) -> None:
        existing = [entry_for("CSTP1-1234-def", seconds=3 * 3600)]

        result = self.upsert("CSTP1-1234-def", day_worklog(3), existing)

        self.assertEqual(result, "unchanged")
        self.add_worklog.assert_not_called()
        self.update_worklog.assert_not_called()

    def test_marker_embedded_in_a_longer_line_is_not_matched(self) -> None:
        """마커가 **줄 일부**로만 들어 있는 항목을 자기 것으로 오인하지 않는다.

        사용자 `--comment` 나 Jira UI 수동 편집으로 생길 수 있는 형태다. 줄 정확일치라
        본문 줄과 구분된다(부분문자열 매칭으로 되돌리면 이 테스트가 Red).
        """
        marker = worklog_marker(TICKET, DAY, "CSTP1-1234-def")
        for body in (f"참고: {marker} 로 기록됨", f"{marker}-2", f"x{marker}"):
            with self.subTest(body):
                self.add_worklog.reset_mock()
                self.update_worklog.reset_mock()
                existing = [worklog(body, seconds=2 * 3600, id_="note-1")]

                result = self.upsert("CSTP1-1234-def", day_worklog(3), existing)

                self.assertEqual(result, "created")
                self.update_worklog.assert_not_called()

    def test_other_author_entry_is_ignored(self) -> None:
        existing = [entry_for("CSTP1-1234-def", seconds=2 * 3600, author=OTHER)]

        result = self.upsert("CSTP1-1234-def", day_worklog(3), existing)

        self.assertEqual(result, "created")
        self.update_worklog.assert_not_called()

    def test_duplicate_own_markers_abort(self) -> None:
        existing = [
            entry_for("CSTP1-1234-def", seconds=2 * 3600, id_="a"),
            entry_for("CSTP1-1234-def", seconds=1 * 3600, id_="b"),
        ]

        with self.assertRaises(JiraError):
            self.upsert("CSTP1-1234-def", day_worklog(3), existing)
        self.add_worklog.assert_not_called()
        self.update_worklog.assert_not_called()

    def test_missing_account_id_aborts(self) -> None:
        with self.assertRaises(JiraError):
            self.upsert("CSTP1-1234-def", day_worklog(3), [], account_id=None)
        self.add_worklog.assert_not_called()


class LegacyMarkerTest(unittest.TestCase):
    """worktree 도입 전 형식(`… <date>`) 항목은 귀속이 모호해 중단한다."""

    def setUp(self) -> None:
        add = mock.patch.object(worklog_register, "add_worklog")
        update = mock.patch.object(worklog_register, "update_worklog")
        self.add_worklog = add.start()
        self.update_worklog = update.start()
        self.addCleanup(add.stop)
        self.addCleanup(update.stop)

    def upsert(self, existing: list[dict]) -> str:
        return worklog_register.upsert_worklog(
            CONFIG, TICKET, day_worklog(3), existing, ME, worktree="CSTP1-1234-def"
        )

    def test_own_legacy_entry_aborts(self) -> None:
        existing = [worklog(legacy_worklog_marker(TICKET, DAY), seconds=2 * 3600, id_="legacy")]

        with self.assertRaises(JiraError) as caught:
            self.upsert(existing)
        self.add_worklog.assert_not_called()
        self.update_worklog.assert_not_called()
        # 안내대로 따라하면 이중계상이 안 되도록, 교체할 정확한 마커를 메시지에 담는다.
        self.assertIn(worklog_marker(TICKET, DAY, "CSTP1-1234-def"), str(caught.exception))

    def test_other_author_legacy_entry_does_not_abort(self) -> None:
        """타인의 구 마커 항목까지 막으면 영구 중단된다."""
        existing = [
            worklog(legacy_worklog_marker(TICKET, DAY), seconds=2 * 3600, author=OTHER,
                    id_="legacy")
        ]

        self.assertEqual(self.upsert(existing), "created")

    def test_scoped_entry_is_not_seen_as_legacy(self) -> None:
        """새 형식 항목은 구 마커를 prefix 로 포함하지만 legacy 로 잡히면 안 된다."""
        existing = [entry_for("CSTP1-1234-def", seconds=3 * 3600)]

        self.assertEqual(self.upsert(existing), "unchanged")


class MarkerValidationTest(unittest.TestCase):
    """빈/개행 worktree 이름은 조용한 이중계상으로 이어지므로 마커 생성에서 막는다."""

    def test_empty_worktree_rejected(self) -> None:
        """빈 이름을 허용하면 구 형식과 같은 마커를 써서 legacy 검사에 자기가 걸린다."""
        with self.assertRaises(ValueError):
            worklog_marker(TICKET, DAY, "")

    def test_newline_in_worktree_rejected(self) -> None:
        """개행이 들어가면 마커가 두 줄로 쪼개져 어떤 줄과도 일치하지 않는다."""
        with self.assertRaises(ValueError):
            worklog_marker(TICKET, DAY, "wt\nbad")


if __name__ == "__main__":
    unittest.main()
