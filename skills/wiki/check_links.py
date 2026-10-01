#!/usr/bin/env python3
"""wiki/ 구조 점검 — /wiki lint·ingest 의 구조 점검 자동화 부분.

`wiki/WIKI.md` 규약 중 기계적으로 검증 가능한 불변식만 점검한다(모순·stale 같은
의미 점검은 LLM 담당):
- frontmatter 필수키(title/category/created/updated/sources)
- 나가는(outbound) 링크 ≥2
- dead link 없음(모든 `[[name]]`·별칭 `[[name|표시]]` 의 name 이 pages/ 에 실재)
- orphan 없음(index.md 제외, 다른 페이지로부터 inbound ≥1)
- index.md ↔ pages/ 동기화(누락·잉여 — 등재는 별칭 없는 `[[name]]` 만 인정)

위반을 한 줄씩 출력하고 위반 시 exit 1(clean 0). UTF-8 이 아닌 페이지·index 는 깨진 바이트를 바꿔 읽고
판정을 이어 가며 `UTF-8 아님` 위반을 더한다. pages 디렉터리가 없거나 페이지·index·하위 디렉터리를 읽지
못하면(권한 등) 위반 목록 없이 2 — 일부만 읽은 판정은 판정이 아니다.
git 없이 파일만 읽으므로 stdlib 외 의존성이 없다.

Usage (wiki/ 또는 repo 루트에서):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/check_links.py" [wiki_root]
"""

from __future__ import annotations

import errno
import io
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

# Windows 콘솔 기본 인코딩에서 한글 출력 시 UnicodeEncodeError 방지. UTF-8 아닌 파일 이름(surrogateescape)도
# 출력에서 죽지 않게 backslashreplace.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# 코드블록·인라인 코드 안의 [[ ]] 도 링크로 센다 — pages 본문은 위키링크를
# 코드 예시로 쓰지 않는 규약이라 단순 스캔으로 충분(걸리면 lint 가 사람에게 보고).
# 별칭 [[name|표시]] 는 name 으로 센다. 별칭에 [ 를 받지 않아야 닫히지 않은 별칭이
# 뒤의 링크를 삼키지 않는다. wiki_search.LINK 와 같은 규칙이지만, 이 파일만 복사해도
# 돌도록 import 하지 않고 따로 적는다.
WIKILINK = re.compile(r"\[\[([a-z0-9-]+)(?:\|[^\[\]\n]*)?\]\]")
PLAIN_WIKILINK = re.compile(r"\[\[([a-z0-9-]+)\]\]")
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


def _raise(error: OSError) -> None:
    raise error


# Python 3.13 까지의 Path.is_file()·is_dir() 이 False 로 보던 오류(없음·깨진·도는 symlink) — pathlib 의 목록과 같다.
_IGNORED_ERRNOS = {errno.ENOENT, errno.ENOTDIR, errno.EBADF, errno.ELOOP}
_IGNORED_WINERRORS = {21, 123, 1921}


def _stat_is(path: Path, test) -> bool:
    """`test(st_mode)`. 위 오류면 False 이고 권한 같은 그 밖의 OSError 는 올린다 — 3.14 의 is_file()·is_dir() 은 모든
    OSError 를 False 로 삼켜, 읽지 못한 페이지가 조용히 빠진 판정이 된다."""
    try:
        mode = path.stat().st_mode
    except OSError as e:
        if e.errno in _IGNORED_ERRNOS or getattr(e, "winerror", None) in _IGNORED_WINERRORS:
            return False
        raise
    return test(mode)


def read_text(path: Path) -> tuple[str, bool]:
    """(본문, UTF-8 이었나). UTF-8 이 아니면 깨진 바이트를 바꿔 읽는다 — 링크 문법은 ASCII 라 판정이 같다.
    줄바꿈은 텍스트 모드처럼 `\\n` 으로 맞춘다(별칭 안의 `\\r` 도 줄바꿈이라 링크가 아니다)."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        if e.filename is None:
            e.filename = str(path)  # read() 단계의 실패(EIO 등)는 경로를 싣지 않는다
        raise
    try:
        text, utf8 = raw.decode("utf-8"), True
    except UnicodeDecodeError:
        text, utf8 = raw.decode("utf-8", "replace"), False
    return text.replace("\r\n", "\n").replace("\r", "\n"), utf8


def check_wiki(wiki_root: Path) -> list[str]:
    """위반 메시지 목록(빈 목록 = clean). 읽지 못하면 OSError."""
    pages_dir = wiki_root / "pages"
    # rglob 은 읽지 못한 하위 디렉터리를 조용히 건너뛴다 — 먼저 걸어 드러낸다.
    for _ in os.walk(pages_dir, onerror=_raise):
        pass
    pages: dict[str, tuple[set[str], set[str]]] = {}
    not_utf8: set[str] = set()
    for md in sorted(pages_dir.rglob("*.md")):
        # 일반 파일만 페이지다(디렉터리·FIFO·장치·깨진·도는 symlink 는 건너뛴다 — wiki_check 와 같다).
        if not _stat_is(md, stat.S_ISREG):
            continue
        text, utf8 = read_text(md)
        if not utf8:
            not_utf8.add(md.stem)
        pages[md.stem] = (extract_links(text), extract_fm_keys(text))

    index_path = wiki_root / "index.md"
    index_text, index_utf8 = read_text(index_path) if _stat_is(index_path, stat.S_ISREG) else ("", True)
    # 등재는 별칭 없는 [[stem]] 으로만 인정한다 — smoke 의 등재 검사와 같은 기준이고, wiki_search 는
    # 별칭 등재 줄에서 index 요약을 읽지 않는다. dead link 판정은 별칭도 본다.
    index_entries = set(PLAIN_WIKILINK.findall(index_text))
    index_links = extract_links(index_text)

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
        if name in not_utf8:
            violations.append(f"UTF-8 아님: {name} (깨진 바이트를 바꿔 읽고 판정했다)")
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

    if not index_utf8:
        violations.append("UTF-8 아님: index.md (깨진 바이트를 바꿔 읽고 판정했다)")
    page_names = set(pages)
    for n in sorted(page_names - index_entries):
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
    try:
        if not _stat_is(wiki_root / "pages", stat.S_ISDIR):
            print(f"wiki pages 디렉터리 없음: {wiki_root}", file=sys.stderr)
            return 2
        violations = check_wiki(wiki_root)
    except OSError as e:
        # 일부만 읽은 판정은 판정이 아니다 — 위반(1)이 아니라 점검 불가(2).
        detail = f"{e.filename}: {e.strerror}" if e.filename and e.strerror else e
        print(f"check_links: 읽기 실패 — {detail}", file=sys.stderr)
        return 2
    for v in violations:
        print(v)
    if violations:
        print(f"\n{len(violations)} 위반", file=sys.stderr)
        return 1
    print("wiki link check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
