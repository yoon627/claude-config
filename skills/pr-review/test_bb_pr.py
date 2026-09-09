#!/usr/bin/env python3
"""Unit tests for the Bitbucket PR review skill CLI."""

from __future__ import annotations

import contextlib
import http.client
import io
import json
import tempfile
import unittest
import urllib.error
import urllib.request
import urllib.response
from email.message import Message
from pathlib import Path
from unittest import mock

import bb_pr
from bb_pr import BitbucketConfig, BitbucketError, PrRef

CONFIG = BitbucketConfig(email="email-placeholder", token="<redacted>")
REF = PrRef(workspace="ws", repo="repo", pr_id=42)

# 실제 git 출력 형식을 따른다: hunk count 는 본문과 일치, 공백 경로는 인용 없이 탭 종결, 비ASCII 는 octal 인용.
DIFF = (
    "diff --git a/src/app.py b/src/app.py\n"
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,3 +1,4 @@\n"
    " import os\n"
    "-old = 1\n"
    "+new = 1\n"
    "+extra = 2\n"
    " keep = 3\n"
    "@@ -20 +21 @@\n"
    "-x = 1\n"
    "+x = 2\n"
    "diff --git a/gone.py b/gone.py\n"
    "deleted file mode 100644\n"
    "--- a/gone.py\n"
    "+++ /dev/null\n"
    "@@ -1,2 +0,0 @@\n"
    "-a\n"
    "-b\n"
    "diff --git a/new.py b/new.py\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/new.py\n"
    "@@ -0,0 +1,2 @@\n"
    "+line1\n"
    "+line2\n"
    "\\ No newline at end of file\n"
    "diff --git a/img.png b/img.png\n"
    "Binary files a/img.png and b/img.png differ\n"
    "diff --git a/old_name.py b/new_name.py\n"
    "similarity index 100%\n"
    "rename from old_name.py\n"
    "rename to new_name.py\n"
    "diff --git a/dir/sp ace.py b/dir/sp ace.py\n"
    "--- a/dir/sp ace.py\t\n"
    "+++ b/dir/sp ace.py\t\n"
    "@@ -1 +1 @@\n"
    "-a\n"
    "+b\n"
    'diff --git "a/\\355\\225\\234.py" "b/\\355\\225\\234.py"\n'
    '--- "a/\\355\\225\\234.py"\n'
    '+++ "b/\\355\\225\\234.py"\n'
    "@@ -1 +1 @@\n"
    "-a\n"
    "+b\n"
    "diff --git a/doc.md b/doc.md\n"
    "--- a/doc.md\n"
    "+++ b/doc.md\n"
    "@@ -1,2 +1,4 @@\n"
    " intro\n"
    "+++ b/other.py\n"
    "+-- a/other.py\n"
    " outro\n"
    "@@ -60 +62 @@\n"
    "-tail\n"
    "+tail2\n"
    "diff --git a/other.py b/other.py\n"
    "--- a/other.py\n"
    "+++ b/other.py\n"
    "@@ -1 +1 @@\n"
    "-z\n"
    "+z2\n"
)


def pr_meta(**overrides: object) -> dict:
    meta = {
        "workspace": "ws",
        "repo": "repo",
        "pr_id": 42,
        "state": "OPEN",
        "source": {"branch": "feat", "commit": "abc123", "repo": "ws/repo"},
        "destination": {"branch": "main", "commit": "def456", "repo": "ws/repo"},
    }
    meta.update(overrides)
    return meta


def draft(comments: list[dict], **overrides: object) -> dict:
    data = {
        "schema_version": bb_pr.SCHEMA_VERSION,
        "workspace": "ws",
        "repo": "repo",
        "pr_id": 42,
        "source_sha": "abc123",
        "comments": comments,
        "notes": [],
    }
    data.update(overrides)
    return data


def write_work_dir(root: Path, comments: list[dict], **draft_overrides: object) -> Path:
    (root / bb_pr.PR_JSON).write_text(json.dumps(pr_meta()), encoding="utf-8")
    (root / bb_pr.PR_DIFF).write_bytes(DIFF.encode("utf-8"))
    (root / bb_pr.DRAFT_JSON).write_text(
        json.dumps(draft(comments, **draft_overrides), ensure_ascii=False),
        encoding="utf-8",
    )
    return root


