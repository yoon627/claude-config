#!/usr/bin/env python3
"""AI 세션 로그 기반 AI 작업시간을 Jira worklog 로 등록/미리보기하는 CLI.

세션 로그(Claude ``~/.claude/projects/<slug>`` + Codex ``~/.codex/sessions``)에서 AI 가 실제
작업한 시간(사용자 응답 대기·긴 공백 제외)을 날짜별로 추정한다. **귀속은 파일이 놓인 폴더가 아니라
줄 단위 cwd 기준**이다 — 세션 파일이 cwd 를 따라 폴더를 옮겨 다녀, 폴더로 귀속하면 오간 세션의
시간이 마지막 위치 한 곳으로 몰린다. 코퍼스는 한 번만 스캔해 worktree 별로 나눈다. 삭제된 worktree
시간은 표시만 하고 등록하지 않는다. 기본은 미리보기(dry-run). 실제 등록은 ``--register`` 이며,
등록 전 diff·게이트를 거쳐 all-or-nothing 으로 반영한다.
(ticket, date, worktree) 마커로 **그 worktree 의** 본인 worklog 를 찾아 없으면 생성, 있으면 시간만
갱신한다(upsert — 재실행 시 skip 아님). 같은 티켓을 여러 worktree 에서 작업하면 worktree 마다
항목이 따로 생기고 티켓 총 작업시간은 Jira 가 합산한다. 인증·설정은 .env / 환경변수 / jira-kit.toml.

이 스킬 디렉토리에서 직접 실행한다(대상 worktree 를 cwd 로):
  python ~/.claude/skills/jira-worklog/jira_worklog.py            # 현재 worktree 미리보기
  python ~/.claude/skills/jira-worklog/jira_worklog.py --all       # 모든 worktree 미리보기
  python ~/.claude/skills/jira-worklog/jira_worklog.py --register   # 현재 worktree 등록
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import date, datetime, tzinfo
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
from jira_kit.markers import worklog_marker  # noqa: E402
from jira_kit.session_time import (  # noqa: E402
    AttributionStats,
    Bucket,
    BucketKind,
    bucket_intervals_from_files,
    codex_intervals,
    find_codex_session_files,
    find_repo_session_files,
    worklog_from_intervals,
)
from jira_kit.worklog_core import DayWorklog, extract_ticket, format_duration  # noqa: E402
from jira_kit.worklog_register import (  # noqa: E402
    gate_reasons,
    plan_worklog_changes,
    upsert_worklog,
)


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


def _ticket_for(wt: Worktree, args: argparse.Namespace, config: Config) -> str | None:
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
    return ticket


def _write_recovery_log(ticket: str, worktree: str, plans: list) -> None:
    """등록 직전 값·worklog id 를 파일로 남긴다 — 수동 복구의 유일한 근거다.

    stdout 만이면 `/e` 가 자동 실행할 때 유실된다. 토큰·PII 는 담지 않는다(§8).
    """
    try:
        log_dir = Path.home() / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"jira-worklog-{date.today().isoformat()}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            for p in plans:
                fh.write(json.dumps({
                    "ticket": ticket, "worktree": worktree, "day": p.day.day.isoformat(),
                    "action": p.action, "old_seconds": p.old_seconds,
                    "new_seconds": p.new_seconds, "worklog_id": p.worklog_id,
                }, ensure_ascii=False) + "\n")
    except OSError as exc:  # 로그 실패가 등록을 막지는 않는다
        print(f"    복구 로그 기록 실패(등록은 진행): {exc}", file=sys.stderr)


def _register(
    config: Config,
    ticket: str,
    worktree: str,
    days: list[DayWorklog],
    user_comment: str | None,
    allow_large: bool = False,
) -> int:
    """그 worktree 의 날짜별 worklog 를 upsert 한다(insert-once 아님). 실패 건수 반환.

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

    # 전 날짜를 먼저 계산해 diff 를 보이고 게이트를 통과한 뒤에만 쓴다(all-or-nothing).
    # Jira 쓰기는 코드 revert 로 되돌릴 수 없어 부분 등록이 남으면 수습이 어렵다.
    try:
        plans = plan_worklog_changes(ticket, worktree, days, existing, my_account_id)
    except JiraError as exc:
        print(f"    등록 계획 실패 → skip: {exc}", file=sys.stderr)
        return len(days)
    for p in plans:
        old = f"{p.old_seconds // 60}m" if p.old_seconds is not None else "없음"
        print(f"    [{p.action}] {p.day.day} {old} → {p.new_seconds // 60}m")
    reasons = gate_reasons(plans)
    if reasons and not allow_large:
        print("    등록 차단 — 변동이 커서 사람이 한 번 봐야 한다:", file=sys.stderr)
        for r in reasons:
            print(f"      {r}", file=sys.stderr)
        print("    확인했으면 --allow-large-change 로 다시 실행", file=sys.stderr)
        return len(days)

    _write_recovery_log(ticket, worktree, plans)
    failures = 0
    for day in days:
        try:
            result = upsert_worklog(
                config.jira, ticket, day, existing, my_account_id,
                worktree=worktree, note_parts=(user_comment,),
            )
            print(f"    {result} {ticket} {day.day} {format_duration(day.seconds)} [{worktree}]")
        except JiraError as exc:
            print(f"    등록 실패 {day.day}: {exc}", file=sys.stderr)
            failures += 1
    return failures


