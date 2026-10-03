#!/usr/bin/env python3
"""jira_worklog CLI 종료코드 계약 (stdlib unittest, Jira·git·세션 로그·실제 홈 없음).

`/e` 6단계는 worklog 가 비0 으로 끝나면 7단계 worktree 정리를 생략하고, 0 이어도 `--register`
뒤 stderr 에 "등록 불가" 가 있으면 생략한다(skills/e/SKILL.md). 그 판정이 기대는 값을 고정한다.
  0: 세션 활동 없음·미리보기·티켓 없음·자격증명 불완전(+ "등록 불가")·등록 성공
  1: 등록 게이트 차단·Jira 실패(조회·계획·일부 쓰기)·worktree 처리 중 git 오류·고를 수 없는 worktree
     (없는 이름, 이름 없이 worktree 최상위가 아닌 cwd — sys.exit 문자열)
  2: 설정 오류(잘못된 티켓 패턴 정규식 — 설정·`--ticket-pattern` — 포함)·worktree 목록 git 오류
실행기 없음(127)과 launcher 의 종료코드 전달은 test_launcher.sh 가 본다.

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_exit_contract.py
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import jira_worklog  # noqa: E402
from jira_kit.config import Config, ConfigError, resolve_config  # noqa: E402
from jira_kit.git_util import GitError, Worktree  # noqa: E402
from jira_kit.jira_client import JiraConfig, JiraError  # noqa: E402
from jira_kit.session_time import AttributionStats  # noqa: E402

PATTERN = r"[A-Z]+-\d+"
SESSION = "claude:0000abcd"
# 이틀 — 항목이 2개라 "일부 실패"와 "전부 실패"가 갈린다.
ACTIVITY = [
    (datetime(2026, 9, 30, 1, 0, tzinfo=timezone.utc), datetime(2026, 9, 30, 1, 30, tzinfo=timezone.utc)),
    (datetime(2026, 10, 1, 1, 0, tzinfo=timezone.utc), datetime(2026, 10, 1, 1, 20, tzinfo=timezone.utc)),
]
CREDENTIALS = JiraConfig("https://jira.invalid", "me@jira.invalid", "token")


def _no_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("테스트가 네트워크에 닿았다")


class ExitContractTest(unittest.TestCase):
    def setUp(self) -> None:
        home = tempfile.mkdtemp(prefix="worklog-exit-home-")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        worktrees = Path(home) / "repo" / ".claude" / "worktrees"
        # 디렉터리 이름과 branch 를 다르게 둔다(EnterWorktree 형) — `/e`·`/wt rm` 은 디렉터리 이름으로 고른다.
        self.live = [
            Worktree(str(Path(home) / "repo"), "main"),
            Worktree(str(worktrees / "ABC-123-demo"), "worktree-ABC-123-demo"),
            Worktree(str(worktrees / "plain-demo"), "plain-demo"),
        ]
        self.config = Config(jira=CREDENTIALS, ticket_pattern=PATTERN, timezone_name="UTC", max_gap_minutes=60)
        self.activity = True
        # 아래 patch 가 빠뜨린 경계가 있어도 실제 홈(복구 로그·세션 로그·토큰)과 네트워크에 닿지 않게 한다.
        for patcher in (
            mock.patch.dict(os.environ, {"HOME": home, "USERPROFILE": home}),
            mock.patch.object(urllib.request, "urlopen", _no_network),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.m: dict[str, mock.Mock] = {}
        for name, fake in {
            "load_config": mock.Mock(side_effect=lambda *_a, **_k: self.config),
            "list_worktrees": mock.Mock(side_effect=lambda: self.live),
            "current_worktree": mock.Mock(return_value=None),
            "find_repo_session_files": mock.Mock(return_value=[]),
            "find_codex_sessions": mock.Mock(return_value=[]),
            "bucket_intervals_from_files": mock.Mock(side_effect=self._buckets),
            "bucket_codex_intervals": mock.Mock(return_value={}),
            "get_myself": mock.Mock(return_value={"accountId": "acct-me"}),
            "get_worklogs": mock.Mock(return_value=[]),
            "gate_reasons": mock.Mock(return_value=[]),
            "upsert_worklog": mock.Mock(return_value="created"),
            "_write_recovery_log": mock.Mock(),
        }.items():
            patcher = mock.patch.object(jira_worklog, name, fake)
            self.m[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def _buckets(self, _files: object, _tz: object, index: object, _max_gap: object) -> tuple[dict, AttributionStats]:
        # 키는 main() 이 넘긴 인덱스로 만든다 — 손으로 만든 Bucket 은 경로 정규화(/var → /private/var)에서 어긋난다.
        if not self.activity:
            return {}, AttributionStats()
        return {index.classify(wt.path): {SESSION: list(ACTIVITY)} for wt in self.live[1:]}, AttributionStats()

    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = jira_worklog.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    # ---- 0: /e 가 정리를 계속하는 정상 경로 ----
    def test_no_session_activity_exits_0(self) -> None:
        self.activity = False
        for argv in (["ABC-123-demo"], ["ABC-123-demo", "--register"]):
            with self.subTest(argv=argv):
                code, out, err = self.run_main(*argv)
                self.assertEqual(code, 0)
                self.assertIn("[ABC-123-demo] 세션 활동 없음", out)
                self.assertNotIn("등록 불가", err)

    def test_preview_exits_0(self) -> None:
        self.m["current_worktree"].return_value = self.live[1]
        for argv in (["ABC-123-demo"], []):  # `/e` 는 worktree 안에서 이름 없이도 부른다
            with self.subTest(argv=argv):
                code, out, err = self.run_main(*argv)
                self.assertEqual(code, 0)
                self.assertIn("[ABC-123-demo] branch=worktree-ABC-123-demo ticket=ABC-123", out)
                self.m["get_myself"].assert_not_called()
                self.assertNotIn("등록 불가", err)

    def test_register_without_ticket_exits_0(self) -> None:
        code, out, err = self.run_main("plain-demo", "--register")
        self.assertEqual(code, 0)
        self.assertIn("[plain-demo] branch=plain-demo ticket=(없음)", out)
        self.assertIn("티켓 매치 없음", out)
        self.m["get_myself"].assert_not_called()
        self.assertNotIn("등록 불가", err)

    def test_register_without_credentials_exits_0_and_warns(self) -> None:
        self.config = replace(self.config, jira=None)
        code, out, err = self.run_main("ABC-123-demo", "--register")
        self.assertEqual(code, 0)
        self.assertIn("등록 불가", err)
        self.assertIn("[ABC-123-demo] branch=", out)
        self.m["get_myself"].assert_not_called()

    def test_register_success_exits_0(self) -> None:
        code, _, err = self.run_main("ABC-123-demo", "--register")
        self.assertEqual(code, 0)
        self.assertEqual(self.m["upsert_worklog"].call_count, 2)  # 세션 1개·이틀 = 항목 2개
        self.assertNotIn("등록 불가", err)

    # ---- 1: /e 가 정리를 생략하는 실패 ----
    def test_gate_block_exits_1(self) -> None:
        self.m["gate_reasons"].return_value = ["변동 폭이 크다"]
        code, _, err = self.run_main("ABC-123-demo", "--register")
        self.assertEqual(code, 1)
        self.assertIn("등록 차단", err)
        self.m["upsert_worklog"].assert_not_called()

    def test_jira_failure_exits_1(self) -> None:
        # 조회·등록 계획·쓰기 — 쓰기는 이틀 중 하루만 실패해도 1 이다.
        for name, effect in (
            ("get_myself", JiraError("boom")),
            ("plan_worklog_changes", JiraError("boom")),
            ("upsert_worklog", ["created", JiraError("boom")]),
        ):
            with self.subTest(fails=name), mock.patch.object(jira_worklog, name, side_effect=effect):
                code, _, err = self.run_main("ABC-123-demo", "--register")
                self.assertEqual(code, 1)
                self.assertIn("boom", err)

    def test_git_error_while_processing_exits_1(self) -> None:
        with mock.patch.object(jira_worklog, "process", side_effect=GitError("rev-parse")):
            code, _, err = self.run_main("ABC-123-demo")
        self.assertEqual(code, 1)
        self.assertIn("git 오류 → skip", err)

    def test_unselectable_worktree_exits_1(self) -> None:
        # 없는 이름, 또는 이름 없이 worktree 최상위가 아닌 cwd — 문자열을 준 SystemExit 은 종료코드 1 이다(파이썬 규약)
        for argv, expected in ((["no-such-worktree"], "no-such-worktree"), ([], "최상위가 아닙니다")):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit) as caught:
                    self.run_main(*argv)
                self.assertIsInstance(caught.exception.code, str)
                self.assertIn(expected, caught.exception.code)

    def test_unexpected_error_is_not_swallowed(self) -> None:
        self.m["bucket_intervals_from_files"].side_effect = RuntimeError("scan")
        with self.assertRaises(RuntimeError):
            self.run_main("ABC-123-demo")

    # ---- 2: 설정·git 오류 ----
    def test_config_or_git_error_exits_2(self) -> None:
        for name, error in (("load_config", ConfigError("toml")), ("list_worktrees", GitError("worktree list"))):
            with self.subTest(raises=name), mock.patch.object(jira_worklog, name, side_effect=error):
                code, _, _ = self.run_main("ABC-123-demo")
                self.assertEqual(code, 2)

    def test_invalid_ticket_pattern_setting_exits_2(self) -> None:
        # 설정 패턴은 --ticket-pattern 이 없을 때만 쓰이므로 그때만 막는다. 설정은 실제 resolve_config 로
        # 만든다 — 검사가 설정을 읽는 단계로 옮겨 가면 CLI 값으로 우회할 수 없게 되는데, 그것도 여기서 잡힌다.
        self.config = replace(
            resolve_config({"JIRA_TICKET_PATTERN": "["}, {}, {}),
            jira=CREDENTIALS, timezone_name="UTC", max_gap_minutes=60,
        )
        code, _, err = self.run_main("ABC-123-demo")
        self.assertEqual(code, 2)
        self.assertIn("JIRA_TICKET_PATTERN", err)
        code, out, _ = self.run_main("ABC-123-demo", "--ticket-pattern", PATTERN)
        self.assertEqual(code, 0)
        self.assertIn("ticket=ABC-123", out)

    def test_invalid_ticket_pattern_option_exits_2(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err), self.assertRaises(SystemExit) as caught:
            jira_worklog.main(["ABC-123-demo", "--ticket-pattern", "["])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--ticket-pattern", err.getvalue())


class ProcessExitTest(unittest.TestCase):
    """`sys.exit(main())` 까지 — `/e` 가 읽는 것은 반환값이 아니라 프로세스 종료코드다."""

    def test_config_error_reaches_the_process_exit_code(self) -> None:
        tmp = tempfile.mkdtemp(prefix="worklog-exit-proc-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        Path(tmp, "jira-kit.toml").write_text("[jira\n", encoding="utf-8")  # 문법 오류 → ConfigError
        Path(tmp, ".env").write_text("", encoding="utf-8")  # 상위 디렉터리의 .env 를 찾아 올라가지 않게 여기서 멈춘다
        env = {k: v for k, v in os.environ.items() if not k.startswith("JIRA_")}
        env.update(HOME=tmp, USERPROFILE=tmp)
        result = subprocess.run(
            [sys.executable, str(HERE / "jira_worklog.py")],
            cwd=tmp, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("설정 로드 실패", result.stderr)
        self.assertIn("jira-kit.toml", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
