#!/usr/bin/env python3
"""check_links.py 의 wiki 구조 점검 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_check_links.py

점검 대상 불변식(`wiki/WIKI.md` 규약): 페이지마다 frontmatter 필수키,
나가는(outbound) 링크 ≥2, dead link 없음, orphan(inbound=0, index 제외) 없음,
index.md ↔ pages/ 동기화.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_links  # noqa: E402
import wiki_search  # noqa: E402  # 규칙 대조용 — check_links 자신은 import 하지 않는다

FRONTMATTER = """---
title: {name}
category: concept
created: 2026-06-16
updated: 2026-06-16
sources: [x]
---
"""


class CheckWikiTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "pages" / "concept").mkdir(parents=True)
        self.addCleanup(self._tmp.cleanup)

    def _page(self, name: str, links: list[str], *, fm: bool = True) -> None:
        body = (FRONTMATTER.format(name=name) if fm else "") + f"\n# {name}\n\n"
        body += " ".join(f"[[{ln}]]" for ln in links) + "\n"
        (self.root / "pages" / "concept" / f"{name}.md").write_text(body, encoding="utf-8")

    def _index(self, names: list[str]) -> None:
        text = "# Wiki Index\n\n" + "\n".join(f"- [[{n}]] — x" for n in names) + "\n"
        (self.root / "index.md").write_text(text, encoding="utf-8")

    def _clean(self) -> None:
        self._page("a", ["b", "c"])
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._index(["a", "b", "c"])

    def test_clean_has_no_violations(self) -> None:
        self._clean()
        self.assertEqual(check_links.check_wiki(self.root), [])

    def test_dead_link(self) -> None:
        self._page("a", ["b", "zzz"])  # zzz 페이지 없음
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._index(["a", "b", "c"])
        v = check_links.check_wiki(self.root)
        self.assertTrue(any("zzz" in x for x in v), v)

    def test_outbound_too_few(self) -> None:
        self._page("a", ["b"])  # 나가는 링크 1개
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._index(["a", "b", "c"])
        v = check_links.check_wiki(self.root)
        self.assertTrue(any("a" in x and "outbound" in x.lower() for x in v), v)

    def test_orphan(self) -> None:
        self._page("a", ["b", "c"])
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._page("d", ["a", "b"])  # outbound 2지만 아무도 d 를 안 가리킴
        self._index(["a", "b", "c", "d"])
        v = check_links.check_wiki(self.root)
        self.assertTrue(any("d" in x and "orphan" in x.lower() for x in v), v)

    def test_frontmatter_missing(self) -> None:
        self._page("a", ["b", "c"], fm=False)
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._index(["a", "b", "c"])
        v = check_links.check_wiki(self.root)
        self.assertTrue(any("a" in x and "frontmatter" in x.lower() for x in v), v)

    def test_index_missing_page(self) -> None:
        self._page("a", ["b", "c"])
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._index(["a", "b"])  # c 미등재
        v = check_links.check_wiki(self.root)
        self.assertTrue(any("c" in x and "index" in x.lower() for x in v), v)

    def test_index_extra(self) -> None:
        self._clean()
        self._index(["a", "b", "c", "ghost"])  # ghost 페이지 없음
        v = check_links.check_wiki(self.root)
        self.assertTrue(any("ghost" in x for x in v), v)

    def test_alias_link_is_an_edge(self) -> None:
        self._page("a", ["b|베타 페이지", "c"])  # 별칭 1개 + 링크 1개로 outbound 2
        self._page("b", ["a", "c"])
        self._page("c", ["a", "d|디"])
        self._page("d", ["a", "b"])  # c 의 별칭으로만 들어온다
        self._index(["a", "b", "c", "d"])
        self.assertEqual(check_links.check_wiki(self.root), [])

    def test_alias_dead_link(self) -> None:
        self._page("a", ["b", "c", "zzz|없는 페이지"])
        self._page("b", ["a", "c"])
        self._page("c", ["a", "b"])
        self._index(["a", "b", "c"])
        self.assertEqual(
            check_links.check_wiki(self.root),
            ["dead link: [[zzz]] in a (대상 페이지 없음)"],
        )

    def test_unclosed_alias_keeps_next_link(self) -> None:
        self._page("a", ["b", "c"])
        self._page("b", ["a", "c"])
        self._page("c", ["a", "x|열림 [[b"])  # 본문 `[[x|열림 [[b]]`
        self._index(["a", "b", "c"])
        self.assertEqual(check_links.check_wiki(self.root), [])

    def test_index_entry_needs_plain_link(self) -> None:
        self._clean()
        self._index(["a", "b", "c|씨", "zzz|없음"])
        self.assertEqual(
            check_links.check_wiki(self.root),
            [
                "index 누락: c (pages 에 있으나 index.md 미등재)",
                "index dead link: [[zzz]] (index.md 에 있으나 페이지 없음)",
            ],
        )

    def _main(self) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = check_links.main(["check_links.py", str(self.root)])
        return code, out.getvalue(), err.getvalue()

    def test_non_utf8_page_and_index_are_violations_and_the_rest_is_judged(self) -> None:
        # wiki_check schema 처럼 위반(1)이다. 링크 문법은 ASCII 라 깨진 바이트를 바꿔 읽어도 판정이 같다.
        self._clean()
        for path in (self.root / "pages" / "concept" / "a.md", self.root / "index.md"):
            path.write_bytes(path.read_bytes() + b"\xff\n")
        code, out, _ = self._main()
        self.assertEqual(code, 1)
        self.assertEqual([line.split(" (")[0] for line in out.splitlines()], ["UTF-8 아님: a", "UTF-8 아님: index.md"])

    def test_read_error_exits_2_without_a_verdict(self) -> None:
        # 일부만 읽은 판정은 판정이 아니다 — 위반(1)이 아니라 점검 불가(2). read() 단계의 실패(EIO)는 경로를 싣지 않는다.
        self._clean()
        target = self.root / "pages" / "concept" / "b.md"
        for error in (PermissionError(13, "Permission denied", str(target)), OSError(5, "Input/output error")):
            with self.subTest(error=error):

                def fail_on_target(real):
                    def read(path, *args, **kwargs):
                        if path == target:
                            raise error
                        return real(path, *args, **kwargs)

                    return read

                with mock.patch.object(Path, "read_bytes", fail_on_target(Path.read_bytes)), mock.patch.object(
                    Path, "read_text", fail_on_target(Path.read_text)
                ):
                    code, out, err = self._main()
                self.assertEqual((code, out), (2, ""))
                self.assertIn(f"check_links: 읽기 실패 — {target}: {error.strerror}", err)

    def test_non_regular_md_entries_are_not_pages(self) -> None:
        # 일반 파일만 페이지다(wiki_check 와 같다). 도는 symlink 를 읽으면 오류, FIFO 는 쓰는 쪽을 기다리며 멈춘다.
        self._clean()
        concept = self.root / "pages" / "concept"
        (concept / "notes.md").mkdir()
        with contextlib.suppress(OSError):  # Windows 는 권한·개발자 모드 없이는 symlink 를 만들지 못한다
            os.symlink(concept / "missing.md", concept / "broken.md")
            os.symlink(concept / "loop.md", concept / "loop.md")
        if hasattr(os, "mkfifo"):
            os.mkfifo(concept / "fifo.md")
        self.assertEqual(self._main()[:2], (0, "wiki link check: clean\n"))

    def test_permission_error_on_a_page_is_reported_not_skipped(self) -> None:
        # Python 3.14 의 is_file() 은 stat 의 권한 오류를 False 로 삼킨다 — 그 페이지가 빠진 판정이 아니라 2 여야 한다.
        self._clean()
        target = self.root / "pages" / "concept" / "b.md"
        real_stat = Path.stat

        def fake_stat(path, *args, **kwargs):
            if path == target:
                raise PermissionError(13, "Permission denied", str(target))
            return real_stat(path, *args, **kwargs)

        with mock.patch.object(Path, "stat", fake_stat):
            code, out, err = self._main()
        self.assertEqual((code, out), (2, ""))
        self.assertIn(f"check_links: 읽기 실패 — {target}: Permission denied", err)

    def test_lone_cr_ends_a_line_like_text_mode(self) -> None:
        # 텍스트 모드로 읽던 때처럼 lone CR 도 줄바꿈이다 — 별칭 안에 있으면 링크가 아니다.
        self._clean()
        page = self.root / "pages" / "concept" / "a.md"
        page.write_bytes(page.read_bytes() + b"[[zzz|x\ry]]\n")
        self.assertEqual(self._main()[:2], (0, "wiki link check: clean\n"))

    @unittest.skipIf(os.name == "nt" or os.geteuid() == 0, "권한으로 디렉터리 읽기를 막을 수 없다")
    def test_unreadable_subdirectory_exits_2(self) -> None:
        # rglob 은 읽지 못한 하위 디렉터리를 조용히 건너뛰어 그 아래 페이지가 빠진 채 판정한다.
        self._clean()
        sub = self.root / "pages" / "entity"
        sub.mkdir()
        sub.chmod(0)
        self.addCleanup(sub.chmod, 0o755)
        code, out, err = self._main()
        self.assertEqual((code, out), (2, ""))
        self.assertIn(f"check_links: 읽기 실패 — {sub}", err)


class WikiLinkTest(unittest.TestCase):
    def test_same_rule_as_wiki_search(self) -> None:
        self.assertEqual(check_links.WIKILINK.pattern, wiki_search.LINK.pattern)

    def test_alias_boundaries(self) -> None:
        cases = {"[[a|]]": {"a"}, "[[a|b|c]]": {"a"}, "[[a|b]c]]": set(), "[[a|b\nc]]": set()}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(check_links.extract_links(text), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