def read_draft(work: Path) -> dict:
    return json.loads((work / bb_pr.DRAFT_JSON).read_text(encoding="utf-8"))


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with mock.patch.object(bb_pr, "_configure_output"):
            code = bb_pr.main(argv)
    return code, out.getvalue(), err.getvalue()


class UrlTests(unittest.TestCase):
    def test_parses_plain_pull_request_url(self) -> None:
        ref = bb_pr.parse_pr_url("https://bitbucket.org/ws/my-repo/pull-requests/477")

        self.assertEqual(ref, PrRef("ws", "my-repo", 477))

    def test_accepts_tab_query_and_fragment_suffixes(self) -> None:
        for suffix in ("/diff", "/overview?w=1", "#comment-1", "/diff?a=b#x"):
            with self.subTest(suffix=suffix):
                ref = bb_pr.parse_pr_url(f"https://bitbucket.org/ws/repo/pull-requests/7{suffix}")
                self.assertEqual(ref, PrRef("ws", "repo", 7))

    def test_rejects_non_bitbucket_or_incomplete_urls(self) -> None:
        for url in (
            "https://github.com/o/r/pull/1",
            "https://bitbucket.org/ws/repo/pull-requests/",
            "https://bitbucket.org/ws/repo/branches",
            "bitbucket.org/ws/repo/pull-requests/1",
        ):
            with self.subTest(url=url), self.assertRaises(BitbucketError):
                bb_pr.parse_pr_url(url)


