#!/usr/bin/env python3
"""wiki/ 구조 점검 — /wiki lint·ingest 의 구조 점검 자동화 부분.

`wiki/WIKI.md` 규약 중 기계적으로 검증 가능한 불변식만 점검한다(모순·stale 같은
의미 점검은 LLM 담당):
- frontmatter 필수키(title/category/created/updated/sources)
- 나가는(outbound) 링크 ≥2
- dead link 없음(모든 `[[name]]` 이 pages/ 에 실재)
- orphan 없음(index.md 제외, 다른 페이지로부터 inbound ≥1)
- index.md ↔ pages/ 동기화(누락·잉여)

위반을 한 줄씩 출력하고 위반 시 exit 1(clean 0, pages 디렉터리 없으면 2).
git 없이 파일만 읽으므로 stdlib 외 의존성이 없다.

Usage (wiki/ 또는 repo 루트에서):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/check_links.py" [wiki_root]
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

# Windows 콘솔 기본 인코딩에서 한글 출력 시 UnicodeEncodeError 방지.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

# 코드블록·인라인 코드 안의 [[ ]] 도 링크로 센다 — pages 본문은 위키링크를
# 코드 예시로 쓰지 않는 규약이라 단순 스캔으로 충분(걸리면 lint 가 사람에게 보고).
WIKILINK = re.compile(r"\[\[([a-z0-9-]+)\]\]")
FM_KEY = re.compile(r"^([a-zA-Z_]+):")
REQUIRED_FM = {"title", "category", "created", "updated", "sources"}


def extract_links(text: str) -> set[str]:
    return set(WIKILINK.findall(text))


def extract_fm_keys(text: str) -> set[str]:
    """파일 선두 `---` 블록의 최상위 키 집합. frontmatter 없으면 빈 집합."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    keys: set[str] = set()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = FM_KEY.match(line)
        if m:
            keys.add(m.group(1))
    return keys


def check_wiki(wiki_root: Path) -> list[str]:
    """위반 메시지 목록(빈 목록 = clean)."""
    pages_dir = wiki_root / "pages"
    pages: dict[str, tuple[set[str], set[str]]] = {}
    for md in sorted(pages_dir.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        pages[md.stem] = (extract_links(text), extract_fm_keys(text))

    index_path = wiki_root / "index.md"
    index_links = (
        extract_links(index_path.read_text(encoding="utf-8"))
        if index_path.is_file()
        else set()
    )

    # inbound 는 pages 끼리만 센다(index.md 의 카탈로그 링크는 제외) — 그래야
    # "어느 본문도 안 가리키는" 진짜 고립 페이지를 orphan 으로 잡는다.
    inbound: dict[str, set[str]] = {n: set() for n in pages}
    for src, (outs, _) in pages.items():
        for tgt in outs:
            if tgt in inbound and tgt != src:
                inbound[tgt].add(src)

    violations: list[str] = []
    for name in sorted(pages):
        outs, fm_keys = pages[name]
        for tgt in sorted(outs):
            if tgt not in pages:
                violations.append(f"dead link: [[{tgt}]] in {name} (대상 페이지 없음)")
        outbound = {o for o in outs if o != name and o in pages}
        if len(outbound) < 2:
            violations.append(f"outbound 부족: {name} — 나가는 링크 {len(outbound)}개 (<2)")
        missing = REQUIRED_FM - fm_keys
        if missing:
            violations.append(f"frontmatter 누락: {name} — {', '.join(sorted(missing))}")
        if not inbound[name]:
            violations.append(f"orphan: {name} (index 외 어느 페이지도 안 가리킴)")

    page_names = set(pages)
    for n in sorted(page_names - index_links):
        violations.append(f"index 누락: {n} (pages 에 있으나 index.md 미등재)")
    for n in sorted(index_links - page_names):
        violations.append(f"index dead link: [[{n}]] (index.md 에 있으나 페이지 없음)")

    return violations


def find_wiki_root(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1])
    cwd = Path.cwd()
    for cand in (cwd, cwd / "wiki"):
        if (cand / "WIKI.md").is_file() or (cand / "pages").is_dir():
            return cand
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return Path(result.stdout.strip()) / "wiki"
    return cwd / "wiki"


def main(argv: list[str]) -> int:
    wiki_root = find_wiki_root(argv)
    if not (wiki_root / "pages").is_dir():
        print(f"wiki pages 디렉터리 없음: {wiki_root}", file=sys.stderr)
        return 2
    violations = check_wiki(wiki_root)
    for v in violations:
        print(v)
    if violations:
        print(f"\n{len(violations)} 위반", file=sys.stderr)
        return 1
    print("wiki link check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
