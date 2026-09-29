#!/usr/bin/env python3
"""wiki_check.py 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_wiki_check.py

Python 3.9·3.10 에는 tomllib 이 없어 config 파일을 읽는 테스트를 건너뛴다.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
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


def covers_page(*covers: str) -> str:
    return page_text(extra="covers:\n" + "\n".join(f"  - {c}" for c in covers))


def verified_page(value: str, *covers: str) -> str:
    lines = ["covers:", *(f"  - {c}" for c in covers)] if covers else []
    return page_text(extra="\n".join([*lines, f"verified_at: {value}"]))


FP = re.compile(r"fp1-[0-9a-f]{16}")


def isolated_git_env(home: Path) -> dict:
    """전역·시스템 git 설정과 격리한다(commit-check 테스트와 같다). 전역 ignore·attributes 파일은
    설정이 없어도 HOME·XDG_CONFIG_HOME 아래에서 읽히므로 둘 다 빈 디렉터리로 돌린다."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        HOME=str(home),
        XDG_CONFIG_HOME=str(home),
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.com",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.com",
    )
    return env


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


class GitWikiTestCase(WikiTestCase):
    """임시 git repo(루트 = self.root, 기본 브랜치 main)의 wiki. 첫 commit 이 있다."""

    def setUp(self) -> None:
        super().setUp()
        home = TemporaryDirectory()
        self.addCleanup(home.cleanup)
        self.env.update(isolated_git_env(Path(home.name)))
        self._init_repo(self.root)

    def _init_repo(self, root: Path) -> None:
        (root / "wiki" / "pages" / "concept").mkdir(parents=True, exist_ok=True)
        (root / "wiki" / "WIKI.md").write_text("# w\n", encoding="utf-8")
        (root / "wiki" / "pages" / "concept" / "plain.md").write_text(page_text(), encoding="utf-8")
        self.git("init", "-q", "-b", "main", cwd=root)
        self.commit("c0", cwd=root)

    def _temp_dir(self) -> Path:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name).resolve()

    def _other_repo(self) -> Path:
        root = self._temp_dir()
        self._init_repo(root)
        return root

    def git(self, *args: str, cwd: Path | None = None) -> str:
        r = subprocess.run(
            ["git", *args], cwd=cwd or self.root, env=self.env, capture_output=True, encoding="utf-8"
        )
        if r.returncode != 0:
            raise AssertionError(f"git {args}: {r.stderr}")
        return r.stdout.strip()

    def write(self, rel: str, text: str = "x\n", root: Path | None = None) -> None:
        path = (root or self.root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message: str, cwd: Path | None = None) -> str:
        self.git("add", "-A", cwd=cwd)
        self.git("commit", "-q", "-m", message, cwd=cwd)
        return self.git("rev-parse", "HEAD", cwd=cwd)

    def repo(self) -> wiki_check.Git:
        return wiki_check.Git(self.root, self.env)


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
            ("covers 정상", "", {"concept/x.md": covers_page("src/a.py", "src/*", "lib/*.py")}, {}, 0),
            ("covers 빈 목록", "covers 빈 값", {"concept/x.md": page_text(extra="covers: []")}, {}, 1),
            ("covers 빈 스칼라", "covers 빈 값", {"concept/x.md": page_text(extra="covers:")}, {}, 1),
            ("covers ./ 시작", "covers 형식", {"concept/x.md": covers_page("./src/a.py")}, {}, 1),
            ("covers / 시작", "covers 형식", {"concept/x.md": covers_page("/src/a.py")}, {}, 1),
            ("covers / 끝", "covers 형식", {"concept/x.md": covers_page("src/")}, {}, 1),
            ("covers \\ 포함", "covers 형식", {"concept/x.md": covers_page("src\\a.py")}, {}, 1),
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
            ("[stale]\nstop_hok = false\n", "stale.stop_hok"),
            ('[stale]\nstop_hook = "false"\n', "stale.stop_hook"),
            ("[stale]\nbase = 1\n", "stale.base"),
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


