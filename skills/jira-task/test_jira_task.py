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
DATE = "2026-08-13"
LEGACY_MARKER = (
    "[jira-task] ticket=ABC1-1234 date=2026-08-13 worktree=demo session=manual"
)
SUMMARY = "Jira task 본문 기록을 추가했다."


def paragraph(*lines: str) -> dict:
    content: list[dict] = []
    for index, line in enumerate(lines):
        if index:
            content.append({"type": "hardBreak"})
        content.append({"type": "text", "text": line})
    return {"type": "paragraph", "content": content}


def heading(text: str, level: int = 2) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def doc(*blocks: dict) -> dict:
    return {"type": "doc", "version": 1, "content": list(blocks)}


class FormattingTests(unittest.TestCase):
    def test_adf_round_trip_preserves_lines(self) -> None:
        body = jira_task.adf_from_text("기존 본문\n둘째 줄")

        self.assertEqual(jira_task.adf_lines(body), ["기존 본문", "둘째 줄"])

    def test_adf_text_treats_null_content_as_empty(self) -> None:
        body = doc(paragraph("기존"), {"type": "paragraph", "content": None})

        self.assertEqual(jira_task.adf_lines(body), ["기존", ""])

    def test_description_entry_lists_date_and_items_without_marker(self) -> None:
        entry = jira_task._description_entry(f"{SUMMARY}\n\n테스트를 보강했다.", DATE)

        self.assertEqual(
            jira_task.adf_lines({"content": [entry]}),
            [DATE, f"- {SUMMARY}", "- 테스트를 보강했다."],
        )
        self.assertEqual(entry["content"][0]["marks"], [{"type": "strong"}])

    def test_description_entry_does_not_duplicate_item_prefixes(self) -> None:
        entry = jira_task._description_entry(
            f"작업 내용: {SUMMARY}\n* 둘째\n• 셋째\n1. 넷째\n- 작업 내용: 다섯째\n"
            "2026. 10. 7 배포분",
            DATE,
        )

        self.assertEqual(
            jira_task.adf_lines({"content": [entry]})[1:],
            [
                f"- {SUMMARY}",
                "- 둘째",
                "- 셋째",
                "- 넷째",
                "- 다섯째",
                "- 2026. 10. 7 배포분",
            ],
        )

    def test_summary_without_items_is_rejected(self) -> None:
        args = jira_task.parse_args(
            ["--ticket", "ABC1-1234", "--summary", "-\n1.\n작업 내용:"]
        )

        with self.assertRaisesRegex(JiraTaskError, "작업 항목이 없습니다"):
            jira_task._summary_from_args(args)

    def test_summary_rejects_secret_like_text(self) -> None:
        args = jira_task.parse_args(
            ["--ticket", "ABC1-1234", "--summary", "JIRA_API_TOKEN ="]
        )

        with self.assertRaisesRegex(JiraTaskError, "credential"):
            jira_task._summary_from_args(args)

    def test_ticket_inference_prefers_worktree_prefix(self) -> None:
        self.assertEqual(
            jira_task.infer_ticket(
                "ABC1-1234-summary",
                "feature/ABC1-9999",
                jira_task.DEFAULT_TICKET_PATTERN,
            ),
            "ABC1-1234",
        )


