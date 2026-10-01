#!/usr/bin/env python3
"""티켓 패턴의 기본값과 머신별 설정 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_ticket_pattern.py

기본값은 범용 Jira 키이고, 조직 고유 키로 좁히는 패턴은 공개 repo 가 아니라 머신별
``jira-kit.toml``·``JIRA_TICKET_PATTERN`` 에 둔다. 기본값과 toml 설정 두 가지를 본다.
"""

from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit.config import flatten_toml, resolve_config  # noqa: E402
from jira_kit.worklog_core import extract_ticket  # noqa: E402


class TicketPatternTest(unittest.TestCase):
    def test_default_matches_any_jira_key(self) -> None:
        """설정이 없으면 프로젝트 키에 숫자가 든 키까지 worktree 이름 앞에서 뽑는다."""
        pattern = resolve_config({}, {}, {}).ticket_pattern
        for name, ticket in (("ABC-123-demo", "ABC-123"), ("AB1-12-fix", "AB1-12")):
            with self.subTest(name):
                self.assertEqual(extract_ticket(name, pattern, anchored=True), ticket)

    def test_toml_literal_string_replaces_the_default(self) -> None:
        """문서 형식(``[worklog]`` 아래 작은따옴표 리터럴)의 패턴이 기본값을 대체해 다른 키는 잡히지 않는다."""
        toml = r"""
[worklog]
ticket_pattern = 'XY-\d+'
"""
        pattern = resolve_config({}, {}, flatten_toml(tomllib.loads(toml))).ticket_pattern
        self.assertEqual(extract_ticket("XY-7-demo", pattern, anchored=True), "XY-7")
        self.assertIsNone(extract_ticket("ABC-123-demo", pattern, anchored=True))


if __name__ == "__main__":
    unittest.main()