class CoversTest(unittest.TestCase):
    def test_covers_match_is_case_sensitive_fnmatch_where_star_crosses_slash(self) -> None:
        cases = [
            ("src/*", "src/a/b.py", True),
            ("src/*.py", "src/a/b.py", True),
            ("src/a.py", "src/a.py", True),
            ("src/a", "src/a.py", False),
            ("src/?.py", "src/a.py", True),
            ("src/[ab].py", "src/c.py", False),
            ("SRC/*", "src/a.py", False),
        ]
        for pattern, path, want in cases:
            self.assertEqual(wiki_check.covers_match(pattern, path), want, (pattern, path))

    def test_stale_needs_covered_change_and_unchanged_page(self) -> None:
        def page(name: str, fm: wiki_check.Frontmatter | None) -> wiki_check.Page:
            rel = f"wiki/pages/concept/{name}.md"
            return wiki_check.Page(Path(rel), rel, fm)

        pages = [
            page("api", wiki_check.Frontmatter("ok", {"covers": ["src/api/*"]})),
            page("db", wiki_check.Frontmatter("ok", {"covers": "src/db.py"})),
            page("plain", wiki_check.Frontmatter("ok", {"title": "x"})),
            page("broken", None),
            page("open", wiki_check.Frontmatter("unclosed", {"covers": ["src/*"]})),
        ]
        covers, unreadable = wiki_check.split_covers(pages)
        self.assertEqual([c.rel for c in covers], ["wiki/pages/concept/api.md", "wiki/pages/concept/db.md"])
        self.assertEqual([p.rel for p in unreadable], ["wiki/pages/concept/broken.md", "wiki/pages/concept/open.md"])
        changed = {"src/api/b.py", "src/api/a.py", "src/db.py", "wiki/pages/concept/db.md", "README.md"}
        self.assertEqual(
            wiki_check.stale_pages(covers, changed),
            [("wiki/pages/concept/api.md", ["src/api/a.py", "src/api/b.py"])],
        )

    def test_hook_context_stays_under_output_cap(self) -> None:
        long = "d" * 80
        stale = [
            (f"wiki/pages/concept/p{i}.md", [f"src/{long}/{j}.py" for j in range(30)]) for i in range(400)
        ]
        text = wiki_check.render_context(stale)
        self.assertLessEqual(len(text), 10_000)
        self.assertIn("외 20개", text)
        self.assertIn("외 ", text.splitlines()[-2])
        self.assertIn("stop_hook = false", text.splitlines()[-1])