class DescriptionBodyTests(unittest.TestCase):
    def test_add_creates_section_after_existing_description(self) -> None:
        existing = jira_task.adf_from_text("사용자가 작성한 기존 본문")

        result, action = jira_task.upsert_description_body(existing, SUMMARY, DATE)

        self.assertEqual(action, "added")
        self.assertEqual(
            jira_task.adf_lines(result),
            ["사용자가 작성한 기존 본문", "작업 내용", DATE, f"- {SUMMARY}"],
        )

    def test_same_summary_is_unchanged(self) -> None:
        first, first_action = jira_task.upsert_description_body(None, SUMMARY, DATE)

        second, second_action = jira_task.upsert_description_body(first, SUMMARY, DATE)

        self.assertEqual(first_action, "added")
        self.assertEqual(second_action, "unchanged")
        self.assertEqual(second, first)

    def test_same_date_is_replaced_and_other_dates_kept(self) -> None:
        original = doc(
            heading("작업 내용"),
            paragraph("2026-08-12", "- 전날 작업"),
            paragraph(DATE, "- 이전 요약"),
            paragraph("- 사람이 Enter 로 나눈 항목"),
        )

        result, action = jira_task.upsert_description_body(original, SUMMARY, DATE)

        self.assertEqual(action, "updated")
        self.assertEqual(
            jira_task.adf_lines(result),
            ["작업 내용", "2026-08-12", "- 전날 작업", DATE, f"- {SUMMARY}"],
        )

    def test_legacy_marker_blocks_for_date_merge_into_one(self) -> None:
        legacy = doc(
            heading("작업 내용"),
            paragraph("작업 내용: 첫 세션", LEGACY_MARKER),
            paragraph(
                "작업 내용: 다른 날",
                LEGACY_MARKER.replace("2026-08-13", "2026-08-12"),
            ),
            paragraph(
                "작업 내용: 둘째 세션",
                LEGACY_MARKER.replace("session=manual", "session=other"),
            ),
        )

        result, action = jira_task.upsert_description_body(legacy, SUMMARY, DATE)

        self.assertEqual(action, "updated")
        lines = jira_task.adf_lines(result)
        self.assertEqual(lines[:3], ["작업 내용", DATE, f"- {SUMMARY}"])
        self.assertNotIn(LEGACY_MARKER, lines)
        self.assertNotIn("작업 내용: 둘째 세션", lines)
        self.assertIn("작업 내용: 다른 날", lines)

    def test_user_content_outside_section_is_untouched(self) -> None:
        original = doc(
            paragraph(DATE, "사람이 쓴 앞 문단"),
            heading("작업 내용"),
            paragraph("2026-08-12", "- 전날 작업"),
            heading("참고"),
            paragraph(DATE, "사람이 쓴 뒤 문단"),
        )

        result, action = jira_task.upsert_description_body(original, SUMMARY, DATE)

        self.assertEqual(action, "added")
        self.assertEqual(
            jira_task.adf_lines(result),
            [
                DATE,
                "사람이 쓴 앞 문단",
                "작업 내용",
                "2026-08-12",
                "- 전날 작업",
                DATE,
                f"- {SUMMARY}",
                "참고",
                DATE,
                "사람이 쓴 뒤 문단",
            ],
        )

    def test_plain_paragraph_with_heading_text_is_not_a_section(self) -> None:
        original = doc(paragraph("작업 내용"), paragraph(DATE, "- 사람 메모"))

        result, action = jira_task.upsert_description_body(original, SUMMARY, DATE)

        self.assertEqual(action, "added")
        self.assertEqual(
            jira_task.adf_lines(result)[-4:],
            ["- 사람 메모", "작업 내용", DATE, f"- {SUMMARY}"],
        )

    def test_other_date_legacy_block_ends_the_date_range(self) -> None:
        other_marker = LEGACY_MARKER.replace("2026-08-13", "2026-08-14")
        for blocks in (
            (paragraph(DATE, "- 이전", LEGACY_MARKER), paragraph("작업 내용: 다음날", other_marker)),
            (paragraph("2026-08-14", "- 다음날", other_marker), paragraph("작업 내용: 이전", LEGACY_MARKER)),
        ):
            original = doc(heading("작업 내용"), *blocks)

            result, _ = jira_task.upsert_description_body(original, SUMMARY, DATE)

            lines = jira_task.adf_lines(result)
            self.assertIn(other_marker, lines)
            self.assertIn(f"- {SUMMARY}", lines)
            self.assertNotIn(LEGACY_MARKER, lines)

    def test_sub_heading_inside_section_ends_the_date_range(self) -> None:
        original = doc(
            heading("작업 내용"),
            paragraph(DATE, "- 이전"),
            heading("메모", 3),
            paragraph("사람 메모"),
        )

        result, _ = jira_task.upsert_description_body(original, SUMMARY, DATE)

        self.assertEqual(
            jira_task.adf_lines(result),
            ["작업 내용", DATE, f"- {SUMMARY}", "메모", "사람 메모"],
        )

    def test_fingerprint_uses_text_of_all_date_blocks(self) -> None:
        plain = doc(heading("작업 내용"), paragraph(DATE, "- 항목"))
        with_attrs = doc(heading("작업 내용"), paragraph(DATE, "- 항목"))
        with_attrs["content"][1]["attrs"] = {"localId": "abc"}

        self.assertEqual(jira_task.entry_fingerprint(None, DATE), "none")
        self.assertEqual(
            jira_task.entry_fingerprint(plain, DATE),
            jira_task.entry_fingerprint(with_attrs, DATE),
        )
        self.assertNotEqual(
            jira_task.entry_fingerprint(plain, DATE),
            jira_task.entry_fingerprint(
                doc(heading("작업 내용"), paragraph(DATE, "- 다른 항목")), DATE
            ),
        )