class SettingsTests(unittest.TestCase):
    def test_env_beats_project_env_beats_global_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "proj" / "sub"
            project.mkdir(parents=True)
            (root / "proj" / ".env").write_text(
                "BITBUCKET_EMAIL=project@example.com\nBITBUCKET_API_TOKEN=project-token\n",
                encoding="utf-8",
            )
            global_dir = root / "jira-kit"
            global_dir.mkdir()
            (global_dir / ".env").write_text(
                "BITBUCKET_EMAIL=global@example.com\nBITBUCKET_API_TOKEN=global-token\n",
                encoding="utf-8",
            )

            values = bb_pr.load_settings(
                project, environ={"BITBUCKET_EMAIL": "env@example.com"}, global_dir=global_dir
            )

        self.assertEqual(values["BITBUCKET_EMAIL"], "env@example.com")
        self.assertEqual(values["BITBUCKET_API_TOKEN"], "project-token")

    def test_jira_email_is_used_only_when_no_bitbucket_email_anywhere(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            global_dir = Path(tmp) / "jira-kit"
            global_dir.mkdir()
            (global_dir / ".env").write_text(
                "JIRA_EMAIL=jira@example.com\nBITBUCKET_EMAIL=bb@example.com\n", encoding="utf-8"
            )
            with_bb = bb_pr.load_settings(
                Path(tmp), environ={"JIRA_EMAIL": "envjira@example.com"}, global_dir=global_dir
            )
            (global_dir / ".env").write_text("JIRA_EMAIL=jira@example.com\n", encoding="utf-8")
            without_bb = bb_pr.load_settings(Path(tmp), environ={}, global_dir=global_dir)

        self.assertEqual(with_bb["BITBUCKET_EMAIL"], "bb@example.com")
        self.assertEqual(without_bb["BITBUCKET_EMAIL"], "jira@example.com")

    def test_token_has_no_fallback_and_config_reports_missing_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            values = bb_pr.load_settings(
                Path(tmp),
                environ={"JIRA_API_TOKEN": "jira-token", "BITBUCKET_EMAIL": "a@b.c"},
                global_dir=Path(tmp) / "missing",
            )

        self.assertNotIn("BITBUCKET_API_TOKEN", values)
        with self.assertRaises(bb_pr.ConfigError) as ctx:
            bb_pr.make_config(values)
        self.assertIn("BITBUCKET_API_TOKEN", str(ctx.exception))
        self.assertNotIn("jira-token", str(ctx.exception))


class DiffParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = bb_pr.parse_diff_lines(DIFF)

    def test_new_file_lines_are_added_plus_context_across_hunks(self) -> None:
        self.assertEqual(self.lines["src/app.py"], {1, 2, 3, 4, 21})

    def test_added_file_and_omitted_hunk_count_are_supported(self) -> None:
        self.assertEqual(self.lines["new.py"], {1, 2})

    def test_deleted_binary_and_rename_only_files_are_not_anchorable(self) -> None:
        self.assertEqual(self.lines["gone.py"], set())
        self.assertEqual(self.lines["img.png"], set())
        self.assertEqual(self.lines["new_name.py"], set())
        self.assertNotIn("old_name.py", self.lines)

    def test_space_path_with_tab_terminator_and_octal_quoted_path(self) -> None:
        self.assertEqual(self.lines["dir/sp ace.py"], {1})
        self.assertEqual(self.lines["한.py"], {1})
        self.assertNotIn("ace.py", self.lines)

    def test_hunk_body_lines_that_look_like_headers_stay_in_their_file(self) -> None:
        self.assertEqual(self.lines["doc.md"], {1, 2, 3, 4, 62})
        self.assertEqual(self.lines["other.py"], {1})

    def test_only_lf_splits_lines_and_crlf_is_tolerated(self) -> None:
        text = (
            "diff --git a/w.py b/w.py\r\n--- a/w.py\r\n+++ b/w.py\r\n@@ -1,2 +1,3 @@\r\n"
            " a\x0cb\r\n+c d\r\n e\r\n"
        )

        self.assertEqual(bb_pr.parse_diff_lines(text)["w.py"], {1, 2, 3})

    def test_git_escape_sequences_in_quoted_paths(self) -> None:
        self.assertEqual(bb_pr._unquote_git_path('"a\\tb\\\\c\\"d.py"'), 'a\tb\\c"d.py')
        self.assertEqual(bb_pr._unquote_git_path('"\\a\\b\\f\\v\\n\\r"'), "\a\b\f\v\n\r")

    def test_overlong_hunk_count_does_not_swallow_next_file(self) -> None:
        text = (
            "diff --git a/o.py b/o.py\n--- a/o.py\n+++ b/o.py\n@@ -1,5 +1,5 @@\n a\n"
            "diff --git a/z.py b/z.py\n--- a/z.py\n+++ b/z.py\n@@ -1 +1 @@\n-x\n+y\n"
        )

        lines = bb_pr.parse_diff_lines(text)

        self.assertEqual(lines["o.py"], {1})
        self.assertEqual(lines["z.py"], {1})


class PlanCommentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.line_map = bb_pr.parse_diff_lines(DIFF)

    def test_valid_items_become_planned_comments(self) -> None:
        planned, problems = bb_pr.plan_comments(
            draft([{"path": "src/app.py", "line": 3, "body": "왜 바뀌었나요?"}]), pr_meta(), self.line_map
        )

        self.assertEqual(problems, [])
        self.assertEqual([(p.path, p.line, p.body) for p in planned], [("src/app.py", 3, "왜 바뀌었나요?")])

    def test_each_invalid_item_gets_its_own_reason(self) -> None:
        items = [
            {"path": "src/app.py", "body": "line 없음"},
            {"line": 3, "body": "path 없음"},
            {"path": "nope.py", "line": 1, "body": "diff 에 없는 파일"},
            {"path": "src/app.py", "line": 10, "body": "앵커 불가 라인"},
            {"path": "gone.py", "line": 1, "body": "삭제 파일"},
            {"path": "src/app.py", "line": 3, "body": "   "},
            {"path": "src/app.py", "line": True, "body": "bool 은 int 가 아님"},
            {"path": "src/app.py", "line": 3, "body": "x", "posted_id": 0},
            {"path": "src/app.py", "line": 3, "body": "x", "posted_id": "../evil"},
        ]

        planned, problems = bb_pr.plan_comments(draft(items), pr_meta(), self.line_map)

        self.assertEqual(planned, [])
        self.assertEqual(len(problems), len(items))
        for index, problem in enumerate(problems):
            self.assertIn(f"#{index + 1}", problem)

    def test_draft_must_match_pr_identity_sha_and_schema(self) -> None:
        cases = {
            "schema": draft([], schema_version=99),
            "schema_bool": draft([], schema_version=True),
            "sha": draft([], source_sha="other"),
            "pr": draft([], pr_id=43),
        }
        for name, data in cases.items():
            with self.subTest(name=name):
                planned, problems = bb_pr.plan_comments(data, pr_meta(), self.line_map)
                self.assertEqual(planned, [])
                self.assertEqual(len(problems), 1)

    def test_posted_and_unknown_items_are_skipped_not_replanned(self) -> None:
        items = [
            {"path": "src/app.py", "line": 1, "body": "done", "posted_id": 1},
            {"path": "src/app.py", "line": 2, "body": "lost", "state": "unknown"},
            {"path": "src/app.py", "line": 3, "body": "todo"},
        ]

        planned, problems = bb_pr.plan_comments(draft(items), pr_meta(), self.line_map)

        self.assertEqual([item.index for item in planned], [3])
        self.assertEqual(len(problems), 1)
        self.assertIn("unknown", problems[0])

    def test_fetch_skeleton_round_trips_through_validation(self) -> None:
        skeleton = bb_pr._draft_skeleton(pr_meta())

        planned, problems = bb_pr.plan_comments(skeleton, pr_meta(), self.line_map)

        self.assertEqual((planned, problems), ([], []))


class PostCommandTests(unittest.TestCase):
    @mock.patch.object(bb_pr, "publish")
    @mock.patch.object(bb_pr, "_request")
    def test_dry_run_makes_no_http_calls(self, request: mock.Mock, publish: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 3, "body": "질문"}])

            code, out, _ = run_main(["post", "--dir", str(work)])

        self.assertEqual(code, 0)
        self.assertIn("src/app.py:3", out)
        self.assertIn("미리보기", out)
        request.assert_not_called()
        publish.assert_not_called()

    def test_dry_run_with_invalid_items_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 10, "body": "x"}])

            code, out, err = run_main(["post", "--dir", str(work)])

        self.assertEqual(code, 2)
        self.assertIn("#1", out + err)

    def test_approve_and_request_changes_are_exclusive_and_need_post(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [])
            with self.assertRaises(SystemExit):
                run_main(["post", "--dir", str(work), "--post", "--approve", "--request-changes"])
            code, _, err = run_main(["post", "--dir", str(work), "--approve"])

        self.assertEqual(code, 2)
        self.assertIn("--post", err)

    @mock.patch.object(bb_pr, "load_settings", return_value={"BITBUCKET_EMAIL": "a@b.c", "BITBUCKET_API_TOKEN": "t"})
    @mock.patch.object(bb_pr, "fetch_pr")
    @mock.patch.object(bb_pr, "publish")
    def test_post_refuses_when_pr_closed_or_source_moved(
        self, publish: mock.Mock, fetch_pr: mock.Mock, _settings: mock.Mock
    ) -> None:
        moved = pr_meta(source={"branch": "feat", "commit": "zzz", "repo": "ws/repo"})
        for meta in (pr_meta(state="MERGED"), moved):
            with self.subTest(meta=meta), tempfile.TemporaryDirectory() as tmp:
                work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 3, "body": "q"}])
                fetch_pr.return_value = meta

                code, _, err = run_main(["post", "--dir", str(work), "--post"])

                self.assertEqual(code, 2)
                self.assertIn("fetch", err)
        publish.assert_not_called()

    @mock.patch.object(bb_pr, "default_log_path")
    @mock.patch.object(bb_pr, "load_settings", return_value={"BITBUCKET_EMAIL": "a@b.c", "BITBUCKET_API_TOKEN": "t"})
    @mock.patch.object(bb_pr, "fetch_pr", return_value=pr_meta())
    @mock.patch.object(bb_pr, "_request")
    @mock.patch.object(bb_pr, "_request_json")
    def test_post_publishes_then_approves_and_records_review_state(
        self, request_json: mock.Mock, request: mock.Mock, _pr: mock.Mock, _s: mock.Mock, log_path: mock.Mock
    ) -> None:
        order: list[str] = []
        request_json.side_effect = lambda *a, **k: (order.append("comment"), {"id": 7, "inline": {"path": "src/app.py", "to": 3}})[1]
        request.side_effect = lambda *a, **k: (order.append(a[2]), (200, b""))[1]
        with tempfile.TemporaryDirectory() as tmp:
            log_path.return_value = Path(tmp) / "log.jsonl"
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 3, "body": "q"}])

            code, out, err = run_main(["post", "--dir", str(work), "--post", "--approve"])
            saved = read_draft(work)

        self.assertEqual((code, err), (0, ""))
        self.assertEqual(order, ["comment", "/repositories/ws/repo/pullrequests/42/approve"])
        self.assertEqual(saved["comments"][0]["posted_id"], 7)
        self.assertEqual(saved["review_state"], "approve")
        self.assertIn("comment 7", out)


