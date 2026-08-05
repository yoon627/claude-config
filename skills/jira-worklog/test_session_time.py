#!/usr/bin/env python3
"""Claude 세션의 줄 단위 cwd 귀속 테스트."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit.session_time import (  # noqa: E402
    SessionFiles,
    ai_worklog_by_date,
    ai_worklogs_by_worktree,
    discover_sessions,
    find_session_files,
    parse_message_events_with_cwd,
    project_slug,
)
from jira_kit.codex_session import find_codex_session_files_for_worktrees  # noqa: E402


UTC = timezone.utc
MAIN = Path("C:/repo")
PARENT = MAIN / ".claude" / "worktrees" / "parent"
NESTED = PARENT / "nested"


def event(timestamp: str, kind: str, cwd: Path) -> str:
    payload = {
        "timestamp": f"2026-08-04T{timestamp}Z",
        "type": kind,
        "cwd": str(cwd),
    }
    if kind == "user":
        payload["message"] = {"content": "request"}
    return json.dumps(payload)


def session_text(*events: str) -> str:
    return "\n".join(events) + "\n"


def codex_meta(cwd: Path) -> str:
    return json.dumps({
        "type": "session_meta",
        "payload": {"cwd": str(cwd)},
    }) + "\n"


def seconds_by_day(days: list) -> int:
    return sum(day.seconds for day in days)


class CwdAttributionTest(unittest.TestCase):
    def test_a_to_b_to_a_intervals_are_not_mixed(self) -> None:
        text = session_text(
            event("09:00:00", "user", PARENT),
            event("09:10:00", "assistant", PARENT),
            event("09:20:00", "user", NESTED),
            event("09:30:00", "assistant", NESTED),
            event("09:40:00", "assistant", PARENT),
            event("09:50:00", "user", PARENT),
            event("10:00:00", "assistant", PARENT),
        )

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(text, encoding="utf-8")
            files = SessionFiles(claude=[path], codex=[])
            result = ai_worklogs_by_worktree(files, [PARENT, NESTED], UTC)

        self.assertEqual(seconds_by_day(result[str(PARENT.resolve())]), 20 * 60)
        self.assertEqual(seconds_by_day(result[str(NESTED.resolve())]), 10 * 60)
        self.assertEqual(
            sum(seconds_by_day(days) for days in result.values()),
            30 * 60,
        )

    def test_longest_worktree_prefix_wins(self) -> None:
        text = session_text(
            event("09:00:00", "user", NESTED / "skills"),
            event("09:10:00", "assistant", NESTED / "skills"),
            event("09:20:00", "user", PARENT / "skills"),
            event("09:30:00", "assistant", PARENT / "skills"),
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(text, encoding="utf-8")
            result = ai_worklogs_by_worktree(
                SessionFiles(claude=[path], codex=[]), [PARENT, NESTED], UTC
            )

        self.assertEqual(seconds_by_day(result[str(NESTED.resolve())]), 10 * 60)
        self.assertEqual(seconds_by_day(result[str(PARENT.resolve())]), 10 * 60)

    def test_single_worktree_keeps_existing_interval_rules(self) -> None:
        text = session_text(
            event("09:00:00", "user", PARENT),
            event("09:10:00", "assistant", PARENT),
            event("09:20:00", "user", PARENT),
            event("09:30:00", "assistant", PARENT),
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(text, encoding="utf-8")
            session_files = SessionFiles(claude=[path], codex=[])
            result = ai_worklog_by_date(
                session_files,
                UTC,
                cwd=PARENT,
                worktree_paths=[PARENT],
            )

        self.assertEqual(seconds_by_day(result), 20 * 60)

    def test_message_parser_preserves_cwd_and_role(self) -> None:
        text = session_text(
            event("09:00:00", "user", PARENT),
            event("09:10:00", "assistant", PARENT),
        )

        parsed = parse_message_events_with_cwd(text, UTC)

        self.assertEqual(parsed, [
            (datetime(2026, 8, 4, 9, 0, tzinfo=UTC), "user", str(PARENT)),
            (datetime(2026, 8, 4, 9, 10, tzinfo=UTC), "assistant", str(PARENT)),
        ])

    def test_find_session_files_scans_related_project_slugs_once(self) -> None:
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            projects = home / ".claude" / "projects"
            projects.mkdir(parents=True)
            main_slug = project_slug(MAIN)
            related = projects / f"{main_slug}--claude-worktrees-parent"
            unrelated = projects / "C--other-repo"
            related.mkdir()
            unrelated.mkdir()
            expected = related / "session.jsonl"
            expected.write_text("{}\n", encoding="utf-8")
            (unrelated / "session.jsonl").write_text("{}\n", encoding="utf-8")

            files = find_session_files(
                PARENT,
                home,
                worktree_paths=[MAIN, PARENT],
            )

        self.assertEqual(files, [expected])

    def test_discovered_sessions_keep_the_current_worktree_target(self) -> None:
        text = session_text(
            event("09:00:00", "user", PARENT),
            event("09:10:00", "assistant", PARENT),
            event("09:20:00", "user", MAIN),
            event("09:30:00", "assistant", MAIN),
        )
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            projects = home / ".claude" / "projects" / project_slug(PARENT)
            projects.mkdir(parents=True)
            (projects / "session.jsonl").write_text(text, encoding="utf-8")

            files = discover_sessions(
                PARENT,
                home,
                worktree_paths=[MAIN, PARENT],
            )
            result = ai_worklog_by_date(files, UTC)

        self.assertEqual(files.target, str(PARENT.resolve()))
        self.assertEqual(seconds_by_day(result), 10 * 60)

    def test_codex_discovery_matches_all_worktree_roots(self) -> None:
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            sessions = home / ".codex" / "sessions" / "2026" / "08" / "04"
            sessions.mkdir(parents=True)
            parent_rollout = sessions / "rollout-parent.jsonl"
            nested_rollout = sessions / "rollout-nested.jsonl"
            unrelated_rollout = sessions / "rollout-unrelated.jsonl"
            parent_rollout.write_text(codex_meta(PARENT / "skills"), encoding="utf-8")
            nested_rollout.write_text(codex_meta(NESTED), encoding="utf-8")
            unrelated_rollout.write_text(codex_meta(Path("C:/other")), encoding="utf-8")

            files = find_codex_session_files_for_worktrees(
                [str(PARENT), str(NESTED)],
                home,
            )

        self.assertCountEqual(files, [parent_rollout, nested_rollout])


if __name__ == "__main__":
    unittest.main()
