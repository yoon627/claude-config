#!/usr/bin/env python3
"""commit_units.py 테스트 (stdlib unittest). 실제 git 을 임시 repo 에서 돌린다.

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_commit_units.py

모든 git 호출은 사용자·CI 전역 설정과 격리된 env 로 돈다(`isolated_env`) — 전역
`commit.gpgsign`·`core.hooksPath`·`init.defaultBranch` 가 fixture 결과를 바꾸지 않게.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
import commit_units as cu  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "commit_units.py"


def isolated_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        HOME=str(home),
        GIT_AUTHOR_NAME="Me",
        GIT_AUTHOR_EMAIL="me@example.com",
        GIT_COMMITTER_NAME="Me",
        GIT_COMMITTER_EMAIL="me@example.com",
    )
    return env


class Repo:
    def __init__(self, root: Path, env: dict[str, str]) -> None:
        self.root = root
        self.env = env

    def git(self, *args: str, env: dict[str, str] | None = None, check: bool = True) -> str:
        r = subprocess.run(
            ["git", *args], cwd=self.root, env=env or self.env, capture_output=True, text=True
        )
        if check and r.returncode != 0:
            raise AssertionError(f"git {args} failed: {r.stderr}")
        return r.stdout.strip()

    def write(self, path: str, text: str) -> None:
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, message: str, files: dict[str, str] | None = None, author: tuple[str, str, str] | None = None,
               remove: list[str] | None = None, allow_empty: bool = False) -> str:
        for path, text in (files or {}).items():
            self.write(path, text)
            self.git("add", "--", path)
        for path in remove or []:
            self.git("rm", "-q", "--", path)
        env = dict(self.env)
        if author:
            env.update(GIT_AUTHOR_NAME=author[0], GIT_AUTHOR_EMAIL=author[1], GIT_AUTHOR_DATE=author[2])
        args = ["commit", "-q", "-F", "-"]
        if allow_empty:
            args.insert(1, "--allow-empty")
        r = subprocess.run(["git", *args], cwd=self.root, env=env, input=message, capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError(r.stderr)
        return self.git("rev-parse", "HEAD")

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def tree(self, rev: str = "HEAD") -> str:
        return self.git("rev-parse", f"{rev}^{{tree}}")

    def subjects(self, rng: str) -> list[str]:
        out = self.git("log", "--reverse", "--format=%s", rng)
        return out.splitlines() if out else []

    def files(self, rev: str) -> set[str]:
        out = self.git("diff-tree", "-r", "--no-commit-id", "--name-only", "--no-renames", rev)
        return set(out.splitlines())

    def state(self) -> tuple[str, str, str, str]:
        return (
            self.git("symbolic-ref", "-q", "HEAD", check=False),
            self.head(),
            self.git("ls-files", "-s"),
            self.git("status", "--porcelain"),
        )


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        self.env = isolated_env(tmp)
        root = tmp / "repo"
        root.mkdir()
        self.r = Repo(root, self.env)
        self.r.git("init", "-q", "-b", "main")
        self.base = self.r.commit("base", {"f": "a\n"})
        self.r.git("checkout", "-q", "-b", "feat")

    def g(self) -> cu.Git:
        return cu.Git(self.r.root, env=self.env)

    def collect(self) -> dict:
        return cu.collect(self.g())

    def apply(self, plan: dict) -> dict:
        return cu.apply(self.g(), plan)

    def plan(self, entries: list[dict], data: dict | None = None) -> dict:
        data = data or self.collect()
        return {"schema": cu.SCHEMA, "base": data["base"], "head": data["head"], "commits": entries}

    def feature_history(self) -> tuple[str, str, str]:
        a = self.r.commit(
            "feat: b and g\n\nCo-Authored-By: Bot <bot@example.com>\n",
            {"f": "a\nb\n", "g": "x\n"},
            author=("Orig", "orig@example.com", "2020-01-02T03:04:05+0000"),
        )
        b = self.r.commit("feat: h", {"h": "c\n"})
        c = self.r.commit("리뷰 반영", {"f": "a\nb\nb2\n"})
        return a, b, c


class ApplyFailureKeepsStateTest(Base):
    """실패하면 심볼릭 HEAD·브랜치·index·작업트리가 호출 전과 같아야 한다."""

    def assert_refused(self, plan: dict) -> None:
        before = self.r.state()
        with self.assertRaises(cu.CommitCheckError):
            self.apply(plan)
        self.assertEqual(before, self.r.state())
        self.assertEqual("", self.r.git("for-each-ref", "refs/commit-check/"))

    def test_missing_commit_rejected(self) -> None:
        a, b, c = self.feature_history()
        self.assert_refused(self.plan([{"from": [a]}, {"from": [b]}]))

    def test_duplicate_commit_rejected(self) -> None:
        a, b, c = self.feature_history()
        self.assert_refused(self.plan([{"from": [a, c]}, {"from": [b]}, {"from": [c]}]))

    def test_split_missing_path_rejected(self) -> None:
        a, b, c = self.feature_history()
        self.assert_refused(self.plan([{"from": [a], "paths": ["f"], "message": "feat: b"}, {"from": [b]}, {"from": [c]}]))

    def test_split_overlapping_paths_rejected(self) -> None:
        a, b, c = self.feature_history()
        self.assert_refused(self.plan([
            {"from": [a], "paths": ["f", "g"], "message": "x"},
            {"from": [a], "paths": ["g"], "message": "y"},
            {"from": [b]}, {"from": [c]},
        ]))

    def test_rename_pair_split_apart_rejected(self) -> None:
        big = self.r.commit("big", {"long.txt": "".join(f"line {i}\n" for i in range(40))})
        self.r.git("mv", "long.txt", "moved.txt")
        self.r.git("commit", "-q", "-m", "move")
        mv = self.r.head()
        data = self.collect()
        self.assertTrue(any(f.get("old_path") == "long.txt" for f in data["commits"][1]["files"]))
        self.assert_refused(self.plan([
            {"from": [big]},
            {"from": [mv], "paths": ["long.txt"], "message": "del"},
            {"from": [mv], "paths": ["moved.txt"], "message": "add"},
        ], data))

    def test_stale_head_rejected(self) -> None:
        self.feature_history()
        data = self.collect()
        self.r.commit("later", {"k": "1\n"})
        entries = [{"from": [c["sha"]]} for c in data["commits"]]
        self.assert_refused(self.plan(entries, data))

    def test_in_progress_rebase_rejected(self) -> None:
        self.feature_history()
        data = self.collect()
        gitdir = Path(self.r.git("rev-parse", "--absolute-git-dir"))
        (gitdir / "rebase-merge").mkdir()
        self.addCleanup(lambda: (gitdir / "rebase-merge").rmdir())
        self.assert_refused(self.plan([{"from": [c["sha"]]} for c in data["commits"]], data))

    def test_detached_head_rejected(self) -> None:
        self.feature_history()
        data = self.collect()
        self.r.git("checkout", "-q", "--detach")
        before = self.r.state()
        with self.assertRaises(cu.CommitCheckError):
            self.apply(self.plan([{"from": [c["sha"]]} for c in data["commits"]], data))
        self.assertEqual(before, self.r.state())

    def test_conflicting_reorder_rejected(self) -> None:
        a = self.r.commit("add line", {"f": "a\nb\n"})
        b = self.r.commit("edit line", {"f": "a\nB\n"})
        self.assert_refused(self.plan([{"from": [b]}, {"from": [a]}]))

    def test_plan_producing_empty_commit_rejected(self) -> None:
        a = self.r.commit("add k", {"k": "1\n"})
        b = self.r.commit("drop k", remove=["k"])
        c = self.r.commit("add m", {"m": "1\n"})
        self.assert_refused(self.plan([{"from": [a, b]}, {"from": [c]}]))

    def test_signed_commit_in_range_rejected(self) -> None:
        self.feature_history()
        raw = self.r.git("cat-file", "commit", "HEAD")
        head_fields, _, msg = raw.partition("\n\n")
        forged = head_fields + "\ngpgsig -----BEGIN PGP SIGNATURE-----\n \n -----END PGP SIGNATURE-----\n\n" + msg + "\n"
        sha = subprocess.run(["git", "hash-object", "-t", "commit", "-w", "--stdin"], cwd=self.r.root, env=self.env,
                             input=forged, capture_output=True, text=True, check=True).stdout.strip()
        self.r.git("update-ref", "refs/heads/feat", sha)
        data = self.collect()
        self.assertTrue(data["signed"])
        self.assert_refused(self.plan([{"from": [c["sha"]]} for c in data["commits"]], data))


    def test_commit_msg_hook_rejecting_new_message(self) -> None:
        a, b, c = self.feature_history()
        hooks = Path(self.r.git("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / "commit-msg"
        hook.write_text("#!/bin/sh\ngrep -q '^\\[X-1\\]' \"$1\" || { echo 'need [X-1]' >&2; exit 1; }\n")
        hook.chmod(0o755)
        self.assert_refused(self.plan([{"from": [a, c], "message": "no prefix"}, {"from": [b]}]))

    def test_old_git_version_rejected(self) -> None:
        a, b, c = self.feature_history()

        class OldGit(cu.Git):
            def run(self, *args, **kw):  # type: ignore[override]
                if list(args) == ["version"]:
                    return b"git version 2.39.5\n"
                return super().run(*args, **kw)

        before = self.r.state()
        with self.assertRaises(cu.CommitCheckError):
            cu.apply(OldGit(self.r.root, env=self.env), self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertEqual(before, self.r.state())


    def test_malformed_plan_rejected_without_traceback(self) -> None:
        a, b, c = self.feature_history()
        data = self.collect()
        for bad in ({"schema": 1, "base": data["base"], "head": data["head"], "commits": [1]},
                    {"schema": 1, "base": data["base"], "head": data["head"], "commits": [{"from": [["x"]]}]},
                    [1, 2]):
            with self.assertRaises(cu.CommitCheckError):
                self.apply(bad)  # type: ignore[arg-type]

    def test_file_to_directory_split_apart_rejected(self) -> None:
        self.r.git("rm", "-q", "f")
        self.r.write("f/z", "1\n")
        self.r.git("add", "f/z")
        a = self.r.commit("f becomes dir")
        self.assert_refused(self.plan([
            {"from": [a], "paths": ["f"], "message": "drop f"},
            {"from": [a], "paths": ["f/z"], "message": "add f/z"},
        ]))

    def test_default_branch_rejected(self) -> None:
        self.r.git("checkout", "-q", "main")
        self.r.commit("local only", {"k": "1\n"})
        self.assert_refused(self.plan([{"from": [c["sha"]]} for c in self.collect()["commits"]]))

    def test_hook_runs_when_trailers_change_message(self) -> None:
        a = self.r.commit("feat: x", {"x": "1\n"})
        b = self.r.commit("fix x\n\nCo-Authored-By: B <b@x>\n", {"x": "2\n"})
        hooks = Path(self.r.git("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks.mkdir(exist_ok=True)
        (hooks / "commit-msg").write_text("#!/bin/sh\nexit 1\n")
        (hooks / "commit-msg").chmod(0o755)
        self.assert_refused(self.plan([{"from": [a, b]}]))


class ApplyRestructureTest(Base):
    def test_apply_in_clone_with_origin_head_symref(self) -> None:
        origin = self.r.root.parent / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], env=self.env, check=True)
        self.r.git("remote", "add", "origin", str(origin))
        self.r.git("push", "-q", "origin", "main")
        self.r.git("remote", "set-head", "origin", "main")
        a, b, c = self.feature_history()
        head_tree = self.r.tree()
        self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertEqual(head_tree, self.r.tree())

    def test_prune_ignores_nested_branch_namespace(self) -> None:
        a, b, c = self.feature_history()
        for i in range(6):
            self.r.git("update-ref", f"refs/commit-check/feat/x/2020010{i}T000000Z", "HEAD")
        res = self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertTrue(self.r.git("rev-parse", "--verify", "-q", res["backup_ref"]))
        self.assertEqual(6, len(self.r.git("for-each-ref", "refs/commit-check/feat/x/").splitlines()))

    def test_prune_is_part_of_ref_transaction(self) -> None:
        self.r.commit("x", {"x": "1\n"})
        for i in range(6):
            self.r.git("update-ref", f"refs/commit-check/feat/2020010{i}T000000Z", "HEAD")
        calls: list[list[str]] = []

        class Recording(cu.Git):
            def run(self, *args, **kw):  # type: ignore[override]
                calls.append(list(args))
                return super().run(*args, **kw)

        data = self.collect()
        cu.apply(Recording(self.r.root, env=self.env),
                 self.plan([{"from": [c["sha"]], "message": "x2"} for c in data["commits"]], data))
        self.assertFalse([c for c in calls if c[:2] == ["update-ref", "-d"]])
        self.assertEqual(5, len(self.r.git("for-each-ref", "refs/commit-check/feat/").splitlines()))

    def test_apply_from_subdirectory_splits_deletion(self) -> None:
        self.r.commit("seed", {"d/keep": "1\n", "d/gone": "1\n"})
        a = self.r.commit("drop and add", {"d/new": "completely different\n"}, remove=["d/gone"])
        head_tree = self.r.tree()
        data = self.collect()
        plan = self.plan([
            {"from": [data["commits"][0]["sha"]]},
            {"from": [a], "paths": ["d/gone"], "message": "drop gone"},
            {"from": [a], "paths": ["d/new"], "message": "add new"},
        ], data)
        cu.apply(cu.Git(self.r.root / "d", env=self.env), plan)
        self.assertEqual(head_tree, self.r.tree())

    def test_gitlink_split(self) -> None:
        self.r.git("update-index", "--add", "--cacheinfo", f"160000,{self.base},sub")
        a = self.r.commit("add sub and k", {"k": "1\n"})
        head_tree = self.r.tree()
        self.apply(self.plan([
            {"from": [a], "paths": ["sub"], "message": "add sub"},
            {"from": [a], "paths": ["k"], "message": "add k"},
        ]))
        self.assertEqual(head_tree, self.r.tree())

    def test_trailer_after_divider_line_kept(self) -> None:
        a = self.r.commit("feat: x", {"x": "1\n"})
        b = self.r.commit("fix x\n\n---\n\nCo-Authored-By: D <d@x>\n", {"x": "2\n"})
        self.apply(self.plan([{"from": [a, b]}]))
        self.assertIn("Co-Authored-By: D <d@x>", self.r.git("log", "-1", "--format=%B"))

    def test_single_value_change_id_keeps_target(self) -> None:
        a = self.r.commit("feat: x\n\nChange-Id: I111\n", {"x": "1\n"})
        b = self.r.commit("fix x\n\nChange-Id: I222\n", {"x": "2\n"})
        self.apply(self.plan([{"from": [a, b]}]))
        body = self.r.git("log", "-1", "--format=%B")
        self.assertIn("Change-Id: I111", body)
        self.assertNotIn("I222", body)

    def test_result_lists_files_per_new_commit(self) -> None:
        a, b, c = self.feature_history()
        res = self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertEqual([["f", "g"], ["h"]], [x["files"] for x in res["commits"]])

    def test_commit_msg_hook_can_rewrite_message(self) -> None:
        a, b, c = self.feature_history()
        hooks = Path(self.r.git("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / "commit-msg"
        hook.write_text("#!/bin/sh\nprintf '[X-1] %s\\n' \"$(cat \"$1\")\" > \"$1.tmp\" && mv \"$1.tmp\" \"$1\"\n")
        hook.chmod(0o755)
        self.apply(self.plan([{"from": [a, c], "message": "feat: b and g"}, {"from": [b]}]))
        self.assertEqual(["[X-1] feat: b and g", "feat: h"], self.r.subjects(f"{self.base}..HEAD"))

    def test_rename_pair_kept_together_in_split(self) -> None:
        self.r.commit("big", {"long.txt": "".join(f"line {i}\n" for i in range(40))})
        self.r.git("mv", "long.txt", "moved.txt")
        self.r.write("n", "1\n")
        self.r.git("add", "n")
        self.r.git("commit", "-q", "-m", "move and add")
        data = self.collect()
        mv = data["commits"][1]
        self.assertTrue(any(f.get("old_path") == "long.txt" for f in mv["files"]))
        head_tree = self.r.tree()
        first = data["commits"][0]["sha"]
        self.apply(self.plan([
            {"from": [first]},
            {"from": [mv["sha"]], "paths": ["long.txt", "moved.txt"], "message": "move"},
            {"from": [mv["sha"]], "paths": ["n"], "message": "add n"},
        ], data))
        self.assertEqual(head_tree, self.r.tree())

    def test_originally_empty_commit_kept(self) -> None:
        a = self.r.commit("marker", allow_empty=True)
        b = self.r.commit("feat: k", {"k": "1\n"})
        self.apply(self.plan([{"from": [a], "message": "marker 2"}, {"from": [b]}]))
        self.assertEqual(["marker 2", "feat: k"], self.r.subjects(f"{self.base}..HEAD"))

    def test_dirty_worktree_preserved(self) -> None:
        a, b, c = self.feature_history()
        self.r.write("h", "staged\n")
        self.r.git("add", "h")
        self.r.write("f", "unstaged\n")
        before = (self.r.git("status", "--porcelain"), self.r.git("diff"), self.r.git("diff", "--cached"))
        self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertEqual(before, (self.r.git("status", "--porcelain"), self.r.git("diff"), self.r.git("diff", "--cached")))
        self.assertEqual("unstaged\n", (self.r.root / "f").read_text())

    def test_fold_followup_into_target(self) -> None:
        a, b, c = self.feature_history()
        head_tree = self.r.tree()
        res = self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertEqual(head_tree, self.r.tree())
        self.assertEqual(["feat: b and g", "feat: h"], self.r.subjects(f"{self.base}..HEAD"))
        first = self.r.git("rev-list", "--reverse", f"{self.base}..HEAD").splitlines()[0]
        self.assertEqual({"f", "g"}, self.r.files(first))
        self.assertEqual("Orig|orig@example.com|1577934245 +0000",
                         self.r.git("log", "-1", "--format=%an|%ae|%ad", "--date=raw", first))
        self.assertIn("Co-Authored-By: Bot <bot@example.com>", self.r.git("log", "-1", "--format=%B", first))
        self.assertEqual(res["new_head"], self.r.head())
        self.assertEqual("", self.r.git("status", "--porcelain"))

    def test_reorder_and_reword(self) -> None:
        a, b, c = self.feature_history()
        head_tree = self.r.tree()
        self.apply(self.plan([{"from": [b], "message": "feat: add h"}, {"from": [a, c]}]))
        self.assertEqual(head_tree, self.r.tree())
        self.assertEqual(["feat: add h", "feat: b and g"], self.r.subjects(f"{self.base}..HEAD"))

    def test_split_by_path_keeps_author_and_trailers(self) -> None:
        a, b, c = self.feature_history()
        head_tree = self.r.tree()
        self.apply(self.plan([
            {"from": [a, c], "paths": ["f"], "message": "feat: b"},
            {"from": [a], "paths": ["g"], "message": "feat: g"},
            {"from": [b]},
        ]))
        self.assertEqual(head_tree, self.r.tree())
        revs = self.r.git("rev-list", "--reverse", f"{self.base}..HEAD").splitlines()
        self.assertEqual(["feat: b", "feat: g", "feat: h"], self.r.subjects(f"{self.base}..HEAD"))
        self.assertEqual([{"f"}, {"g"}, {"h"}], [self.r.files(x) for x in revs])
        for rev in revs[:2]:
            self.assertEqual("Orig", self.r.git("log", "-1", "--format=%an", rev))
            self.assertIn("Co-Authored-By: Bot <bot@example.com>", self.r.git("log", "-1", "--format=%B", rev))

    def test_trailers_merged_without_duplicates(self) -> None:
        a = self.r.commit("feat: x\n\nCo-Authored-By: A <a@x>\n", {"x": "1\n"})
        b = self.r.commit("fix x\n\nCo-Authored-By: A <a@x>\nCo-Authored-By: B <b@x>\n", {"x": "2\n"})
        self.apply(self.plan([{"from": [a, b]}]))
        body = self.r.git("log", "-1", "--format=%B")
        self.assertEqual(1, body.count("Co-Authored-By: A <a@x>"))
        self.assertIn("Co-Authored-By: B <b@x>", body)
        self.assertTrue(body.startswith("feat: x"))

    def test_korean_path_split(self) -> None:
        a = self.r.commit("feat: 두 파일", {"한글.txt": "1\n", "other.txt": "2\n"})
        head_tree = self.r.tree()
        self.apply(self.plan([
            {"from": [a], "paths": ["한글.txt"], "message": "feat: 한글"},
            {"from": [a], "paths": ["other.txt"], "message": "feat: other"},
        ]))
        self.assertEqual(head_tree, self.r.tree())

    def test_backup_ref_and_rollback(self) -> None:
        a, b, c = self.feature_history()
        old = self.r.head()
        res = self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertEqual(old, self.r.git("rev-parse", res["backup_ref"]))
        self.assertTrue(res["backup_ref"].startswith("refs/commit-check/feat/"))
        args = res["rollback"]
        self.assertEqual(["git", "update-ref", "refs/heads/feat", old, res["new_head"]], args)
        self.r.git(*args[1:])
        self.assertEqual(old, self.r.head())

    def test_backups_pruned_to_five(self) -> None:
        self.r.commit("x", {"x": "1\n"})
        for i in range(7):
            self.r.git("update-ref", f"refs/commit-check/feat/2020010{i}T000000Z", "HEAD")
        data = self.collect()
        self.apply(self.plan([{"from": [c["sha"]], "message": "x2"} for c in data["commits"]], data))
        refs = self.r.git("for-each-ref", "--format=%(refname)", "refs/commit-check/feat/").splitlines()
        self.assertEqual(5, len(refs))

    def test_second_run_on_restructured_branch_is_noop_plan(self) -> None:
        a, b, c = self.feature_history()
        self.apply(self.plan([{"from": [a, c]}, {"from": [b]}]))
        data = self.collect()
        self.assertEqual(2, len(data["commits"]))
        self.assertEqual([], [x for x in data["overlaps"]])

    def test_no_push_in_apply(self) -> None:
        a, b, c = self.feature_history()
        calls: list[list[str]] = []

        class Recording(cu.Git):
            def run(self, *args, **kw):  # type: ignore[override]
                calls.append(list(args))
                return super().run(*args, **kw)

        g = Recording(self.r.root, env=self.env)
        cu.apply(g, self.plan([{"from": [a, c]}, {"from": [b]}]))
        self.assertTrue(calls)
        self.assertFalse([c for c in calls if "push" in c])


class CollectTest(Base):
    def test_range_and_base(self) -> None:
        a, b, c = self.feature_history()
        data = self.collect()
        self.assertEqual(cu.SCHEMA, data["schema"])
        self.assertEqual(self.base, data["base"])
        self.assertEqual([a, b, c], [x["sha"] for x in data["commits"]])
        self.assertEqual("feat", data["branch"])

    def test_local_main_ahead_excludes_merged_commits(self) -> None:
        a = self.r.commit("feat: a", {"k": "1\n"})
        self.r.git("checkout", "-q", "main")
        self.r.git("merge", "-q", "--ff-only", "feat")
        self.r.git("checkout", "-q", "feat")
        b = self.r.commit("feat: b", {"k": "2\n"})
        data = self.collect()
        self.assertEqual([b], [x["sha"] for x in data["commits"]])
        self.assertEqual(a, data["base"])

    def test_pushed_commits_excluded(self) -> None:
        origin = self.r.root.parent / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], env=self.env, check=True)
        self.r.git("remote", "add", "origin", str(origin))
        self.r.git("push", "-q", "origin", "main")
        a = self.r.commit("feat: a", {"k": "1\n"})
        self.r.git("push", "-q", "origin", "feat")
        b = self.r.commit("feat: b", {"k": "2\n"})
        data = self.collect()
        self.assertEqual([b], [x["sha"] for x in data["commits"]])
        self.assertEqual(1, data["excluded"]["published"])

    def test_origin_ahead_of_local_main(self) -> None:
        origin = self.r.root.parent / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], env=self.env, check=True)
        self.r.git("remote", "add", "origin", str(origin))
        self.r.git("push", "-q", "origin", "main")
        other = self.r.root.parent / "other"
        subprocess.run(["git", "clone", "-q", str(origin), str(other)], env=self.env, check=True)
        o = Repo(other, self.env)
        o.commit("upstream", {"u": "1\n"})
        o.git("push", "-q", "origin", "main")
        self.r.git("fetch", "-q", "origin")
        a = self.r.commit("feat: a", {"k": "1\n"})
        data = self.collect()
        self.assertEqual([a], [x["sha"] for x in data["commits"]])

    def test_tagged_commits_excluded(self) -> None:
        a = self.r.commit("feat: a", {"k": "1\n"})
        self.r.git("tag", "v1", a)
        b = self.r.commit("feat: b", {"k": "2\n"})
        data = self.collect()
        self.assertEqual([b], [x["sha"] for x in data["commits"]])
        self.assertEqual(1, data["excluded"]["tags"])

    def test_tag_named_like_branch(self) -> None:
        self.r.git("tag", "feat", self.base)
        a = self.r.commit("feat: a", {"k": "1\n"})
        data = self.collect()
        self.assertEqual("feat", data["branch"])
        self.assertEqual([a], [x["sha"] for x in data["commits"]])

    def test_published_counts_only_branch_commits(self) -> None:
        origin = self.r.root.parent / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], env=self.env, check=True)
        self.r.git("remote", "add", "origin", str(origin))
        self.r.git("checkout", "-q", "main")
        self.r.commit("upstream", {"u": "1\n"})
        self.r.git("push", "-q", "origin", "main")
        self.r.git("reset", "-q", "--soft", "HEAD~1")
        self.r.git("stash", "-q")
        self.r.git("remote", "set-head", "origin", "main")
        self.r.git("checkout", "-q", "-B", "feat", "origin/main")
        data = self.collect()
        self.assertEqual([], data["commits"])
        self.assertEqual(0, data["excluded"]["published"])

    def test_single_branch_repo_explains_missing_base(self) -> None:
        self.r.git("branch", "-q", "-D", "main")
        self.r.commit("feat: a", {"k": "1\n"})
        with self.assertRaisesRegex(cu.CommitCheckError, "기준"):
            self.collect()

    def test_convention_samples_skip_merges(self) -> None:
        self.r.git("checkout", "-q", "main")
        self.r.git("checkout", "-q", "-b", "side")
        self.r.commit("side work", {"s": "1\n"})
        self.r.git("checkout", "-q", "main")
        self.r.git("merge", "-q", "--no-ff", "-m", "Merge side", "side")
        self.r.git("checkout", "-q", "feat")
        self.assertNotIn("Merge side", self.collect()["convention_samples"])

    def test_backup_refs_do_not_lock_range(self) -> None:
        a = self.r.commit("feat: a", {"k": "1\n"})
        self.r.git("update-ref", "refs/commit-check/feat/20200101T000000Z", a)
        self.assertEqual([a], [x["sha"] for x in self.collect()["commits"]])

    def test_merge_commit_in_range_rejected(self) -> None:
        self.r.commit("feat: a", {"k": "1\n"})
        self.r.git("checkout", "-q", "-b", "side", "main")
        self.r.commit("side", {"s": "1\n"})
        self.r.git("checkout", "-q", "feat")
        self.r.git("merge", "-q", "--no-ff", "-m", "merge side", "side")
        self.r.git("branch", "-q", "-D", "side")
        with self.assertRaises(cu.CommitCheckError):
            self.collect()

    def test_flags(self) -> None:
        self.r.commit("wip: halfway", {"k": "1\n"})
        self.r.commit("fixup! feat: a", {"k": "2\n"})
        self.r.commit("리뷰 반영", {"k": "3\n"})
        self.r.commit("docs(plan): sync", {"plans/2026-01-01-x/x-plan.md": "p\n"})
        self.r.commit("empty", allow_empty=True)
        flags = [x["flags"] for x in self.collect()["commits"]]
        self.assertIn("wip", flags[0])
        self.assertIn("fixup", flags[1])
        self.assertIn("review-followup", flags[2])
        self.assertIn("plan-only", flags[3])
        self.assertIn("empty", flags[4])

    def test_overlap_ignores_plans(self) -> None:
        self.r.commit("feat: a", {"k": "1\n", "plans/p/p-plan.md": "1\n"})
        self.r.commit("feat: b", {"m": "1\n", "plans/p/p-plan.md": "2\n"})
        self.r.commit("fix k", {"k": "2\n"})
        overlaps = self.collect()["overlaps"]
        self.assertEqual(1, len(overlaps))
        self.assertEqual(["k"], overlaps[0]["files"])

    def test_korean_path_raw(self) -> None:
        self.r.commit("feat: 한글", {"경로/한글.txt": "1\n"})
        files = [f["path"] for f in self.collect()["commits"][0]["files"]]
        self.assertEqual(["경로/한글.txt"], files)

    def test_empty_range(self) -> None:
        data = self.collect()
        self.assertEqual([], data["commits"])
        self.assertEqual(self.r.head(), data["base"])

    def test_convention_samples_from_default(self) -> None:
        self.r.git("checkout", "-q", "main")
        self.r.commit("[ABC-1] feat: 설명", {"z": "1\n"})
        self.r.git("checkout", "-q", "feat")
        self.assertIn("[ABC-1] feat: 설명", self.collect()["convention_samples"])


class CliTest(Base):
    def run_cli(self, *args: str, input: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.r.root, env=self.env,
                              input=input, capture_output=True, text=True)

    def test_collect_then_apply_via_cli(self) -> None:
        a, b, c = self.feature_history()
        out = self.run_cli("collect")
        self.assertEqual(0, out.returncode, out.stderr)
        data = json.loads(out.stdout)
        plan = self.plan([{"from": [a, c]}, {"from": [b]}], data)
        plan_file = self.r.root.parent / "plan.json"
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        res = self.run_cli("apply", str(plan_file))
        self.assertEqual(0, res.returncode, res.stderr)
        self.assertIn("backup_ref", json.loads(res.stdout))

    def test_apply_error_exit_nonzero(self) -> None:
        a, b, c = self.feature_history()
        plan_file = self.r.root.parent / "plan.json"
        plan_file.write_text(json.dumps(self.plan([{"from": [a]}])), encoding="utf-8")
        res = self.run_cli("apply", str(plan_file))
        self.assertNotEqual(0, res.returncode)
        self.assertTrue(res.stderr.strip())

    def test_show_rejects_option_like_argument(self) -> None:
        self.feature_history()
        out = self.r.root.parent / "leak.txt"
        res = self.run_cli("show", "--", f"--output={out}")
        self.assertNotEqual(0, res.returncode)
        self.assertFalse(out.exists())

    def test_show(self) -> None:
        a, b, c = self.feature_history()
        res = self.run_cli("show", b)
        self.assertEqual(0, res.returncode, res.stderr)
        self.assertIn("feat: h", res.stdout)
        self.assertIn("+c", res.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
