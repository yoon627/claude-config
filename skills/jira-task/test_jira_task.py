#!/usr/bin/env python3
"""Unit tests for the Jira task comment skill."""

from __future__ import annotations

import contextlib
import io
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest import mock

import jira_task
from jira_task import JiraConfig, JiraTaskError


CONFIG = JiraConfig(
    base_url="https://example.atlassian.net",
    email="email-placeholder",
    token="<redacted>",
)
MARKER = "[jira-task] ticket=CSTP1-1234 date=2026-08-13 worktree=demo session=manual"


def comment(comment_id: str, author: str, text: str) -> dict:
    return {
        "id": comment_id,
        "author": {"accountId": author},
        "body": jira_task.adf_from_text(text),
    }


class FormattingTests(unittest.TestCase):
    def test_adf_round_trip_preserves_marker_line(self) -> None:
        body = jira_task.adf_from_text(f"작업 내용\n본문\n\n{MARKER}")

        self.assertEqual(jira_task.adf_lines(body), ["작업 내용", "본문", "", MARKER])
        self.assertTrue(jira_task.comment_has_marker({"body": body}, MARKER))

    def test_hard_break_is_a_line_boundary(self) -> None:
        body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "앞"},
                        {"type": "hardBreak"},
                        {"type": "text", "text": MARKER},
                    ],
                }
            ],
        }

        self.assertEqual(jira_task.adf_lines(body), ["앞", MARKER])
        self.assertTrue(jira_task.comment_has_marker({"body": body}, MARKER))

    def test_build_comment_rejects_reserved_marker_in_summary(self) -> None:
        args = jira_task.parse_args(["--ticket", "CSTP1-1234", "--summary", MARKER])

        with self.assertRaisesRegex(JiraTaskError, "예약된"):
            jira_task._summary_from_args(args)

    def test_summary_rejects_secret_like_text(self) -> None:
        args = jira_task.parse_args(
            ["--ticket", "CSTP1-1234", "--summary", "JIRA_API_TOKEN ="]
        )

        with self.assertRaisesRegex(JiraTaskError, "credential"):
            jira_task._summary_from_args(args)

    def test_ticket_inference_prefers_worktree_prefix(self) -> None:
        self.assertEqual(
            jira_task.infer_ticket(
                "CSTP1-1234-summary",
                "feature/CSTP1-9999",
                jira_task.DEFAULT_TICKET_PATTERN,
            ),
            "CSTP1-1234",
        )


class ConfigurationTests(unittest.TestCase):
    def test_environment_overrides_project_and_global_env(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "repo"
            project.mkdir()
            (project / ".env").write_text(
                "JIRA_BASE_URL=https://project.example\nJIRA_API_TOKEN=PROJECT\n",
                encoding="utf-8",
            )
            global_dir = root / "global"
            global_dir.mkdir()
            (global_dir / ".env").write_text(
                "JIRA_BASE_URL=https://global.example\nJIRA_EMAIL=global-placeholder\nJIRA_API_TOKEN=GLOBAL\n",
                encoding="utf-8",
            )

            settings = jira_task.load_settings(
                project,
                environ={
                    "JIRA_BASE_URL": "https://env.example",
                    "JIRA_EMAIL": "env-placeholder",
                },
                global_dir=global_dir,
            )

        self.assertEqual(settings.get("JIRA_BASE_URL"), "https://env.example")
        self.assertEqual(settings.get("JIRA_EMAIL"), "env-placeholder")
        self.assertEqual(settings.get("JIRA_API_TOKEN"), "PROJECT")

    def test_jira_config_rejects_plain_http(self) -> None:
        settings = jira_task.Settings(
            {
                "JIRA_BASE_URL": "http://example.atlassian.net",
                "JIRA_EMAIL": "email-placeholder",
                "JIRA_API_TOKEN": "<redacted>",
            }
        )

        with self.assertRaisesRegex(jira_task.ConfigError, "https URL"):
            jira_task.make_jira_config(settings)


class ApiTests(unittest.TestCase):
    @mock.patch.object(jira_task, "_request")
    def test_get_comments_follows_pagination(self, request: mock.Mock) -> None:
        request.side_effect = [
            {"comments": [{"id": "1"}], "total": 2},
            {"comments": [{"id": "2"}], "total": 2},
        ]

        result = jira_task.get_comments(CONFIG, "CSTP1-1234")

        self.assertEqual([item["id"] for item in result], ["1", "2"])
        self.assertIn("startAt=0", request.call_args_list[0].args[2])
        self.assertIn("startAt=1", request.call_args_list[1].args[2])

    @mock.patch.object(jira_task, "_request")
    def test_add_comment_uses_adf_body_and_issue_key_path(
        self, request: mock.Mock
    ) -> None:
        request.return_value = {"id": "42"}

        result = jira_task.add_comment(CONFIG, "CSTP1-1234", "작업 내용")

        self.assertEqual(result["id"], "42")
        self.assertEqual(request.call_args.args[1], "POST")
        self.assertIn("/issue/CSTP1-1234/comment", request.call_args.args[2])
        self.assertEqual(request.call_args.args[3]["body"]["type"], "doc")

    @mock.patch.object(jira_task.urllib.request, "urlopen")
    def test_http_error_redacts_credentials(self, urlopen: mock.Mock) -> None:
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.atlassian.net/rest/api/3/issue/CSTP1-1234/comment",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b"<redacted> email-placeholder"),
        )

        with self.assertRaises(JiraTaskError) as raised:
            jira_task.add_comment(CONFIG, "CSTP1-1234", "작업")
        self.assertNotIn("<redacted>", str(raised.exception))
        self.assertNotIn("email-placeholder", str(raised.exception))


