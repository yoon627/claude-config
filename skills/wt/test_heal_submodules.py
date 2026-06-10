#!/usr/bin/env python3
"""heal_submodules.py 의 submodule self-heal 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_heal_submodules.py

핵심 회귀(B1): corrupt submodule 의 work tree 에 사용자 파일이 남아있을 때 heal 이
그걸 deinit 으로 날리면 안 된다 — work tree 에 파일이 있으면 heal 을 거부한다.
이 안전 게이트(`_submodule_worktree_has_files`)는 mock 으로 우회하지 않고 실제
임시 디렉터리로 검증한다(게이트를 mock 하면 버그를 통째로 우회하므로).
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heal_submodules as bootstrap  # noqa: E402


def _err() -> subprocess.CalledProcessError:
    return subprocess.CalledProcessError(1, ["git", "submodule", "update"])


class InitSubmodulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".gitmodules").write_text('[submodule "x"]\n\tpath = sub\n')
        self.addCleanup(self._tmp.cleanup)

    def test_no_gitmodules_returns_early(self) -> None:
        (self.root / ".gitmodules").unlink()
        with mock.patch.object(bootstrap, "run") as run:
            bootstrap.init_submodules(self.root)
        run.assert_not_called()

    def test_update_success_no_heal(self) -> None:
        with (
            mock.patch.object(bootstrap, "run") as run,
            mock.patch.object(bootstrap, "_reset_submodule") as reset,
        ):
            bootstrap.init_submodules(self.root)
        run.assert_called_once()
        reset.assert_not_called()

    def test_heal_when_worktree_empty(self) -> None:
        (self.root / "sub").mkdir()  # empty work tree → safe to reset
        run = mock.Mock(side_effect=[_err(), None])
        with (
            mock.patch.object(bootstrap, "run", run),
            mock.patch.object(
                bootstrap, "_submodule_entries", return_value=[("x", "sub")]
            ),
            mock.patch.object(bootstrap, "_reset_submodule") as reset,
        ):
            bootstrap.init_submodules(self.root)
        self.assertEqual(run.call_count, 2)  # update 실패 → 재clone 성공
        reset.assert_called_once_with("x", "sub")

    def test_refuse_when_worktree_has_files(self) -> None:
        """B1 회귀: work tree 에 파일이 있으면 heal 거부, 절대 reset(파괴) 안 함."""
        sub = self.root / "sub"
        sub.mkdir()
        (sub / "user_edit.txt").write_text("precious work in progress")
        run = mock.Mock(side_effect=[_err()])
        with (
            mock.patch.object(bootstrap, "run", run),
            mock.patch.object(
                bootstrap, "_submodule_entries", return_value=[("x", "sub")]
            ),
            mock.patch.object(bootstrap, "_reset_submodule") as reset,
        ):
            with self.assertRaises(SystemExit):
                bootstrap.init_submodules(self.root)
        reset.assert_not_called()  # 파괴 연산 미실행
        run.assert_called_once()  # 첫 update 만, 재clone 안 함
        self.assertEqual(
            (sub / "user_edit.txt").read_text(), "precious work in progress"
        )

    def test_worktree_with_only_dotgit_is_safe(self) -> None:
        """work tree 에 .git gitlink 파일만 있으면 (사용자 데이터 아님) heal 진행."""
        sub = self.root / "sub"
        sub.mkdir()
        (sub / ".git").write_text("gitdir: ../../.git/modules/x\n")
        run = mock.Mock(side_effect=[_err(), None])
        with (
            mock.patch.object(bootstrap, "run", run),
            mock.patch.object(
                bootstrap, "_submodule_entries", return_value=[("x", "sub")]
            ),
            mock.patch.object(bootstrap, "_reset_submodule") as reset,
        ):
            bootstrap.init_submodules(self.root)
        reset.assert_called_once_with("x", "sub")

    def test_retry_failure_propagates(self) -> None:
        (self.root / "sub").mkdir()
        run = mock.Mock(side_effect=[_err(), _err()])
        with (
            mock.patch.object(bootstrap, "run", run),
            mock.patch.object(
                bootstrap, "_submodule_entries", return_value=[("x", "sub")]
            ),
            mock.patch.object(bootstrap, "_reset_submodule"),
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                bootstrap.init_submodules(self.root)
        self.assertEqual(run.call_count, 2)


class WorktreeHasFilesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.d = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_missing_dir(self) -> None:
        self.assertFalse(bootstrap._submodule_worktree_has_files(self.d / "nope"))

    def test_empty_dir(self) -> None:
        (self.d / "sub").mkdir()
        self.assertFalse(bootstrap._submodule_worktree_has_files(self.d / "sub"))

    def test_only_dotgit(self) -> None:
        sub = self.d / "sub"
        sub.mkdir()
        (sub / ".git").write_text("gitdir: ...")
        self.assertFalse(bootstrap._submodule_worktree_has_files(sub))

    def test_has_real_file(self) -> None:
        sub = self.d / "sub"
        sub.mkdir()
        (sub / "ReportForm.docx").write_text("x")
        self.assertTrue(bootstrap._submodule_worktree_has_files(sub))

    def test_dotgit_dir_is_unsafe(self) -> None:
        """.git 이 디렉터리(미흡수 submodule)면 고유 데이터 가능 → '파일 있음'으로 본다."""
        sub = self.d / "sub"
        (sub / ".git").mkdir(parents=True)
        self.assertTrue(bootstrap._submodule_worktree_has_files(sub))


class ResetSubmoduleTest(unittest.TestCase):
    def test_deinit_failure_tolerated(self) -> None:
        """미초기화 등으로 deinit 이 실패해도 module dir 삭제로 진행한다(best-effort)."""
        with (
            mock.patch.object(bootstrap, "try_capture", return_value="some/modules/x"),
            mock.patch.object(bootstrap, "run", side_effect=_err()),
            mock.patch.object(bootstrap, "_force_rmtree") as rmtree,
        ):
            bootstrap._reset_submodule("x", "sub")  # raise 없이 통과
        rmtree.assert_called_once()

    def test_rmtree_failure_is_surfaced(self) -> None:
        """module dir 삭제가 파일 점유로 실패하면 bare traceback 대신 OSError 를 surface."""
        with (
            mock.patch.object(bootstrap, "try_capture", return_value="some/modules/x"),
            mock.patch.object(bootstrap, "run"),
            mock.patch.object(
                bootstrap, "_force_rmtree", side_effect=OSError("locked")
            ),
        ):
            with self.assertRaises(OSError):
                bootstrap._reset_submodule("x", "sub")


class ForceRmtreeTest(unittest.TestCase):
    def test_removes_readonly_tree(self) -> None:
        """Windows: git pack 파일이 read-only 라 일반 rmtree 가 실패 → 사전 chmod 로 제거."""
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "modules" / "x"
            (target / "objects").mkdir(parents=True)
            ro = target / "objects" / "pack-readonly.idx"
            ro.write_text("data")
            os.chmod(ro, stat.S_IREAD)
            bootstrap._force_rmtree(target)
            self.assertFalse(target.exists())

    def test_missing_path_noop(self) -> None:
        with TemporaryDirectory() as tmp:
            bootstrap._force_rmtree(Path(tmp) / "absent")  # raise 없이 통과


class SubmoduleEntriesTest(unittest.TestCase):
    """`git config -f .gitmodules --get-regexp` 실제 호출(테스트 환경에 git 존재)."""

    def test_parses_name_and_path(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitmodules").write_text(
                '[submodule "manager/app/resources/templates"]\n'
                "\tpath = manager/app/resources/templates\n"
                "\turl = git@example.com:x.git\n"
            )
            entries = bootstrap._submodule_entries(root)
        self.assertEqual(
            entries,
            [("manager/app/resources/templates", "manager/app/resources/templates")],
        )

    def test_no_gitmodules(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(bootstrap._submodule_entries(Path(tmp)), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