class PublishTests(unittest.TestCase):
    def prepare(self, work: Path) -> tuple[list, dict]:
        data = read_draft(work)
        planned, problems = bb_pr.plan_comments(data, pr_meta(), bb_pr.parse_diff_lines(DIFF))
        self.assertEqual(problems, [])
        return planned, data

    def publish(self, work: Path) -> bb_pr.PublishResult:
        planned, data = self.prepare(work)
        return bb_pr.publish(CONFIG, REF, planned, data, work / bb_pr.DRAFT_JSON, log_path=work / "log.jsonl")

    @mock.patch.object(bb_pr, "_request_json")
    def test_publish_posts_inline_body_and_writes_back_ids(self, request_json: mock.Mock) -> None:
        request_json.side_effect = [
            {"id": 101, "inline": {"path": "src/app.py", "to": 3}},
            {"id": 102, "inline": {"path": "new.py", "to": 2}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(
                Path(tmp),
                [{"path": "src/app.py", "line": 3, "body": "첫째"}, {"path": "new.py", "line": 2, "body": "둘째"}],
            )

            result = self.publish(work)
            saved = read_draft(work)
            log_lines = (work / "log.jsonl").read_text(encoding="utf-8").splitlines()

        self.assertEqual([item["posted_id"] for item in saved["comments"]], [101, 102])
        self.assertEqual(result.posted, [(1, 101), (2, 102)])
        self.assertIsNone(result.failed_index)
        self.assertEqual(len(log_lines), 2)
        method, path, body = request_json.call_args_list[0].args[1:4]
        self.assertEqual((method, path), ("POST", "/repositories/ws/repo/pullrequests/42/comments"))
        self.assertEqual(body, {"content": {"raw": "첫째"}, "inline": {"path": "src/app.py", "to": 3}})

    @mock.patch.object(bb_pr, "_request_json")
    def test_publish_stops_at_first_failure_and_marks_unknown_only_without_4xx(self, request_json: mock.Mock) -> None:
        items = [
            {"path": "src/app.py", "line": 1, "body": "a"},
            {"path": "src/app.py", "line": 2, "body": "b"},
            {"path": "src/app.py", "line": 3, "body": "c"},
        ]
        cases = {
            "transport": (BitbucketError("Bitbucket 요청 실패: IncompleteRead"), "unknown"),
            "client_error": (BitbucketError("댓글 게시 실패 (400): bad anchor", 400), None),
        }
        for name, (error, expected_state) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                request_json.reset_mock()
                request_json.side_effect = [{"id": 101, "inline": {"path": "src/app.py", "to": 1}}, error]
                work = write_work_dir(Path(tmp), items)

                result = self.publish(work)
                saved = read_draft(work)

                self.assertEqual(result.posted, [(1, 101)])
                self.assertEqual(result.failed_index, 2)
                self.assertEqual(saved["comments"][0]["posted_id"], 101)
                self.assertEqual(saved["comments"][1].get("state"), expected_state)
                self.assertNotIn("posted_id", saved["comments"][2])
                self.assertEqual(request_json.call_count, 2)

    @mock.patch.object(bb_pr, "_request_json")
    def test_publish_flags_anchor_mismatch_but_records_id(self, request_json: mock.Mock) -> None:
        request_json.return_value = {"id": 5, "inline": {"path": "src/app.py", "to": 9}}
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 3, "body": "a"}])

            result = self.publish(work)
            saved = read_draft(work)

        self.assertEqual(saved["comments"][0]["posted_id"], 5)
        self.assertEqual(result.failed_index, 1)
        self.assertIn("anchor", result.error)

    @mock.patch.object(bb_pr, "_request_json", return_value={"id": 5, "inline": {"path": "src/app.py", "from": 3}})
    def test_publish_accepts_response_without_to_for_context_lines(self, _rj: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 1, "body": "a"}])

            result = self.publish(work)

        self.assertIsNone(result.failed_index)

    @mock.patch.object(bb_pr, "_request", return_value=(200, b""))
    def test_set_review_state_posts_approve_or_request_changes(self, request: mock.Mock) -> None:
        bb_pr.set_review_state(CONFIG, REF, "approve")
        bb_pr.set_review_state(CONFIG, REF, "request-changes")

        calls = [(call.args[1], call.args[2]) for call in request.call_args_list]
        self.assertEqual(
            calls,
            [
                ("POST", "/repositories/ws/repo/pullrequests/42/approve"),
                ("POST", "/repositories/ws/repo/pullrequests/42/request-changes"),
            ],
        )