def task_list(*items: tuple[bool, str]) -> dict:
    return {
        "type": "taskList",
        "attrs": {"localId": "list"},
        "content": [
            {
                "type": "taskItem",
                "attrs": {"localId": f"item-{index}", "state": "DONE" if done else "TODO"},
                "content": [{"type": "text", "text": text}],
            }
            for index, (done, text) in enumerate(items)
        ],
    }


TODO = [(True, "kb_ask 도구 추가"), (False, "Plan 단계 실측")]


class TodoTests(unittest.TestCase):
    def test_parse_todo_reads_checkbox_lines(self) -> None:
        text = "[x] kb_ask 도구 추가\n- [ ] Plan 단계 실측\n\n* [X] 대문자 표시\n"

        self.assertEqual(
            jira_task.parse_todo(text),
            [(True, "kb_ask 도구 추가"), (False, "Plan 단계 실측"), (True, "대문자 표시")],
        )

    def test_parse_todo_rejects_lines_without_checkbox(self) -> None:
        with self.assertRaisesRegex(JiraTaskError, "체크 표시"):
            jira_task.parse_todo("[x] 완료\n그냥 문장")

    def test_todo_section_is_created_before_work_log_as_task_list(self) -> None:
        current = doc(paragraph("기존 설명"), heading("작업 내용"), paragraph("2026-08-12", "- 어제"))

        result, _ = jira_task.upsert_description_body(current, SUMMARY, DATE, TODO)

        content = result["content"]
        self.assertEqual(jira_task._adf_node_text(content[0]), "기존 설명")
        self.assertEqual(jira_task._adf_node_text(content[1]), "해야 할 일")
        self.assertEqual(content[2]["type"], "taskList")
        self.assertEqual(
            [item["attrs"]["state"] for item in content[2]["content"]], ["DONE", "TODO"]
        )
        self.assertEqual(jira_task._adf_node_text(content[3]), "작업 내용")
        self.assertEqual(jira_task.todo_section_text(result), "[x] kb_ask 도구 추가\n[ ] Plan 단계 실측")

    def test_existing_todo_section_is_replaced_and_rest_kept(self) -> None:
        current = doc(
            heading("해야 할 일"),
            task_list((False, "옛 항목")),
            paragraph("사람이 덧붙인 메모"),
            heading("작업 내용"),
            paragraph(DATE, f"- {SUMMARY}"),
        )

        result, action = jira_task.upsert_description_body(current, SUMMARY, DATE, TODO)

        self.assertEqual(action, "updated")
        self.assertEqual(jira_task.todo_section_text(result), "[x] kb_ask 도구 추가\n[ ] Plan 단계 실측")
        self.assertEqual(
            [jira_task._adf_node_text(block) for block in result["content"][2:]],
            ["작업 내용", f"{DATE}\n- {SUMMARY}"],
        )

    def test_todo_section_ends_at_any_heading_so_work_log_survives(self) -> None:
        current = doc(
            heading("해야 할 일", level=1),
            paragraph("[ ] 옛 항목"),
            heading("참고", level=3),
            paragraph("사람 메모"),
            heading("작업 내용", level=2),
            paragraph("2026-08-01", "- 옛 기록"),
        )

        result, _ = jira_task.upsert_description_body(current, SUMMARY, DATE, TODO)

        texts = [jira_task._adf_node_text(block) for block in result["content"]]
        self.assertEqual(texts[2:6], ["참고", "사람 메모", "작업 내용", "2026-08-01\n- 옛 기록"])
        self.assertEqual(result["content"][1]["type"], "taskList")

    def test_plain_text_checkbox_paragraph_becomes_task_list(self) -> None:
        current = doc(
            heading("해야 할 일"),
            paragraph("[x] kb_ask 도구 추가", "[ ] Plan 단계 실측"),
            heading("작업 내용"),
            paragraph(DATE, f"- {SUMMARY}"),
        )

        result, action = jira_task.upsert_description_body(current, SUMMARY, DATE, TODO)

        self.assertEqual(action, "updated")
        self.assertEqual(result["content"][1]["type"], "taskList")

    def test_without_todo_existing_todo_section_is_kept_as_is(self) -> None:
        current = doc(heading("해야 할 일"), task_list((True, "사람이 체크")), heading("작업 내용"))

        result, _ = jira_task.upsert_description_body(current, SUMMARY, DATE)

        self.assertEqual(result["content"][:3], current["content"])

    def test_same_todo_and_summary_is_unchanged(self) -> None:
        current, _ = jira_task.upsert_description_body(None, SUMMARY, DATE, TODO)

        _, action = jira_task.upsert_description_body(current, SUMMARY, DATE, TODO)

        self.assertEqual(action, "unchanged")

    def test_fingerprint_covers_todo_state_only_when_todo_is_given(self) -> None:
        unchecked = doc(heading("해야 할 일"), task_list((False, "항목")), heading("작업 내용"))
        checked = doc(heading("해야 할 일"), task_list((True, "항목")), heading("작업 내용"))

        self.assertEqual(
            jira_task.entry_fingerprint(unchecked, DATE),
            jira_task.entry_fingerprint(checked, DATE),
        )
        self.assertNotEqual(
            jira_task.entry_fingerprint(unchecked, DATE, include_todo=True),
            jira_task.entry_fingerprint(checked, DATE, include_todo=True),
        )


