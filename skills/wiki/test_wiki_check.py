#!/usr/bin/env python3
"""wiki_check.py 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_wiki_check.py

Python 3.9·3.10 에는 tomllib 이 없어 config 파일을 읽는 테스트를 건너뛴다.
"""

from __future__ import annotations

import ast
import errno
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

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


def smoke_toml(*questions: tuple[str, str, str], forbid: str = "") -> str:
    """(q, page, expect) 마다 [[smoke.questions]] 하나. json 문자열은 TOML basic string 으로도 유효하다."""
    parts = [
        "[[smoke.questions]]\n"
        + "".join(f"{key} = {json.dumps(value, ensure_ascii=False)}\n" for key, value in zip(("q", "page", "expect"), q))
        for q in questions
    ]
    if forbid:
        parts.append(f"[smoke.forbid]\n{forbid}\n")
    return "\n".join(parts)


def _alive(pid: int) -> bool:
    """zombie 는 죽은 것으로 본다 — 고아를 거두지 않는 PID 1(컨테이너) 아래에서는 죽은 손자가 Z 로 남는다."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        ps = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
        return ps.returncode == 0 and not ps.stdout.strip().startswith("Z")


def isolated_git_env(home: Path) -> dict:
    """전역·시스템 git 설정과 격리한다(commit-check 테스트와 같다). 전역 ignore·attributes 파일은
    설정이 없어도 HOME·XDG_CONFIG_HOME 아래에서 읽히므로 둘 다 빈 디렉터리로 돌린다. commit-check 와 달리
    auto-maintenance·auto gc 도 끈다 — commit 이 띄운 detached maintenance 가 fixture 의 loose object 를
    테스트 도중에 pack 한다."""
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
        GIT_CONFIG_COUNT="2",
        GIT_CONFIG_KEY_0="maintenance.auto",
        GIT_CONFIG_VALUE_0="false",
        GIT_CONFIG_KEY_1="gc.auto",
        GIT_CONFIG_VALUE_1="0",
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
        input: str | None = None,
    ) -> subprocess.CompletedProcess:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        proc_env.update(env or {})
        return subprocess.run(
            [sys.executable, str(script), *args],
            input=input,
            cwd=cwd or self.root,
            env=proc_env,
            capture_output=True,
            encoding="utf-8",
        )

    def _run_code(self, code: str) -> subprocess.CompletedProcess:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        # -c 는 __main__ 의 stdout 설정(UTF-8 로 다시 감싸기)을 거치지 않는다.
        proc_env["PYTHONIOENCODING"] = "utf-8"
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
            "trailing: [a, ]\n"
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
                "trailing": ["a"],
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
                "여러 줄 흐름 목록",
                "값 형식",
                {"concept/x.md": page_text(extra="covers: [src/a.py,\n  src/b.py]")},
                {},
                1,
            ),
            (
                "categories 끔",
                "",
                {"x.md": page_text()},
                {"categories": [], "enums": {"category": ["concept"]}},
                0,
            ),
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
            (
                "covers 흐름 빈 항목",
                "covers 빈 값",
                {"concept/x.md": page_text(extra="covers: [src/a.py,,src/b.py]")},
                {},
                1,
            ),
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

    def test_unclosed_flow_names_its_cause(self) -> None:
        # YAML 처럼 공백 뒤 # 부터 주석이라 `[PR #82, …]` 는 그 줄에서 닫았어도 `[PR` 만 남는다.
        self._page("concept/cut.md", page_text(sources="[PR #82, a.kt]"))
        self._page("concept/extra.md", page_text(sources="[PR #82] # 참고 ]"))
        self._page("concept/multi.md", page_text(extra="covers: [src/a.py,\n  src/b.py]"))
        self._page("concept/quoted.md", page_text(extra='covers: ["src/a]b.py",\n  src/c.py]'))
        self._page("concept/note.md", page_text(extra="covers: [src/a.py,  # 진입점 [main]\n  src/b.py]"))
        self._page("concept/block.md", page_text(extra="covers:\n  - [src/a.py,\n  - src/b.py"))
        # 닫은 뒤 글자가 붙으면 YAML 에서 깨진 값이다 — 여러 줄 목록으로 안내하면 블록 항목에서 틀린다.
        self._page("concept/trail.md", page_text(sources="[a.kt] 설명"))
        self._page("concept/link.md", page_text(extra="covers:\n  - [[x]] (`# y` 설명)"))
        details = {f.path.rsplit("/", 1)[-1]: f.detail for f in self._findings()}
        # 설명을 옮길 자리를 알린다 — 설명까지 따옴표로 감싸면 covers 가 어디에도 맞지 않는 패턴이 된다.
        for name in ("cut.md", "extra.md"):
            self.assertIn("주석에 잘렸다", details[name])
            self.assertIn("] 뒤로", details[name])
        for name in ("trail.md", "link.md"):
            self.assertIn("뒤에 글자", details[name])
            self.assertIn("# 주석으로", details[name])
        for name in ("multi.md", "quoted.md", "note.md"):
            self.assertIn("여러 줄 흐름 목록", details[name])
        self.assertIn("항목마다", details["block.md"])
        self.assertNotIn("블록 - 목록", details["block.md"])

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

    def test_closed_stdout_exits_2_without_traceback(self) -> None:
        # 결과를 끝까지 내지 못했으면 판정(0·1)을 말할 수 없다.
        self._page("concept/x.md", page_text())
        rfd, wfd = os.pipe()
        os.close(rfd)
        try:
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "schema", "wiki"],
                stdout=wfd,
                stderr=subprocess.PIPE,
                cwd=self.root,
                env={**os.environ, **self.env},
            )
        finally:
            os.close(wfd)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertNotIn(b"Traceback", r.stderr)

    def test_closed_stderr_pipe_keeps_verdict(self) -> None:
        # stderr 의 안내를 못 쓴 것은 stdout 판정과 exit code 를 바꾸지 않는다.
        self._page("concept/x.md", page_text(drop="sources"))
        rfd, wfd = os.pipe()
        os.close(rfd)
        try:
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "schema", "wiki"],
                stdout=subprocess.PIPE,
                stderr=wfd,
                cwd=self.root,
                env={**os.environ, **self.env},
            )
        finally:
            os.close(wfd)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout.decode().splitlines(), ["wiki/pages/concept/x.md: 필수 키 누락 — sources"])


class StdoutTest(unittest.TestCase):
    def test_einval_from_a_closed_pipe_is_a_broken_pipe_only_on_windows(self) -> None:
        class FailingPipe(io.RawIOBase):
            def __init__(self, err: int) -> None:
                super().__init__()
                self.err = err

            def writable(self) -> bool:
                return True

            def write(self, b) -> int:
                if self.err:
                    raise OSError(self.err, os.strerror(self.err))
                return len(b)

        cases = (("nt", errno.EINVAL, BrokenPipeError), ("posix", errno.EINVAL, OSError), ("nt", errno.ENOSPC, OSError))
        for name, err, want in cases:
            for where in ("write", "flush"):
                with self.subTest(os_name=name, errno=err, where=where):
                    raw = FailingPipe(err)
                    out = wiki_check._Stdout(io.BufferedWriter(raw), encoding="utf-8", write_through=where == "write")
                    # os.name 은 write·flush 둘레에서만 바꾼다 — pathlib 도 실행 중에 읽는다.
                    with self.assertRaises(OSError) as caught, mock.patch.object(wiki_check.os, "name", name):
                        out.write("x" * (1 << 16) if where == "write" else "x")
                        out.flush()
                    raw.err = 0  # GC 가 닫으며 flush 할 때 'Exception ignored' 를 내지 않게
                    self.assertIs(type(caught.exception), want)
                    if want is BrokenPipeError:
                        self.assertEqual(caught.exception.__cause__.errno, errno.EINVAL)


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
    def test_template_smoke_example_is_valid_once_uncommented(self) -> None:
        example = re.compile(r"# (\[\[?smoke[a-z.]*\]\]?|(q|page|expect|branch_names|plan_status|patterns) = .*)")
        lines = []
        for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
            m = example.fullmatch(line)
            lines.append(m.group(1) if m else line)
        smoke = self._load("\n".join(lines)).smoke
        self.assertTrue(smoke.questions)
        self.assertTrue(smoke.forbid.branch_names and smoke.forbid.plan_status and smoke.forbid.patterns)

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
            ("[smoke]\nquestion = []\n", "smoke.question"),
            ('[smoke.questions]\nq = "a"\n', "smoke.questions"),
            ('[[smoke.questions]]\nq = "a"\npage = "x.md"\n', "expect"),
            ('[[smoke.questions]]\nq = "a"\npage = "../x.md"\nexpect = "b"\n', "smoke.questions[1].page"),
            ('[smoke.forbid]\nplan_status = "yes"\n', "smoke.forbid.plan_status"),
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

    def test_unreadable_config_at_default_path_is_error_not_absent(self) -> None:
        self._page("concept/x.md", page_text())
        config = self.wiki / "wiki-check.toml"
        makers = {"디렉터리": config.mkdir}
        if os.name != "nt":
            makers["깨진 symlink"] = lambda: config.symlink_to(self.root / "gone.toml")
        for name, make in makers.items():
            with self.subTest(case=name):
                make()
                try:
                    r = self._cli("schema", "wiki")
                    self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                    self.assertIn("wiki-check.toml", r.stderr)
                finally:
                    if config.is_symlink():
                        config.unlink()
                    else:
                        config.rmdir()

    def test_list_values_reject_empty_string_and_duplicates(self) -> None:
        # date_keys 기본값(created, updated)과 겹쳐도 거부하고, 적지 않은 기본값을 문구에 보인다.
        cases = (
            ({"required": ["a", "a"]}, ""),
            ({"categories": [""]}, ""),
            ({"date_prefixed_keys": ["updated"]}, "created, updated.*기본값"),
        )
        for schema, shown in cases:
            with self.subTest(schema=schema):
                with self.assertRaisesRegex(wiki_check.ConfigError, shown):
                    wiki_check.build_config({"schema": schema})

    def test_escaped_bracket_is_not_a_posix_class(self) -> None:
        # grep 과 Python 이 같은 뜻으로 읽는 식 — escape 된 `[`, 집합 안의 문자 `[`.
        for pattern in (r"\[:alpha:]", r"\[[=a]", r"\[\[[.a-z0-9-]+\]\]", "[.[]x"):
            with self.subTest(pattern=pattern):
                wiki_check._check_regex(pattern, "x")
        # grep 은 집합 안의 `\` 를 문자로 읽어 뒤의 [:space:] 를 클래스로 본다.
        for pattern in ("[[:space:]]", "[^[:space:]]", r"[\[:space:]]", r"[\\[:space:]]"):
            with self.subTest(pattern=pattern):
                with self.assertRaises(wiki_check.ConfigError):
                    wiki_check._check_regex(pattern, "x")

    def test_gnu_grep_dialect_is_rejected(self) -> None:
        for pattern in (r"\<TODO\>", "[[=a=]]", "[[.hyphen.]]", "[^[=e=]]", "[x[.-.]]", r"\\\<TODO"):
            with self.subTest(pattern=pattern):
                with self.assertRaises(wiki_check.ConfigError) as cm:
                    wiki_check._check_regex(pattern, "x")
                self.assertIn(r"\b", str(cm.exception))

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
            ("app/[id]/page.tsx", "app/[id]/page.tsx", True),
            ("app/[id]/*", "app/[id]/page.tsx", True),
            # 리터럴 `[` 와 문자 집합을 섞으면 어느 해석으로도 맞지 않는다 — 리터럴 쪽을 `[[]` 로 쓴다.
            ("app/[id]/[ab].py", "app/[id]/a.py", False),
            ("app/[[]id]/[ab].py", "app/[id]/a.py", True),
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

    def test_deadline_is_checked_within_a_page(self) -> None:
        # 패턴이 많은 페이지 하나로도 예산을 넘는다 — 페이지 사이에서만 보면 판정을 낸다.
        match = wiki_check.covers_match
        self.addCleanup(setattr, wiki_check, "covers_match", match)
        wiki_check.covers_match = lambda pattern, path: time.sleep(0.05) or match(pattern, path)
        page = wiki_check.CoversPage("wiki/pages/concept/a.md", ("src/*",))
        start = time.monotonic()
        with self.assertRaises(wiki_check.OutOfTime):
            wiki_check.stale_pages([page], {f"src/{i}.py" for i in range(20)}, time.monotonic() + 0.1)
        self.assertLess(time.monotonic() - start, 0.6)

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

    def test_single_page_with_long_paths_is_still_named(self) -> None:
        text = wiki_check.render_context([("wiki/pages/concept/a.md", ["d/" + "x" * 1000] * 10)])
        self.assertIn("wiki/pages/concept/a.md", text)
        self.assertLessEqual(len(text), 10_000)


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

    def test_version_with_more_digits_is_future_without_int_limit(self) -> None:
        self.assertEqual(wiki_check.value_kind("fp" + "9" * 5000 + "-0"), "future")


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

    @unittest.skipIf(os.name == "nt", "가짜 git 이 sh 스크립트다")
    def test_timeout_kills_what_git_started(self) -> None:
        fake = self._temp_dir()
        pidfile = fake / "pid"
        script = f'#!/bin/sh\n/bin/sleep 30 &\necho $! > "{pidfile}.tmp"\n/bin/mv "{pidfile}.tmp" "{pidfile}"\nwait\n'
        (fake / "git").write_text(script, encoding="utf-8")
        (fake / "git").chmod(0o755)
        # 부하가 걸리면 셸이 자식을 띄우기 전에 시간이 끝난다 — 그때는 검사할 자식이 없어 시간을 늘려 다시 한다.
        for limit in (0.5, 2, 8):
            git = wiki_check.Git(self.root, dict(self.env, PATH=str(fake)), deadline=time.monotonic() + limit)
            with self.assertRaises(wiki_check.OutOfTime):
                git.out("status")
            if pidfile.exists():
                break
        else:
            self.fail("가짜 git 이 자식을 띄우기 전에 매번 시간이 끝났다")
        pid = int(pidfile.read_text())
        end = time.monotonic() + 3
        while time.monotonic() < end:
            if not _alive(pid):
                return
            time.sleep(0.05)
        os.kill(pid, 9)
        self.fail("git 이 띄운 자식이 남았다")


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

    def test_submodule_move_counts_under_diff_ignore_submodules_all(self) -> None:
        source = self._temp_dir()
        self.write("x", "1\n", root=source)
        self.git("init", "-q", "-b", "main", cwd=source)
        self.commit("s1", cwd=source)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "sub")
        base = self.commit("sub")
        self.git("config", "diff.ignoreSubmodules", "all")
        self.write("sub/x", "2\n")
        self.commit("s2", cwd=self.root / "sub")
        git = self.repo()
        self.assertIn("sub", wiki_check.changed_files(git, worktree=True, base=None))
        # git 2.39 의 commit 은 이 설정을 따라 gitlink 만 바뀐 commit 을 "바뀐 것 없음" 으로 거부한다.
        self.git("add", "-A")
        self.git("-c", "diff.ignoreSubmodules=none", "commit", "-q", "-m", "bump")
        self.assertEqual(wiki_check.changed_files(git, worktree=False, base=base), {"sub"})

    def test_untracked_nested_repo_is_its_gitlink_path(self) -> None:
        nested = self.root / "tools" / "cli"
        self.write("y", root=nested)
        self.git("init", "-q", "-b", "main", cwd=nested)
        self.commit("n1", cwd=nested)
        self.assertEqual(wiki_check.changed_files(self.repo(), worktree=True, base=None), {"tools/cli"})


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
            wiki_check.add_view(self.repo(), {}, lambda path: True)
        self.assertIn("src/u.py", str(cm.exception))

    def test_split_index_repo_keeps_its_shared_index(self) -> None:
        for key, value in (
            ("core.splitIndex", "true"),
            ("splitIndex.maxPercentChange", "0"),
            ("splitIndex.sharedIndexExpire", "now"),
        ):
            self.git("config", key, value)
        self.write("src/a.py", "v1\n")
        self.commit("split")
        shared = sorted((self.root / ".git").glob("sharedindex.*"))
        self.assertTrue(shared)
        self.write("src/a.py", "v2\n")
        git = self.repo()
        wiki_check.add_view(git, wiki_check.worktree_status(git), lambda path: True)
        self.assertEqual(sorted((self.root / ".git").glob("sharedindex.*")), shared)
        self.git("status")

    def test_racily_clean_entry_is_read_again_like_add(self) -> None:
        # 같은 크기·같은 mtime 의 수정 — index 파일 mtime 이 entry mtime 이하라는 것만이 내용을 다시 읽게 한다.
        self.git("config", "core.trustctime", "false")
        path = self.root / "src" / "r.py"
        past = (int(time.time()) - 100) * 10**9
        self.write("src/r.py", "v1\n")
        os.utime(path, ns=(past, past))
        self.commit("r")
        path.write_text("v2\n", encoding="utf-8")
        os.utime(path, ns=(past, past))
        os.utime(self.root / ".git" / "index", ns=(past, past))
        git = self.repo()
        view = wiki_check.add_view(git, wiki_check.worktree_status(git), lambda p: p == "src/r.py")
        self.assertEqual(view["src/r.py"][1], self.git("hash-object", "src/r.py"))

    def test_ignored_file_removed_from_index_stays_out_like_add(self) -> None:
        self.write("src/a.py")
        self.write("src/cache.py")
        self.commit("c")
        self.write(".gitignore", "src/cache.py\n")
        self.git("rm", "-q", "--cached", "src/cache.py")
        git = self.repo()
        view = wiki_check.add_view(git, wiki_check.worktree_status(git), lambda path: True)
        self.assertEqual(view, self._add_all_in_copy())

    @unittest.skipIf(os.name == "nt", "hook 이 sh 스크립트다")
    def test_post_index_change_hook_does_not_run(self) -> None:
        marker = self._temp_dir() / "ran"
        hook = self.root / ".git" / "hooks" / "post-index-change"
        hook.parent.mkdir(exist_ok=True)
        hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)
        self.write("wiki/WIKI.md", "# changed\n")
        git = self.repo()
        wiki_check.add_view(git, wiki_check.worktree_status(git), lambda path: True)
        self.assertFalse(marker.exists())

    @unittest.skipIf(os.name == "nt", "symlink 이 필요하다")
    def test_directory_turned_file_or_symlink_matches_add(self) -> None:
        for rel in ("src/f/a.py", "src/l/a.py", "src/d", "other/a.py"):
            self.write(rel)
        self.commit("dirs")
        shutil.rmtree(self.root / "src" / "f")
        self.write("src/f", "file\n")
        shutil.rmtree(self.root / "src" / "l")
        os.symlink("../other", self.root / "src" / "l")
        (self.root / "src" / "d").unlink()
        self.write("src/d/a.py")
        git = self.repo()
        want = self._add_all_in_copy()
        # covers 경계(wanted)가 파일·디렉터리 전환의 한쪽만 고를 때도 add 와 같아야 한다.
        for prefix in ("", "src/f/", "src/l/", "src/d/"):
            with self.subTest(prefix=prefix):
                view = wiki_check.add_view(git, wiki_check.worktree_status(git), lambda p: p.startswith(prefix))
                self.assertEqual(view, {k: v for k, v in want.items() if k.startswith(prefix)})

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

    def test_given_name_of_both_branch_and_tag_is_refused(self) -> None:
        # git 은 태그를 먼저 고른다 — HEAD 의 태그면 범위가 비어 조용히 clean 이다.
        self.git("checkout", "-q", "-b", "feat")
        self.write("src/a.py")
        self.commit("a")
        self.git("tag", "main", "HEAD")
        base = wiki_check.resolve_base(self.repo(), "main")
        self.assertEqual((base.sha, base.quiet), (None, False), base.reason)
        self.assertIn("refs/heads/main", base.reason)

    def test_given_name_of_remote_branch_and_local_ref_is_refused(self) -> None:
        # git 은 refs/tags → refs/heads → refs/remotes 순으로 고른다 — 원격 추적 ref 가 가려진다.
        c0 = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", c0)
        self.git("checkout", "-q", "-b", "feat")
        self.write("src/a.py")
        self.commit("a")
        for kind in ("tag", "branch"):
            with self.subTest(kind=kind):
                self.git(kind, "origin/main", "HEAD")
                base = wiki_check.resolve_base(self.repo(), "origin/main")
                self.git(kind, "-d", "origin/main")
                self.assertEqual((base.sha, base.quiet), (None, False), base.reason)

    def test_criss_cross_range_does_not_depend_on_merge_base_dates(self) -> None:
        for page, path in (("pm", "src/m.py"), ("pf", "src/f.py")):
            self._page(f"concept/{page}.md", covers_page(path))
            self.write(path, "0\n")
        self.commit("base")
        clock = iter(range(int(time.time()) + 100, int(time.time()) + 200))
        self.addCleanup(self.env.pop, "GIT_COMMITTER_DATE", None)
        for later in ("trunk", "feat"):
            with self.subTest(later=later):
                feat = f"feat-{later}"
                self.git("checkout", "-q", "-B", feat, "main")
                self.git("branch", "-f", "trunk", "main")
                sides = [("trunk", "src/m.py"), (feat, "src/f.py")]
                tips = {}
                for branch, path in sides if later == "feat" else sides[::-1]:
                    self.git("checkout", "-q", branch)
                    self.write(path, f"{later}\n")
                    self.env["GIT_COMMITTER_DATE"] = f"{next(clock)} +0000"
                    tips[branch] = self.commit(path)
                self.git("checkout", "-q", "trunk")
                self.env["GIT_COMMITTER_DATE"] = f"{next(clock)} +0000"
                self.git("merge", "-q", "--no-edit", tips[feat])
                self.git("checkout", "-q", feat)
                self.env["GIT_COMMITTER_DATE"] = f"{next(clock)} +0000"
                self.git("merge", "-q", "--no-edit", tips["trunk"])
                r = self._cli("stale", "--branch", "--base", "trunk")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                hook = self._cli("stale", "--stop-hook", "--base", "trunk", input=json.dumps({"cwd": str(self.root)}))
                self.assertEqual((hook.returncode, hook.stdout), (0, ""), hook.stderr)
                self.git("checkout", "-q", "main")


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
        self.assertIn("얕은 clone", r.stderr)

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
        self._page("concept/flow.md", "---\ntitle: x\ncovers: [src/api/x.py,\n  src/b.py]\n---\n")
        self._page("concept/cut.md", "---\ntitle: x\ncovers: [src/api/x.py #1, src/b.py]\n---\n")
        self._page("concept/tags.md", "---\ntitle: x\ntags: [a,\n  b]\n---\n")
        self._page("concept/trail.md", "---\ntitle: x\ncovers:\n  - [src/api/x.py] 설명\n---\n")
        self._page("concept/item.md", "---\ntitle: x\ncovers:\n  - [src/api/x.py,\n  - src/b.py\n---\n")
        r = self._branch()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(
            r.stdout.splitlines(),
            [
                "wiki/pages/concept/bad.md: covers 읽기 실패 — UTF-8 아님",
                "wiki/pages/concept/cut.md: covers 읽기 실패 — covers 의 [ … ] 가 주석에 잘림",
                "wiki/pages/concept/flow.md: covers 읽기 실패 — covers 의 [ 가 그 줄에서 닫히지 않음",
                "wiki/pages/concept/item.md: covers 읽기 실패 — covers 의 [ 로 시작한 항목이 그 줄에서 닫히지 않음",
                "wiki/pages/concept/open.md: covers 읽기 실패 — frontmatter 닫힘 없음",
                "wiki/pages/concept/trail.md: covers 읽기 실패 — covers 의 [ … ] 뒤에 글자가 있음",
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

    def test_inherited_global_pathspec_env_is_neutralized(self) -> None:
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        want = self._branch()
        for var in ("GIT_GLOB_PATHSPECS", "GIT_ICASE_PATHSPECS"):
            with self.subTest(var=var):
                r = self._branch(env={var: "1"})
                self.assertEqual((r.returncode, r.stdout), (want.returncode, want.stdout), r.stderr)

    def test_wiki_in_nested_repo_is_refused(self) -> None:
        inner = self.root / "vendor" / "inner"
        self._init_repo(inner)
        (inner / "wiki" / "pages" / "concept" / "api.md").write_text(covers_page("src/*"), encoding="utf-8")
        self.write("src/a.py", "1\n", root=inner)
        self.commit("i0", cwd=inner)
        self.git("checkout", "-q", "-b", "feat", cwd=inner)
        self.write("src/a.py", "2\n", root=inner)
        self.commit("i1", cwd=inner)
        self.assertEqual(self._branch(cwd=inner).returncode, 1)
        r = self._branch("vendor/inner/wiki", "--base", "HEAD")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    @unittest.skipIf(os.name == "nt", "symlink 이 필요하다")
    def test_auto_discovered_symlink_wiki_is_judged_at_its_target(self) -> None:
        self.git("checkout", "-q", "main")
        (self.root / "docs").mkdir()
        self.git("mv", "wiki", "docs/wiki")
        (self.root / "wiki").symlink_to("docs/wiki")
        self.commit("move wiki")
        self.git("checkout", "-q", "-B", "feat")
        self.write("src/api/x.py", "v2\n")
        self.commit("code")
        r = self._branch()
        self.assertEqual(
            (r.returncode, r.stdout.splitlines()), (1, ["docs/wiki/pages/concept/api.md: covers 변경 — src/api/x.py"]), r.stderr
        )
        self.write("docs/wiki/pages/concept/api.md", covers_page("src/api/*") + "upd\n")
        self.commit("page")
        self.assertEqual(self._branch().returncode, 0)

    def test_case_mismatched_wiki_argument_is_refused(self) -> None:
        if not (self.root / "WIKI").exists():
            self.skipTest("대소문자를 가리는 파일시스템")
        self._page("concept/api.md", covers_page("src/api/*") + "upd\n")
        self.write("src/api/x.py", "v2\n")
        self.commit("code+page")
        self.assertEqual(self._branch().returncode, 0)
        r = self._branch("Wiki")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


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

    def test_reference_lists_submodule_move_under_diff_ignore_submodules_all(self) -> None:
        source = self._temp_dir()
        self.write("x", "1\n", root=source)
        self.git("init", "-q", "-b", "main", cwd=source)
        self.commit("s1", cwd=source)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "sub")
        self._page("concept/api.md", covers_page("sub"))
        self.commit("sub")
        value = self._current()
        self._page("concept/api.md", verified_page(value, "sub"))
        self.commit("confirm")
        self.git("config", "diff.ignoreSubmodules", "all")
        self.write("sub/x", "2\n")
        self.commit("s2", cwd=self.root / "sub")
        # git 2.39 의 commit 은 이 설정을 따라 gitlink 만 바뀐 commit 을 "바뀐 것 없음" 으로 거부한다.
        self.git("add", "-A")
        self.git("-c", "diff.ignoreSubmodules=none", "commit", "-q", "-m", "bump")
        line = self._line(self._report())
        self.assertIn(": STALE — ", line)
        self.assertIn("covers 파일): sub — ", line)

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
        self.assertNotIn("Traceback", r.stderr)

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
        no_wiki = self._temp_dir()
        self.git("init", "-q", cwd=no_wiki)
        rows = {
            "stop_hook_active": ({"stop_hook_active": True}, ()),
            "subagent 대기": ({"background_tasks": [{"type": "subagent"}]}, ()),
            "workflow 대기": ({"background_tasks": [{"type": "workflow"}]}, ()),
            "없는 cwd": ({"cwd": str(self.root / "gone")}, ()),
            "repo 밖": ({"cwd": str(outside)}, ()),
            "repo 밖 명시 wiki": ({"cwd": str(outside)}, ("nope",)),
            "탐색한 wiki 없음": ({"cwd": str(no_wiki)}, ()),
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
        broken = self.root / "broken"
        broken.mkdir()
        (broken / ".git").write_text(f"gitdir: {self.root / 'gone'}\n", encoding="utf-8")
        other = self._other_repo()
        rows = {
            "인자 오류": ({"argv": ["stale", "--stop-hook", "--bogus"]}, "인자 오류"),
            "UTF-8 아님": ({"raw": b'{"cwd": "\xff"}'}, "UTF-8 이 아니다"),
            "JSON 오류": ({"raw": b"{"}, "JSON 오류"),
            "객체 아님": ({"raw": b"[]"}, "객체가 아니다"),
            "cwd 없음": ({"raw": b'{"hook_event_name": "Stop"}'}, "cwd 문자열"),
            "cwd 문자열 아님": ({"payload": {"cwd": 1}}, "cwd 문자열"),
            "명시 wiki 없음": ({"args": ("nope",)}, "pages 디렉터리 없음"),
            "git 없음": ({"env": {"PATH": str(self._temp_dir())}}, "git 을 실행하지 못했다"),
            "rev-parse 실패": ({"payload": {"cwd": str(broken)}, "args": (str(self.wiki),)}, "rev-parse 실패"),
            "최상위 불일치": ({"payload": {"cwd": str(mismatch)}, "args": (str(self.wiki),)}, "탐색한 repo 루트"),
            "wiki 가 repo 밖": ({"payload": {"cwd": str(other)}, "args": (str(self.wiki),)}, "밖이다"),
        }
        for name, (kwargs, expected) in rows.items():
            with self.subTest(row=name):
                out, _ = self._hook(**kwargs)
                self.assertTrue(out["systemMessage"].startswith("wiki_check stale:"), out)
                self.assertIn(expected, out["systemMessage"])
                self.assertNotIn("예상 밖 오류", out["systemMessage"])

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

    @unittest.skipIf(os.name == "nt", "가짜 git 이 sh 스크립트다")
    def test_git_timeout_gives_system_message_within_budget(self) -> None:
        fake = self._temp_dir()
        (fake / "git").write_text("#!/bin/sh\nexec /bin/sleep 5\n", encoding="utf-8")
        (fake / "git").chmod(0o755)
        start = time.monotonic()
        out = self._hook_code(f"wiki_check.HOOK_BUDGET = 1.0\nimport os\nos.environ['PATH'] = {str(fake)!r}")
        self.assertLess(time.monotonic() - start, 3)
        self.assertIn("시간 예산", out["systemMessage"])

    def test_time_spent_after_git_counts_toward_budget(self) -> None:
        out = self._hook_code(
            "import time\n"
            "wiki_check.HOOK_BUDGET = 0.5\n"
            "_changed = wiki_check.changed_files\n"
            "def _slow(*a, **k):\n"
            "    r = _changed(*a, **k)\n"
            "    time.sleep(0.7)\n"
            "    return r\n"
            "wiki_check.changed_files = _slow"
        )
        self.assertIn("시간 예산", out["systemMessage"])

    def test_oversized_stdin_gives_system_message(self) -> None:
        out = self._hook_code("wiki_check.STDIN_MAX = 4")
        self.assertIn("stdin", out["systemMessage"])

    def test_abbreviated_or_valued_flag_is_system_message_not_exit_2(self) -> None:
        for argv in (["stale", "--st"], ["stale", "--stop"], ["stale", "--stop-h"], ["stale", "--stop-hook=1"]):
            with self.subTest(argv=argv):
                out, _ = self._hook(argv=argv)
                self.assertIn("인자 오류", out["systemMessage"])

    def test_hook_flag_on_other_subcommand_or_after_dashes_is_usage_error(self) -> None:
        # 닫힌 모드의 사용 오류가 hook 경로의 exit 0 으로 바뀌면 CI 가 잘못 적은 명령을 통과시킨다.
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        for argv in (["schema", "--st"], ["smoke", "--stop-hook"], ["stale", "--branch", "--", "--stop"]):
            with self.subTest(argv=argv):
                r = subprocess.run(
                    [sys.executable, str(SCRIPT), *argv], input=b"", cwd=self.root, env=proc_env, capture_output=True
                )
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertEqual(r.stdout, b"")

    def test_closed_stderr_pipe_still_gives_system_message(self) -> None:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        rfd, wfd = os.pipe()
        os.close(rfd)
        try:
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "stale", "--stop-hook", "--bogus"],
                input=b"{}",
                stdout=subprocess.PIPE,
                stderr=wfd,
                cwd=self.root,
                env=proc_env,
            )
        finally:
            os.close(wfd)
        self.assertEqual(r.returncode, 0)
        self.assertIn("인자 오류", json.loads(r.stdout)["systemMessage"])

    @unittest.skipIf(os.name == "nt", "프로세스 그룹 신호")
    def test_group_sigterm_still_ends_what_git_started(self) -> None:
        # git 은 새 세션이라 hook 의 그룹에 온 SIGTERM 을 받지 않는다 — hook 이 git 의 그룹을 정리해야 한다.
        fake = self._temp_dir()
        pidfile = fake / "pid"
        (fake / "git").write_text(
            '#!/bin/sh\nfor a in "$@"; do\n  if [ "$a" = status ]; then\n'
            f'    /bin/sleep 30 &\n    echo $! > "{pidfile}.tmp"\n    /bin/mv "{pidfile}.tmp" "{pidfile}"\n'
            f'    wait\n    exit 0\n  fi\ndone\nexec "{shutil.which("git")}" "$@"\n',
            encoding="utf-8",
        )
        (fake / "git").chmod(0o755)
        (fake / "in.json").write_text(json.dumps({"cwd": str(self.root)}), encoding="utf-8")
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        proc_env["PATH"] = f"{fake}{os.pathsep}{proc_env['PATH']}"
        with open(fake / "in.json", "rb") as stdin:
            proc = subprocess.Popen(
                [sys.executable, str(SCRIPT), "stale", "--stop-hook"],
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.root,
                env=proc_env,
                start_new_session=True,
            )
        end = time.monotonic() + 10
        while not pidfile.exists() and time.monotonic() < end:
            time.sleep(0.05)
        if not pidfile.exists():
            proc.kill()
            proc.communicate()
            self.fail("가짜 git 이 자식을 띄우지 않았다")
        os.killpg(proc.pid, signal.SIGTERM)
        proc.communicate(timeout=10)
        pid = int(pidfile.read_text())
        end = time.monotonic() + 3
        while _alive(pid) and time.monotonic() < end:
            time.sleep(0.05)
        if _alive(pid):
            os.kill(pid, signal.SIGKILL)
            self.fail("git 이 띄운 자식이 남았다")
        self.assertEqual(proc.returncode, 0)

    @unittest.skipIf(os.name == "nt", "fd 를 닫는 sh 리다이렉트")
    def test_closed_stdout_or_stderr_still_exits_0(self) -> None:
        proc_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        proc_env.update(self.env)
        payload = json.dumps({"cwd": str(self.root)}).encode("utf-8")
        # 빈 stdin 은 안내를 stderr 로 쓰는 경로다 — 닫힌 stderr 에서 그 안내가 stdout(JSON 자리)에 새면 안 된다.
        for redirect, data in ((">&-", payload), ("2>&-", payload), ("2>&-", b"")):
            with self.subTest(redirect=redirect, empty=not data):
                r = subprocess.run(
                    ["/bin/sh", "-c", f'"$0" "$1" stale --stop-hook {redirect}', sys.executable, str(SCRIPT)],
                    input=data,
                    cwd=self.root,
                    env=proc_env,
                    capture_output=True,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                if not data:
                    self.assertEqual(r.stdout, b"")
        rfd, wfd = os.pipe()
        os.close(rfd)
        try:
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "stale", "--stop-hook"],
                input=payload,
                stdout=wfd,
                stderr=subprocess.PIPE,
                cwd=self.root,
                env=proc_env,
            )
        finally:
            os.close(wfd)
        self.assertEqual(r.returncode, 0, r.stderr)

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

    def test_unborn_head_judges_worktree_without_warning(self) -> None:
        self.git("checkout", "-q", "--orphan", "fresh")
        # orphan 직후에는 index 의 모든 파일이 새 파일이다 — 페이지를 변경 집합에서 빼야 판정이 드러난다.
        self.git("rm", "-q", "-r", "--cached", "wiki")
        (self.root / ".git" / "info").mkdir(exist_ok=True)
        (self.root / ".git" / "info" / "exclude").write_text("wiki/\n", encoding="utf-8")
        out, _ = self._hook()
        self.assertEqual(set(out), {"hookSpecificOutput"})
        self.assertIn("src/api/x.py", out["hookSpecificOutput"]["additionalContext"])

    def test_uncommitted_change_counts_when_base_is_found(self) -> None:
        self.git("checkout", "-q", "-b", "feat")
        out, _ = self._hook()
        self.assertEqual(set(out), {"hookSpecificOutput"})
        self.assertIn("src/api/x.py", out["hookSpecificOutput"]["additionalContext"])

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

    def test_inherited_repo_env_does_not_redirect_repo(self) -> None:
        other = self._other_repo()
        for name, value in (
            ("GIT_DIR", other / ".git"),
            ("GIT_WORK_TREE", other),
            ("GIT_INDEX_FILE", other / ".git" / "index"),
        ):
            with self.subTest(var=name):
                out, _ = self._hook(env={name: str(value)})
                self.assertIn("hookSpecificOutput", out or {}, out)

    @NEEDS_TOMLLIB
    def test_relative_config_arg_is_resolved_from_input_repo_root(self) -> None:
        self.write("docs/c.toml", "[stale]\nstop_hook = false\n")
        src = self.root / "src"
        self.assertIsNone(self._hook({"cwd": str(src)}, ("--config", "docs/c.toml"), cwd=src)[0])

    def test_relative_wiki_arg_is_resolved_from_input_repo_root(self) -> None:
        self.write("docs/wiki/pages/concept/d.md", covers_page("src/api/*"))
        self.commit("docs wiki")
        self.write("src/api/x.py", "v3\n")
        src = self.root / "src"
        out, _ = self._hook({"cwd": str(src)}, ("docs/wiki",), cwd=src)
        self.assertIn("docs/wiki/pages/concept/d.md", out["hookSpecificOutput"]["additionalContext"])


class SmokeTest(WikiTestCase):
    def _config(self, content: str) -> None:
        (self.wiki / "wiki-check.toml").write_text(content, encoding="utf-8")

    def _index(self, *stems: str) -> None:
        (self.wiki / "index.md").write_text("".join(f"- [[{s}]]\n" for s in stems), encoding="utf-8")

    @NEEDS_TOMLLIB
    def test_question_needs_page_index_entry_and_body_evidence(self) -> None:
        self._page("concept/ok.md", page_text() + "근거 문구\n")
        self._page("concept/unlisted.md", page_text() + "근거 문구\n")
        self._page("concept/fm-only.md", page_text(extra="note: 근거 문구"))
        self._page("concept/open.md", page_text(close=False) + "근거 문구\n")
        self._index("ok", "fm-only", "open")
        self._config(
            smoke_toml(
                ("통과", "concept/ok.md", "근거 문구"),
                ("파일", "concept/nope.md", "근거 문구"),
                ("등재", "concept/unlisted.md", "근거 문구"),
                ("본문", "concept/fm-only.md", "근거 문구"),
                ("닫힘", "concept/open.md", "근거 문구"),
            )
        )
        r = self._cli("smoke", "wiki")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(
            r.stdout.splitlines(),
            [
                "PASS | 통과 → wiki/pages/concept/ok.md",
                "FAIL | 파일 → wiki/pages/concept/nope.md — 파일 없음",
                "FAIL | 등재 → wiki/pages/concept/unlisted.md — index.md 에 [[unlisted]] 등재 없음",
                "FAIL | 본문 → wiki/pages/concept/fm-only.md — 본문에 근거 없음: 근거 문구",
                "FAIL | 닫힘 → wiki/pages/concept/open.md — frontmatter 가 닫히지 않아 본문을 가를 수 없다",
                "wiki smoke check: PASS 1 · FAIL 4",
            ],
        )
        self.assertIn("4 위반", r.stderr)

    @NEEDS_TOMLLIB
    def test_expect_is_searched_line_by_line_like_grep(self) -> None:
        self._page("concept/lines.md", page_text() + "앞 부분\n줄 머리 문구\n뒷 부분\n")
        self._index("lines")
        self._config(
            smoke_toml(
                ("앵커", "concept/lines.md", "^줄 머리"),
                ("끝 앵커", "concept/lines.md", "문구$"),
                ("줄 넘김", "concept/lines.md", "앞 부분[^!]*뒷 부분"),
            )
        )
        r = self._cli("smoke", "wiki")
        self.assertEqual([line[:4] for line in r.stdout.splitlines()[:3]], ["PASS", "PASS", "FAIL"], r.stdout)

    @NEEDS_TOMLLIB
    def test_bom_and_crlf_page_splits_body_like_schema(self) -> None:
        text = page_text(extra="note: 머리 근거") + "줄 끝 문구\n"
        self._page("concept/crlf.md", "\ufeff" + text.replace("\n", "\r\n"))
        self._index("crlf")
        self._config(smoke_toml(("줄 끝", "concept/crlf.md", "문구$"), ("머리", "concept/crlf.md", "머리 근거")))
        r = self._cli("smoke", "wiki")
        self.assertEqual([line[:4] for line in r.stdout.splitlines()[:2]], ["PASS", "FAIL"], r.stdout)

    @NEEDS_TOMLLIB
    def test_missing_index_fails_question_with_its_own_reason(self) -> None:
        self._page("concept/x.md", page_text() + "근거 문구\n")
        self._config(smoke_toml(("등재", "concept/x.md", "근거 문구")))
        r = self._cli("smoke", "wiki")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("FAIL | 등재 → wiki/pages/concept/x.md — index.md 없음", r.stdout)

    def test_without_config_is_not_applicable(self) -> None:
        r = self._cli("smoke", "wiki")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("검사 대상 아님", r.stdout)

    @NEEDS_TOMLLIB
    def test_template_copied_as_config_is_not_applicable(self) -> None:
        shutil.copy2(TEMPLATE, self.wiki / "wiki-check.toml")
        r = self._cli("smoke", "wiki")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("검사 대상 아님", r.stdout)

    @NEEDS_TOMLLIB
    def test_unusable_smoke_config_exits_2(self) -> None:
        self._page("concept/x.md", page_text())
        cases = [
            (smoke_toml(("q", "concept/x.md", "[[:space:]]본문")), "POSIX"),
            ('[smoke.forbid]\npatterns = ["[[:digit:]]+건"]\n', "POSIX"),
            (smoke_toml(("q", "concept/x.md", "(")), "정규식 오류"),
            ("[smoke]\n", "검사가 0개"),
            ("[smoke.forbid]\nbranch_names = false\n", "검사가 0개"),
            ("[smoke.forbid]\nbranch_names = true\n", "repo 밖"),
        ]
        for content, needle in cases:
            with self.subTest(content=content):
                self._config(content)
                r = self._cli("smoke", "wiki")
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn(needle, r.stderr)
                self.assertNotIn("Traceback", r.stderr)


class SmokeForbidTest(GitWikiTestCase):
    @NEEDS_TOMLLIB
    def test_forbid_checks_print_path_and_line_of_each_hit(self) -> None:
        for branch in ("feat-alpha", "Upper-case", "single", "topic/sub-gamma"):
            self.git("branch", branch)
        self.git("update-ref", "refs/remotes/upstream/fix-beta", "HEAD")
        self.write(
            "wiki/pages/concept/leak.md",
            page_text(extra="status: in_progress")
            + "feat-alpha 를 머지하면\n"
            + "fix-beta 와 feat-alpha, Upper-case single sub-gamma\n"
            + "열린 이슈 3건\n",
        )
        self.write(
            "wiki/wiki-check.toml",
            '[smoke.forbid]\nbranch_names = true\nplan_status = true\npatterns = ["이슈 [0-9]+건", "없는 문구"]\n',
        )
        r = self._cli("smoke", "wiki")
        self.assertEqual(r.returncode, 1, r.stderr)
        leak = "wiki/pages/concept/leak.md"
        self.assertEqual(
            r.stdout.splitlines(),
            [
                f"FAIL | 금지 — 작업 브랜치 이름 2개 → {leak}:11 (feat-alpha)",
                f"FAIL | 금지 — 작업 브랜치 이름 2개 → {leak}:12 (feat-alpha, fix-beta)",
                f"FAIL | 금지 — status: in_progress → {leak}:7 (status: in_progress)",
                f"FAIL | 금지 — 패턴 이슈 [0-9]+건 → {leak}:13 (이슈 3건)",
                "PASS | 금지 — 패턴 없는 문구",
                "wiki smoke check: PASS 1 · FAIL 4",
            ],
        )

    def test_ref_name_with_unicode_line_break_is_one_branch(self) -> None:
        self.git("branch", "zz\u0085refs/heads/ghost-branch")
        self.assertNotIn("ghost-branch", wiki_check.work_branches(self.repo()))


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

    @NEEDS_TOMLLIB
    def test_copied_script_alone_catches_failing_smoke_question(self) -> None:
        solo = self.root / "solo"
        solo.mkdir()
        shutil.copy2(SCRIPT, solo / "wiki_check.py")
        no_git = self.root / "empty-path"
        no_git.mkdir()
        self._page("concept/x.md", page_text())
        (self.wiki / "index.md").write_text("[[x]]\n", encoding="utf-8")
        (self.wiki / "wiki-check.toml").write_text(
            smoke_toml(("근거", "concept/x.md", "없는 근거")), encoding="utf-8"
        )
        r = self._cli("smoke", "wiki", env={"PATH": str(no_git)}, script=solo / "wiki_check.py")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("FAIL | 근거 → wiki/pages/concept/x.md", r.stdout)

    def test_source_parses_with_python_39_grammar(self) -> None:
        ast.parse(SCRIPT.read_text(encoding="utf-8"), feature_version=(3, 9))


if __name__ == "__main__":
    unittest.main(verbosity=2)
