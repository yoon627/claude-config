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

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kit.session_time import BucketKind, classify_cwd  # noqa: E402

ROOT = "/repo"
LIVE_WT = "/repo/.claude/worktrees/alive"
NESTED_WT = "/repo/.claude/worktrees/alive/.claude/worktrees/nested"
LIVE = [ROOT, LIVE_WT]


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