class ApiTests(unittest.TestCase):
    @mock.patch.object(jira_task, "_request")
    def test_get_issue_description_requests_only_description(
        self, request: mock.Mock
    ) -> None:
        description = jira_task.adf_from_text("기존")
        request.return_value = {"fields": {"description": description}}

        result = jira_task.get_issue_description(CONFIG, "ABC1-1234")

        self.assertEqual(result, description)
        self.assertEqual(request.call_args.args[1], "GET")
        self.assertIn("/issue/ABC1-1234?fields=description", request.call_args.args[2])

    @mock.patch.object(jira_task, "_request")
    def test_update_issue_description_sends_adf_fields_and_accepts_204(
        self, request: mock.Mock
    ) -> None:
        request.return_value = {}
        description = jira_task.adf_from_text("본문")

        result = jira_task.update_issue_description(CONFIG, "ABC1-1234", description)

        self.assertEqual(result, {})
        self.assertEqual(request.call_args.args[1], "PUT")
        self.assertIn("/issue/ABC1-1234", request.call_args.args[2])
        self.assertEqual(
            request.call_args.args[3], {"fields": {"description": description}}
        )
        self.assertEqual(request.call_args.kwargs["expected_status"], 204)
        self.assertTrue(request.call_args.kwargs["allow_empty_response"])

    @mock.patch.object(jira_task.urllib.request, "urlopen")
    def test_http_error_redacts_credentials(self, urlopen: mock.Mock) -> None:
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.atlassian.net/rest/api/3/issue/ABC1-1234",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b"<redacted> email-placeholder"),
        )

        with self.assertRaises(JiraTaskError) as raised:
            jira_task.get_issue_description(CONFIG, "ABC1-1234")
        self.assertNotIn("<redacted>", str(raised.exception))
        self.assertNotIn("email-placeholder", str(raised.exception))


