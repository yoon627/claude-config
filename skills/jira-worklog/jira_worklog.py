#!/usr/bin/env python3
"""AI 세션 로그 기반 AI 작업시간을 Jira worklog 로 등록/미리보기하는 CLI.

그 worktree 의 세션 로그(Claude ``~/.claude/projects/<slug>`` + Codex ``~/.codex/sessions``)
에서 AI 가 실제 작업한 시간(사용자 응답 대기·긴 공백 제외)을 날짜별로 추정한다. 두 소스가 다
있으면 시간을 union 한다. 어느 소스도 세션이 없으면 '세션 활동 없음'. 기본은 미리보기(dry-run).
실제 등록은 ``--register``. (ticket,date) 마커로 그날 **본인** worklog 를 찾아 없으면 생성,
있으면 시간만 갱신한다(upsert — 재실행 시 skip 아님). 인증·설정은 .env / 환경변수 / jira-kit.toml.

이 스킬 디렉토리에서 직접 실행한다(대상 worktree 를 cwd 로):
  python ~/.claude/skills/jira-worklog/jira_worklog.py            # 현재 worktree 미리보기
  python ~/.claude/skills/jira-worklog/jira_worklog.py --all       # 모든 worktree 미리보기
  python ~/.claude/skills/jira-worklog/jira_worklog.py --register   # 현재 worktree 등록
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from datetime import tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows 콘솔(cp1252)에서 한글·기호 출력 시 UnicodeEncodeError 방지.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

from jira_kit.config import Config, ConfigError, load_config, resolve_timezone  # noqa: E402
from jira_kit.git_util import GitError, Worktree, current_worktree, list_worktrees  # noqa: E402
from jira_kit.jira_client import JiraError, get_myself, get_worklogs  # noqa: E402
from jira_kit.session_time import SessionFiles, ai_worklog_by_date, discover_sessions  # noqa: E402
from jira_kit.worklog_core import DayWorklog, extract_ticket, format_duration  # noqa: E402
from jira_kit.worklog_register import upsert_worklog  # noqa: E402


def select_worktrees(name: str | None, all_worktrees: bool) -> list[Worktree]:
    if all_worktrees:
        return list_worktrees()
    if name:
        matched = [w for w in list_worktrees() if Path(w.path).name == name or w.branch == name]
        if not matched:
            sys.exit(f"worktree 를 찾을 수 없음: {name}")
        return matched
    current = current_worktree()
    if current is None:
        sys.exit("현재 디렉토리가 worktree 최상위가 아닙니다")
    return [current]


def _days_for(
    wt: Worktree, args: argparse.Namespace, config: Config, tz: tzinfo, sessions: SessionFiles
) -> tuple[str | None, list[DayWorklog]]:
    # AI 작업시간: 이 worktree 의 Claude·Codex 세션 로그에서 추정(사용자 대기 제외).
    # 티켓은 worktree 디렉토리 이름의 prefix 에서 우선 뽑는다(anchored) — worklog 는 그
    # worktree 세션 시간이라 대상 티켓도 worktree 자체로 정한다. dir prefix 규약
    # (CSTP1-<id>-<slug>)을 앵커해 이름 중간에 박힌 다른 티켓의 오귀속(billable)을 막는다.
    # dir 이 prefix 로 티켓을 안 주면(비규약 이름·티켓 없음) 브랜치로 fallback 한다(부분일치).
    # detached HEAD(브랜치 없음)도 dir prefix 로 잡히고, 기존 CSTP1 브랜치 worktree 는 회귀 없다.
    pattern = args.ticket_pattern or config.ticket_pattern
    ticket = extract_ticket(Path(wt.path).name, pattern, anchored=True)
    if ticket is None and wt.branch:
        ticket = extract_ticket(wt.branch, pattern)
    max_gap = args.max_gap if args.max_gap is not None else config.max_gap_minutes
    days = ai_worklog_by_date(sessions, tz, max_gap)
    return ticket, days


def _register(config: Config, ticket: str, days: list[DayWorklog], user_comment: str | None) -> int:
    """Jira worklog 를 그날 항목마다 upsert 한다(insert-once 아님). 실패 건수 반환.

    create/update/unchanged 판정·author-scoping·comment 조립은 upsert_worklog 가 담당한다.
    사용자/기존 worklog 조회가 실패하면 안전하게 전량 skip(오등록 방지).
    """
    assert config.jira is not None
    try:
        my_account_id = get_myself(config.jira).get("accountId")
        existing = get_worklogs(config.jira, ticket)
    except JiraError as exc:
        print(f"    worklog 조회 실패 → 등록 skip: {exc}", file=sys.stderr)
        return len(days)
    failures = 0
    for day in days:
        try:
            result = upsert_worklog(
                config.jira, ticket, day, existing, my_account_id, note_parts=(user_comment,)
            )
            print(f"    {result} {ticket} {day.day} {format_duration(day.seconds)}")
        except JiraError as exc:
            print(f"    등록 실패 {day.day}: {exc}", file=sys.stderr)
            failures += 1
    return failures


def process(
    wt: Worktree, args: argparse.Namespace, config: Config, tz: tzinfo, register: bool
) -> int:
    # register 는 main 이 계산한 실효값(--all 이면 False) — args.register 를 직접 보지 않는다.
    name = Path(wt.path).name
    sessions = discover_sessions(wt.path)
    ticket, days = _days_for(wt, args, config, tz, sessions)
    if not days:
        print(f"[{name}] 세션 활동 없음 → skip")
        return 0

    total = sum(d.seconds for d in days)
    print(
        f"[{name}] branch={wt.branch or '(detached)'} "
        f"ticket={ticket or '(없음)'} 활동 {len(days)}일 합계 {format_duration(total)}"
    )
    for day in days:
        print(f"    {day.day}  {format_duration(day.seconds):>8}  (시작 {day.started.strftime('%H:%M')})")

    if ticket is None and register:
        print("    티켓 매치 없음 → 등록 skip (--ticket-pattern 또는 worktree 이름/브랜치명 확인)")
        return 0
    if register and config.jira is not None and ticket:
        return _register(config, ticket, days, args.comment)
    return 0


def _non_negative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("0 이상이어야 합니다")
    return number


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="worktree 작업시간 → Jira worklog 등록")
    parser.add_argument("name", nargs="?", help="worktree 이름(dir 또는 branch). 생략 시 현재 worktree")
    parser.add_argument("--all", action="store_true", help="모든 worktree 미리보기(등록은 안 함)")
    parser.add_argument("--register", action="store_true", help="실제 Jira 등록(기본은 미리보기)")
    parser.add_argument("--max-gap", type=_non_negative_int, default=None, dest="max_gap",
                        help="세션 활동을 끊는 idle gap(분). 미지정 시 설정값")
    parser.add_argument("--ticket-pattern", default=None, dest="ticket_pattern",
                        help="티켓 추출 정규식. 미지정 시 설정값")
    parser.add_argument("--timezone", default=None, help="IANA 타임존(예: Asia/Seoul). 미지정 시 설정값")
    parser.add_argument("--comment", default=None, help="worklog 코멘트(마커와 함께 기록)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.all and args.register:
        print("경고: --all 과 --register 동시 지정 — 등록하지 않고 미리보기만 합니다", file=sys.stderr)

    try:
        config = load_config(Path.cwd())
    except ConfigError as exc:
        print(f"설정 로드 실패: {exc}", file=sys.stderr)
        return 2

    tz_name = args.timezone or config.timezone_name
    tz = resolve_timezone(tz_name)
    if not isinstance(tz, ZoneInfo):
        print(
            f"경고: 타임존 '{tz_name}' 미해석(tzdata 미설치?) — 시스템 로컬 사용. "
            f"정확한 IANA 타임존은 'pip install tzdata'",
            file=sys.stderr,
        )
    register = args.register and not args.all
    if register and config.jira is None:
        print(
            "JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN 미설정 — 등록 불가 (미리보기만 진행)",
            file=sys.stderr,
        )

    try:
        worktrees = select_worktrees(args.name, args.all)
        failures = 0
        for wt in worktrees:
            try:
                failures += process(wt, args, config, tz, register)
            except GitError as exc:
                print(f"[{Path(wt.path).name}] git 오류 → skip: {exc}", file=sys.stderr)
                failures += 1
    except GitError as exc:
        print(f"git 오류: {exc}", file=sys.stderr)
        return 2

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