class FingerprintTest(unittest.TestCase):
    def test_golden_vector_pins_fp1(self) -> None:
        # 값은 consumer 페이지에 저장되는 계약이다 — 이 값이 바뀌면 정의를 fp2 로 올린다. 정렬은 경로
        # 바이트 순이다: 문자열 순이면 `한`(U+D55C)과 바이트 0x80(U+DC80)의 순서가 뒤집혀 값이 달라진다.
        entries = {
            "src/run.sh": ("100755", "8ab686eafeb1f44702738c8b0f24f2567c36da6d"),
            "vendor/sub": ("160000", "4b825dc642cb6eb9a060e54bf8d69288fbee4904"),
            "src/한글.md": ("100644", "d00491fd7e5bb6fa28c517a0bb32b8b506539d4d"),
            "src/\udc80.bin": ("100644", "0cfbf08886fca9a91cb753ec8734c84fcbe52c9f"),
            "src/link": ("120000", "2e65efe2a145dda7ee51d1741299f848e5bf752e"),
            "src/a.py": ("100644", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"),
        }
        self.assertEqual(wiki_check.fingerprint(entries), "fp1-bb86b9374ac8ff41")


class GitAdapterTest(GitWikiTestCase):
    @unittest.skipIf(os.name == "nt", "가짜 git 이 sh 스크립트다")
    def test_deadline_bounds_each_call(self) -> None:
        fake = self._temp_dir()
        (fake / "git").write_text("#!/bin/sh\nexec /bin/sleep 5\n", encoding="utf-8")
        (fake / "git").chmod(0o755)
        git = wiki_check.Git(self.root, dict(self.env, PATH=str(fake)), deadline=time.monotonic() + 0.5)
        start = time.monotonic()
        with self.assertRaises(wiki_check.GitError) as cm:
            git.out("status")
        self.assertLess(time.monotonic() - start, 3)
        self.assertIn("초", str(cm.exception))


class ChangedFilesTest(GitWikiTestCase):
    def test_worktree_set_has_staged_unstaged_untracked_and_rename_old_path(self) -> None:
        for rel in ("src/old/a.py", "src/b.py", "src/한글.py", "src/same.py"):
            self.write(rel)
        self.write(".gitignore", "*.log\n")
        self.commit("code")
        (self.root / "lib").mkdir()
        self.git("mv", "src/old/a.py", "lib/a.py")
        self.write("src/b.py", "changed\n")
        self.write("src/한글.py", "changed\n")
        self.git("add", "src/한글.py")
        self.write("src/new/deep/d.py")
        self.write("src/e.log")
        got = wiki_check.changed_files(self.repo(), worktree=True, base=None)
        self.assertEqual(got, {"src/old/a.py", "lib/a.py", "src/b.py", "src/한글.py", "src/new/deep/d.py"})

    def test_branch_set_is_commits_after_merge_base_only(self) -> None:
        self.git("checkout", "-q", "-b", "feat")
        self.write("src/a.py")
        self.commit("a")
        self.git("checkout", "-q", "main")
        self.write("src/main-only.py")
        self.commit("main moves")
        self.git("checkout", "-q", "feat")
        self._page("concept/plain.md", page_text() + "작업 트리\n")
        self.write("src/untracked.py")
        repo = self.repo()
        base = wiki_check.resolve_base(repo, "")
        self.assertEqual(wiki_check.changed_files(repo, worktree=False, base=base.sha), {"src/a.py"})


class AddViewTest(GitWikiTestCase):
    @unittest.skipIf(os.name == "nt", "symlink 이 필요하다")
    def test_add_view_equals_git_add_all_across_worktree_states(self) -> None:
        for name in ("mm", "del", "cached", "t", "u", "ud"):
            self.write(f"src/{name}.py", f"{name} v1\n")
        self.write('"quoted.py', "q\n")
        source = self._temp_dir()
        self.write("x", "1\n", root=source)
        self.git("init", "-q", "-b", "main", cwd=source)
        self.commit("s1", cwd=source)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "sub")
        self.commit("c1")
        self.git("checkout", "-q", "-b", "other")
        self.write("src/u.py", "u other\n")
        (self.root / "src" / "ud.py").unlink()
        self.commit("other")
        self.git("checkout", "-q", "main")
        self.write("src/u.py", "u main\n")
        self.write("src/ud.py", "ud main\n")
        self.commit("main")
        merge = subprocess.run(["git", "merge", "-q", "other"], cwd=self.root, env=self.env, capture_output=True)
        self.assertEqual(merge.returncode, 1, merge.stderr)  # UU·UD 충돌
        self.write("src/mm.py", "mm staged\n")
        self.git("add", "src/mm.py")
        self.write("src/mm.py", "mm worktree\n")
        (self.root / "src" / "del.py").unlink()
        self.git("rm", "-q", "--cached", "src/cached.py")
        self.write("src/ita.py", "intent\n")
        self.git("add", "-N", "src/ita.py")
        (self.root / "src" / "t.py").unlink()
        os.symlink("mm.py", self.root / "src" / "t.py")
        os.symlink("mm.py", self.root / "src" / "link.py")
        os.symlink("nowhere", self.root / "src" / "broken.py")
        self.write("src/new line\n.py", "nl\n")
        self.write('"quoted.py', "q2\n")
        self.write("sub/x", "2\n")
        self.commit("s2", cwd=self.root / "sub")
        nested = self.root / "nested"
        self.write("y", "y\n", root=nested)
        self.git("init", "-q", "-b", "main", cwd=nested)
        self.commit("n1", cwd=nested)
        # 작업 트리에 없는 UTF-8 아닌 경로 — git 이 낸 바이트 그대로 update-index 에 돌려줘야 지워진다.
        blob = self._git_bytes("hash-object", "-w", "--stdin", input=b"bin\n").strip()
        self._git_bytes("update-index", "--index-info", input=b"100644 " + blob + b"\tsrc/\xff.bin\n")
        git = self.repo()
        view = wiki_check.add_view(git, wiki_check.worktree_status(git), lambda path: True)
        self.assertEqual(view, self._add_all_in_copy())

    def test_conflict_left_in_index_copy_is_error(self) -> None:
        # status 와 index 복사 사이에 merge 가 끼면 status 에 없던 충돌이 사본에 남는다 — 빼면 지문에서 파일이 사라진다.
        self.write("src/u.py", "base\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "other")
        self.write("src/u.py", "other\n")
        self.commit("other")
        self.git("checkout", "-q", "main")
        self.write("src/u.py", "main\n")
        self.commit("main")
        merge = subprocess.run(["git", "merge", "-q", "other"], cwd=self.root, env=self.env, capture_output=True)
        self.assertEqual(merge.returncode, 1, merge.stderr)
        with self.assertRaises(wiki_check.GitError) as cm:
            wiki_check.add_view(self.repo(), [], lambda path: True)
        self.assertIn("src/u.py", str(cm.exception))

    def _git_bytes(self, *args: str, input: bytes) -> bytes:
        r = subprocess.run(["git", *args], input=input, cwd=self.root, env=self.env, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def _add_all_in_copy(self) -> dict:
        copy = self._temp_dir() / "copy"
        shutil.copytree(self.root, copy, symlinks=True)
        self.git("add", "-A", cwd=copy)
        out = subprocess.run(
            ["git", "ls-files", "-s", "-z"], cwd=copy, env=self.env, capture_output=True, check=True
        ).stdout
        view = {}
        for record in filter(None, out.split(b"\0")):
            meta, _, path = record.partition(b"\t")
            mode, blob, stage = meta.decode("ascii").split()
            self.assertEqual(stage, "0", path)
            view[path.decode("utf-8", "surrogateescape")] = (mode, blob)
        return view


class BaseTest(GitWikiTestCase):
    def test_auto_base_is_nearest_fork_point_and_skips_current_branch(self) -> None:
        c0 = self.git("rev-parse", "HEAD")
        self.write("src/c1.py")
        c1 = self.commit("c1")
        self.git("update-ref", "refs/remotes/origin/main", c1)
        self.git("checkout", "-q", "-b", "feat")
        self.git("branch", "-f", "main", c0)
        self.write("src/c2.py")
        self.commit("c2")
        self.assertEqual(wiki_check.resolve_base(self.repo(), "").sha, c1)
        # 기본 브랜치에서 직접 실행하면 현재 브랜치(main)를 빼고 origin/main 으로 — push 전 commit 이 범위다.
        self.git("checkout", "-q", "main")
        self.git("reset", "-q", "--hard", c1)
        self.write("src/c3.py")
        c3 = self.commit("c3")
        self.assertEqual(wiki_check.resolve_base(self.repo(), "").sha, c1)
        self.assertEqual(wiki_check.resolve_base(self.repo(), "main").sha, c3)

    def test_unresolved_base_states(self) -> None:
        cases = [
            ("후보가 현재 브랜치뿐", [], "", True),
            ("없는 base", [], "nope", False),
            ("후보 없음", ["branch", "-m", "main", "trunk"], "", False),
            ("unborn HEAD", ["checkout", "-q", "--orphan", "fresh"], "trunk", True),
        ]
        for name, step, configured, quiet in cases:
            with self.subTest(case=name):
                if step:
                    self.git(*step)
                base = wiki_check.resolve_base(self.repo(), configured)
                self.assertEqual((base.sha, base.quiet), (None, quiet), base.reason)
                self.assertTrue(base.reason)


class StaleBranchTest(GitWikiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self._page("concept/api.md", covers_page("src/api/*"))
        self.write("src/api/x.py", "v1\n")
        self.commit("api")
        self.git("checkout", "-q", "-b", "feat")

    def _branch(self, *args: str, **kwargs) -> subprocess.CompletedProcess:
        return self._cli("stale", "--branch", *args, **kwargs)

    def test_covered_commit_without_page_change_is_stale(self) -> None:
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        self.write("src/api/new.py")
        r = self._branch()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["wiki/pages/concept/api.md: covers 변경 — src/api/x.py"])

    def test_page_change_anywhere_in_branch_silences_regardless_of_order(self) -> None:
        for name, steps in (("page-code", ["page", "code"]), ("code-page-code", ["code", "page", "code"])):
            with self.subTest(order=name):
                self.git("checkout", "-q", "-B", name, "main")
                for i, step in enumerate(steps):
                    if step == "page":
                        self._page("concept/api.md", covers_page("src/api/*") + f"{name} {i}\n")
                    else:
                        self.write("src/api/x.py", f"{name} {i}\n")
                    self.commit(f"{name} {i}")
                r = self._branch()
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("clean", r.stdout)

    def test_uncommitted_wiki_change_is_warned_in_output_head_and_stderr(self) -> None:
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        self._page("concept/plain.md", page_text() + "미커밋\n")
        r = self._branch()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("미커밋 변경 1개", r.stdout.splitlines()[0])
        self.assertIn("미커밋 변경 1개", r.stderr)

    def test_no_covers_pages_is_not_applicable_without_calling_git(self) -> None:
        (self.wiki / "pages" / "concept" / "api.md").unlink()
        r = self._branch(env={"PATH": str(self._temp_dir())})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("검사 대상 아님", r.stdout)

    def test_unresolvable_base_exits_2(self) -> None:
        r = self._branch("--base", "nope")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("nope", r.stderr)
        self.git("branch", "-m", "main", "trunk")
        r = self._branch()
        self.assertEqual(r.returncode, 2, r.stdout)
        self.git("branch", "-m", "trunk", "main")
        self.git("checkout", "-q", "main")
        r = self._branch()
        self.assertEqual(r.returncode, 2, r.stdout)

    def test_shallow_clone_without_merge_base_exits_2(self) -> None:
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        self.git("checkout", "-q", "main")
        self.write("src/main.py")
        self.commit("main moves")
        clone = self._temp_dir()
        self.git("clone", "-q", "--depth", "1", "--no-single-branch", "--branch", "feat", self.root.as_uri(), str(clone))
        r = self._branch(cwd=clone)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("merge-base", r.stderr)

    def test_paths_are_toplevel_relative_from_any_directory(self) -> None:
        self.git("checkout", "-q", "main")
        self.write("docs/wiki/pages/concept/api.md", covers_page("src/api/*"))
        self.commit("docs wiki")
        self.git("checkout", "-q", "-b", "docs-feat")
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        self.git("config", "diff.relative", "true")
        want = ["docs/wiki/pages/concept/api.md: covers 변경 — src/api/x.py"]
        for cwd, arg in ((self.root, "docs/wiki"), (self.root / "src", "../docs/wiki")):
            with self.subTest(cwd=cwd.name):
                r = self._branch(arg, cwd=cwd)
                self.assertEqual((r.returncode, r.stdout.splitlines()), (1, want), r.stderr)

    def test_copied_script_alone_catches_branch_stale(self) -> None:
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        solo = self._temp_dir()
        shutil.copy2(SCRIPT, solo / "wiki_check.py")
        r = self._branch(script=solo / "wiki_check.py")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("covers 변경", r.stdout)

    def test_unreadable_page_is_violation_even_without_covers_pages(self) -> None:
        (self.wiki / "pages" / "concept" / "api.md").unlink()
        self._page("concept/bad.md", b"---\ntitle: \xff\n---\n")
        self._page("concept/open.md", "---\ntitle: x\n")
        r = self._branch()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(
            r.stdout.splitlines(),
            [
                "wiki/pages/concept/bad.md: covers 읽기 실패 — UTF-8 아님",
                "wiki/pages/concept/open.md: covers 읽기 실패 — frontmatter 닫힘 없음",
            ],
        )

    @unittest.skipIf(os.name == "nt", "파일 이름에 * 를 쓸 수 없다")
    def test_wiki_path_is_literal_not_pathspec_glob(self) -> None:
        # glob pathspec 이면 `docs/w*` 의 `*` 가 `/` 를 넘어 다른 디렉터리의 미커밋 변경을 센다.
        self.write("docs/w*/pages/concept/api.md", covers_page("src/api/*"))
        self.commit("star wiki")
        self.write("docs/wiki/pages/x.md")
        r = self._branch("docs/w*")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("미커밋", r.stdout)


class StaleReportTest(GitWikiTestCase):
    """--report(규칙 D). 기본 상태: api.md 가 covers src/api/* 이고 verified_at 이 없다(미확인)."""

    API = "wiki/pages/concept/api.md"

    def setUp(self) -> None:
        super().setUp()
        self._page("concept/api.md", covers_page("src/api/*"))
        self.write("src/api/x.py", "v1\n")
        self.commit("api")

    def _report(self, **kwargs) -> subprocess.CompletedProcess:
        return self._cli("stale", "--report", **kwargs)

    def _line(self, r: subprocess.CompletedProcess, rel: str = API) -> str:
        lines = [line for line in r.stdout.splitlines() if line.startswith(f"{rel}: ")]
        self.assertEqual(len(lines), 1, r.stdout + r.stderr)
        return lines[0]

    def _current(self, rel: str = API, **kwargs) -> str:
        """보고가 그 페이지 줄에 보인 현재 값(줄의 마지막 지문)."""
        return FP.findall(self._line(self._report(**kwargs), rel))[-1]

    def _confirm(self) -> str:
        value = self._current()
        self._page("concept/api.md", verified_page(value, "src/api/*"))
        return value

    def test_changed_covered_file_is_stale_and_restoring_confirmed_content_is_ok(self) -> None:
        self._confirm()
        self.commit("confirm")
        r = self._report()
        self.assertEqual((r.returncode, self._line(r)), (0, f"{self.API}: OK"), r.stderr)
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        r = self._report()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(": STALE — ", self._line(r))
        self.write("src/api/x.py", "v1\n")
        self.commit("restore")
        self.assertEqual(self._report().returncode, 0)

    def test_same_content_through_squash_or_shallow_clone_is_judged_the_same(self) -> None:
        self._confirm()
        self.commit("confirm")
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        self.write("src/api/x.py", "v1\n")
        self.commit("restore")
        self.git("checkout", "-q", "--orphan", "squashed")
        self.commit("squashed")
        self.assertEqual(self._report().returncode, 0)
        self.write("src/api/x.py", "v3\n")
        self.commit("code again")
        self.assertEqual(self._report().returncode, 1)
        clone = self._temp_dir()
        self.git("clone", "-q", "--depth", "1", "--branch", "squashed", self.root.as_uri(), str(clone))
        r = self._report(cwd=clone)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(": STALE — ", self._line(r))

    def test_crlf_blob_under_text_auto_gives_the_value_a_clean_clone_computes(self) -> None:
        # CRLF 가 blob 에 든 채 commit 된 파일은 text=auto 에서도 add 가 CRLF 를 그대로 둔다. hash-object 는 LF 로
        # 바꿔 커밋 전 값이 CI(깨끗한 clone)의 값과 어긋난다.
        x = self.root / "src" / "api" / "x.py"
        x.write_bytes(b"one\r\ntwo\r\n")
        self.commit("crlf blob")
        self.write(".gitattributes", "* text=auto\n")
        self.commit("attributes")
        x.write_bytes(b"one\r\ntwo\r\nthree\r\n")
        self._confirm()
        self.commit("code and confirm")
        clone = self._temp_dir()
        self.git("clone", "-q", "--no-local", str(self.root), str(clone))
        r = self._report(cwd=clone)
        self.assertEqual((r.returncode, self._line(r)), (0, f"{self.API}: OK"), r.stdout + r.stderr)

    @unittest.skipIf(os.name == "nt", "실행 비트가 없다")
    def test_exec_bit_only_change_is_stale(self) -> None:
        self._confirm()
        (self.root / "src" / "api" / "x.py").chmod(0o755)
        r = self._report()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(": STALE — ", self._line(r))

    def test_wiki_pages_are_left_out_of_fingerprint(self) -> None:
        # 서로를 covers 에 건 두 페이지 — 한쪽 값을 적는 편집이 다른 쪽 지문을 바꾸면 둘이 함께 OK 가 될 수 없다.
        a, b = "wiki/pages/concept/a.md", "wiki/pages/concept/b.md"
        self._page("concept/a.md", covers_page(b, "src/api/*"))
        self._page("concept/b.md", covers_page(a, "src/api/*"))
        self._page("concept/only.md", covers_page(a))
        r = self._report()
        value_a, value_b = (FP.findall(self._line(r, rel))[-1] for rel in (a, b))
        self._page("concept/a.md", verified_page(value_a, b, "src/api/*"))
        self._page("concept/b.md", verified_page(value_b, a, "src/api/*") + "본문을 고쳤다\n")
        r = self._report()
        self.assertEqual(self._line(r, a), f"{a}: OK")
        self.assertEqual(self._line(r, b), f"{b}: OK")
        self.assertIn("covers 매칭 0건", self._line(r, "wiki/pages/concept/only.md"))
        self.assertEqual(r.returncode, 1)

    def test_value_formats(self) -> None:
        current = self._current()
        listed = page_text(extra="covers:\n  - src/api/*\nverified_at: [fp1-0123456789abcdef]")
        cases = [
            # (이름, 페이지, exit, 줄에 든 말, 현재 값을 보이나)
            ("미확인", covers_page("src/api/*"), 0, "미확인", True),
            ("옛 형식", verified_page("0a1b2c3", "src/api/*"), 1, "옛 형식", True),
            ("대문자 옛 형식", verified_page("0A1B2C3D", "src/api/*"), 1, "옛 형식", True),
            ("형식 위반", verified_page("fp1-0123", "src/api/*"), 1, "verified_at 형식", True),
            ("목록 값", listed, 1, "verified_at 형식", True),
            ("옵션 모양", verified_page("--output=pwned", "src/api/*"), 1, "verified_at 형식", True),
            ("모르는 판", verified_page("fp2-0123456789abcdef", "src/api/*"), 2, "스크립트 갱신 필요", False),
            ("covers 없음", verified_page("fp1-0123456789abcdef"), 1, "covers", False),
        ]
        for name, content, code, word, shows in cases:
            with self.subTest(case=name):
                self._page("concept/api.md", content)
                r = self._report()
                self.assertEqual(r.returncode, code, r.stdout + r.stderr)
                line = self._line(r)
                self.assertIn(word, line)
                self.assertEqual(current in line, shows, line)
        # 값은 git 에 넘기지 않는다.
        self.assertFalse((self.root / "pwned").exists())

    def test_stale_line_shows_reference_files_then_current_value(self) -> None:
        self._confirm()
        self.commit("confirm")
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        self.write("src/api/new.py")
        self.write("src/other.py")
        line = self._line(self._report())
        current = FP.findall(line)[-1]
        for path in ("src/api/x.py", "src/api/new.py"):
            self.assertLess(line.index(path), line.index(current), line)
        self.assertNotIn("src/other.py", line)
        self.assertIn("참고 파일을 페이지 주장과 대조한 뒤에만", line)
        clone = self._temp_dir()
        self.git("clone", "-q", "--depth", "1", self.root.as_uri(), str(clone))
        line = self._line(self._report(cwd=clone))
        self.assertNotIn("src/api/x.py", line)
        self.assertIn("얕은 clone", line)

    def test_uncommitted_wiki_or_covered_change_is_warned(self) -> None:
        self.write("src/api/x.py", "v2\n")
        self._page("concept/plain.md", page_text() + "미커밋\n")
        self.write("src/other.py")
        r = self._report()
        self.assertIn("미커밋 변경 2개", r.stdout.splitlines()[0])
        self.assertIn("미커밋 변경 2개", r.stderr)

    def test_nothing_to_judge_is_not_applicable_without_calling_git(self) -> None:
        (self.wiki / "pages" / "concept" / "api.md").unlink()
        r = self._report(env={"PATH": str(self._temp_dir())})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("검사 대상 아님", r.stdout)

    def test_unreadable_page_alone_is_violation(self) -> None:
        (self.wiki / "pages" / "concept" / "api.md").unlink()
        self._page("concept/bad.md", b"---\ntitle: \xff\n---\n")
        r = self._report()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("covers 읽기 실패", self._line(r, "wiki/pages/concept/bad.md"))

    @unittest.skipIf(os.name == "nt" or os.geteuid() == 0, "권한으로 읽기를 막지 못한다")
    def test_page_read_error_exits_2(self) -> None:
        page = self.wiki / "pages" / "concept" / "api.md"
        page.chmod(0)
        self.addCleanup(page.chmod, 0o644)
        r = self._report()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("api.md", r.stderr)

    def test_base_is_rejected_not_ignored(self) -> None:
        r = self._cli("stale", "--report", "--base", "main")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("--report 는 이력을 보지 않는다", r.stderr)

    def test_real_index_and_objects_stay_unchanged(self) -> None:
        self._confirm()
        self.commit("confirm")
        self.write("src/api/x.py", "v2\n")
        self.write("src/api/new.py")
        past = time.time() - 1000
        os.utime(self.wiki / "pages" / "concept" / "plain.md", (past, past))
        index = self.root / ".git" / "index"
        before = (index.read_bytes(), self._objects())
        r = self._report()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual((index.read_bytes(), self._objects()), before)

    def _objects(self) -> list[str]:
        return sorted(p.parent.name + p.name for p in (self.root / ".git" / "objects").glob("??/*"))

    def test_git_calls_do_not_grow_with_covers_pages(self) -> None:
        counts = []
        for n in (0, 5):
            for i in range(n):
                self._page(f"concept/p{i}.md", covers_page("src/api/*"))
            counts.append(self._git_calls())
        self.assertEqual(counts[0], counts[1])

    def _git_calls(self) -> int:
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(HERE)!r})\n"
            "import wiki_check\n"
            "calls = []\n"
            "run = wiki_check.Git.run\n"
            "def counted(self, *args, **kwargs):\n"
            "    calls.append(args)\n"
            "    return run(self, *args, **kwargs)\n"
            "wiki_check.Git.run = counted\n"
            "rc = wiki_check.main(['stale', '--report'])\n"
            "print(len(calls), rc)\n"
        )
        r = self._run_code(code)
        count, rc = r.stdout.splitlines()[-1].split()
        self.assertEqual(rc, "0", r.stdout + r.stderr)
        return int(count)


