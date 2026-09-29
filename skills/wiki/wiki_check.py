#!/usr/bin/env python3
"""wiki 정합성 검사 — 페이지 frontmatter 형식(schema).

wiki 의 `WIKI.md` 형식 규약 중 frontmatter 불변식을 기계로 검사한다. 규칙은
`<wiki>/wiki-check.toml`(또는 --config)로 조정하고, 파일이 없으면 공용 WIKI.md 규약
(필수 키 5개, category 5종, created·updated 날짜)으로 돈다. 형식의 정본은 그 wiki 의
WIKI.md 이고 config 는 그것을 기계로 검사하는 설정이다 — 어긋나면 config 를 고친다.

stdlib 만 쓰고 이 파일 하나만 복사해도 돈다. config 를 읽을 때만 tomllib(Python 3.11+)이
필요하다 — 3.9·3.10 은 config 없는 검사만 된다.

exit: 0 통과, 1 위반, 2 사용·설정·환경 오류.

Usage (repo 안 어디서든 — wiki 경로를 주지 않으면 repo 루트까지 올라가며 찾는다):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" schema [wiki_root] [--config PATH]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

CONFIG_NAME = "wiki-check.toml"
SUPPORTED_VERSION = 1

# check_links.WIKILINK 가 링크로 읽는 이름과 같은 집합 — 링크할 수 없는 stem 을 잡는다.
STEM = re.compile(r"[a-z0-9-]+")
# `\d` 는 전각 등 유니코드 숫자에도 맞고, 3.11+ 의 date.fromisoformat 은 20260929·2026-W40-2
# 도 받는다. ASCII 형식을 먼저 보고 실재 여부만 fromisoformat 에 맡긴다.
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
DATE_PREFIX = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])")
# YAML 처럼 콜론 뒤가 공백·탭·줄 끝일 때만 키다 — `key:value` 는 값 하나짜리 스칼라다.
KEY_LINE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?=[ \t]|$)(.*)")


class ConfigError(Exception):
    """config 를 읽거나 검증하지 못했다 — exit 2."""


# ---------- frontmatter 파서 ----------


@dataclass
class Frontmatter:
    status: str  # "ok" | "missing"(첫 줄이 --- 아님) | "unclosed"(닫는 --- 없음)
    fields: dict[str, str | list[str]] = field(default_factory=dict)
    duplicates: list[str] = field(default_factory=list)


def normalize(text: str) -> str:
    return text.lstrip("\ufeff").replace("\r\n", "\n")


def _outside_quotes(raw: str):
    """따옴표 밖 문자의 (위치, 문자). 따옴표는 값 첫머리나 흐름 목록의 `[`·`,` 뒤에서만 연다
    — `it's` 같은 평문의 따옴표는 문자 그대로다."""
    quote = None
    opens = True
    i = 0
    while i < len(raw):
        ch = raw[i]
        if quote:
            if quote == '"' and ch == "\\":
                i += 2
                continue
            if ch == quote:
                if quote == "'" and raw[i + 1 : i + 2] == "'":
                    i += 2
                    continue
                quote = None
        elif ch in "'\"" and opens:
            quote = ch
        else:
            yield i, ch
        if not ch.isspace():
            opens = ch in "[,"
        i += 1


def strip_comment(raw: str) -> str:
    for i, ch in _outside_quotes(raw):
        if ch == "#" and (i == 0 or raw[i - 1] in " \t"):
            return raw[:i].strip()
    return raw.strip()


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _split_flow(inner: str) -> list[str]:
    items, start = [], 0
    for i, ch in _outside_quotes(inner):
        if ch == ",":
            items.append(inner[start:i])
            start = i + 1
    items.append(inner[start:])
    return [unquote(item.strip()) for item in items if item.strip()]


def parse_frontmatter(text: str) -> Frontmatter:
    """선두 `---` 블록의 최상위 키. 목록은 흐름 `[a, b]` 와 블록 `- a`(들여쓰기 무관)를 읽고,
    여러 줄 스칼라(`|`·`>`)는 표지 문자 그대로 둔다. 중복 키는 첫 값을 쓴다."""
    lines = normalize(text).split("\n")
    if lines[0].strip() != "---":
        return Frontmatter("missing")
    fm = Frontmatter("unclosed")
    list_key = None  # 값이 비어 있어 뒤따르는 `- item` 을 받는 키
    for line in lines[1:]:
        if line.strip() == "---":
            fm.status = "ok"
            break
        m = KEY_LINE.match(line)
        if m:
            key, raw = m.group(1), strip_comment(m.group(2))
            if key in fm.fields:
                if key not in fm.duplicates:
                    fm.duplicates.append(key)
                list_key = None
            else:
                raw_list = raw.startswith("[") and raw.endswith("]")
                fm.fields[key] = _split_flow(raw[1:-1]) if raw_list else unquote(raw)
                list_key = key if raw == "" else None
            continue
        item = line.strip()
        if list_key and (item == "-" or item.startswith("- ")):
            value = fm.fields[list_key]
            if not isinstance(value, list):
                value = fm.fields[list_key] = []
            value.append(unquote(strip_comment(item[1:])))
    return fm


# ---------- 문맥: wiki·repo 루트 후보·config 위치 (git 을 부르지 않는다) ----------


@dataclass(frozen=True)
class Context:
    start: Path
    wiki_root: Path | None
    repo_root: Path | None  # `.git` 이 있는 가장 가까운 상위 디렉터리
    config_path: Path | None  # None — config 없음(기본 규칙)

    def display(self, path: Path) -> str:
        """출력 경로: wiki 가 repo 루트 후보 안이면 그 기준, 아니면 wiki 루트의 부모 기준."""
        inside = self.repo_root is not None and self.wiki_root.is_relative_to(self.repo_root)
        base = self.repo_root if inside else self.wiki_root.parent
        return path.relative_to(base).as_posix()


def _ceilings(env) -> set[Path]:
    raw = env.get("GIT_CEILING_DIRECTORIES", "")
    return {Path(p).resolve() for p in raw.split(os.pathsep) if os.path.isabs(p)}


def find_repo_root(start: Path, ceilings: set[Path]) -> Path | None:
    """git 처럼 위로 올라가며 `.git`(파일 또는 디렉터리)을 찾는다. ceiling 안으로는 올라가지 않는다."""
    for level in (start, *start.parents):
        if level != start and level in ceilings:
            return None
        if (level / ".git").exists():
            return level
    return None


def find_wiki(start: Path, repo_root: Path | None) -> Path | None:
    """단계마다 `wiki/`(WIKI.md 또는 pages/)를 먼저, 그 단계 자신(WIKI.md 가 있을 때)을 다음에
    본다. repo 루트 후보까지 올라가고, repo 밖이면 시작점만 본다 — 웹 앱의 `src/pages` 나 홈의
    무관한 `wiki/` 를 잡지 않기 위해서다."""
    levels = [start]
    if repo_root is not None:
        levels += [p for p in start.parents if p.is_relative_to(repo_root)]
    for level in levels:
        candidate = level / "wiki"
        if (candidate / "WIKI.md").is_file() or (candidate / "pages").is_dir():
            return candidate
        if (level / "WIKI.md").is_file():
            return level
    return None


def resolve_context(start, wiki_arg=None, config_arg=None, *, env=None) -> Context:
    """상대 인자(wiki 경로·--config)는 시작점 기준이다."""
    env = os.environ if env is None else env
    start = Path(start).resolve()
    repo_root = find_repo_root(start, _ceilings(env))
    if wiki_arg is not None:
        wiki_root = (start / wiki_arg).resolve()
    else:
        wiki_root = find_wiki(start, repo_root)
    if config_arg is not None:
        config_path = (start / config_arg).resolve()
    elif wiki_root is not None and (wiki_root / CONFIG_NAME).is_file():
        config_path = wiki_root / CONFIG_NAME
    else:
        config_path = None
    return Context(start, wiki_root, repo_root, config_path)


@dataclass
class Page:
    path: Path
    rel: str
    fm: Frontmatter | None  # None — UTF-8 로 읽지 못했다

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def folder(self) -> str:
        return self.path.parent.name


def load_pages(ctx: Context) -> list[Page]:
    pages = []
    for path in sorted((ctx.wiki_root / "pages").rglob("*.md")):
        if not path.is_file():
            continue
        try:
            fm = parse_frontmatter(path.read_bytes().decode("utf-8"))
        except UnicodeDecodeError:
            fm = None
        pages.append(Page(path, ctx.display(path), fm))
    return pages


# ---------- config ----------


@dataclass
class SchemaConfig:
    required: list[str] = field(
        default_factory=lambda: ["title", "category", "created", "updated", "sources"]
    )
    categories: list[str] = field(
        default_factory=lambda: ["concept", "entity", "decision", "source", "query"]
    )
    date_keys: list[str] = field(default_factory=lambda: ["created", "updated"])
    date_prefixed_keys: list[str] = field(default_factory=list)
    page_count: list[int] = field(default_factory=list)  # [] — 끔, [최소, 최대]
    enums: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Config:
    version: int = SUPPORTED_VERSION
    schema: SchemaConfig = field(default_factory=SchemaConfig)


SCHEMA_LIST_KEYS = ("required", "categories", "date_keys", "date_prefixed_keys")


def import_tomllib():
    """config 를 읽을 때만 부른다 — config 없는 검사는 tomllib 없는 3.9·3.10 에서도 돈다."""
    try:
        import tomllib
    except ModuleNotFoundError:
        return None
    return tomllib


def load_config(path: Path | None) -> Config:
    if path is None:
        return Config()
    try:
        # tomllib 은 BOM 을 거부한다.
        text = path.read_bytes().decode("utf-8").lstrip("\ufeff")
    except OSError as e:
        raise ConfigError(f"{path}: 읽지 못했다 — {e.strerror or e}") from None
    except UnicodeDecodeError:
        raise ConfigError(f"{path}: UTF-8 이 아니다") from None
    toml = import_tomllib()
    if toml is None:
        version = f"{sys.version_info[0]}.{sys.version_info[1]}"
        raise ConfigError(
            f"{path}: config 를 읽으려면 Python 3.11+ 가 필요하다(지금 {version})."
            " config 가 없으면 기본 규칙으로 돈다"
        )
    try:
        data = toml.loads(text)
    except toml.TOMLDecodeError as e:
        raise ConfigError(f"{path}: TOML 문법 오류 — {e}") from None
    try:
        return build_config(data)
    except ConfigError as e:
        raise ConfigError(f"{path}: {e}") from None


def build_config(data: dict) -> Config:
    version = data.get("version", SUPPORTED_VERSION)
    if type(version) is not int or version < 1:
        raise ConfigError(f"version 은 1 이상의 정수여야 한다 — {version!r}")
    # 모르는 키 검사보다 먼저 — 옛 스크립트가 새 형식의 키를 "모르는 키" 로 보고하면
    # 사용자가 키를 지우게 된다.
    if version > SUPPORTED_VERSION:
        raise ConfigError(
            f"version {version} 은 이 스크립트가 아는 {SUPPORTED_VERSION} 보다 새 형식이다"
            " — 스크립트 갱신 필요"
        )
    _reject_unknown(data, ("version", "schema"), "")
    schema = _table(data.get("schema", {}), "schema")
    _reject_unknown(schema, (*SCHEMA_LIST_KEYS, "page_count", "enums"), "schema.")
    kwargs = {k: _str_list(schema[k], f"schema.{k}") for k in SCHEMA_LIST_KEYS if k in schema}
    if "page_count" in schema:
        kwargs["page_count"] = _page_count(schema["page_count"])
    if "enums" in schema:
        kwargs["enums"] = {
            key: _str_list(allowed, f"schema.enums.{key}", nonempty=True)
            for key, allowed in _table(schema["enums"], "schema.enums").items()
        }
    return Config(version=version, schema=SchemaConfig(**kwargs))


def _reject_unknown(table: dict, known: tuple, prefix: str) -> None:
    unknown = sorted(set(table) - set(known))
    if unknown:
        names = ", ".join(prefix + key for key in unknown)
        raise ConfigError(f"모르는 키 — {names} (아는 키: {', '.join(known)})")


def _table(value, name: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} 는 테이블이어야 한다")
    return value


def _str_list(value, name: str, *, nonempty: bool = False) -> list:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"{name} 는 문자열 목록이어야 한다")
    if nonempty and not value:
        raise ConfigError(f"{name} 가 비었다")
    return value


def _page_count(value) -> list:
    valid = (
        isinstance(value, list)
        and len(value) in (0, 2)
        and all(type(v) is int and v >= 0 for v in value)
        and (not value or value[0] <= value[1])
    )
    if not valid:
        raise ConfigError("schema.page_count 는 [] 또는 [최소, 최대] 정수 쌍이어야 한다")
    return value


# ---------- schema 검사 ----------


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.rule} — {self.detail}"


def is_empty(value) -> bool:
    return not any(value) if isinstance(value, list) else value == ""


def check_schema(pages: list[Page], cfg: SchemaConfig, pages_label: str) -> list[Finding]:
    """위반 목록(빈 목록 = 통과). 페이지 0개도 위반이다 — 검사가 통째로 건너뛰어진 것을
    통과로 보고하지 않는다."""
    if not pages:
        return [Finding(pages_label, "페이지 없음", "pages 아래 .md 가 0개다")]
    findings = []
    if cfg.page_count:
        low, high = cfg.page_count
        if not low <= len(pages) <= high:
            detail = f"{len(pages)}개 — 기대 범위 {low}~{high}"
            findings.append(Finding(pages_label, "페이지 수", detail))
    same_stem: dict[str, list[str]] = {}
    for page in pages:
        same_stem.setdefault(page.stem, []).append(page.rel)
    for page in pages:
        others = [rel for rel in same_stem[page.stem] if rel != page.rel]
        findings.extend(
            Finding(page.rel, rule, detail) for rule, detail in _page_problems(page, cfg, others)
        )
    return findings


def _page_problems(page: Page, cfg: SchemaConfig, same_stem: list[str]):
    if not STEM.fullmatch(page.stem):
        yield "stem 형식", f"{page.stem} — [a-z0-9-]+ 가 아니다"
    if same_stem:
        yield "stem 중복", f"같은 stem: {', '.join(same_stem)}"
    fm = page.fm
    if fm is None:
        yield "UTF-8 아님", "UTF-8 로 읽지 못했다"
        return
    # 경계를 모르는 채 본문을 키로 읽지 않도록 키 규칙을 건너뛴다.
    if fm.status == "missing":
        yield "frontmatter 없음", "첫 줄이 --- 가 아니다"
        return
    if fm.status == "unclosed":
        yield "frontmatter 닫힘 없음", "닫는 --- 가 없다"
        return
    for key in fm.duplicates:
        yield "중복 키", key
    for key in cfg.required:
        if key not in fm.fields:
            yield "필수 키 누락", key
        elif is_empty(fm.fields[key]):
            yield "필수 키 빈 값", key

    # 형식 규칙은 비지 않은 값 하나에만 건다 — 없음·빈 값은 required 가 맡는다.
    rule_keys = (["category"] if cfg.categories else []) + cfg.date_keys
    rule_keys += cfg.date_prefixed_keys + list(cfg.enums)
    values = {}
    for key in dict.fromkeys(rule_keys):
        value = fm.fields.get(key, "")
        if is_empty(value):
            continue
        if isinstance(value, list):
            yield "값 형식", f"{key} 가 목록이다 — 값 하나여야 한다"
        else:
            values[key] = value

    category = values.get("category")
    if category is not None:
        if category not in cfg.categories:
            yield "category 허용 밖", f"{category} (허용: {', '.join(cfg.categories)})"
        if category != page.folder:
            yield "category 불일치", f"frontmatter={category}, 디렉터리={page.folder}"
    for key in cfg.date_keys:
        if key in values:
            yield from _date_problems(
                key, values[key], DATE.fullmatch, "날짜 형식", "YYYY-MM-DD 가 아니다"
            )
    for key in cfg.date_prefixed_keys:
        if key in values:
            yield from _date_problems(
                key, values[key], DATE_PREFIX.match, "날짜 접두 형식", "YYYY-MM-DD 로 시작하지 않는다"
            )
    for key, allowed in cfg.enums.items():
        if key in values and values[key] not in allowed:
            yield "enum 허용 밖", f"{key}={values[key]} (허용: {', '.join(allowed)})"


def _date_problems(key: str, value: str, match, rule: str, want: str):
    m = match(value)
    if m is None:
        yield rule, f"{key}={value} — {want}"
        return
    try:
        date.fromisoformat(m.group(0))
    except ValueError:
        yield "날짜 실재 안 함", f"{key}={value}"


# ---------- CLI ----------


def cmd_schema(args: argparse.Namespace) -> int:
    ctx = resolve_context(Path.cwd(), args.wiki_root, args.config)
    if ctx.wiki_root is None:
        print(
            f"wiki 를 찾지 못했다 — {ctx.start} 에서 repo 루트까지 wiki/ 가 없다."
            " wiki 경로를 인자로 넘긴다",
            file=sys.stderr,
        )
        return 2
    pages_dir = ctx.wiki_root / "pages"
    if not pages_dir.is_dir():
        print(f"wiki pages 디렉터리 없음: {pages_dir}", file=sys.stderr)
        return 2
    config = load_config(ctx.config_path)
    pages = load_pages(ctx)
    findings = check_schema(pages, config.schema, ctx.display(pages_dir))
    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} 위반", file=sys.stderr)
        return 1
    print(f"wiki schema check: clean ({len(pages)} pages)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki_check.py",
        description="wiki 정합성 검사. exit 0 통과, 1 위반, 2 사용·설정·환경 오류.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    schema = commands.add_parser(
        "schema",
        help="페이지 frontmatter 형식 검사",
        description=(
            f"pages 아래 *.md 의 frontmatter 를 <wiki>/{CONFIG_NAME} 규칙으로 검사한다."
            " config 가 없으면 공용 WIKI.md 규약(필수 키 5개, category 5종, created·updated"
            " 날짜)으로 돈다."
        ),
    )
    schema.add_argument(
        "wiki_root", nargs="?", help="wiki 디렉터리 (생략하면 repo 루트까지 올라가며 찾는다)"
    )
    schema.add_argument(
        "--config", help=f"config 파일 (생략하면 <wiki>/{CONFIG_NAME}, 없으면 기본 규칙)"
    )
    schema.set_defaults(run=cmd_schema)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except ConfigError as e:
        print(f"config 오류: {e}", file=sys.stderr)
        return 2
    except Exception:
        # 파이썬 기본 exit 1 은 "위반" 과 겹친다.
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
