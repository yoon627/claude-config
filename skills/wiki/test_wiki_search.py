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
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wiki_check  # noqa: E402
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

    def run_main(self, *argv: str, cwd: Path | None = None, env: dict[str, str] | None = None, crash: bool = False):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = wiki_search.main(
                    list(argv), env=self.env if env is None else env, cwd=cwd or self.outside, home=self.home
                )
            except SystemExit as e:  # argparse 사용 오류
                code = e.code
        # main 은 예상 밖 예외도 exit 2 로 받는다 — traceback 이 있으면 처리된 2 가 아니라 crash 다.
        if not crash:
            self.assertNotIn("Traceback", err.getvalue())
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


GRAPH_ALPHA_FM = '## 주석 — frontmatter 안이라 제목이 아니다\nsee:\n  - "[[beta]]"\n'
GRAPH_ALPHA = """소개 문단.

## 결정

- 다음은 [[gamma]] 를 본다. 별칭 [[beta|베타 페이지]] 도 링크다.
- 자기 자신 [[alpha]] 와 없는 [[ghost]] 는 관련에서 뺀다.

```bash
# 코드 안 주석은 제목이 아니다
echo "[[beta]]"
```

### 세부

> [!open] 아직 정하지 않은 경계
> 두 번째 줄은 보이지 않는다

## 기록

> [!conflict] 두 문서가 다르게 말한다
> [!note] 이 종류는 모으지 않는다"""
GRAPH_FENCES = """## 앞

~~~
```
## 여전히 코드
~~~

## 뒤

````
```
## 긴 fence 안
````

```
```bash
## 정보가 붙은 fence 줄은 닫는 fence 가 아니다
```

```인라인``` 처럼 info 에 backtick 이 든 줄은 fence 가 아니다

## 인라인 뒤

## 마지막

```
## 닫히지 않은 코드"""


def graph_page(stem: str, category: str, body: str, extra: str = "") -> str:
    return (
        f"---\ntitle: {stem}\ncategory: {category}\ncreated: 2026-09-30\nupdated: 2026-09-30\n"
        f"{extra}sources: [https://example.com/pr/1]\n---\n\n# {stem}\n\n{body}\n"
    )


GRAPH_PAGES = {
    "decision/alpha.md": graph_page("alpha", "decision", GRAPH_ALPHA, GRAPH_ALPHA_FM),
    "entity/beta.md": graph_page("beta", "entity", "## 참고\n\n[[alpha]] 로 돌아간다."),
    "concept/gamma.md": graph_page("gamma", "concept", "## 연결\n\n[[alpha]] 와 [[beta]]."),
    "concept/many.md": graph_page("many", "concept", "## 반복\n\n" + "\n".join(f"- {i}번째 [[alpha]]" for i in range(6))),
    "concept/fences.md": graph_page("fences", "concept", GRAPH_FENCES),
}
GRAPH_INDEX = {stem: f"{stem} 요약" for stem in ("alpha", "beta", "gamma", "many", "fences")}


def structure_of(text: str):
    text = wiki_check.normalize(text)
    lines = wiki_check.text_lines(text)
    return lines, wiki_search.parse_structure(lines, len(lines) - len(wiki_check.body_lines(text)))