class UndoTests(unittest.TestCase):
    @mock.patch.object(bb_pr, "_request", return_value=(204, b""))
    def test_undo_deletes_posted_comments_and_clears_ids(self, request: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(
                Path(tmp),
                [{"path": "src/app.py", "line": 3, "body": "a", "posted_id": 101}, {"path": "src/app.py", "line": 4, "body": "b"}],
                review_state="approve",
            )

            result = bb_pr.undo(CONFIG, REF, read_draft(work), work / bb_pr.DRAFT_JSON)
            saved = read_draft(work)

        calls = [(call.args[1], call.args[2]) for call in request.call_args_list]
        self.assertEqual(
            calls,
            [
                ("DELETE", "/repositories/ws/repo/pullrequests/42/comments/101"),
                ("DELETE", "/repositories/ws/repo/pullrequests/42/approve"),
            ],
        )
        self.assertNotIn("posted_id", saved["comments"][0])
        self.assertNotIn("review_state", saved)
        self.assertEqual(result.deleted, [101])

    @mock.patch.object(bb_pr, "_request")
    def test_undo_refuses_non_integer_posted_id_and_foreign_draft(self, request: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 3, "body": "a", "posted_id": "../x"}])

            bad_id = bb_pr.undo(CONFIG, REF, read_draft(work), work / bb_pr.DRAFT_JSON)
            foreign = bb_pr.undo(CONFIG, PrRef("ws", "repo", 99), read_draft(work), work / bb_pr.DRAFT_JSON)

        self.assertIn("posted_id", bad_id.error)
        self.assertIn("식별자", foreign.error)
        request.assert_not_called()

    @mock.patch.object(bb_pr, "undo")
    @mock.patch.object(bb_pr, "_request")
    def test_undo_command_is_dry_run_by_default_and_checks_identity(self, request: mock.Mock, undo: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = write_work_dir(Path(tmp), [{"path": "src/app.py", "line": 3, "body": "a", "posted_id": 7}])
            code, out, _ = run_main(["undo", "--dir", str(work)])

            (work / bb_pr.DRAFT_JSON).write_text(json.dumps(draft([], pr_id=99)), encoding="utf-8")
            mismatch_code, _, err = run_main(["undo", "--dir", str(work), "--post"])

        self.assertEqual(code, 0)
        self.assertIn("7", out)
        self.assertEqual(mismatch_code, 2)
        self.assertIn("식별자", err)
        request.assert_not_called()
        undo.assert_not_called()


def fake_response(url: str, code: int, body: bytes = b"", **headers: str) -> urllib.response.addinfourl:
    message = Message()
    for key, value in headers.items():
        message[key.replace("_", "-")] = value
    response = urllib.response.addinfourl(io.BytesIO(body), message, url, code)
    response.msg = "fake"
    return response


class RedirectSafetyTests(unittest.TestCase):
    def make_handler(self, responses: dict[str, tuple[int, bytes, dict[str, str]]]) -> type:
        seen: list[tuple[str, str | None]] = []

        class FakeHttps(urllib.request.BaseHandler):
            handler_order = 100

            def https_open(self, req: urllib.request.Request) -> urllib.response.addinfourl:
                seen.append((req.full_url, req.get_header("Authorization")))
                code, body, headers = responses[req.full_url]
                return fake_response(req.full_url, code, body, **headers)

        FakeHttps.seen = seen
        return FakeHttps

    def test_same_host_redirect_is_followed(self) -> None:
        start = "https://api.bitbucket.org/2.0/repositories/ws/repo/pullrequests/1/diff"
        target = "https://api.bitbucket.org/2.0/repositories/ws/repo/diff/abc..def"
        handler = self.make_handler({start: (302, b"", {"Location": target}), target: (200, b"diff --git", {})})

        status, body = bb_pr._request(
            CONFIG, "GET", start, accept="text/plain", what="diff", opener=bb_pr._build_opener(handler)
        )

        self.assertEqual((status, body), (200, b"diff --git"))
        self.assertEqual([url for url, _ in handler.seen], [start, target])

    def test_cross_host_redirect_is_refused_before_any_request_leaves(self) -> None:
        start = "https://api.bitbucket.org/2.0/repositories/ws/repo/pullrequests/1/diff"
        evil = "https://evil.example.com/diff"
        handler = self.make_handler({start: (302, b"", {"Location": evil}), evil: (200, b"", {})})

        with self.assertRaises(BitbucketError):
            bb_pr._request(CONFIG, "GET", start, accept="text/plain", what="diff", opener=bb_pr._build_opener(handler))

        self.assertEqual([url for url, _ in handler.seen], [start])

    def test_paged_next_url_outside_api_host_is_refused(self) -> None:
        with mock.patch.object(bb_pr, "_request_json") as request_json:
            request_json.return_value = {"values": [{"id": 1}], "next": "https://evil.example.com/2.0/x"}
            with self.assertRaises(BitbucketError):
                bb_pr._get_paged(CONFIG, "/repositories/ws/repo/pullrequests/1/comments")

    def test_api_url_check_tolerates_case_and_port_but_not_userinfo(self) -> None:
        bb_pr._check_api_url("https://API.bitbucket.org:443/2.0/x")
        for bad in (
            "http://api.bitbucket.org/2.0/x",
            "https://user@api.bitbucket.org/2.0/x",
            "https://:pw@api.bitbucket.org/2.0/x",
            "https://api.bitbucket.org:notaport/x",
            "https://api.bitbucket.org.evil.com/x",
        ):
            with self.subTest(url=bad), self.assertRaises(BitbucketError):
                bb_pr._check_api_url(bad)


class FailingRead:
    status = 201

    def __enter__(self) -> "FailingRead":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self) -> bytes:
        raise http.client.IncompleteRead(b"")