class UpsertTests(unittest.TestCase):
    @mock.patch.object(jira_task, "add_comment")
    @mock.patch.object(jira_task, "get_comments")
    @mock.patch.object(jira_task, "get_myself")
    def test_missing_marker_creates_comment(
        self, myself: mock.Mock, comments: mock.Mock, add: mock.Mock
    ) -> None:
        myself.return_value = {"accountId": "me"}
        comments.return_value = []
        add.return_value = {"id": "new"}

        action, result = jira_task.upsert_comment(CONFIG, "CSTP1-1234", "본문", MARKER)

        self.assertEqual((action, result["id"]), ("created", "new"))
        add.assert_called_once_with(CONFIG, "CSTP1-1234", "본문", timeout=15.0)

    @mock.patch.object(jira_task, "update_comment")
    @mock.patch.object(jira_task, "get_comments")
    @mock.patch.object(jira_task, "get_myself")
    def test_own_marker_updates_comment(
        self, myself: mock.Mock, comments: mock.Mock, update: mock.Mock
    ) -> None:
        myself.return_value = {"accountId": "me"}
        comments.return_value = [comment("7", "me", f"old\n{MARKER}")]
        update.return_value = {"id": "7"}

        action, result = jira_task.upsert_comment(CONFIG, "CSTP1-1234", "new", MARKER)

        self.assertEqual((action, result["id"]), ("updated", "7"))
        update.assert_called_once_with(CONFIG, "CSTP1-1234", "7", "new", timeout=15.0)

    @mock.patch.object(jira_task, "get_comments")
    @mock.patch.object(jira_task, "get_myself")
    def test_foreign_marker_does_not_update(
        self, myself: mock.Mock, comments: mock.Mock
    ) -> None:
        myself.return_value = {"accountId": "me"}
        comments.return_value = [comment("7", "other", MARKER)]

        with self.assertRaisesRegex(JiraTaskError, "다른 author"):
            jira_task.upsert_comment(CONFIG, "CSTP1-1234", "new", MARKER)

    @mock.patch.object(jira_task, "get_comments")
    @mock.patch.object(jira_task, "get_myself")
    def test_duplicate_marker_stops(
        self, myself: mock.Mock, comments: mock.Mock
    ) -> None:
        myself.return_value = {"accountId": "me"}
        comments.return_value = [comment("7", "me", MARKER), comment("8", "me", MARKER)]

        with self.assertRaisesRegex(JiraTaskError, "2개"):
            jira_task.upsert_comment(CONFIG, "CSTP1-1234", "new", MARKER)


class CliTests(unittest.TestCase):
    def test_preview_does_not_require_credentials_or_write(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = jira_task.main(
                [
                    "--ticket",
                    "CSTP1-1234",
                    "--worktree",
                    "demo",
                    "--date",
                    "2026-08-13",
                    "--session-id",
                    "manual",
                    "--summary",
                    "작업: comment skill 추가",
                ]
            )

        self.assertEqual(result, 0)
        self.assertIn("외부 변경 없음", output.getvalue())
        self.assertIn(MARKER, output.getvalue())

    @mock.patch.object(jira_task, "_configure_output")
    def test_preview_handles_unicode_when_stdout_is_cp1252(
        self, configure: mock.Mock
    ) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = jira_task.main(
                [
                    "--ticket",
                    "CSTP1-1234",
                    "--worktree",
                    "demo",
                    "--summary",
                    "작업: 한국어 요약",
                ]
            )

        self.assertEqual(result, 0)
        self.assertIn("한국어 요약", output.getvalue())
        configure.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