def line_no(lines: list[str], prefix: str) -> int:
    return next(i for i, line in enumerate(lines, 1) if line.startswith(prefix))


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
        # POSIX 에서 `\` 는 이름의 글자라, 경로를 repr 로 내면 Windows 처럼 역슬래시가 겹쳐 POSIX 에서도 실패한다.
        shared = make_wiki(self.tmp / "sha\\red", SHARED_PAGES, SHARED_INDEX)
        (shared / "index.md").unlink()
        (shared / "index.md").mkdir()
        code, out, err = self.run_main("clone", env=dict(self.env, CLAUDE_SHARED_WIKI=str(shared)))
        self.assertEqual((code, out), (2, ""))
        self.assertIn(str(shared / "index.md"), err)

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

    def test_closed_stdout_exits_2_with_a_reason_and_no_traceback(self):
        # 결과를 끝까지 내지 못했으면 결과 유무(0·1)를 말할 수 없다. 작은 출력은 끝의 flush 에서, 큰 출력은 print 안에서 실패한다.
        todo = "\n".join(f"> [!open] 할 일 {i} {'x' * 60}" for i in range(2000))
        many = make_wiki(self.tmp / "many", {"concept/todo.md": page("todo", "concept", todo)}, {"todo": "할 일 목록"})
        for name, argv, shared in (("결과 있음", ["보관방식을"], self.shared), ("결과 없음", ["없는단어"], self.shared), ("큰 출력", ["--open"], many)):
            with self.subTest(name):
                rfd, wfd = os.pipe()
                os.close(rfd)
                try:
                    r = subprocess.run(
                        [sys.executable, str(SCRIPT), *argv],
                        stdout=wfd,
                        stderr=subprocess.PIPE,
                        cwd=self.outside,
                        env={**os.environ, "HOME": str(self.home), **self.env, "CLAUDE_SHARED_WIKI": str(shared)},
                    )
                finally:
                    os.close(wfd)
                err = r.stderr.decode("utf-8", "replace")
                self.assertEqual(r.returncode, 2, err)
                self.assertNotIn("Traceback", err)
                self.assertNotIn("Exception ignored", err)
                self.assertIn("출력을 끝까지 내지 못했다", err)

    def test_unexpected_error_exits_2_not_1(self):
        # 1 은 "결과 없음" 이다 — 예상 밖 오류가 그 값으로 끝나면 호출자는 빈손이었다고 읽는다.
        with mock.patch.object(wiki_search, "rank", side_effect=RuntimeError("boom")):
            code, _, err = self.run_main("clone", crash=True)
        self.assertEqual(code, 2)
        self.assertIn("Traceback", err)
        self.assertIn("RuntimeError: boom", err)

    def test_unwritable_stdout_exits_2_not_120(self):
        # 닫힌 pipe 가 아닌 쓰기 실패(디스크 가득·잘못 연 리디렉트)도 예상 밖 오류다 — 버퍼를 남기면 종료 때의 flush 가
        # 다시 실패해 "Exception ignored" 와 120 이 된다.
        readonly = self.tmp / "readonly.txt"
        readonly.write_bytes(b"")
        with readonly.open("rb") as stdout:
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "보관방식을"],
                stdout=stdout,
                stderr=subprocess.PIPE,
                cwd=self.outside,
                env={**os.environ, "HOME": str(self.home), **self.env},
            )
        err = r.stderr.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 2, err)
        self.assertIn("Traceback", err)  # 닫힌 pipe 분기가 아니라 예상 밖 오류 분기다
        self.assertNotIn("Exception ignored", err)


class StructureTest(unittest.TestCase):
    def test_sections_skip_code_blocks_and_frontmatter(self):
        lines, structure = structure_of(graph_page("alpha", "decision", GRAPH_ALPHA, GRAPH_ALPHA_FM))
        self.assertEqual([(s.level, s.title) for s in structure.sections], [(2, "결정"), (3, "세부"), (2, "기록")])
        # H3 은 다음 H2 앞에서, H2 는 다음 H2 앞에서 끝난다.
        self.assertEqual(structure.sections[1].end, line_no(lines, "## 기록") - 1)
        self.assertEqual(structure.sections[0].end, line_no(lines, "## 기록") - 1)
        self.assertEqual([(kind, text) for _, kind, text in structure.callouts], [("open", "아직 정하지 않은 경계"), ("conflict", "두 문서가 다르게 말한다")])

    def test_fence_rules(self):
        # 같은 문자·같거나 긴 길이로만 닫힘, 뒤에 글자가 붙은 줄은 닫지 않음, backtick info 줄은 fence 아님, 미종료는 끝까지.
        _, structure = structure_of(graph_page("fences", "concept", GRAPH_FENCES))
        self.assertEqual([s.title for s in structure.sections], ["앞", "뒤", "인라인 뒤", "마지막"])

    def test_empty_heading_bounds_sections(self):
        structure = wiki_search.parse_structure(["## Before", "### Child", "## ", "body"], 0)
        self.assertEqual([(s.title, s.start, s.end) for s in structure.sections], [("Before", 1, 2), ("Child", 2, 2), ("", 3, 4)])

    def test_links_include_alias_frontmatter_and_code(self):
        lines, structure = structure_of(graph_page("alpha", "decision", GRAPH_ALPHA, GRAPH_ALPHA_FM))
        stems = [stem for _, stem in structure.links]
        self.assertEqual(stems, ["beta", "gamma", "beta", "alpha", "ghost", "beta"])
        self.assertEqual(structure.links[0][0], line_no(lines, '  - "[[beta]]"'))
        # 닫히지 않은 별칭이 뒤의 링크를 삼키지 않는다(check_links 도 beta 를 읽는다).
        self.assertEqual(wiki_search.parse_structure(["[[alpha|미완성 설명 [[beta]]"], 0).links, [(1, "beta")])

    def test_callout_variants(self):
        structure = wiki_search.parse_structure(["> [!OPEN]- 접힌 것", "> > [!conflict] 중첩", "> [!note] 아님"], 0)
        self.assertEqual([(kind, text) for _, kind, text in structure.callouts], [("open", "접힌 것"), ("conflict", "중첩")])