class RedactionTests(unittest.TestCase):
    def opener_raising(self, error: BaseException) -> mock.Mock:
        opener = mock.Mock()
        opener.open.side_effect = error
        return opener

    def test_http_error_hides_credentials_including_basic_value(self) -> None:
        body = f"denied for email-placeholder with <redacted> {bb_pr._auth_value(CONFIG)}".encode()
        error = urllib.error.HTTPError("https://api.bitbucket.org/x", 403, "Forbidden", Message(), io.BytesIO(body))

        with self.assertRaises(BitbucketError) as ctx:
            bb_pr._request(CONFIG, "GET", "/x", None, what="PR 조회", opener=self.opener_raising(error))

        text = str(ctx.exception)
        self.assertIn("403", text)
        for secret in ("email-placeholder", "<redacted>", bb_pr._auth_value(CONFIG)):
            self.assertNotIn(secret, text)

    def test_url_error_hides_credentials(self) -> None:
        error = urllib.error.URLError("resolve failed for email-placeholder")

        with self.assertRaises(BitbucketError) as ctx:
            bb_pr._request(CONFIG, "GET", "/x", None, what="PR 조회", opener=self.opener_raising(error))

        self.assertNotIn("email-placeholder", str(ctx.exception))

    def test_incomplete_read_becomes_bitbucket_error_without_status(self) -> None:
        opener = mock.Mock()
        opener.open.return_value = FailingRead()

        with self.assertRaises(BitbucketError) as ctx:
            bb_pr._request(CONFIG, "POST", "/x", {"a": 1}, what="게시", opener=opener)

        self.assertIsNone(ctx.exception.status)


