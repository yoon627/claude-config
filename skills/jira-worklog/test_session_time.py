#!/usr/bin/env python3
"""세션 시간의 worktree 귀속 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_session_time.py

점검 대상 불변식: 한 세션 파일이 여러 worktree 를 오가더라도 각 구간이 자기 worktree
에만 귀속된다. 세션 파일은 cwd 를 따라 폴더를 옮겨 다니므로 파일이 놓인 폴더가 아니라
**줄 단위 cwd** 가 귀속의 근거다.

``classify_cwd`` 는 이 귀속의 급소라 테이블 테스트로 고정한다. 특히 main 은 모든
worktree 경로의 조상이면서 자신도 worktree 목록에 있어, 매칭 실패를 조상으로 폴백하면
삭제된 worktree 의 시간이 통째로 main 에 흡수된다(실측 3.5배 과다).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit.codex_session import find_codex_sessions  # noqa: E402
from jira_kit.session_time import (  # noqa: E402
    DEFAULT_MAX_GAP_MINUTES,
    Bucket,
    BucketKind,
    WorktreeIndex,
    ai_intervals,
    ai_worklog_by_bucket,
    bucket_codex_intervals,
    bucket_intervals,
    classify_cwd,
    parse_message_events,
    worklog_from_intervals,
)

ROOT = "/repo"
LIVE_WT = "/repo/.claude/worktrees/alive"
NESTED_WT = "/repo/.claude/worktrees/alive/.claude/worktrees/nested"
LIVE = [ROOT, LIVE_WT]

TZ = timezone.utc
T0 = datetime(2026, 8, 4, 10, 0, tzinfo=TZ)


def _event(minutes: int, kind: str, cwd: str | None) -> dict:
    obj: dict = {
        "type": kind,
        "timestamp": (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z"),
    }
    if cwd is not None:
        obj["cwd"] = cwd
    return obj


def line(minutes: int, kind: str, cwd: str | None) -> str:
    """세션 jsonl 한 줄. cwd 가 None 이면 필드 자체를 뺀다(실데이터의 메타 줄 모사)."""
    obj = _event(minutes, kind, cwd)
    if kind == "user":
        obj["message"] = {"content": "hi"}
    return json.dumps(obj)


def tool_use(minutes: int, name: str, cwd: str | None, tool_id: str = "t1") -> str:
    """assistant 의 tool_use 줄. 대화형 도구면 이 뒤 gap 이 사용자 대기다."""
    obj = _event(minutes, "assistant", cwd)
    obj["message"] = {"content": [{"type": "tool_use", "id": tool_id, "name": name}]}
    return json.dumps(obj)


def tool_result(minutes: int, cwd: str | None, tool_id: str = "t1") -> str:
    """tool_result 는 ``type=user`` 로 기록되지만 AI 작업 흐름이다."""
    obj = _event(minutes, "user", cwd)
    obj["message"] = {"content": [{"type": "tool_result", "tool_use_id": tool_id}]}
    return json.dumps(obj)


def jsonl(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def seconds(intervals) -> float:
    return sum((end - start).total_seconds() for start, end in intervals)


class ClassifyCwdTest(unittest.TestCase):
    """cwd → bucket 분류. 각 케이스는 실데이터에서 관찰된 경로 형태다."""

    def assert_bucket(self, cwd, kind, name, live=None):
        bucket = classify_cwd(cwd, ROOT, live if live is not None else LIVE)
        self.assertEqual(bucket.kind, kind, f"{cwd} → kind")
        self.assertEqual(bucket.name, name, f"{cwd} → name")

    def test_repo_root_itself_is_main(self):
        self.assert_bucket(ROOT, BucketKind.MAIN, None)

    def test_subdirectory_of_root_is_main(self):
        self.assert_bucket("/repo/skills/jira-worklog", BucketKind.MAIN, None)

    def test_live_worktree(self):
        self.assert_bucket(LIVE_WT, BucketKind.LIVE, "alive")

    def test_subdirectory_of_live_worktree_belongs_to_it(self):
        # 실데이터에 <wt>/.claude/plans/... 같은 하위 cwd 가 흔하다.
        self.assert_bucket(f"{LIVE_WT}/skills/wt", BucketKind.LIVE, "alive")

    def test_deleted_worktree_is_dead_not_absorbed_into_main(self):
        # 급소: live 목록에 없지만 <root>/.claude/worktrees/<name> 규약으로 복원된다.
        self.assert_bucket("/repo/.claude/worktrees/gone", BucketKind.DEAD, "gone")

    def test_subdirectory_of_deleted_worktree_is_dead(self):
        self.assert_bucket("/repo/.claude/worktrees/gone/src", BucketKind.DEAD, "gone")

    def test_nested_worktree_picks_deepest_candidate(self):
        # <root>, alive, nested 가 모두 매치된다 — 가장 깊은 것을 골라야 한다.
        self.assert_bucket(NESTED_WT, BucketKind.LIVE, "nested", live=[*LIVE, NESTED_WT])

    def test_deleted_nested_worktree_does_not_leak_to_parent_worktree(self):
        # nested 가 삭제돼도 상위 live worktree(alive) 로 흡수되면 과다등록이 된다.
        self.assert_bucket(NESTED_WT, BucketKind.DEAD, "nested")

    def test_worktrees_container_itself_is_main(self):
        # 실데이터에 존재하는 중간 경로. 어떤 worktree 도 아니므로 main.
        self.assert_bucket("/repo/.claude/worktrees", BucketKind.MAIN, None)

    def test_other_repo_is_unmatched_not_main(self):
        # 선검증이 없으면 타 repo 시간이 통째로 main 으로 간다.
        self.assert_bucket("/elsewhere/other-repo", BucketKind.UNMATCHED, None)

    def test_ancestor_of_root_is_unmatched(self):
        # 홈 디렉토리 cwd 가 실데이터에 있다. root 의 조상이지 하위가 아니다.
        self.assert_bucket("/", BucketKind.UNMATCHED, None)

    def test_sibling_with_shared_prefix_is_unmatched(self):
        # 문자열 접두 비교였다면 /repo 가 /repo-backup 에 걸린다.
        self.assert_bucket("/repo-backup", BucketKind.UNMATCHED, None)

    def test_worktree_sibling_with_shared_prefix(self):
        # /repo/.claude/worktrees/alive 가 .../alive-2 의 접두다.
        self.assert_bucket("/repo/.claude/worktrees/alive-2", BucketKind.DEAD, "alive-2")

    def test_missing_cwd_is_unmatched(self):
        self.assert_bucket(None, BucketKind.UNMATCHED, None)


class ParseEventsTest(unittest.TestCase):
    """이벤트에 cwd 가 함께 실려야 bucket 분리가 가능하다."""

    def test_events_carry_cwd(self):
        text = jsonl(
            line(0, "assistant", LIVE_WT),
            line(1, "assistant", ROOT),
        )
        events = parse_message_events(text, TZ)
        self.assertEqual([e[2] for e in events], [LIVE_WT, ROOT])

    def test_missing_cwd_is_none_not_inherited(self):
        # 앞줄 cwd 를 물려받으면 경계가 사라져 오귀속이 된다.
        text = jsonl(
            line(0, "assistant", LIVE_WT),
            line(1, "assistant", None),
        )
        events = parse_message_events(text, TZ)
        self.assertEqual([e[2] for e in events], [LIVE_WT, None])


class WaitExclusionTest(unittest.TestCase):
    """사용자 대기는 role 단계에서 제외한다 — idle gap 백스톱에 기대지 않는다.

    실측(세션 157개 전수): 백스톱을 넘긴 non-wait gap 13건 중 12건이 ``AskUserQuestion``
    응답 대기(합 76.6h), 1건이 ``user→user`` 였다. 즉 백스톱이 하던 일의 실체는 이 두 가지다.
    """

    def intervals(self, *lines: str):
        return ai_intervals(parse_message_events(jsonl(*lines), TZ))

    def test_gap_before_user_input_is_wait_whatever_precedes_it(self):
        # prev==assistant 일 때만 대기로 보면 user→user 구간이 작업으로 샌다(실측 132분).
        self.assertEqual(self.intervals(
            line(0, "user", LIVE_WT),
            line(30, "user", LIVE_WT),
        ), [])

    def test_ask_user_question_wait_is_excluded(self):
        # 사용자가 답하기 전에는 tool_result 가 오지 않는다 — 이 구간은 AI 가 논 시간이다.
        self.assertEqual(self.intervals(
            tool_use(0, "AskUserQuestion", LIVE_WT),
            tool_result(30, LIVE_WT),
        ), [])

    def test_exit_plan_mode_wait_is_excluded(self):
        self.assertEqual(self.intervals(
            tool_use(0, "ExitPlanMode", LIVE_WT),
            tool_result(30, LIVE_WT),
        ), [])

    def test_ordinary_tool_run_is_still_work(self):
        # 회귀 방지: 도구 실행 구간을 대기로 보면 AI 작업시간이 통째로 과소된다.
        self.assertEqual(seconds(self.intervals(
            tool_use(0, "Bash", LIVE_WT),
            tool_result(30, LIVE_WT),
        )), 30 * 60)

    def test_work_before_the_question_is_kept(self):
        # 질문을 만들기까지는 AI 가 일한 시간이다 — 대기는 질문 **이후**부터다.
        self.assertEqual(seconds(self.intervals(
            line(0, "assistant", LIVE_WT),
            tool_use(10, "AskUserQuestion", LIVE_WT),
            tool_result(70, LIVE_WT),
        )), 10 * 60)

    def test_long_tool_run_survives_default_backstop(self):
        # 대기를 정면으로 걸러낸 대가로 백스톱을 완화했다 — 2시간짜리 빌드가 살아난다.
        self.assertEqual(seconds(self.intervals(
            tool_use(0, "Bash", LIVE_WT),
            tool_result(120, LIVE_WT),
        )), 120 * 60)

    def test_backstop_still_cuts_absurd_gaps(self):
        # 백스톱은 남긴다 — 앞으로 추가될 대화형 도구가 같은 구멍을 내면 여기서 막힌다.
        self.assertEqual(self.intervals(
            tool_use(0, "Bash", LIVE_WT),
            tool_result(DEFAULT_MAX_GAP_MINUTES + 60, LIVE_WT),
        ), [])


class BucketIntervalsTest(unittest.TestCase):
    """인접 쌍의 bucket 이 같을 때만 interval 을 발행한다."""

    # bucket 은 분류기에서 얻는다 — 직접 조립하면 프로덕션이 겪은 "키 재구성" 결함을
    # 테스트가 그대로 재현해 회귀를 못 잡는다.
    LIVE_BUCKET = classify_cwd(LIVE_WT, ROOT, LIVE)
    MAIN_BUCKET = classify_cwd(ROOT, ROOT, LIVE)

    def classify(self, text):
        return [
            (moment, role, classify_cwd(cwd, ROOT, LIVE))
            for moment, role, cwd in parse_message_events(text, TZ)
        ]

    def test_round_trip_gives_each_bucket_only_its_own_time(self):
        # main(0~10) → worktree(10~30) → main(30~40). 이동 구간 2개는 폐기된다.
        text = jsonl(
            line(0, "assistant", ROOT),
            line(10, "assistant", ROOT),
            line(20, "assistant", LIVE_WT),
            line(30, "assistant", LIVE_WT),
            line(40, "assistant", ROOT),
            line(50, "assistant", ROOT),
        )
        buckets, stats = bucket_intervals(self.classify(text))
        self.assertEqual(seconds(buckets[self.MAIN_BUCKET]), 20 * 60)
        self.assertEqual(seconds(buckets[self.LIVE_BUCKET]), 10 * 60)
        self.assertEqual(stats.boundary_dropped, 2)
        self.assertEqual(stats.boundary_seconds, 20 * 60)

    def test_total_never_exceeds_elapsed(self):
        text = jsonl(
            line(0, "assistant", ROOT),
            line(10, "assistant", LIVE_WT),
            line(20, "assistant", ROOT),
        )
        buckets, _ = bucket_intervals(self.classify(text))
        total = sum(seconds(v) for v in buckets.values())
        self.assertLessEqual(total, 20 * 60)

    def test_no_bridging_across_other_bucket(self):
        # main 이벤트 두 개 사이에 worktree 구간이 끼면, main 을 가로질러 이어붙이면 안 된다.
        text = jsonl(
            line(0, "assistant", ROOT),
            line(5, "assistant", LIVE_WT),
            line(10, "assistant", ROOT),
        )
        buckets, _ = bucket_intervals(self.classify(text))
        self.assertNotIn(self.MAIN_BUCKET, buckets)

    def test_single_cwd_file_matches_legacy_total(self):
        # 회귀: 오가지 않은 파일은 기존 ai_intervals 결과와 같아야 한다.
        text = jsonl(
            line(0, "assistant", LIVE_WT),
            line(10, "assistant", LIVE_WT),
            line(70, "assistant", LIVE_WT),  # 60분 gap — 백스톱 안이라 작업으로 잡힌다
            line(75, "user", LIVE_WT),       # 사용자 입력 직전 → 대기로 제외
        )
        events = parse_message_events(text, TZ)
        legacy = ai_intervals(events)
        buckets, stats = bucket_intervals(self.classify(text))
        self.assertEqual(seconds(buckets[self.LIVE_BUCKET]), seconds(legacy))
        self.assertEqual(stats.boundary_dropped, 0)

    def test_missing_cwd_acts_as_boundary(self):
        text = jsonl(
            line(0, "assistant", LIVE_WT),
            line(5, "assistant", None),
            line(10, "assistant", LIVE_WT),
        )
        buckets, _ = bucket_intervals(self.classify(text))
        self.assertNotIn(self.LIVE_BUCKET, buckets)

    def test_unmatched_is_kept_separately_not_merged_into_main(self):
        text = jsonl(
            line(0, "assistant", "/elsewhere/other"),
            line(10, "assistant", "/elsewhere/other"),
        )
        buckets, _ = bucket_intervals(self.classify(text))
        self.assertIn(classify_cwd("/elsewhere/other", ROOT, LIVE), buckets)
        self.assertNotIn(self.MAIN_BUCKET, buckets)


class BucketLookupTest(unittest.TestCase):
    """CLI 가 worktree → bucket 을 찾는 규칙. 여기가 어긋나면 시간이 조용히 0 이 된다."""

    def test_same_name_worktrees_are_separate_buckets(self):
        # 이름만으로 가르면 두 worktree 시간이 합쳐져 양쪽에 통째로 등록된다(과다 등록).
        live = [ROOT, "/repo/.claude/worktrees/A", "/elsewhere/A"]
        inside = classify_cwd("/repo/.claude/worktrees/A", ROOT, live)
        outside = classify_cwd("/elsewhere/A", ROOT, live)
        self.assertEqual((inside.name, outside.name), ("A", "A"))
        self.assertNotEqual(inside, outside)

    def test_main_worktree_is_main_bucket_not_live(self):
        # main 은 모든 worktree 의 조상이라 LIVE 후보에서 빠진다. 이름으로 LIVE 를 찾으면
        # main 시간이 통째로 0 이 된다(실제로 겪은 버그).
        bucket = classify_cwd(ROOT, ROOT, LIVE)
        self.assertEqual(bucket.kind, BucketKind.MAIN)
        self.assertNotEqual(bucket, Bucket(BucketKind.LIVE, Path(ROOT).name))

    def test_main_bucket_is_not_registrable(self):
        # main 은 티켓이 없는 게 보통이지만, 등록 가능 판정은 kind 로만 한다.
        self.assertFalse(classify_cwd(ROOT, ROOT, LIVE).registrable)


class WorklogFromIntervalsTest(unittest.TestCase):
    def test_splits_by_date_and_sums(self):
        start = datetime(2026, 8, 4, 23, 30, tzinfo=TZ)
        worklogs = worklog_from_intervals([(start, start + timedelta(hours=1))])
        self.assertEqual([w.day.day for w in worklogs], [4, 5])
        self.assertEqual(sum(w.seconds for w in worklogs), 3600)


class NestedAndOutOfRootTest(unittest.TestCase):
    """리뷰가 재현한 오귀속 두 건의 회귀 방지."""

    def test_nested_dead_with_same_name_as_parent_live_is_not_registrable(self):
        # 이름으로 비교하면 상위 live 로 흡수돼 죽은 worktree 가 등록 대상이 된다.
        bucket = classify_cwd(
            "/repo/.claude/worktrees/A/.claude/worktrees/A", ROOT,
            [ROOT, "/repo/.claude/worktrees/A"],
        )
        self.assertEqual(bucket.kind, BucketKind.DEAD)
        self.assertFalse(bucket.registrable)

    def test_live_worktree_outside_root_is_not_lost(self):
        # root 소속 검증을 live 매칭보다 먼저 하면 규약 밖 worktree 시간이 통째로 사라진다.
        bucket = classify_cwd("/elsewhere/wt", ROOT, [ROOT, "/elsewhere/wt"])
        self.assertEqual(bucket.kind, BucketKind.LIVE)
        self.assertEqual(bucket.name, "wt")

    def test_bucket_name_preserves_case(self):
        # 소문자화되면 extract_ticket 의 대문자 패턴이 어긋나 조용히 미등록된다.
        bucket = classify_cwd(
            "/repo/.claude/worktrees/CSTP1-2812-Foo", ROOT, [ROOT],
        )
        self.assertEqual(bucket.name, "CSTP1-2812-Foo")

    def test_malformed_cwd_does_not_abort(self):
        # cwd 는 로그에서 온 외부 입력이다. 한 줄이 전체 집계를 죽이면 안 된다.
        self.assertEqual(classify_cwd("/repo/\0bad", ROOT, [ROOT]).kind, BucketKind.UNMATCHED)


class AiWorklogByBucketTest(unittest.TestCase):
    """파일을 가로지르는 집계 — 여기서만 드러나는 불변식이 있다."""

    def write(self, directory: Path, name: str, text: str) -> Path:
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_bucket(self, paths):
        return ai_worklog_by_bucket(paths, TZ, ROOT, LIVE)

    def test_does_not_bridge_across_files(self):
        # 파일 = 독립 세션. 서로 다른 파일의 이벤트를 이어붙이면 세션 사이 공백이
        # 작업시간으로 잡힌다.
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            a = self.write(directory, "a.jsonl", jsonl(
                line(0, "assistant", LIVE_WT), line(5, "assistant", LIVE_WT)))
            b = self.write(directory, "b.jsonl", jsonl(
                line(30, "assistant", LIVE_WT), line(35, "assistant", LIVE_WT)))
            worklogs, _ = self.run_bucket([a, b])
        total = sum(w.seconds for w in worklogs[classify_cwd(LIVE_WT, ROOT, LIVE)])
        self.assertEqual(total, 10 * 60)  # 25분 공백이 끼면 안 된다

    def test_unions_overlapping_intervals_across_files(self):
        # 동시에 돌던 두 세션의 겹치는 시간은 한 번만 센다.
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            a = self.write(directory, "a.jsonl", jsonl(
                line(0, "assistant", LIVE_WT), line(10, "assistant", LIVE_WT)))
            b = self.write(directory, "b.jsonl", jsonl(
                line(5, "assistant", LIVE_WT), line(15, "assistant", LIVE_WT)))
            worklogs, _ = self.run_bucket([a, b])
        total = sum(w.seconds for w in worklogs[classify_cwd(LIVE_WT, ROOT, LIVE)])
        self.assertEqual(total, 15 * 60)

    def test_accumulates_boundary_stats_across_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            text = jsonl(line(0, "assistant", ROOT), line(5, "assistant", LIVE_WT))
            paths = [self.write(directory, f"{i}.jsonl", text) for i in range(3)]
            _, stats = self.run_bucket(paths)
        self.assertEqual(stats.boundary_dropped, 3)
        self.assertEqual(stats.boundary_seconds, 3 * 5 * 60)

    def test_unreadable_file_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            good = self.write(directory, "good.jsonl", jsonl(
                line(0, "assistant", LIVE_WT), line(10, "assistant", LIVE_WT)))
            worklogs, _ = self.run_bucket([directory / "missing.jsonl", good])
        self.assertIn(classify_cwd(LIVE_WT, ROOT, LIVE), worklogs)

    def test_dead_bucket_is_not_registrable(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            dead = "/repo/.claude/worktrees/gone"
            path = self.write(directory, "a.jsonl", jsonl(
                line(0, "assistant", dead), line(10, "assistant", dead)))
            worklogs, _ = self.run_bucket([path])
        registrable = [b for b in worklogs if b.registrable]
        self.assertEqual(registrable, [])


def rollout(cwd: str | None, *minutes: int) -> str:
    """Codex rollout jsonl. 첫 줄은 session_meta(cwd), 이후는 response_item(=assistant).

    ``cwd`` 가 None 이면 session_meta 자체를 빼 cwd 미상 rollout 을 모사한다.
    """
    lines = []
    if cwd is not None:
        lines.append(json.dumps({"type": "session_meta", "payload": {"cwd": cwd}}))
    for minute in minutes:
        lines.append(json.dumps({
            "type": "response_item",
            "payload": {"role": "assistant"},
            "timestamp": (T0 + timedelta(minutes=minute)).isoformat().replace("+00:00", "Z"),
        }))
    return "\n".join(lines) + "\n"


class CodexSessionScanTest(unittest.TestCase):
    """rollout 을 **한 번만** 훑어 (파일, cwd) 로 넘긴다 — 필터는 호출자 분류기의 몫."""

    def write(self, home: Path, relative: str, text: str) -> Path:
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_scans_both_live_and_archived_roots(self):
        # 보관된 rollout 을 빼면 보관 후 그 세션 시간이 조용히 사라진다.
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.write(home, ".codex/sessions/2026/08/05/rollout-a.jsonl", rollout("/repo", 0))
            self.write(home, ".codex/archived_sessions/rollout-b.jsonl", rollout("/elsewhere", 0))
            found = dict(find_codex_sessions(home))
        self.assertEqual(sorted(found.values()), ["/elsewhere", "/repo"])

    def test_returns_every_cwd_without_filtering(self):
        # 정확일치 필터를 여기 두면 하위 디렉토리 cwd 가 어느 버킷에도 못 간다(실측 26건).
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.write(home, ".codex/sessions/rollout-a.jsonl", rollout("/repo/sub/dir", 0))
            found = dict(find_codex_sessions(home))
        self.assertEqual(list(found.values()), ["/repo/sub/dir"])

    def test_skips_unusable_first_lines(self):
        # rollout 은 외부 입력이다 — 깨진 파일 하나가 전체 스캔을 죽이면 안 된다.
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.write(home, ".codex/sessions/bad-json.jsonl", "{not json\n")
            self.write(home, ".codex/sessions/rollout-bad.jsonl", "{not json\n")
            self.write(home, ".codex/sessions/rollout-nometa.jsonl",
                       json.dumps({"type": "response_item"}) + "\n")
            self.write(home, ".codex/sessions/rollout-ok.jsonl", rollout("/repo", 0))
            found = dict(find_codex_sessions(home))
        self.assertEqual(list(found.values()), ["/repo"])

    def test_missing_roots_are_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(find_codex_sessions(Path(tmp)), [])


class CodexBucketTest(unittest.TestCase):
    """Codex 귀속을 Claude 와 같은 분류기로 통일 — 소스마다 규칙이 다르면 시간이 샌다."""

    def bucket(self, *sessions: tuple[str, str]) -> dict[Bucket, list]:
        index = WorktreeIndex(ROOT, LIVE)
        with tempfile.TemporaryDirectory() as tmp:
            entries = []
            for name, cwd in sessions:
                path = Path(tmp) / name
                path.write_text(rollout(cwd, 0, 10), encoding="utf-8")
                entries.append((path, cwd))
            return bucket_codex_intervals(entries, TZ, index)

    def test_exact_cwd_goes_to_live_bucket(self):
        buckets = self.bucket(("a.jsonl", LIVE_WT))
        self.assertEqual([b.kind for b in buckets], [BucketKind.LIVE])
        self.assertEqual(next(iter(buckets)).name, "alive")

    def test_subdirectory_cwd_goes_to_the_containing_worktree(self):
        # 정확일치만 보던 옛 규칙은 이 rollout 을 통째로 버렸다.
        buckets = self.bucket(("a.jsonl", LIVE_WT + "/skills/jira-worklog"))
        self.assertEqual([b.kind for b in buckets], [BucketKind.LIVE])
        self.assertEqual(next(iter(buckets)).name, "alive")

    def test_subdirectory_of_dead_worktree_is_dead_not_main(self):
        # main 은 모든 worktree 의 조상이라, 폴백하면 죽은 시간이 main 에 흡수돼 등록된다.
        buckets = self.bucket(("a.jsonl", "/repo/.claude/worktrees/gone/sub"))
        bucket = next(iter(buckets))
        self.assertEqual(bucket.kind, BucketKind.DEAD)
        self.assertEqual(bucket.name, "gone")
        self.assertFalse(bucket.registrable)

    def test_unrelated_cwd_is_unmatched(self):
        buckets = self.bucket(("a.jsonl", "/other/repo"))
        self.assertEqual([b.kind for b in buckets], [BucketKind.UNMATCHED])

    def test_files_in_one_bucket_stay_separate_sessions(self):
        # 파일=독립 세션. 합쳐서 구간을 뽑으면 파일 경계의 긴 공백이 작업시간으로 둔갑한다.
        buckets = self.bucket(("a.jsonl", LIVE_WT), ("b.jsonl", LIVE_WT))
        intervals = next(iter(buckets.values()))
        self.assertEqual(len(intervals), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