class GraphTest(SearchCase):
    def setUp(self):
        super().setUp()
        self.graph = make_wiki(self.tmp / "graph", GRAPH_PAGES, GRAPH_INDEX)
        self.env = dict(self.env, CLAUDE_SHARED_WIKI=str(self.graph))

    def records(self, out: str) -> list[str]:
        return [line.strip() for line in out.splitlines() if line.startswith("   L")]

    def test_matched_line_shows_section_and_range(self):
        lines = GRAPH_PAGES["decision/alpha.md"].split("\n")
        n, start, end = line_no(lines, "- 자기 자신"), line_no(lines, "## 결정"), line_no(lines, "## 기록") - 1
        code, out, _ = self.run_main("ghost")
        self.assertEqual(code, 0, out)
        self.assertIn(f"L{n} §결정 (L{start}-{end}): - 자기 자신", out)

    def test_related_pages_are_existing_pages_of_the_same_wiki(self):
        code, out, _ = self.run_main("ghost")
        self.assertEqual(code, 0, out)
        self.assertIn("관련: → entity/beta, concept/gamma · ← concept/gamma, concept/many, entity/beta", out)

    def test_links_to_lists_every_occurrence_with_category_on_the_source(self):
        code, out, _ = self.run_main("--links-to", "alpha")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.records(out)), 8, out)  # --limit 기본값 5 를 넘는다
        self.assertIn(f"[공용] concept/many  {self.graph / 'pages' / 'concept' / 'many.md'}", out)
        n = line_no(GRAPH_PAGES["concept/many.md"].split("\n"), "- 0번째")
        self.assertIn(f"L{n} §반복: - 0번째 [[alpha]]", out)
        code, out, _ = self.run_main("--links-to", "gamma", "--category", "decision")
        self.assertEqual((code, len(self.records(out))), (0, 1), out)
        # frontmatter 안의 링크 줄은 섹션 대신 frontmatter 로 표시한다.
        fm_line = line_no(GRAPH_PAGES["decision/alpha.md"].split("\n"), '  - "[[beta]]"')
        self.assertIn(f'L{fm_line} frontmatter: - "[[beta]]"', self.run_main("--links-to", "beta")[1])

    def test_links_to_exit_codes(self):
        cases = ((["--links-to", "fences"], 1), (["--links-to", "ghost"], 2), (["--links-to", "alpha", "--category", "nosuch"], 2))
        for argv, expected in cases:
            with self.subTest(argv=argv):
                self.assertEqual(self.run_main(*argv)[0], expected)

    def test_open_lists_open_and_conflict_callouts(self):
        code, out, _ = self.run_main("--open")
        self.assertEqual(code, 0, out)
        self.assertEqual(
            [r.split(": ", 1)[1] for r in self.records(out)],
            ["[!open] 아직 정하지 않은 경계", "[!conflict] 두 문서가 다르게 말한다"],
        )
        self.assertIn("§세부: [!open]", out)
        self.assertEqual(self.run_main("--open", "--category", "entity")[0], 1)

    def test_query_mode_usage_errors(self):
        for argv in (["--links-to", "alpha", "질의어"], ["--links-to", "alpha", "--open"]):
            with self.subTest(argv=argv):
                code, out, err = self.run_main(*argv)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err, err)

    def test_links_to_is_per_wiki_shared_first(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        make_wiki(
            repo / "wiki",
            # gamma 는 공용 wiki 에만 있다 — 링크는 같은 wiki 안에서만 잇는다.
            {"decision/alpha.md": graph_page("alpha", "decision", "본문"), "concept/user.md": graph_page("user", "concept", "[[alpha]] 사용, [[gamma]] 는 공용에만")},
            {"alpha": "repo 알파", "user": "repo 사용"},
        )
        code, out, _ = self.run_main("--links-to", "alpha", cwd=repo)
        self.assertEqual(code, 0, out)
        heads = [line.split("]", 1)[0] + "]" for line in out.splitlines() if line.startswith("[")]
        self.assertEqual(heads[-1], "[repo]", out)
        self.assertEqual(heads.count("[repo]"), 1, out)
        self.assertTrue(all(h == "[공용]" for h in heads[:-1]), out)
        code, out, _ = self.run_main("--links-to", "gamma", cwd=repo)
        self.assertEqual(code, 0, out)
        self.assertNotIn("[repo]", out)
        code, out, _ = self.run_main("공용에만", cwd=repo)
        related = [line for line in out.split("[repo] concept/user", 1)[1].splitlines() if line.startswith("   관련:")]
        self.assertEqual(related, ["   관련: → decision/alpha"], out)

    def test_self_link_is_by_stem_even_with_duplicate_stems(self):
        dup = make_wiki(
            self.tmp / "dup",
            {"concept/alpha.md": graph_page("alpha", "concept", "본문"), "decision/alpha.md": graph_page("alpha", "decision", "[[alpha]] 자기 참조")},
            {"alpha": "중복"},
        )
        env = dict(self.env, CLAUDE_SHARED_WIKI=str(dup))
        self.assertEqual(self.run_main("--links-to", "alpha", env=env)[0], 1)


if __name__ == "__main__":
    unittest.main()
