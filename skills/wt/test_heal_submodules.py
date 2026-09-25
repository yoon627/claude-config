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
            mock.patch.object(
                bootstrap, "_module_dir", return_value=Path("modules/x")
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
            mock.patch.object(
                bootstrap, "_module_dir", return_value=Path("modules/x")
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
            mock.patch.object(
                bootstrap, "_module_dir", return_value=Path("modules/x")
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
            mock.patch.object(
                bootstrap, "_module_dir", return_value=Path("modules/x")
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
            mock.patch.object(
                bootstrap, "_module_dir", return_value=Path("some/modules/x")
            ),
            mock.patch.object(bootstrap, "run", side_effect=_err()),
            mock.patch.object(bootstrap, "_force_rmtree") as rmtree,
        ):
            bootstrap._reset_submodule("x", "sub")  # raise 없이 통과
        rmtree.assert_called_once()

    def test_escaping_module_dir_stops_before_any_delete(self) -> None:
        with (
            mock.patch.object(bootstrap, "_module_dir", return_value=None),
            mock.patch.object(bootstrap, "run") as run,
            mock.patch.object(bootstrap, "_force_rmtree") as rmtree,
        ):
            with self.assertRaises(SystemExit):
                bootstrap._reset_submodule("x", "sub")
        run.assert_not_called()
        rmtree.assert_not_called()

    def test_rmtree_failure_is_surfaced(self) -> None:
        """module dir 삭제가 파일 점유로 실패하면 bare traceback 대신 OSError 를 surface."""
        with (
            mock.patch.object(
                bootstrap, "_module_dir", return_value=Path("some/modules/x")
            ),
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

    def test_name_and_path_with_spaces(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitmodules").write_text(
                '[submodule "my sub"]\n\tpath = my sub dir\n'
            )
            self.assertEqual(
                bootstrap._submodule_entries(root), [("my sub", "my sub dir")]
            )

    def test_carriage_return_in_name_is_kept(self) -> None:
        """text 모드는 `\\r` 을 `\\n` 으로 바꿔 name `x\\r` 을 `x` 로 잘라 버린다."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitmodules").write_bytes(b'[submodule "x\r"]\n\tpath = sub\n')
            self.assertEqual(bootstrap._submodule_entries(root), [("x\r", "sub")])


_ISOLATED_GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    env.update(_ISOLATED_GIT_ENV)
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, env=env, check=True, capture_output=True, text=True,
    ).stdout.strip()


class UnsafeModuleNameTest(unittest.TestCase):
    """악성 `.gitmodules` name 이 heal 의 module dir 삭제를 repo·.git 밖으로 돌리지 못해야 한다.
    victim 은 TemporaryDirectory 안에만 두고, 실행 전에 삭제 대상 경로가 정말 victim 인지
    단언한다 — 배치가 틀리면 테스트가 엉뚱한 곳을 지울 수 있다."""

    def setUp(self) -> None:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        env = mock.patch.dict(os.environ, _ISOLATED_GIT_ENV)
        env.start()
        self.addCleanup(env.stop)
        for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            os.environ.pop(var, None)

    def _plant(self, target: Path) -> Path:
        target.mkdir(parents=True)
        keep = target / "keep.txt"
        keep.write_text("must survive")
        return keep

    def _assert_heal_refuses(self, repo: Path, name: str, target: Path) -> None:
        (repo / ".gitmodules").write_text(f'[submodule "{name}"]\n\tpath = sub\n')
        git_path = _git(repo, "rev-parse", "--git-path", f"modules/{name}")
        self.assertEqual((repo / git_path).resolve(), target.resolve())  # 배치 사전 단언
        keep = self._plant(target)
        os.chdir(repo)
        with mock.patch.object(bootstrap, "run", side_effect=_err()):
            with self.assertRaises(SystemExit):
                bootstrap.init_submodules(repo)
        self.assertEqual(keep.read_text(), "must survive")

    def test_refuses_name_escaping_repo(self) -> None:
        repo = self.base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        self._assert_heal_refuses(repo, "../../../victim", self.base / "victim")

    def test_refuses_name_escaping_into_main_git_dir_from_linked_worktree(self) -> None:
        """/wt 실사용 배치: linked worktree 의 modules/<name> 은 <main>/.git/worktrees/<wt>/
        modules 아래라, ../../../ 가 <main>/.git 안(objects 등)을 가리킨다."""
        main = self.base / "main"
        main.mkdir()
        _git(main, "init", "-q")
        _git(main, "commit", "-q", "--allow-empty", "-m", "init")
        wt = self.base / "wt1"
        _git(main, "worktree", "add", "-q", "-b", "wt1", str(wt))
        self._assert_heal_refuses(wt, "../../../sentinel", main / ".git" / "sentinel")

    def test_nested_name_is_allowed(self) -> None:
        repo = self.base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        target = bootstrap._module_dir("manager/app/resources/templates", repo)
        self.assertIsNotNone(target)

    def test_symlinked_module_dir_escaping_is_refused(self) -> None:
        """name 에 `..` 가 없어도 modules 아래 symlink 가 밖을 가리키면 containment 로 거부."""
        repo = self.base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        outside = self.base / "outside"
        outside.mkdir()
        (repo / ".git" / "modules").mkdir()
        (repo / ".git" / "modules" / "evil").symlink_to(outside)
        self.assertIsNone(bootstrap._module_dir("evil", repo))

    def test_trailing_space_name_is_not_trimmed_into_a_sibling(self) -> None:
        repo = self.base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        self.assertNotEqual(
            bootstrap._module_dir("sub ", repo), bootstrap._module_dir("sub", repo)
        )
        self.assertNotEqual(
            bootstrap._module_dir("sub\r", repo), bootstrap._module_dir("sub", repo)
        )

    def test_overlapping_module_dirs_are_refused(self) -> None:
        """name `a/objects` 는 submodule a 의 object DB 를 가리킨다 — 형제 module dir 을 지울 수 있다."""
        repo = self.base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        (repo / ".gitmodules").write_text(
            '[submodule "a"]\n\tpath = a\n[submodule "a/objects"]\n\tpath = b\n'
        )
        os.chdir(repo)
        with (
            mock.patch.object(bootstrap, "run", side_effect=_err()),
            mock.patch.object(bootstrap, "_reset_submodule") as reset,
        ):
            with self.assertRaises(SystemExit):
                bootstrap.init_submodules(repo)
        reset.assert_not_called()


class EntriesFailClosedTest(unittest.TestCase):
    """update 실패 뒤 `.gitmodules` 를 믿을 수 없으면 아무것도 리셋하지 않고 멈춘다."""

    def _assert_stops(self, gitmodules: str) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitmodules").write_text(gitmodules)
            with (
                mock.patch.object(bootstrap, "run", side_effect=_err()),
                mock.patch.object(bootstrap, "_reset_submodule") as reset,
            ):
                with self.assertRaises(SystemExit):
                    bootstrap.init_submodules(root)
            reset.assert_not_called()

    def test_no_path_entries(self) -> None:
        self._assert_stops('[submodule "x"]\n\turl = ./nowhere\n')

    def test_valueless_path(self) -> None:
        self._assert_stops('[submodule "x"]\n\tpath\n')

    def test_config_syntax_error(self) -> None:
        self._assert_stops('[submodule "x"\n\tpath = sub\n')


if __name__ == "__main__":
    unittest.main(verbosity=2)
