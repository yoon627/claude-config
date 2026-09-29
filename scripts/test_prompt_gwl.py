#!/usr/bin/env python3
"""prompt-gwl.py 테스트 (stdlib unittest). 수동 실행: python3 scripts/test_prompt_gwl.py"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("prompt_gwl", Path(__file__).resolve().parent / "prompt-gwl.py")
gwl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gwl)

MAIN = "/home/u/.claude"
NESTED = "/home/u/.claude/.claude/worktrees/feat"
PORCELAIN = (
    f"worktree {MAIN}\nHEAD 1111111aaaa\nbranch refs/heads/main\n\n"
    f"worktree {NESTED}\nHEAD 2222222bbbb\nbranch refs/heads/feat\n\n"
)


def current(cwd: str) -> list[str]:
    return [name for is_cur, name, _, _ in gwl.parse_porcelain(PORCELAIN, gwl.normalize(cwd)) if is_cur]


class ParsePorcelainTest(unittest.TestCase):
    def test_marks_only_the_innermost_worktree(self) -> None:
        self.assertEqual(["feat"], current(NESTED + "/scripts"))
        self.assertEqual([".claude"], current(MAIN + "/scripts"))
        self.assertEqual([], current("/home/u/elsewhere"))


class HookTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "creating symlinks needs extra privileges on Windows")
    def test_symlinked_cwd_marks_the_worktree_git_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            main = Path(tmp) / "main"
            run = lambda *a, cwd=main: subprocess.run(["git", *a], cwd=cwd, env=env, check=True, capture_output=True)
            main.mkdir()
            run("init", "-q", "-b", "main")
            run("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "i")
            run("worktree", "add", "-q", str(main / ".claude" / "worktrees" / "feat"), "-b", "feat")
            link = Path(tmp) / "link"
            link.symlink_to(main / ".claude" / "worktrees" / "feat")
            out = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "prompt-gwl.py")], env=env,
                                 input=json.dumps({"prompt": "gwl", "cwd": str(link / ".")}), capture_output=True, text=True, check=True)
            marked = [ln for ln in json.loads(out.stdout)["reason"].splitlines() if ln.startswith("→")]
            self.assertEqual(1, len(marked), out.stdout)
            self.assertIn("feat", marked[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