class WorkDirTests(unittest.TestCase):
    def test_default_work_dir_is_outside_any_git_work_tree(self) -> None:
        path = bb_pr.default_work_dir(REF)

        self.assertFalse(bb_pr.inside_git_work_tree(path))
        self.assertTrue(str(path).endswith("ws-repo-42"))

    def test_dir_inside_git_work_tree_is_refused_for_every_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            target = root / "out"
            target.mkdir()

            with self.assertRaises(BitbucketError):
                bb_pr.ensure_work_dir(target)
            code, _, err = run_main(["post", "--dir", str(target)])

        self.assertEqual(code, 2)
        self.assertIn("work tree", err)

    @mock.patch.object(bb_pr, "_get_paged")
    @mock.patch.object(bb_pr, "_request")
    @mock.patch.object(bb_pr, "_request_json")
    def test_fetch_writes_meta_diff_and_draft_skeleton(
        self, request_json: mock.Mock, request: mock.Mock, get_paged: mock.Mock
    ) -> None:
        request_json.return_value = {
            "id": 42,
            "title": "제목",
            "description": "설명",
            "state": "OPEN",
            "author": {"display_name": "작성자"},
            "source": {"branch": {"name": "feat"}, "commit": {"hash": "abc123"}, "repository": {"full_name": "ws/repo"}},
            "destination": {"branch": {"name": "main"}, "commit": {"hash": "def456"}, "repository": {"full_name": "ws/repo"}},
            "links": {"html": {"href": "https://bitbucket.org/ws/repo/pull-requests/42"}},
        }
        request.return_value = (200, "diff --git a/한글.py b/한글.py\n".encode("utf-8"))
        get_paged.return_value = [
            {"id": 9, "inline": {"path": "src/app.py", "to": 3}, "user": {"display_name": "동료"}, "content": {"raw": "기존 지적"}},
            {"id": 10, "content": {"raw": "일반 댓글"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "out"

            summary = bb_pr.fetch_all(CONFIG, REF, work)
            meta = json.loads((work / bb_pr.PR_JSON).read_text(encoding="utf-8"))
            diff_bytes = (work / bb_pr.PR_DIFF).read_bytes()
            skeleton = read_draft(work)

            (work / bb_pr.DRAFT_JSON).write_text(json.dumps(draft([], pr_id=99)), encoding="utf-8")
            (work / bb_pr.PR_JSON).write_text("{}", encoding="utf-8")
            with self.assertRaises(BitbucketError):
                bb_pr.fetch_all(CONFIG, REF, work)
            untouched = (work / bb_pr.PR_JSON).read_text(encoding="utf-8")

        self.assertEqual(untouched, "{}")
        self.assertEqual(meta["source"], {"branch": "feat", "commit": "abc123", "repo": "ws/repo"})
        self.assertEqual(meta["state"], "OPEN")
        self.assertEqual(len(meta["existing_inline_comments"]), 1)
        self.assertEqual(meta["existing_inline_comments"][0]["to"], 3)
        self.assertEqual(diff_bytes, "diff --git a/한글.py b/한글.py\n".encode("utf-8"))
        self.assertEqual(skeleton["source_sha"], "abc123")
        self.assertEqual(skeleton["comments"], [])
        self.assertIn("제목", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