def process(
    wt: Worktree,
    args: argparse.Namespace,
    config: Config,
    tz: tzinfo,
    register: bool,
    claude_intervals: list[tuple[datetime, datetime]],
) -> int:
    # register 는 main 이 계산한 실효값(--all 이면 False) — args.register 를 직접 보지 않는다.
    # claude_intervals 는 main 이 코퍼스를 한 번만 읽어 이 worktree bucket 으로 나눠준 것.
    # Codex 는 줄 단위 cwd 이동이 없어 파일 단위로 이미 갈리므로 여기서 합친다 —
    # 날짜 분할 **전에** union 해야 두 소스의 겹치는 시간이 이중계상되지 않는다.
    name = Path(wt.path).name
    max_gap = args.max_gap if args.max_gap is not None else config.max_gap_minutes
    codex = codex_intervals(find_codex_session_files(wt.path), tz, max_gap)
    days = worklog_from_intervals([*claude_intervals, *codex])
    ticket = _ticket_for(wt, args, config)
    if not days:
        print(f"[{name}] 세션 활동 없음 → skip")
        return 0

    total = sum(d.seconds for d in days)
    print(
        f"[{name}] branch={wt.branch or '(detached)'} "
        f"ticket={ticket or '(없음)'} 활동 {len(days)}일 합계 {format_duration(total)}"
    )
    for day in days:
        # worklog 항목은 worktree 단위로 갈리므로 어떤 마커로 기록될지 등록 전에 보여준다
        # (Jira 를 수동 정리할 때 그대로 찾아 쓸 문자열이라 날짜별 실물을 찍는다).
        marker = f"  {worklog_marker(ticket, day.day, name)}" if ticket else ""
        print(
            f"    {day.day}  {format_duration(day.seconds):>8}  "
            f"(시작 {day.started.strftime('%H:%M')}){marker}"
        )

    if ticket is None and register:
        print("    티켓 매치 없음 → 등록 skip (--ticket-pattern 또는 worktree 이름/브랜치명 확인)")
        return 0
    if register and config.jira is not None and ticket:
        return _register(config, ticket, name, days, args.comment, args.allow_large_change)
    return 0


def _report_unregistrable(
    per_bucket: dict[Bucket, list[tuple[datetime, datetime]]],
    stats: AttributionStats,
    tz: tzinfo,
) -> None:
    """등록되지 않는 시간을 보여준다 — 유실이 안 보이면 감시가 안 된다.

    삭제된 worktree(dead)는 이름을 복원해 표시만 하고 **등록하지 않는다**(등록 가능 여부는
    이름이 아니라 ``Bucket.kind`` 로 판정 — 티켓형 이름의 죽은 worktree 가 새지 않도록).
    """
    dead = sorted(
        ((b, worklog_from_intervals(iv)) for b, iv in per_bucket.items() if b.kind is BucketKind.DEAD),
        key=lambda r: -sum(d.seconds for d in r[1]),
    )
    if dead:
        print("\n삭제된 worktree 의 시간 (표시만 — 등록 대상 아님):")
        for bucket, days in dead[:10]:
            total = sum(d.seconds for d in days)
            print(f"    {format_duration(total):>8}  {bucket.name}")
        if len(dead) > 10:
            print(f"    … 외 {len(dead) - 10}개")

    # 경계 이동 구간만 "폐기"다. repo 밖 cwd 는 **다른 repo 의 시간**이라 유실이 아니고,
    # 거기서 이 CLI 를 돌리면 정상 집계된다 — "제외"로 묶으면 뭔가 잃은 것처럼 오해된다.
    if stats.boundary_dropped:
        print(
            f"\nworktree 경계 이동 {stats.boundary_dropped}구간 "
            f"{format_duration(int(stats.boundary_seconds))} 폐기 (어느 쪽 것도 아니라 버린다)"
        )
    # 규약 밖 삭제 worktree 는 이름 복원이 안 돼 main 으로 흡수된다 — 낯선 항목이 보이면 신호다.
    if len(stats.main_subroots) > 1:
        shown = ", ".join(sorted(stats.main_subroots)[:8])
        more = f" +{len(stats.main_subroots) - 8}" if len(stats.main_subroots) > 8 else ""
        print(f"main 에 귀속된 cwd 갈래: {shown}{more}")


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
    parser.add_argument(
        "--allow-large-change", action="store_true", dest="allow_large_change",
        help="변동 폭이 커서 차단된 등록을 확인 후 진행",
    )
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
        live = list_worktrees()
        root = live[0].path if live else str(Path.cwd())
        max_gap = args.max_gap if args.max_gap is not None else config.max_gap_minutes
        # 코퍼스를 **한 번만** 읽는다. worktree 마다 다시 읽으면 N배 스캔이 된다.
        per_bucket, stats = bucket_intervals_from_files(
            find_repo_session_files(), tz, root, [w.path for w in live], max_gap
        )
        failures = 0
        root_key = Path(root).resolve()
        for wt in worktrees:
            # main worktree 는 LIVE 후보에서 빠져(모든 worktree 의 조상이라) MAIN bucket 에 담긴다.
            # 이름으로만 찾으면 main 시간이 통째로 0 이 된다.
            bucket = (
                Bucket(BucketKind.MAIN)
                if Path(wt.path).resolve() == root_key
                else Bucket(BucketKind.LIVE, Path(wt.path).name)
            )
            try:
                failures += process(wt, args, config, tz, register, per_bucket.get(bucket, []))
            except GitError as exc:
                print(f"[{Path(wt.path).name}] git 오류 → skip: {exc}", file=sys.stderr)
                failures += 1
        _report_unregistrable(per_bucket, stats, tz)
    except GitError as exc:
        print(f"git 오류: {exc}", file=sys.stderr)
        return 2

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
