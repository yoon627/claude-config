#!/usr/bin/env python3
"""wiki_check.py 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_wiki_check.py

Python 3.9·3.10 에는 tomllib 이 없어 config 파일을 읽는 테스트를 건너뛴다.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_links  # noqa: E402
import wiki_check  # noqa: E402

SCRIPT = HERE / "wiki_check.py"
TEMPLATE = HERE / "templates" / "wiki-check.toml"
REPO_WIKI_MD = HERE.parent.parent / "wiki" / "WIKI.md"
NEEDS_TOMLLIB = unittest.skipUnless(
    importlib.util.find_spec("tomllib") is not None, "tomllib 없음 — config 는 Python 3.11+"
)

# wiki/WIKI.md "페이지 frontmatter (필수)" 블록 원문. 원본이 있으면 같은지 대조하고,
# 없어도(wiki 보관 방식이 바뀌어도) 이 사본으로 fixture 를 뜬다.
WIKI_MD_BLOCK = """\
---
title: <kebab-name>
category: concept|entity|decision|source|query
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [원문경로 | PR | 커밋 | URL]
---
"""


def filled(stem: str) -> str:
    """WIKI.md 블록의 자리표시자를 채운 concept 페이지."""
    return (
        WIKI_MD_BLOCK.replace("<kebab-name>", stem)
        .replace("concept|entity|decision|source|query", "concept")
        .replace("YYYY-MM-DD", "2026-09-29")
        .replace("[원문경로 | PR | 커밋 | URL]", "[https://example.com/pr/1]")
        + f"\n# {stem}\n"
    )


def page_text(
    *,
    category: str = "concept",
    created: str = "2026-09-29",
    sources: str = "[x]",
    drop: str | None = None,
    extra: str = "",
    close: bool = True,
) -> str:
    fields = {
        "title": "x",
        "category": category,
        "created": created,
        "updated": "2026-09-29",
        "sources": sources,
    }
    if drop:
        del fields[drop]
    lines = ["---", *(f"{k}: {v}" for k, v in fields.items())]
    if extra:
        lines.append(extra)
    if close:
        lines.append("---")
    return "\n".join(lines) + "\n\n본문\n"


class WikiTestCase(unittest.TestCase):
    """임시 디렉터리의 wiki. 탐색이 임시 디렉터리 위로 올라가지 않게 ceiling 을 둔다."""

    def setUp(self) -> None:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.wiki = self.root / "wiki"
        (self.wiki / "pages").mkdir(parents=True)
        self.env = {"GIT_CEILING_DIRECTORIES": str(self.root.parent)}

    def _page(self, rel: str, content: str | bytes) -> None:
        path = self.wiki / "pages" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)

    def _findings(self, schema: wiki_check.SchemaConfig | None = None) -> list:
        ctx = wiki_check.resolve_context(self.root, "wiki", env=self.env)
        pages = wiki_check.load_pages(ctx)
        return wiki_check.check_schema(pages, schema or wiki_check.SchemaConfig(), "pages")

    def _cli(
        self,
        *args: str,
        cwd: Path | None = None,
        env: dict | None = None,
        script: Path = SCRIPT,
    ) -> subprocess.CompletedProcess:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        proc_env.update(env or {})
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=cwd or self.root,
            env=proc_env,
            capture_output=True,
            encoding="utf-8",
        )

    def _run_code(self, code: str) -> subprocess.CompletedProcess:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.root,
            env=proc_env,
            capture_output=True,
            encoding="utf-8",
        )


class ParserTest(unittest.TestCase):
    def test_line_endings_and_bom_parse_the_same(self) -> None:
        text = "---\ntitle: a\nsources:\n  - x\n---\n본문\n"
        crlf = text.replace("\n", "\r\n")
        for variant in (text, crlf, "\ufeff" + text, "\ufeff" + crlf):
            fm = wiki_check.parse_frontmatter(variant)
            self.assertEqual((fm.status, fm.fields), ("ok", {"title": "a", "sources": ["x"]}))

    def test_comment_cut_outside_quotes_only(self) -> None:
        fm = wiki_check.parse_frontmatter(
            "---\n"
            "plain: a # 주석\n"
            'double: "b # 유지" # 주석\n'
            "single: 'c # 유지'\n"
            "nospace: d#e\n"
            "---\n"
        )
        self.assertEqual(
            fm.fields,
            {"plain": "a", "double": "b # 유지", "single": "c # 유지", "nospace": "d#e"},
        )

    def test_inline_and_block_lists(self) -> None:
        fm = wiki_check.parse_frontmatter(
            "---\n"
            "inline: [x, \"y, z\", 'w'] # 주석\n"
            "empty: []\n"
            "block:\n"
            "  - one\n"
            '  - "two # 유지"  # 주석\n'
            "flush:\n"
            "- three\n"
            "literal: |\n"
            "  - 목록 아님\n"
            "---\n"
        )
        self.assertEqual(
            fm.fields,
            {
                "inline": ["x", "y, z", "w"],
                "empty": [],
                "block": ["one", "two # 유지"],
                "flush": ["three"],
                "literal": "|",
            },
        )

    def test_missing_unclosed_and_duplicate_keys_are_detected(self) -> None:
        self.assertEqual(wiki_check.parse_frontmatter("# 제목\n").status, "missing")
        self.assertEqual(wiki_check.parse_frontmatter("---\ntitle: a\n본문\n").status, "unclosed")
        fm = wiki_check.parse_frontmatter("---\ntitle: a\ntitle: b\n---\n")
        self.assertEqual((fm.status, fm.duplicates, fm.fields), ("ok", ["title"], {"title": "a"}))

    def test_key_needs_space_or_line_end_after_colon(self) -> None:
        fm = wiki_check.parse_frontmatter(
            "---\ncategory:concept\nurl: https://example.com/a:b\ntab:\tx\nempty:\n---\n"
        )
        self.assertEqual(fm.fields, {"url": "https://example.com/a:b", "tab": "x", "empty": ""})


class SchemaTest(WikiTestCase):
    def test_filled_wiki_md_block_passes_with_crlf_and_bom(self) -> None:
        self._page("concept/a.md", filled("a"))
        self._page("concept/b.md", filled("b").replace("\n", "\r\n"))
        self._page("concept/c.md", "\ufeff" + filled("c").replace("\n", "\r\n"))
        self.assertEqual(self._findings(), [])

    def test_each_violation_kind_is_one_line(self) -> None:
        cases = [
            # (사례, 기대 규칙, {pages 아래 경로: 내용}, SchemaConfig 인자, 기대 줄 수)
            ("stem", "stem 형식", {"concept/Bad_Name.md": page_text()}, {}, 1),
            (
                "stem 중복",
                "stem 중복",
                {"concept/dup.md": page_text(), "entity/dup.md": page_text(category="entity")},
                {},
                2,
            ),
            ("category≠디렉터리", "category 불일치", {"concept/x.md": page_text(category="entity")}, {}, 1),
            ("허용 밖 category", "category 허용 밖", {"misc/x.md": page_text(category="misc")}, {}, 1),
            ("필수 키 없음", "필수 키 누락", {"concept/x.md": page_text(drop="sources")}, {}, 1),
            ("필수 키 빈 목록", "필수 키 빈 값", {"concept/x.md": page_text(sources="[]")}, {}, 1),
            ("구분자 없는 날짜", "날짜 형식", {"concept/x.md": page_text(created="20260929")}, {}, 1),
            ("ISO 주 날짜", "날짜 형식", {"concept/x.md": page_text(created="2026-W40-2")}, {}, 1),
            ("전각 숫자 날짜", "날짜 형식", {"concept/x.md": page_text(created="２０２６-０９-２９")}, {}, 1),
            ("없는 날짜", "날짜 실재 안 함", {"concept/x.md": page_text(created="2026-02-30")}, {}, 1),
            ("날짜가 목록", "값 형식", {"concept/x.md": page_text(created="[2026-09-29]")}, {}, 1),
            (
                "enum",
                "enum 허용 밖",
                {"concept/x.md": page_text(extra="claim_state: bogus")},
                {"enums": {"claim_state": ["current"]}},
                1,
            ),
            (
                "날짜 접두",
                "날짜 접두 형식",
                {"concept/x.md": page_text(extra="verified: 17/09/2026 — 확인")},
                {"date_prefixed_keys": ["verified"]},
                1,
            ),
            ("페이지 수 범위", "페이지 수", {"concept/x.md": page_text()}, {"page_count": [2, 3]}, 1),
            ("페이지 0개", "페이지 없음", {}, {}, 1),
            ("UTF-8 아님", "UTF-8 아님", {"concept/x.md": b"---\ntitle: \xff\n---\n"}, {}, 1),
            ("frontmatter 없음", "frontmatter 없음", {"concept/x.md": "# 제목\n"}, {}, 1),
            ("닫는 --- 없음", "frontmatter 닫힘 없음", {"concept/x.md": page_text(close=False)}, {}, 1),
            ("중복 키", "중복 키", {"concept/x.md": page_text(extra="title: again")}, {}, 1),
        ]
        for case, rule, files, schema, count in cases:
            with self.subTest(case=case):
                shutil.rmtree(self.wiki / "pages")
                (self.wiki / "pages").mkdir()
                for rel, content in files.items():
                    self._page(rel, content)
                found = self._findings(wiki_check.SchemaConfig(**schema))
                self.assertEqual([f.rule for f in found], [rule] * count, [str(f) for f in found])
                for f in found:
                    self.assertRegex(str(f), rf"^\S.*: {re.escape(rule)} — \S")

    def test_cli_exit_codes_and_line_format(self) -> None:
        self._page("concept/x.md", page_text())
        r = self._cli("schema", "wiki")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("clean", r.stdout)

        self._page("concept/x.md", page_text(drop="sources"))
        r = self._cli("schema", "wiki")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["wiki/pages/concept/x.md: 필수 키 누락 — sources"])

        shutil.rmtree(self.wiki / "pages")
        r = self._cli("schema", "wiki")
        self.assertEqual(r.returncode, 2)
        self.assertIn("pages", r.stderr)


class DiscoveryTest(WikiTestCase):
    def _ctx(self, start: Path, env: dict | None = None) -> wiki_check.Context:
        return wiki_check.resolve_context(start, env=self.env if env is None else env)

    def test_walks_up_to_repo_root(self) -> None:
        (self.root / ".git").mkdir()
        (self.wiki / "WIKI.md").write_text("# w\n", encoding="utf-8")
        deep = self.root / "src" / "deep"
        deep.mkdir(parents=True)
        ctx = self._ctx(deep)
        self.assertEqual((ctx.wiki_root, ctx.repo_root), (self.wiki, self.root))

    def test_pages_dir_without_wiki_md_is_not_a_wiki_on_the_way_up(self) -> None:
        (self.root / ".git").mkdir()
        app = self.root / "app"
        (app / "pages").mkdir(parents=True)
        self.assertEqual(self._ctx(app).wiki_root, self.wiki)

    def test_outside_repo_only_start_level_is_searched(self) -> None:
        sub = self.root / "sub"
        sub.mkdir()
        self.assertIsNone(self._ctx(sub).wiki_root)
        self.assertEqual(self._ctx(self.root).wiki_root, self.wiki)
        r = self._cli("schema", cwd=sub)
        self.assertEqual(r.returncode, 2)
        self.assertIn("wiki", r.stderr)

    def test_ceiling_directories_stop_the_walk(self) -> None:
        (self.root / ".git").mkdir()
        deep = self.root / "a" / "b"
        deep.mkdir(parents=True)
        self.assertEqual(self._ctx(deep).wiki_root, self.wiki)
        ctx = self._ctx(deep, env={"GIT_CEILING_DIRECTORIES": str(self.root)})
        self.assertEqual((ctx.wiki_root, ctx.repo_root), (None, None))

    def test_output_paths_are_repo_root_relative(self) -> None:
        (self.root / ".git").mkdir()
        page = self.root / "docs" / "wiki" / "pages" / "concept" / "x.md"
        page.parent.mkdir(parents=True)
        page.write_bytes(page_text(drop="sources").encode("utf-8"))
        (self.root / "src").mkdir()
        want = ["docs/wiki/pages/concept/x.md: 필수 키 누락 — sources"]
        for cwd, arg in ((self.root, "docs/wiki"), (self.root / "src", "../docs/wiki")):
            with self.subTest(cwd=cwd.name):
                r = self._cli("schema", arg, cwd=cwd)
                self.assertEqual((r.returncode, r.stdout.splitlines()), (1, want), r.stderr)


class ConfigTest(WikiTestCase):
    def _load(self, content: str | bytes) -> wiki_check.Config:
        path = self.root / "c.toml"
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return wiki_check.load_config(path)

    def test_default_required_matches_check_links_and_wiki_md_block(self) -> None:
        required = set(wiki_check.SchemaConfig().required)
        self.assertEqual(required, check_links.REQUIRED_FM)
        self.assertEqual(required, set(wiki_check.parse_frontmatter(WIKI_MD_BLOCK).fields))

    def test_wiki_md_block_copy_matches_original(self) -> None:
        if not REPO_WIKI_MD.is_file():
            self.skipTest(f"{REPO_WIKI_MD} 없음 — wiki 보관 방식에 따라 없을 수 있다")
        self.assertIn(WIKI_MD_BLOCK, REPO_WIKI_MD.read_text(encoding="utf-8"))

    def test_stem_rule_matches_check_links_link_regex(self) -> None:
        samples = ["", "a", "a-1", "0", "-", "A", "a_b", "a.b", "a b", "é", "１"]
        samples += [chr(c) for c in range(0x20, 0x250)]
        for s in samples:
            self.assertEqual(
                bool(wiki_check.STEM.fullmatch(s)),
                bool(check_links.WIKILINK.fullmatch(f"[[{s}]]")),
                repr(s),
            )

    @NEEDS_TOMLLIB
    def test_template_equals_code_defaults(self) -> None:
        self.assertEqual(wiki_check.load_config(TEMPLATE), wiki_check.Config())

    @NEEDS_TOMLLIB
    def test_unknown_key_and_wrong_type_are_rejected(self) -> None:
        cases = [
            ("[schema]\nrequird = []\n", "schema.requird"),
            ("[bogus]\n", "bogus"),
            ('[schema]\nrequired = "title"\n', "schema.required"),
            ("version = true\n", "version"),
            ("[schema]\npage_count = [3, 1]\n", "schema.page_count"),
        ]
        for content, needle in cases:
            with self.subTest(content=content):
                with self.assertRaises(wiki_check.ConfigError) as cm:
                    self._load(content)
                self.assertIn(needle, str(cm.exception))

    @NEEDS_TOMLLIB
    def test_newer_version_is_reported_before_unknown_keys(self) -> None:
        with self.assertRaises(wiki_check.ConfigError) as cm:
            self._load("version = 99\n[bogus]\n")
        self.assertIn("스크립트 갱신", str(cm.exception))
        self.assertNotIn("bogus", str(cm.exception))

    @NEEDS_TOMLLIB
    def test_bom_config_is_read(self) -> None:
        config = self._load(b'\xef\xbb\xbf[schema]\ncategories = ["a"]\n')
        self.assertEqual(config.schema.categories, ["a"])

    @NEEDS_TOMLLIB
    def test_config_in_wiki_dir_is_used(self) -> None:
        self._page("misc/x.md", page_text(category="misc"))
        self.assertEqual(self._cli("schema", "wiki").returncode, 1)
        (self.wiki / "wiki-check.toml").write_text("[schema]\ncategories = []\n", encoding="utf-8")
        r = self._cli("schema", "wiki")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @NEEDS_TOMLLIB
    def test_config_errors_exit_2(self) -> None:
        self._page("concept/x.md", page_text())
        (self.wiki / "wiki-check.toml").write_text("[bogus]\n", encoding="utf-8")
        r = self._cli("schema", "wiki")
        self.assertEqual(r.returncode, 2)
        self.assertIn("bogus", r.stderr)
        r = self._cli("schema", "wiki", "--config", "missing.toml")
        self.assertEqual(r.returncode, 2)
        self.assertIn("missing.toml", r.stderr)

    def test_config_without_tomllib_exits_2_with_version_hint(self) -> None:
        self._page("concept/x.md", page_text())
        (self.wiki / "wiki-check.toml").write_text("version = 1\n", encoding="utf-8")
        r = self._run_code(
            "import runpy, sys\n"
            "sys.modules['tomllib'] = None\n"
            f"sys.argv = ['wiki_check.py', 'schema', {str(self.wiki)!r}]\n"
            f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
        )
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("3.11", r.stderr)

    def test_no_config_does_not_import_tomllib(self) -> None:
        self._page("concept/x.md", page_text())
        r = self._run_code(
            "import runpy, sys\n"
            f"sys.argv = ['wiki_check.py', 'schema', {str(self.wiki)!r}]\n"
            "try:\n"
            f"    runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
            "except SystemExit as e:\n"
            "    rc = e.code\n"
            "print('tomllib' in sys.modules)\n"
            "sys.exit(rc)\n"
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[-1], "False")


class StandaloneTest(WikiTestCase):
    def test_copied_script_alone_catches_violation_without_git(self) -> None:
        solo = self.root / "solo"
        solo.mkdir()
        shutil.copy2(SCRIPT, solo / "wiki_check.py")
        no_git = self.root / "empty-path"
        no_git.mkdir()
        self._page("concept/x.md", page_text(created="2026-02-30"))
        r = self._cli("schema", "wiki", env={"PATH": str(no_git)}, script=solo / "wiki_check.py")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("날짜 실재 안 함", r.stdout)

    def test_source_parses_with_python_39_grammar(self) -> None:
        ast.parse(SCRIPT.read_text(encoding="utf-8"), feature_version=(3, 9))


if __name__ == "__main__":
    unittest.main(verbosity=2)
