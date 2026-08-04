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
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit.session_time import (  # noqa: E402
    Bucket,
    BucketKind,
    ai_intervals,
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


def line(minutes: int, kind: str, cwd: str | None) -> str:
    """세션 jsonl 한 줄. cwd 가 None 이면 필드 자체를 뺀다(실데이터의 메타 줄 모사)."""
    obj: dict = {
        "type": kind,
        "timestamp": (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z"),
    }
    if cwd is not None:
        obj["cwd"] = cwd
    if kind == "user":
        obj["message"] = {"content": "hi"}
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


class BucketIntervalsTest(unittest.TestCase):
    """인접 쌍의 bucket 이 같을 때만 interval 을 발행한다."""

    LIVE_BUCKET = Bucket(BucketKind.LIVE, "alive")
    MAIN_BUCKET = Bucket(BucketKind.MAIN, None)

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
            line(70, "assistant", LIVE_WT),  # 60분 초과 gap → 기존 규칙대로 제외
            line(75, "user", LIVE_WT),       # assistant→user 대기 → 제외
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
        self.assertIn(Bucket(BucketKind.UNMATCHED, None), buckets)
        self.assertNotIn(self.MAIN_BUCKET, buckets)


class WorklogFromIntervalsTest(unittest.TestCase):
    def test_splits_by_date_and_sums(self):
        start = datetime(2026, 8, 4, 23, 30, tzinfo=TZ)
        worklogs = worklog_from_intervals([(start, start + timedelta(hours=1))])
        self.assertEqual([w.day.day for w in worklogs], [4, 5])
        self.assertEqual(sum(w.seconds for w in worklogs), 3600)


if __name__ == "__main__":
    unittest.main(verbosity=2)