class StopHookTest(GitWikiTestCase):
    """hook 분류표(plan # Decisions)의 행마다 하나 이상. 기본 상태는 stale 이다 — 조용한 행이
    판정할 것이 없어서 조용한 것이 아님을 보인다."""

    def setUp(self) -> None:
        super().setUp()
        self._page("concept/api.md", covers_page("src/api/*"))
        self.write("src/api/x.py", "v1\n")
        self.commit("api")
        self.write("src/api/x.py", "v2\n")

    def _hook(
        self,
        payload: dict | None = None,
        args: tuple = (),
        *,
        raw: bytes | None = None,
        env: dict | None = None,
        cwd: Path | None = None,
        argv: list | None = None,
    ) -> tuple[dict | None, str]:
        if raw is None:
            data = {"cwd": str(self.root), "hook_event_name": "Stop", "stop_hook_active": False}
            raw = json.dumps({**data, **(payload or {})}).encode("utf-8")
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        proc_env.update(env or {})
        r = subprocess.run(
            [sys.executable, str(SCRIPT), *(argv or ["stale", "--stop-hook", *args])],
            input=raw,
            cwd=cwd or self.root,
            env=proc_env,
            capture_output=True,
        )
        return self._parse(r)

    def _hook_code(self, patch: str) -> dict | None:
        """모듈을 import 해 patch 를 적용한 뒤 hook 을 돈다."""
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(HERE)!r})\n"
            "import wiki_check\n"
            f"{patch}\n"
            "sys.exit(wiki_check.main(['stale', '--stop-hook']))\n"
        )
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        payload = json.dumps({"cwd": str(self.root), "hook_event_name": "Stop"}).encode("utf-8")
        r = subprocess.run(
            [sys.executable, "-c", code], input=payload, cwd=self.root, env=proc_env, capture_output=True
        )
        return self._parse(r)[0]

    def _parse(self, r: subprocess.CompletedProcess) -> tuple[dict | None, str]:
        err = r.stderr.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 0, err)
        out = r.stdout.decode("utf-8")
        if not out:
            return None, err
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        return json.loads(lines[0]), err

    def test_stale_change_gives_additional_context(self) -> None:
        out, _ = self._hook()
        self.assertEqual(set(out), {"hookSpecificOutput"})
        spec = out["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "Stop")
        self.assertIn("wiki/pages/concept/api.md", spec["additionalContext"])
        self.assertIn("src/api/x.py", spec["additionalContext"])
        self.assertIn("stop_hook = false", spec["additionalContext"])

    def test_quiet_rows(self) -> None:
        outside = self._temp_dir()
        self.write("wiki/pages/concept/api.md", covers_page("*"), root=outside)
        rows = {
            "stop_hook_active": ({"stop_hook_active": True}, ()),
            "subagent 대기": ({"background_tasks": [{"type": "subagent"}]}, ()),
            "workflow 대기": ({"background_tasks": [{"type": "workflow"}]}, ()),
            "없는 cwd": ({"cwd": str(self.root / "gone")}, ()),
            "repo 밖": ({"cwd": str(outside)}, ()),
            "wiki 없음": ({}, ("nope",)),
        }
        for name, (payload, args) in rows.items():
            with self.subTest(row=name):
                self.assertIsNone(self._hook(payload, args)[0])
        out, _ = self._hook({"background_tasks": [{"type": "shell"}, {"type": "monitor"}]})
        self.assertIn("hookSpecificOutput", out)

    def test_empty_stdin_is_quiet_with_manual_hint(self) -> None:
        out, err = self._hook(raw=b"")
        self.assertIsNone(out)
        self.assertIn("--branch", err)

    @unittest.skipIf(os.name == "nt", "pty 는 POSIX 만")
    def test_tty_stdin_is_quiet(self) -> None:
        master, slave = os.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "stale", "--stop-hook"],
            stdin=slave,
            cwd=self.root,
            env=proc_env,
            capture_output=True,
            timeout=10,
        )
        out, err = self._parse(r)
        self.assertIsNone(out)
        self.assertIn("--branch", err)

    def test_no_covers_pages_is_quiet_without_calling_git(self) -> None:
        (self.wiki / "pages" / "concept" / "api.md").unlink()
        self.assertIsNone(self._hook(env={"PATH": str(self._temp_dir())})[0])

    def test_warning_rows(self) -> None:
        mismatch = self.root / "sub"
        (mismatch / ".git").mkdir(parents=True)
        other = self._other_repo()
        rows = {
            "인자 오류": {"argv": ["stale", "--stop-hook", "--bogus"]},
            "UTF-8 아님": {"raw": b'{"cwd": "\xff"}'},
            "JSON 오류": {"raw": b"{"},
            "객체 아님": {"raw": b"[]"},
            "cwd 없음": {"raw": b'{"hook_event_name": "Stop"}'},
            "cwd 문자열 아님": {"payload": {"cwd": 1}},
            "git 없음": {"env": {"PATH": str(self._temp_dir())}},
            "최상위 불일치": {"payload": {"cwd": str(mismatch)}, "args": (str(self.wiki),)},
            "wiki 가 repo 밖": {"payload": {"cwd": str(other)}, "args": (str(self.wiki),)},
        }
        for name, kwargs in rows.items():
            with self.subTest(row=name):
                out, _ = self._hook(**kwargs)
                self.assertIsNotNone(out)
                self.assertTrue(out["systemMessage"].startswith("wiki_check stale:"), out)

    @NEEDS_TOMLLIB
    def test_config_rows(self) -> None:
        config = self.wiki / "wiki-check.toml"
        for content in ("[bogus]\n", "version = 99\n", "[[\n"):
            with self.subTest(config=content):
                config.write_text(content, encoding="utf-8")
                out, _ = self._hook()
                self.assertIn("config", out["systemMessage"])
        config.write_text("[stale]\nstop_hook = false\n", encoding="utf-8")
        self.assertIsNone(self._hook()[0])

    def test_config_without_tomllib_gives_version_hint(self) -> None:
        (self.wiki / "wiki-check.toml").write_text("version = 1\n", encoding="utf-8")
        out = self._hook_code("sys.modules['tomllib'] = None")
        self.assertIn("3.11", out["systemMessage"])

    def test_unexpected_error_and_time_budget_give_system_message(self) -> None:
        out = self._hook_code("wiki_check.changed_files = None")
        self.assertIn("예상 밖 오류", out["systemMessage"])
        out = self._hook_code("wiki_check.HOOK_BUDGET = 0.0")
        self.assertIn("초", out["systemMessage"])

    def test_stdin_without_eof_ends_within_3_seconds(self) -> None:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "stale", "--stop-hook"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.root,
            env=proc_env,
        )
        start = time.monotonic()
        proc.stdin.write(b'{"cwd": ')
        proc.stdin.flush()
        try:
            proc.wait(timeout=3)
        finally:
            proc.stdin.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait()
        elapsed = time.monotonic() - start
        out = proc.stdout.read()
        proc.stdout.close()
        proc.stderr.close()
        self.assertLess(elapsed, 3)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("1초", json.loads(out)["systemMessage"])

    def test_unreadable_page_and_stale_page_share_one_json(self) -> None:
        self._page("concept/bad.md", b"---\ntitle: \xff\n---\n")
        out, _ = self._hook()
        self.assertIn("bad.md", out["systemMessage"])
        self.assertIn("src/api/x.py", out["hookSpecificOutput"]["additionalContext"])

    def test_base_rows(self) -> None:
        # 원격 없는 repo 의 기본 브랜치(setUp 상태) — 작업 트리만 보고 경고하지 않는다.
        out, _ = self._hook()
        self.assertEqual(set(out), {"hookSpecificOutput"})
        self.git("branch", "-m", "main", "trunk")
        out, _ = self._hook()
        self.assertIn("[stale] base", out["systemMessage"])
        self.assertIn("src/api/x.py", out["hookSpecificOutput"]["additionalContext"])
        self.git("checkout", "-q", "--orphan", "fresh")
        self.assertIsNone(self._hook()[0])

    def test_branch_commits_count_and_order_does_not(self) -> None:
        self.git("checkout", "-q", "-b", "feat")
        self.commit("code")
        out, _ = self._hook()
        self.assertIn("src/api/x.py", out["hookSpecificOutput"]["additionalContext"])
        for name, steps in (("page-code", ["page", "code"]), ("code-page-code", ["code", "page", "code"])):
            with self.subTest(order=name):
                self.git("checkout", "-q", "-B", name, "main")
                for i, step in enumerate(steps):
                    if step == "page":
                        self._page("concept/api.md", covers_page("src/api/*") + f"{name} {i}\n")
                    else:
                        self.write("src/api/x.py", f"{name} {i}\n")
                    self.commit(f"{name} {i}")
                self.assertIsNone(self._hook()[0])

    def test_hook_leaves_index_bytes_unchanged(self) -> None:
        past = time.time() - 1000
        os.utime(self.wiki / "pages" / "concept" / "plain.md", (past, past))
        index = self.root / ".git" / "index"
        before = index.read_bytes()
        self.assertIsNotNone(self._hook()[0])
        self.assertEqual(index.read_bytes(), before)

    def test_input_cwd_repo_is_judged_not_process_cwd(self) -> None:
        other = self._other_repo()
        self.write("wiki/pages/concept/lib.md", covers_page("lib/*"), root=other)
        self.write("lib/y.py", "v1\n", root=other)
        self.commit("lib", cwd=other)
        self.write("lib/y.py", "v2\n", root=other)
        out, _ = self._hook({"cwd": str(other)})
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("lib/y.py", context)
        self.assertNotIn("src/api/x.py", context)

    def test_relative_wiki_arg_is_resolved_from_input_repo_root(self) -> None:
        self.write("docs/wiki/pages/concept/d.md", covers_page("src/api/*"))
        self.commit("docs wiki")
        self.write("src/api/x.py", "v3\n")
        src = self.root / "src"
        out, _ = self._hook({"cwd": str(src)}, ("docs/wiki",), cwd=src)
        self.assertIn("docs/wiki/pages/concept/d.md", out["hookSpecificOutput"]["additionalContext"])


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