class UpsertTests(unittest.TestCase):
    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_adds_and_verifies_description(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        current = jira_task.adf_from_text("기존")
        planned, _ = jira_task.upsert_description_body(current, SUMMARY, DATE)
        get_description.side_effect = [current, planned]

        action, saved = jira_task.upsert_description(
            CONFIG, "ABC1-1234", SUMMARY, DATE, "none"
        )

        self.assertEqual(action, "added")
        self.assertEqual(saved, planned)
        update.assert_called_once_with(CONFIG, "ABC1-1234", planned, timeout=15.0)

    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_todo_is_written_and_verified_with_todo_fingerprint(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        current = doc(heading("해야 할 일"), task_list((False, "kb_ask 도구 추가")))
        planned, _ = jira_task.upsert_description_body(current, SUMMARY, DATE, TODO)
        get_description.side_effect = [current, planned]

        action, _ = jira_task.upsert_description(
            CONFIG,
            "ABC1-1234",
            SUMMARY,
            DATE,
            jira_task.entry_fingerprint(current, DATE, include_todo=True),
            todo=TODO,
        )

        self.assertEqual(action, "added")
        update.assert_called_once()
        sent = update.call_args.args[2]
        self.assertEqual(jira_task.todo_section_text(sent), "[x] kb_ask 도구 추가\n[ ] Plan 단계 실측")
        self.assertEqual(jira_task.existing_entry_text(sent, DATE), f"{DATE}\n- {SUMMARY}")

        get_description.side_effect = [current, current]
        with self.assertRaisesRegex(JiraTaskError, "저장값 확인 불일치"):
            jira_task.upsert_description(
                CONFIG,
                "ABC1-1234",
                SUMMARY,
                DATE,
                jira_task.entry_fingerprint(current, DATE, include_todo=True),
                todo=TODO,
            )

    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_same_description_does_not_put(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        current, _ = jira_task.upsert_description_body(None, SUMMARY, DATE)
        get_description.return_value = current

        action, saved = jira_task.upsert_description(
            CONFIG,
            "ABC1-1234",
            SUMMARY,
            DATE,
            jira_task.entry_fingerprint(current, DATE),
        )

        self.assertEqual(action, "unchanged")
        self.assertEqual(saved, current)
        update.assert_not_called()

    @mock.patch.object(jira_task, "update_issue_description")
    @mock.patch.object(jira_task, "get_issue_description")
    def test_fingerprint_mismatch_does_not_put(
        self, get_description: mock.Mock, update: mock.Mock
    ) -> None:
        get_description.return_value = doc(
            heading("작업 내용"), paragraph(DATE, "- 다른 세션 항목")
        )

        for expected in ("none", "unknown"):
            with self.assertRaisesRegex(JiraTaskError, "지문이 다릅니다"):
                jira_task.upsert_description(
                    CONFIG, "ABC1-1234", SUMMARY, DATE, expected
                )

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
            jira_task.upsert_description(CONFIG, "ABC1-1234", SUMMARY, DATE, "none")

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


@mock.patch.object(jira_task, "load_settings", return_value=jira_task.Settings({}))
class CliTests(unittest.TestCase):
    def test_preview_without_credentials_reports_unknown_and_does_not_write(
        self, _settings: mock.Mock
    ) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = jira_task.main(
                ["--ticket", "ABC1-1234", "--date", DATE, "--summary", SUMMARY]
            )

        self.assertEqual(result, 0)
        self.assertIn(
            "task description 갱신 (미리보기; 외부 변경 없음)", output.getvalue()
        )
        self.assertIn("기존 항목 지문: unknown", output.getvalue())
        self.assertIn(f"- {SUMMARY}", output.getvalue())
        self.assertNotIn("[jira-task]", output.getvalue())

    @mock.patch.object(jira_task, "get_issue_description")
    @mock.patch.object(jira_task, "make_jira_config", return_value=CONFIG)
    def test_preview_shows_existing_entry_and_fingerprint(
        self, _config: mock.Mock, get_description: mock.Mock, _settings: mock.Mock
    ) -> None:
        current = doc(heading("작업 내용"), paragraph(DATE, "- 오전 작업"))
        get_description.return_value = current
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = jira_task.main(
                ["--ticket", "ABC1-1234", "--date", DATE, "--summary", SUMMARY]
            )

        self.assertEqual(result, 0)
        self.assertIn("- 오전 작업", output.getvalue())
        self.assertNotIn("(없음)", output.getvalue())
        self.assertIn(
            f"기존 항목 지문: {jira_task.entry_fingerprint(current, DATE)}",
            output.getvalue(),
        )

        get_description.return_value = None
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            jira_task.main(["--ticket", "ABC1-1234", "--date", DATE, "--summary", SUMMARY])
        self.assertIn("(없음)", output.getvalue())
        self.assertIn("기존 항목 지문: none", output.getvalue())

    @mock.patch.object(jira_task, "get_issue_description")
    @mock.patch.object(jira_task, "make_jira_config", return_value=CONFIG)
    def test_preview_with_todo_file_shows_existing_and_new_todo(
        self, _config: mock.Mock, get_description: mock.Mock, _settings: mock.Mock
    ) -> None:
        current = doc(heading("해야 할 일"), task_list((True, "사람이 체크한 항목")))
        get_description.return_value = current
        with tempfile.TemporaryDirectory() as directory:
            todo_file = Path(directory) / "todo.txt"
            todo_file.write_text("[x] kb_ask 도구 추가\n[ ] Plan 단계 실측\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = jira_task.main(
                    [
                        "--ticket", "ABC1-1234", "--date", DATE,
                        "--summary", SUMMARY, "--todo-file", str(todo_file),
                    ]
                )

        self.assertEqual(result, 0)
        self.assertIn("[x] 사람이 체크한 항목", output.getvalue())
        self.assertIn("[ ] Plan 단계 실측", output.getvalue())
        self.assertIn(
            f"기존 항목 지문: {jira_task.entry_fingerprint(current, DATE, include_todo=True)}",
            output.getvalue(),
        )

    @mock.patch.object(jira_task, "upsert_description")
    def test_post_requires_expected_fingerprint(
        self, upsert: mock.Mock, _settings: mock.Mock
    ) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as error:
            result = jira_task.main(
                ["--ticket", "ABC1-1234", "--summary", SUMMARY, "--post"]
            )

        self.assertEqual(result, 2)
        self.assertIn("--expect-existing", error.getvalue())
        upsert.assert_not_called()

    @mock.patch.object(jira_task, "_configure_output")
    def test_preview_handles_unicode_when_stdout_is_cp1252(
        self, configure: mock.Mock, _settings: mock.Mock
    ) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = jira_task.main(
                [
                    "--ticket",
                    "ABC1-1234",
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
