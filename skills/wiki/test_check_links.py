#!/usr/bin/env python3
"""check_links.py 의 wiki 구조 점검 단위 테스트 (stdlib unittest, 의존성 0).

수동 실행 (이 디렉터리에서):
    uv run --no-project python test_check_links.py

점검 대상 불변식(`wiki/WIKI.md` 규약): 페이지마다 frontmatter 필수키,
나가는(outbound) 링크 ≥2, dead link 없음, orphan(inbound=0, index 제외) 없음,
index.md ↔ pages/ 동기화.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_links  # noqa: E402

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
