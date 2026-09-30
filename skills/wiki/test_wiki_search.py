#!/usr/bin/env python3
"""wiki_search.py 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_wiki_search.py

fixture wiki 만 읽는다 — main 에 env·cwd·home 을 넘긴다. main 체크아웃(~/.claude)에서 cwd 로 찾으면
실제 공용 wiki 가 repo wiki 로 잡혀 결과가 섞인다.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wiki_search  # noqa: E402

SCRIPT = HERE / "wiki_search.py"


def page(stem: str, category: str, body: str, heading: bool = True) -> str:
    """실제 공용 wiki 처럼 title 이 stem 과 같은 페이지. heading=False 면 본문에 `# stem` 을 넣지 않는다."""
    return (
        "---\n"
        f"title: {stem}\n"
        f"category: {category}\n"
        "created: 2026-09-30\n"
        "updated: 2026-09-30\n"
        "sources: [https://example.com/pr/1]\n"
        "---\n"
        + (f"\n# {stem}\n" if heading else "")
        + f"\n{body}\n"
    )


def make_wiki(root: Path, pages: dict[str, str], index: dict[str, str]) -> Path:
    """root 에 WIKI.md·index.md·pages/<경로> 를 만든다. index — stem → 한 줄 요약."""
    (root / "pages").mkdir(parents=True)
    (root / "WIKI.md").write_text("# WIKI\n", encoding="utf-8")
    for rel, text in pages.items():
        path = root / "pages" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    lines = ["# Wiki Index", ""] + [f"- [[{stem}]] — {summary}" for stem, summary in index.items()]
    (root / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


SHARED_PAGES = {
    "decision/wiki-storage.md": page("wiki-storage", "decision", "비공개 repo 에 따로 clone 한다."),
    "entity/check-tool.md": page("check-tool", "entity", "frontmatter 형식은 `wiki_check.py schema` 로 본다."),
    # `freshness` 는 stem 에만, `신선도` 는 index 요약에만 있다(본문에 H1 도 없다).
    "decision/covers-freshness.md": page("covers-freshness", "decision", "코드가 바뀌면 페이지를 다시 대조한다.", heading=False),
    # 같은 단어를 본문에만 200번 쓴 페이지 — 본문 BM25 가 상한 2.2 가까이 가도 stem(3)·요약(2.5) 일치보다 아래다.
    "concept/notes.md": page("notes", "concept", " ".join(["freshness 신선도"] * 200)),
}
SHARED_INDEX = {
    "wiki-storage": "공용 wiki 보관 방식 — 비공개 repo 로 옮긴 결정",
    "check-tool": "frontmatter 검사 스크립트",
    "covers-freshness": "covers 신선도 — 갱신 누락을 찾는다",
    "notes": "작업 메모",
}


class SearchCase(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.shared = make_wiki(self.tmp / "shared", SHARED_PAGES, SHARED_INDEX)
        self.outside = self.tmp / "outside"
        self.outside.mkdir()
        self.home = self.tmp / "home"
        self.home.mkdir()
        # fixture 밖의 `.git` 을 repo 루트로 잡지 않는다.
        self.env = {"CLAUDE_SHARED_WIKI": str(self.shared), "GIT_CEILING_DIRECTORIES": str(self.tmp)}

    def run_main(self, *argv: str, cwd: Path | None = None, env: dict[str, str] | None = None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = wiki_search.main(
                    list(argv), env=self.env if env is None else env, cwd=cwd or self.outside, home=self.home
                )
            except SystemExit as e:  # argparse 사용 오류
                code = e.code
        return code, out.getvalue(), err.getvalue()

    def ranked_stems(self, *argv: str, **kwargs) -> list[str]:
        code, out, err = self.run_main(*argv, **kwargs)
        self.assertEqual(code, 0, out + err)
        return [line.split("] ", 1)[1].split(" ", 1)[0].split("/")[-1] for line in out.splitlines() if line[:1].isdigit()]

    def make_repo(self, wiki: bool = True) -> Path:
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / "src").mkdir()
        if wiki:
            make_wiki(repo / "wiki", {"decision/local-rule.md": page("local-rule", "decision", "repo 전용 clone 규칙.")}, {"local-rule": "repo 결정"})
        return repo


class TokenizeTest(unittest.TestCase):
    def test_identifier_splits_into_parts_and_whole(self):
        tokens = wiki_search.tokenize("wiki_check.py 를")
        self.assertTrue({"wiki_check.py", "wiki", "check", "py"} <= set(tokens), tokens)

    def test_hangul_is_bigrams_and_script_boundary_splits(self):
        self.assertEqual(wiki_search.tokenize("보관방식을 봐"), ["보관", "관방", "방식", "식을"])
        self.assertEqual(wiki_search.tokenize("worktree에서 hook이"), ["worktree", "에서", "hook"])


class RankingTest(SearchCase):
    def test_particle_attached_query_finds_spaced_index_summary(self):
        self.assertEqual(self.ranked_stems("보관방식을")[0], "wiki-storage")

    def test_identifier_parts_match(self):
        self.assertEqual(self.ranked_stems("wiki_check")[0], "check-tool")

    def test_stem_and_index_match_outrank_repeated_body_match(self):
        self.assertEqual(self.ranked_stems("freshness")[:2], ["covers-freshness", "notes"])
        self.assertEqual(self.ranked_stems("신선도")[:2], ["covers-freshness", "notes"])

    def test_category_filter_with_option_between_query_words(self):
        self.assertEqual(self.ranked_stems("freshness", "--category", "concept", "신선도"), ["notes"])


class OutputTest(SearchCase):
    def test_result_shows_tier_absolute_path_index_line_and_matched_line(self):
        code, out, _ = self.run_main("clone")
        self.assertEqual(code, 0, out)
        self.assertIn(f"공용 {self.shared} (4쪽)", out.splitlines()[0])
        self.assertIn("1. [공용] decision/wiki-storage ", out)
        self.assertIn(str(self.shared / "pages" / "decision" / "wiki-storage.md"), out)
        self.assertIn("index.md:3: 공용 wiki 보관 방식 — 비공개 repo 로 옮긴 결정", out)
        # frontmatter 7줄·빈 줄·H1·빈 줄 뒤라 파일 기준 11번째 줄이다.
        self.assertIn("L11: 비공개 repo 에 따로 clone 한다.", out)

    def test_bom_and_crlf_page(self):
        text = page("crlf-page", "entity", "첫 줄\n둘째 줄 개행문자 확인").replace("\n", "\r\n")
        (self.shared / "pages" / "entity" / "crlf-page.md").write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
        code, out, _ = self.run_main("개행문자", "--category", "entity")
        self.assertEqual(code, 0, out)
        self.assertIn("1. [공용] entity/crlf-page ", out)
        self.assertIn("L12: 둘째 줄 개행문자 확인", out)


class TargetTest(SearchCase):
    def test_searches_shared_and_repo_wiki_from_subdirectory(self):
        repo = self.make_repo()
        code, out, _ = self.run_main("clone", cwd=repo / "src")
        self.assertEqual(code, 0, out)
        self.assertIn(f"repo {repo / 'wiki'} (1쪽)", out.splitlines()[0])
        self.assertIn("[공용] decision/wiki-storage", out)
        self.assertIn("[repo] decision/local-rule", out)

    def test_same_wiki_is_searched_once(self):
        repo = self.make_repo(wiki=False)
        (repo / "wiki").symlink_to(self.shared, target_is_directory=True)
        # 두 경로 모두 resolve 한 뒤 비교해야 같다고 본다.
        env = dict(self.env, CLAUDE_SHARED_WIKI=str(self.outside / ".." / "shared"))
        code, out, _ = self.run_main("clone", cwd=repo, env=env)
        self.assertEqual(code, 0, out)
        self.assertIn(f"공용 {self.shared} (4쪽", out.splitlines()[0])
        self.assertEqual(out.count("] decision/wiki-storage"), 1, out)
        self.assertNotIn("[repo]", out)

    def test_default_shared_wiki_is_under_home(self):
        home, cwd = Path("/home/someone"), Path("/work")
        self.assertEqual(wiki_search.shared_wiki_path({}, home, cwd), home / ".claude" / "wiki")
        self.assertEqual(wiki_search.shared_wiki_path({"CLAUDE_SHARED_WIKI": ""}, home, cwd), home / ".claude" / "wiki")
        self.assertEqual(wiki_search.shared_wiki_path({"CLAUDE_SHARED_WIKI": "w"}, home, cwd), cwd / "w")
        self.assertEqual(wiki_search.shared_wiki_path({"CLAUDE_SHARED_WIKI": "~/w"}, home, cwd), home / "w")


class ExitCodeTest(SearchCase):
    def test_results_exit_0_and_no_results_exit_1_with_searched_wikis(self):
        self.assertEqual(self.run_main("clone")[0], 0)
        code, out, _ = self.run_main("없는단어")
        self.assertEqual(code, 1)
        self.assertIn(f"공용 {self.shared} (4쪽)", out.splitlines()[0])
        self.assertIn("결과 없음", out)

    def test_default_shared_wiki_missing_warns_and_searches_repo(self):
        repo = self.make_repo()
        unset = {"GIT_CEILING_DIRECTORIES": str(self.tmp)}
        default = self.home / ".claude" / "wiki"
        for state, env in (("없음", unset), ("빈 값", dict(unset, CLAUDE_SHARED_WIKI="")), ("raw 만 남음", unset)):
            with self.subTest(state=state):
                if state == "raw 만 남음":
                    (default / "raw").mkdir(parents=True)
                code, out, err = self.run_main("clone", cwd=repo, env=env)
                self.assertEqual(code, 0, out + err)
                self.assertIn(f"공용 wiki 없음 — {default}", err)
                self.assertIn(f"공용 없음({default})", out.splitlines()[0])
                self.assertIn("[repo] decision/local-rule", out)

    def test_explicit_shared_wiki_that_is_not_a_wiki_exit_2(self):
        repo = self.make_repo()
        env = dict(self.env, CLAUDE_SHARED_WIKI=str(self.tmp / "missing"))
        code, out, err = self.run_main("clone", cwd=repo, env=env)
        self.assertEqual((code, out), (2, ""))
        self.assertIn(f"CLAUDE_SHARED_WIKI 가 wiki 가 아니다 — {self.tmp / 'missing'}", err)

    def test_no_wiki_at_all_exit_2(self):
        code, out, err = self.run_main("clone", env={"GIT_CEILING_DIRECTORIES": str(self.tmp)})
        self.assertEqual((code, out), (2, ""))
        self.assertIn("찾을 wiki 가 없다", err)

    def test_usage_errors_exit_2(self):
        cases = (
            ([], "찾을 단어"),
            (["을", "!"], "찾을 단어"),
            (["clone", "--limit", "0"], "--limit"),
            (["clone", "--category", "decisoin"], "있는 category: concept, decision, entity"),
        )
        for argv, reason in cases:
            with self.subTest(argv=argv):
                code, out, err = self.run_main(*argv)
                self.assertEqual((code, out), (2, ""))
                self.assertIn(reason, err)

    def test_unreadable_index_exit_2(self):
        (self.shared / "index.md").unlink()
        (self.shared / "index.md").mkdir()
        code, out, err = self.run_main("clone")
        self.assertEqual((code, out), (2, ""))
        self.assertIn(str(self.shared / "index.md"), err)

    @unittest.skipIf(os.name == "nt" or os.geteuid() == 0, "권한으로 디렉터리 읽기를 막을 수 없다")
    def test_unreadable_pages_directory_exit_2(self):
        entity = self.shared / "pages" / "entity"
        entity.chmod(0)
        self.addCleanup(entity.chmod, 0o755)
        code, out, err = self.run_main("clone")
        self.assertEqual((code, out), (2, ""))
        self.assertIn(str(entity), err)

    def test_cli_runs_from_any_directory(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "보관방식을"],
            cwd=self.outside,
            env=dict(os.environ, HOME=str(self.home), **self.env),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1. [공용] decision/wiki-storage ", result.stdout)


if __name__ == "__main__":
    unittest.main()
