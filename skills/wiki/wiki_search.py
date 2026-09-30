#!/usr/bin/env python3
"""wiki 검색 — 공용 wiki 와 현재 repo 의 wiki 에서 질의어로 페이지를 찾아 점수순으로 보인다.

대상은 공용 wiki(`CLAUDE_SHARED_WIKI`, 없으면 `~/.claude/wiki`)와 현재 디렉터리에서 repo 루트까지
올라가며 찾은 `wiki/` 다. 공용 wiki 는 cwd 와 무관하게 찾는다 — `~/.claude` worktree 에는 사본이 없고
`~/.claude` 루트의 rg·Grep 은 그 clone 을 건너뛴다. 첫 줄에 찾은 wiki 와 쪽수를 적는다. 결과가
없을 때 어디를 찾았는지 남아야 "wiki 에 없음" 을 판단할 수 있다.

점수는 질의 토큰마다 idf × (3·[stem·title 에 있음] + 2.5·[index 요약에 있음] + 본문 BM25) 의 합이다.
본문 BM25 는 아무리 반복해도 K1+1(2.2)을 넘지 않아, stem·title·요약 일치가 같은 단어의 본문 반복보다
늘 위다. 토큰은 영문·숫자 단어(식별자는 `_`·`-`·`.` 로 나눈 조각과 전체)와 한글 연속 음절의 2-gram
이다(조사가 붙어도 앞 음절이 맞는다). 한 음절 한글은 버리므로 `훅` 같은 한 음절 질의는 찾지 못한다.

페이지는 구조로도 읽는다. 구조는 섹션(H2 이하 제목, 코드 블록 밖), `[[링크]]`(별칭 `[[a|b]]` 포함, 전문 어디서나),
`[!open]`·`[!conflict]` callout 이다. 검색 결과의 맞은 줄에는 섹션과 그 줄 범위를 붙이고, 결과마다 같은 wiki 안에서
링크로 이어진 관련 페이지(→ 나가는·← 들어오는, index.md 제외)를 붙인다. 질의 모드 `--links-to <stem>` 은 그 stem 을
가리키는 링크가 든 줄을, `--open` 은 미해결 callout 을 전부(`--limit` 무관) 낸다. `--category` 는 검색 대상과 질의 모드의
출발 페이지에만 적용하고, 그래프는 거르기 전 전체로 만든다.

stdlib 만 쓰고, frontmatter·BOM·CRLF 는 같은 디렉터리의 wiki_check.py 로 읽는다.

exit: 0 결과 있음, 1 결과 없음, 2 찾을 wiki·단어·category·stem 이 없음·질의 모드 사용 오류·`CLAUDE_SHARED_WIKI` 가
wiki 가 아님·읽기 오류.

Usage (어디서든, 옵션은 질의어 사이 어디든 된다. `-` 로 시작하는 단어는 앞의 `-` 를 떼고 넣는다 — 토큰은
영문·숫자부터라 결과가 같고, 3.12 까지의 argparse 는 섞인 옵션과 `--` 를 함께 처리하지 못한다):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_search.py" <질의어…> [--limit N] [--category C]
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_search.py" --links-to <stem> [--category C]
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_search.py" --open [--category C]
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import wiki_check

NAME_WEIGHT = 3.0
SUMMARY_WEIGHT = 2.5  # 본문 BM25 상한(K1 + 1)보다 커야 요약 일치가 본문 반복보다 위다.
K1 = 1.2
B = 0.75
SHOWN_BODY_LINES = 2
SHOWN_WIDTH = 200
SHOWN_TITLE_WIDTH = 40
SHOWN_RELATED = 6

WORD = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*|[가-힣]+")
PART = re.compile(r"[._-]")
# wiki_check.STEM 은 check_links.WIKILINK 가 링크로 읽는 이름과 같은 집합이다.
INDEX_ENTRY = re.compile(r"\s*[-*+]\s+\[\[(" + wiki_check.STEM.pattern + r")\]\]\s*[—–:-]*\s*(.*)")
# 별칭 `[[a|b]]` 도 간선이다(check_links.WIKILINK 와 같은 규칙). 별칭에 `[` 를 받지 않아야
# 닫히지 않은 별칭이 뒤의 링크를 삼키지 않는다.
LINK = re.compile(r"\[\[(" + wiki_check.STEM.pattern + r")(?:\|[^\[\]\n]*)?\]\]")
HEADING = re.compile(r"(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")  # 빈 제목(`##`)도 섹션 경계다
CLOSING_HASHES = re.compile(r"(?:^|[ \t]+)#+$")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
# WIKI.md 표기(`> [!open]`) 밖의 변형(대소문자·접기 표시 `-`/`+`·중첩 인용)도 모은다 — 놓치는 쪽이 더 나쁘다.
CALLOUT = re.compile(r"(?:>[ \t]*)+\[!(open|conflict)\][-+]?[ \t]*(.*)", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    tokens = []
    for word in WORD.findall(text.lower()):
        if "가" <= word[0] <= "힣":
            tokens += [word[i : i + 2] for i in range(len(word) - 1)]
            continue
        parts = PART.split(word)
        if len(parts) > 1:
            tokens.append(word)
        tokens += [part for part in parts if len(part) > 1]
    return tokens


@dataclass(frozen=True)
class Section:
    level: int
    title: str
    start: int  # 파일 기준 줄 번호
    end: int


@dataclass
class Structure:
    sections: list[Section]
    links: list[tuple[int, str]]  # (줄 번호, stem)
    callouts: list[tuple[int, str, str]]  # (줄 번호, open|conflict, 첫 줄 문장)


def parse_structure(lines: list[str], body_start: int) -> Structure:
    """links 는 check_links 처럼 전문(frontmatter·코드 블록 포함)에서, 제목·callout 은 본문의 코드 블록 밖에서만 찾는다.
    body_start — 본문 첫 줄의 0 기준 위치. 코드 블록은 CommonMark 처럼 여는 fence 와 같은 문자·같거나 긴 길이로만
    닫히고, backtick fence 의 info 에 backtick 이 있으면 fence 가 아니다. 인용(`>`) 안의 코드 블록은 코드로 보지 않는다."""
    links = [(n, m.group(1)) for n, line in enumerate(lines, 1) for m in LINK.finditer(line)]
    headings, callouts, fence = [], [], ""
    for n, line in enumerate(lines[body_start:], body_start + 1):
        m = FENCE.match(line)
        info = line[m.end() :] if m else ""
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not info.strip():
                fence = ""
            continue
        if m and not (m.group(1)[0] == "`" and "`" in info):
            fence = m.group(1)
            continue
        h = HEADING.match(line)
        if h:
            headings.append((len(h.group(1)), CLOSING_HASHES.sub("", (h.group(2) or "").strip()), n))
            continue
        c = CALLOUT.match(line)
        if c:
            callouts.append((n, c.group(1).lower(), c.group(2).strip()))
    sections = [
        Section(level, title, start, next((s - 1 for lv, _, s in headings[i + 1 :] if lv <= level), len(lines)))
        for i, (level, title, start) in enumerate(headings)
        if level > 1  # H1 은 페이지 제목이다
    ]
    return Structure(sections, links, callouts)


def section_at(sections: list[Section], n: int) -> Section | None:
    """n 번째 줄을 담은 가장 깊은 섹션."""
    found = None
    for section in sections:
        if section.start <= n <= section.end and (found is None or section.level > found.level):
            found = section
    return found


@dataclass
class Page:
    tier: str
    path: Path
    name: str  # pages 기준 경로에서 .md 를 뗀 것
    stem: str
    title: str
    category: str
    index_line: int  # 0 — index 에 없음
    summary: str
    body_offset: int  # 파일에서 본문 앞 줄 수 — 본문은 lines[body_offset:]
    name_terms: set[str]
    summary_terms: set[str]
    body_counts: Counter
    body_length: int
    lines: list[str]  # frontmatter 를 포함한 전문
    structure: Structure
    outbound: list[Page] = field(default_factory=list)  # 같은 wiki 에 있는 페이지만, self 제외
    inbound: list[Page] = field(default_factory=list)


def read_index(path: Path) -> dict[str, tuple[int, str]]:
    """stem → (index.md 줄 번호, 요약). index 가 없으면 빈 값이다 — 읽지 못하면 OSError."""
    if not path.exists():
        return {}
    entries: dict[str, tuple[int, str]] = {}
    text = wiki_check.normalize(path.read_bytes().decode("utf-8", "replace"))
    for n, line in enumerate(wiki_check.text_lines(text), 1):
        m = INDEX_ENTRY.match(line)
        if m and m.group(1) not in entries:
            entries[m.group(1)] = (n, m.group(2).strip())
    return entries


def _raise(error: OSError) -> None:
    raise error


def load_pages(tier: str, wiki: Path) -> list[Page]:
    index = read_index(wiki / "index.md")
    pages_dir = wiki / "pages"
    texts = {}
    if pages_dir.is_dir():
        # read_texts 의 rglob 은 읽지 못한 하위 디렉터리를 조용히 건너뛴다 — 먼저 걸어 OSError 로 드러낸다.
        for _ in os.walk(pages_dir, onerror=_raise):
            pass
        texts = wiki_check.read_texts(pages_dir)
    pages = []
    for rel, text in texts.items():
        posix = PurePosixPath(rel)
        fields = wiki_check.parse_frontmatter(text).fields
        title = fields.get("title")
        title = title if isinstance(title, str) else ""
        category = fields.get("category")
        if not isinstance(category, str) or not category:
            category = posix.parts[0] if len(posix.parts) > 1 else ""
        lines = wiki_check.text_lines(text)
        body = wiki_check.body_lines(text)
        if body is None:  # frontmatter 가 닫히지 않으면 경계를 모른다 — 전부 본문으로 찾는다.
            body = lines
        index_line, summary = index.get(posix.stem, (0, ""))
        body_offset = len(lines) - len(body)
        body_counts = Counter(tokenize("\n".join(body)))
        pages.append(
            Page(
                tier=tier,
                path=pages_dir / rel,
                name=posix.with_suffix("").as_posix(),
                stem=posix.stem,
                title=title,
                category=category,
                index_line=index_line,
                summary=summary,
                body_offset=body_offset,
                name_terms=set(tokenize(posix.stem)) | set(tokenize(title)),
                summary_terms=set(tokenize(summary)),
                body_counts=body_counts,
                body_length=sum(body_counts.values()),
                lines=lines,
                structure=parse_structure(lines, body_offset),
            )
        )
    return pages


def link_graph(pages: list[Page]) -> dict[str, dict[str, Page]]:
    """wiki(계층)마다 stem → 페이지를 만들고 각 페이지의 outbound·inbound 를 채운다. 링크는 같은 wiki 안에서만
    잇는다. 한 wiki 에 같은 stem 이 둘이면(schema 위반) pages 기준 경로 순으로 앞의 것을 쓴다."""
    by_wiki: dict[str, dict[str, Page]] = {}
    for page in pages:
        by_wiki.setdefault(page.tier, {}).setdefault(page.stem, page)
    for page in pages:
        names = by_wiki[page.tier]
        seen = {page.stem}
        for _, stem in page.structure.links:
            target = names.get(stem)
            if target is not None and stem not in seen:
                seen.add(stem)
                page.outbound.append(target)
                target.inbound.append(page)
    return by_wiki


def rank(pages: list[Page], terms: list[str]) -> list[tuple[float, Page]]:
    """점수가 0 보다 큰 페이지를 점수 내림차순으로. 동점은 들어온 순서(대상 순서 → pages 기준 경로)."""
    n = len(pages)
    avg_length = max(sum(p.body_length for p in pages) / n, 1) if n else 1
    idf = {}
    for term in terms:
        df = sum(1 for p in pages if term in p.name_terms or term in p.summary_terms or p.body_counts[term])
        if df:
            idf[term] = math.log(1 + (n - df + 0.5) / (df + 0.5))
    ranked = []
    for order, page in enumerate(pages):
        norm = K1 * (1 - B + B * page.body_length / avg_length)
        score = 0.0
        for term, weight in idf.items():
            tf = page.body_counts[term]
            fields = NAME_WEIGHT * (term in page.name_terms) + SUMMARY_WEIGHT * (term in page.summary_terms)
            score += weight * (fields + tf * (K1 + 1) / (tf + norm))
        if score > 0:
            ranked.append((score, order, page))
    ranked.sort(key=lambda r: (-r[0], r[1]))
    return [(score, page) for score, _, page in ranked]


def matched_lines(page: Page, terms: set[str]) -> list[tuple[int, str]]:
    """질의 토큰이 가장 많이 맞은 본문 줄(파일 기준 줄 번호, 줄)."""
    body = page.lines[page.body_offset :]
    hits = []
    for i, line in enumerate(body):
        count = len(terms & set(tokenize(line)))
        if count:
            hits.append((-count, i))
    return [(page.body_offset + i + 1, body[i].strip()) for _, i in sorted(hits)[:SHOWN_BODY_LINES]]


def shorten(text: str, width: int = SHOWN_WIDTH) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def locate(page: Page, n: int, with_range: bool = False) -> str:
    """`L<n>` 뒤에 그 줄이 든 곳 — frontmatter, 섹션(원하면 줄 범위까지), 첫 제목 앞 본문이면 붙이지 않는다."""
    if n <= page.body_offset:
        return f"L{n} frontmatter"
    section = section_at(page.structure.sections, n)
    if section is None or not section.title:
        return f"L{n}"
    span = f" (L{section.start}-{section.end})" if with_range else ""
    return f"L{n} §{shorten(section.title, SHOWN_TITLE_WIDTH)}{span}"


def related_line(page: Page) -> str:
    outs = [p.name for p in page.outbound][:SHOWN_RELATED]
    ins = [p.name for p in page.inbound][: SHOWN_RELATED - len(outs)]
    parts = ([f"→ {', '.join(outs)}"] if outs else []) + ([f"← {', '.join(ins)}"] if ins else [])
    return "관련: " + " · ".join(parts) if parts else ""


def link_records(page: Page, stem: str, by_wiki: dict[str, dict[str, Page]]) -> list[tuple[int, str]]:
    """page 에서 같은 wiki 의 stem 페이지를 가리키는 줄(한 줄에 여럿이어도 한 번). self-link 는 link_graph 처럼 stem 으로
    가른다."""
    if stem not in by_wiki[page.tier] or page.stem == stem:
        return []
    lines = dict.fromkeys(n for n, s in page.structure.links if s == stem)
    return [(n, page.lines[n - 1].strip()) for n in lines]


def callout_records(page: Page) -> list[tuple[int, str]]:
    return [(n, f"[!{kind}] {text}") for n, kind, text in page.structure.callouts]


def print_records(pages: list[Page], records_of, empty: str) -> int:
    """페이지마다 머리줄(계층·이름·절대경로) 아래 레코드를 한 줄씩 낸다. `--limit` 없이 전부 낸다."""
    count = 0
    for page in pages:
        records = records_of(page)
        if records:
            print(f"[{page.tier}] {page.name}  {page.path}")
            for n, text in records:
                print(f"   {locate(page, n)}: {shorten(text)}")
            count += len(records)
    if not count:
        print(f"결과 없음 — {empty}")
        return 1
    return 0


def shared_wiki_path(env: Mapping[str, str], home: Path, cwd: Path) -> Path:
    raw = env.get("CLAUDE_SHARED_WIKI", "")
    if not raw:
        return home / ".claude" / "wiki"
    path = Path(raw)
    # expanduser 는 주입한 home 이 아니라 프로세스의 HOME 을 읽는다.
    return home.joinpath(*path.parts[1:]) if path.parts[:1] == ("~",) else cwd / path


def not_wiki_reason(path: Path) -> str | None:
    """wiki 판정은 wiki_check.find_wiki 와 같다 — WIKI.md 또는 pages/."""
    if (path / "WIKI.md").is_file() or (path / "pages").is_dir():
        return None
    return "wiki 아님(WIKI.md·pages/ 없음)" if path.exists() else "경로 없음"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki_search.py", description="공용 wiki 와 현재 repo 의 wiki 에서 질의어로 페이지를 찾는다."
    )
    parser.add_argument("query", nargs="*", help="질의어(여러 단어 가능)")
    parser.add_argument("--limit", type=int, default=5, help="보일 결과 수(기본 5, 검색에만 쓴다)")
    parser.add_argument("--category", help="이 category 의 페이지만(frontmatter category, 없으면 pages 아래 첫 디렉터리)")
    parser.add_argument("--links-to", metavar="STEM", help="이 stem 을 가리키는 링크가 든 줄을 전부 낸다(index.md 제외)")
    parser.add_argument("--open", action="store_true", help="[!open]·[!conflict] callout 을 전부 낸다")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    home: Path | None = None,
) -> int:
    env = os.environ if env is None else env
    cwd = Path.cwd() if cwd is None else Path(cwd)
    parser = build_parser()
    args = parser.parse_intermixed_args(argv)
    if args.limit < 1:
        parser.error("--limit 은 1 이상이다")
    if args.links_to is not None and args.open:
        parser.error("--links-to 와 --open 은 함께 쓸 수 없다")
    query_mode = args.links_to is not None or args.open
    if query_mode and args.query:
        parser.error("--links-to·--open 은 질의어와 함께 쓸 수 없다")
    terms = list(dict.fromkeys(tokenize(" ".join(args.query))))
    if not query_mode and not terms:
        print("wiki_search: 질의에 찾을 단어가 없다 — 두 음절 이상의 한글이나 두 글자 이상의 영문·숫자를 넣는다", file=sys.stderr)
        return 2

    shared = shared_wiki_path(env, Path.home() if home is None else home, cwd)
    missing = not_wiki_reason(shared)
    if missing and env.get("CLAUDE_SHARED_WIKI"):
        print(f"wiki_search: CLAUDE_SHARED_WIKI 가 wiki 가 아니다 — {shared}: {missing}", file=sys.stderr)
        return 2
    targets = [] if missing else [("공용", shared.resolve())]
    repo_wiki = wiki_check.resolve_context(cwd, env=env).wiki_root
    same = repo_wiki is not None and not missing and repo_wiki.resolve() == targets[0][1]
    if repo_wiki is not None and not same:
        targets.append(("repo", repo_wiki.resolve()))
    if not targets:
        print(
            f"wiki_search: 찾을 wiki 가 없다 — 공용 {shared}: {missing} · repo: {cwd} 에서 repo 루트까지 wiki/ 없음",
            file=sys.stderr,
        )
        return 2
    try:
        pages = [page for tier, root in targets for page in load_pages(tier, root)]
    except OSError as e:
        print(f"wiki_search: 읽기 실패 — {e}", file=sys.stderr)
        return 2
    if missing:
        print(f"wiki_search: 공용 wiki 없음 — {shared}: {missing}. clone 방법은 ~/.claude README Install E", file=sys.stderr)
    counts = Counter(page.tier for page in pages)
    by_wiki = link_graph(pages)  # 거르기 전 전체로 만든다 — category 밖 페이지와의 간선도 남는다
    if args.links_to is not None and not any(args.links_to in names for names in by_wiki.values()):
        print(f"wiki_search: {args.links_to} 페이지가 없다 — 찾은 wiki 어디에도 그 stem 이 없다", file=sys.stderr)
        return 2
    if args.category:
        known = sorted({page.category for page in pages if page.category})
        pages = [page for page in pages if page.category == args.category]
        if not pages:
            print(f"wiki_search: category {args.category} 인 페이지가 없다 — 있는 category: {', '.join(known) or '없음'}", file=sys.stderr)
            return 2

    found = [f"{tier} {root} ({counts[tier]}쪽{', repo wiki 와 같다' if same else ''})" for tier, root in targets]
    if missing:
        found.insert(0, f"공용 없음({shared})")
    if repo_wiki is None:
        found.append("repo 없음")
    print("찾은 wiki: " + " · ".join(found))

    if args.links_to is not None:
        stem = args.links_to
        return print_records(pages, lambda page: link_records(page, stem, by_wiki), f"[[{stem}]] 을 가리키는 링크가 없다(index.md 제외)")
    if args.open:
        return print_records(pages, callout_records, "[!open]·[!conflict] 가 없다")

    ranked = rank(pages, terms)
    if not ranked:
        scope = f" · category {args.category} {len(pages)}쪽" if args.category else ""
        print(f"결과 없음 — 찾은 단어: {' '.join(terms)}{scope}")
        return 1
    for i, (score, page) in enumerate(ranked[: args.limit], 1):
        title = f" — {page.title}" if page.title and page.title != page.stem else ""
        print(f"{i}. [{page.tier}] {page.name}{title}  {score:.2f}")
        print(f"   {page.path}")
        if page.index_line:
            print(f"   index.md:{page.index_line}: {shorten(page.summary)}")
        for n, line in matched_lines(page, set(terms)):
            print(f"   {locate(page, n, with_range=True)}: {shorten(line)}")
        related = related_line(page)
        if related:
            print(f"   {related}")
    return 0


if __name__ == "__main__":
    # Windows 콘솔 기본 인코딩에서 한국어 출력이 죽지 않게 한다(wiki_check.py 와 같다).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
