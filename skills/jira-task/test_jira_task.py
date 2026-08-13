#!/usr/bin/env python3
"""Unit tests for the Jira task description skill."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
import urllib.error
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
SUMMARY = "Jira task 본문 기록을 추가했다."


class FormattingTests(unittest.TestCase):
    def test_adf_round_trip_preserves_lines(self) -> None:
        body = jira_task.adf_from_text("기존 본문\n둘째 줄")

        self.assertEqual(jira_task.adf_lines(body), ["기존 본문", "둘째 줄"])

    def test_description_entry_contains_summary_and_marker(self) -> None:
        entry = jira_task._description_entry(SUMMARY, MARKER)

        self.assertEqual(
            jira_task.adf_lines({"content": [entry]}),
            [f"작업 내용: {SUMMARY}", MARKER],
        )

    def test_description_entry_does_not_duplicate_summary_prefix(self) -> None:
        entry = jira_task._description_entry(f"작업 내용: {SUMMARY}", MARKER)

        self.assertEqual(
            jira_task.adf_lines({"content": [entry]}),
            [f"작업 내용: {SUMMARY}", MARKER],
        )

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


class DescriptionBodyTests(unittest.TestCase):
    def test_add_preserves_existing_description(self) -> None:
        existing = jira_task.adf_from_text("사용자가 작성한 기존 본문")

        result, action = jira_task.upsert_description_body(existing, SUMMARY, MARKER)

        self.assertEqual(action, "added")
        self.assertEqual(
            jira_task.adf_lines(result),
            ["사용자가 작성한 기존 본문", "작업 내용", f"작업 내용: {SUMMARY}", MARKER],
        )

    def test_same_marker_is_idempotent(self) -> None:
        first, first_action = jira_task.upsert_description_body(None, SUMMARY, MARKER)

        second, second_action = jira_task.upsert_description_body(
            first, SUMMARY, MARKER
        )

        self.assertEqual(first_action, "added")
        self.assertEqual(second_action, "unchanged")
        self.assertEqual(second, first)
        self.assertEqual(jira_task.adf_lines(second).count(MARKER), 1)

    def test_same_marker_updates_only_its_entry(self) -> None:
        original, _ = jira_task.upsert_description_body(None, "이전 요약", MARKER)

        result, action = jira_task.upsert_description_body(original, SUMMARY, MARKER)

        self.assertEqual(action, "updated")
        self.assertIn(f"작업 내용: {SUMMARY}", jira_task.adf_lines(result))
        self.assertNotIn("작업 내용: 이전 요약", jira_task.adf_lines(result))
        self.assertEqual(jira_task.adf_lines(result).count(MARKER), 1)

    def test_different_markers_append_entries_under_one_heading(self) -> None:
        first, _ = jira_task.upsert_description_body(None, "첫 작업", MARKER)
        other_marker = MARKER.replace("session=manual", "session=other")

        result, action = jira_task.upsert_description_body(
            first, "둘째 작업", other_marker
        )

        self.assertEqual(action, "added")
        lines = jira_task.adf_lines(result)
        self.assertEqual(lines.count("작업 내용"), 1)
        self.assertIn("작업 내용: 첫 작업", lines)
        self.assertIn("작업 내용: 둘째 작업", lines)


class ApiTests(unittest.TestCase):
    @mock.patch.object(jira_task, "_request")
    def test_get_issue_description_requests_only_description(
        self, request: mock.Mock
    ) -> None:
        description = jira_task.adf_from_text("기존")
        request.return_value = {"fields": {"description": description}}

        result = jira_task.get_issue_description(CONFIG, "CSTP1-1234")

        self.assertEqual(result, description)
        self.assertEqual(request.call_args.args[1], "GET")
        self.assertIn("/issue/CSTP1-1234?fields=description", request.call_args.args[2])

    @mock.patch.object(jira_task, "_request")
    def test_update_issue_description_sends_adf_fields_and_accepts_204(
        self, request: mock.Mock
    ) -> None:
        request.return_value = {}
        description = jira_task.adf_from_text("본문")

        result = jira_task.update_issue_description(CONFIG, "CSTP1-1234", description)

        self.assertEqual(result, {})
        self.assertEqual(request.call_args.args[1], "PUT")
        self.assertIn("/issue/CSTP1-1234", request.call_args.args[2])
        self.assertEqual(
            request.call_args.args[3], {"fields": {"description": description}}
        )
        self.assertEqual(request.call_args.kwargs["expected_status"], 204)
        self.assertTrue(request.call_args.kwargs["allow_empty_response"])

    @mock.patch.object(jira_task.urllib.request, "urlopen")
    def test_http_error_redacts_credentials(self, urlopen: mock.Mock) -> None:
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.atlassian.net/rest/api/3/issue/CSTP1-1234",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b"<redacted> email-placeholder"),
        )

        with self.assertRaises(JiraTaskError) as raised:
            jira_task.get_issue_description(CONFIG, "CSTP1-1234")
        self.assertNotIn("<redacted>", str(raised.exception))
        self.assertNotIn("email-placeholder", str(raised.exception))


class UpsertTests(unittest.TestCase):
    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_adds_and_verifies_description(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        current = jira_task.adf_from_text("기존")
        planned, _ = jira_task.upsert_description_body(current, SUMMARY, MARKER)
        get_description.side_effect = [current, planned]

        action, saved = jira_task.upsert_description(
            CONFIG, "CSTP1-1234", SUMMARY, MARKER
        )

        self.assertEqual(action, "added")
        self.assertEqual(saved, planned)
        update.assert_called_once_with(CONFIG, "CSTP1-1234", planned, timeout=15.0)

    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_same_description_does_not_put(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        current, _ = jira_task.upsert_description_body(None, SUMMARY, MARKER)
        get_description.return_value = current

        action, saved = jira_task.upsert_description(
            CONFIG, "CSTP1-1234", SUMMARY, MARKER
        )

        self.assertEqual(action, "unchanged")
        self.assertEqual(saved, current)
        update.assert_not_called()

    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_saved_description_mismatch_is_not_reported_as_success(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        current = jira_task.adf_from_text("기존")
        get_description.side_effect = [
            current,
            jira_task.adf_from_text("서버가 다른 본문을 저장"),
        ]

        with self.assertRaisesRegex(JiraTaskError, "저장값 확인 불일치"):
            jira_task.upsert_description(CONFIG, "CSTP1-1234", SUMMARY, MARKER)

        update.assert_called_once()


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
                    SUMMARY,
                ]
            )

        self.assertEqual(result, 0)
        self.assertIn(
            "task description 갱신 (미리보기; 외부 변경 없음)", output.getvalue()
        )
        self.assertIn(MARKER, output.getvalue())
        self.assertIn(SUMMARY, output.getvalue())
        self.assertNotIn("comment", output.getvalue().lower())

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
                    "작업 내용: 한국어 요약",
                ]
            )

        self.assertEqual(result, 0)
        self.assertIn("한국어 요약", output.getvalue())
        configure.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
