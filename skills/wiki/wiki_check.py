#!/usr/bin/env python3
"""wiki 정합성 검사 — 페이지 frontmatter 형식(schema), covers 신선도(stale), 대표 질문(smoke).

schema 는 wiki 의 `WIKI.md` 형식 규약 중 frontmatter 불변식을 기계로 검사한다. 규칙은
`<wiki>/wiki-check.toml`(또는 --config)로 조정하고, 파일이 없으면 공용 WIKI.md 규약
(필수 키 5개, category 5종, created·updated 날짜)으로 돈다. 형식의 정본은 그 wiki 의
WIKI.md 이고 config 는 그것을 기계로 검사하는 설정이다 — 어긋나면 config 를 고친다.

stale 은 페이지 frontmatter `covers`(git 최상위 기준 fnmatch 패턴)에 걸린 파일이 바뀌었는데 페이지는
바뀌지 않은 것을 찾는다. --branch 는 merge-base(HEAD, base)..HEAD 의 commit 만 보고(CI·push 전),
--stop-hook 은 Claude Code Stop hook 어댑터로 작업 트리까지 본다. --report 는 이력을 보지 않고 페이지의
`verified_at`(페이지를 코드와 대조한 때의 covers 파일 내용 지문)을 지금 지문과 비교한다. 규약의 정본은
SKILL.md 신선도 절이다.

smoke 는 config `[smoke]` 의 대표 질문마다 답할 페이지가 있고 index.md 에 등재됐고 본문에 근거가 있는지,
`[smoke.forbid]` 의 금지 흔적(작업 브랜치 이름·plan 상태·사용자 패턴)이 pages 에 없는지 본다. `[smoke]` 가
없으면 검사 대상이 아니다.

stdlib 만 쓰고 이 파일 하나만 복사해도 돈다. config 를 읽을 때만 tomllib(Python 3.11+)이
필요하다 — 3.9·3.10 은 config 없는 검사만 된다.

exit: 0 통과, 1 위반, 2 사용·설정·환경 오류. --stop-hook 은 언제나 0 이다(판정은 stdout JSON).

Usage (repo 안 어디서든 — wiki 경로를 주지 않으면 repo 루트까지 올라가며 찾는다):
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" schema [wiki_root] [--config PATH]
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" stale --branch [wiki_root] [--base REF]
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" stale --report [wiki_root]
  uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" smoke [wiki_root] [--config PATH]
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fnmatch
import hashlib
import io
import json
import os
import queue
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath

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
# grep 이 문자 집합 안에서 읽는 `[:이름:]`·`[=x=]`·`[.x.]` — Python re 는 그 `[` 를 문자로 읽는다.
BRACKET_ELEMENT = re.compile(r"\[(?::[A-Za-z]+:|=[^\]]+=|\.[^\]]+\.)\]")


class ConfigError(Exception):
    """config 를 읽거나 검증하지 못했다 — exit 2."""


# ---------- frontmatter 파서 ----------


@dataclass
class Frontmatter:
    status: str  # "ok" | "missing"(첫 줄이 --- 아님) | "unclosed"(닫는 --- 없음)
    fields: dict[str, str | list[str]] = field(default_factory=dict)
    duplicates: list[str] = field(default_factory=list)
    # `[` 로 시작해 `]` 로 끝나지 않는 값의 키 → FLOW_CAUSES 의 원인
    unclosed_flow: dict[str, str] = field(default_factory=dict)


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


def _bracket_depth(raw: str) -> int:
    depth = 0
    for _, ch in _outside_quotes(raw):
        depth += (ch == "[") - (ch == "]")
    return depth


# 원인 → (schema 문구, stale 의 covers 읽기 실패 사유)
FLOW_CAUSES = {
    "comment": ("[ … ] 가 주석에 잘렸다 — 공백 뒤 # 부터는 주석이다. 설명이면 ] 뒤로 옮기고, 항목의 일부면 그 항목을 따옴표로 감싼다", "[ … ] 가 주석에 잘림"),
    "trailing": ("[ … ] 뒤에 글자가 있다 — 설명이면 공백 뒤 # 주석으로 옮기고, [ 로 시작하는 문자열이면 값 전체를 따옴표로 감싼다", "[ … ] 뒤에 글자가 있음"),
    "multiline": ("[ 가 그 줄에서 닫히지 않는다 — 여러 줄 흐름 목록은 읽지 못한다(블록 - 목록으로 쓴다)", "[ 가 그 줄에서 닫히지 않음"),
    # 블록 항목에서는 multiline 의 "블록 - 목록으로 쓴다" 를 따를 수 없다.
    "multiline_item": ("[ 로 시작한 항목이 그 줄에서 닫히지 않는다 — 여러 줄 목록이면 항목마다 - 로 나누고, 문자열이면 따옴표로 감싼다", "[ 로 시작한 항목이 그 줄에서 닫히지 않음"),
}


def _flow_cause(raw: str, line: str) -> str:
    """`[` 로 시작해 `]` 로 끝나지 않는 값의 원인. raw 는 주석을 뗀 값, line 은 raw 로 시작하는 주석까지 든 원문."""
    if _bracket_depth(raw) <= 0:
        return "trailing"
    # 주석을 넣어 괄호가 닫혀야(깊이 0 이하) 주석 탓이다 — `[a,  # 설명 [x]` 는 여러 줄 목록이다.
    if "]" in line[len(raw) :] and _bracket_depth(line) <= 0:
        return "comment"
    return "multiline"


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
    # `[]`·`[a, ]` — YAML 은 끝 쉼표를 받는다. 가운데 빈 항목은 남겨 schema 가 위반으로 본다.
    if not items[-1].strip():
        items.pop()
    return [unquote(item.strip()) for item in items]


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
            key, rest = m.group(1), m.group(2)
            raw = strip_comment(rest)
            if key in fm.fields:
                if key not in fm.duplicates:
                    fm.duplicates.append(key)
                list_key = None
            else:
                raw_list = raw.startswith("[") and raw.endswith("]")
                if raw.startswith("[") and not raw_list:
                    fm.unclosed_flow[key] = _flow_cause(raw, rest.lstrip())
                fm.fields[key] = _split_flow(raw[1:-1]) if raw_list else unquote(raw)
                list_key = key if raw == "" else None
            continue
        item = line.strip()
        if list_key and (item == "-" or item.startswith("- ")):
            value = fm.fields[list_key]
            if not isinstance(value, list):
                value = fm.fields[list_key] = []
            raw = strip_comment(item[1:])
            if raw.startswith("[") and not raw.endswith("]"):
                cause = _flow_cause(raw, item[1:].lstrip())
                fm.unclosed_flow[list_key] = "multiline_item" if cause == "multiline" else cause
            value.append(unquote(raw))
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
            # symlink 이면 대상 경로로 — 페이지 경로가 git 이 내는 경로와 같아야 한다(인자 경로와 같은 기준).
            return candidate.resolve()
        if (level / "WIKI.md").is_file():
            return level
    return None


def resolve_context(
    start, wiki_arg=None, config_arg=None, *, env=None, relative_to_repo=False
) -> Context:
    """상대 인자(wiki 경로·--config)는 시작점 기준이다. relative_to_repo 면 repo 루트 후보 기준이다
    — hook 의 시작점(입력 cwd)은 세션을 따라 움직여서, 등록 명령의 상대 경로를 repo 에 묶어야 한다."""
    env = os.environ if env is None else env
    start = Path(start).resolve()
    repo_root = find_repo_root(start, _ceilings(env))
    base = repo_root if relative_to_repo and repo_root is not None else start
    if wiki_arg is not None:
        wiki_root = (base / wiki_arg).resolve()
    else:
        wiki_root = find_wiki(start, repo_root)
    if config_arg is not None:
        config_path = (base / config_arg).resolve()
    elif wiki_root is not None and os.path.lexists(wiki_root / CONFIG_NAME):
        # 깨진 symlink·디렉터리도 config 자리다 — 없는 것으로 보면 기본 규칙으로 조용히 돈다.
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
class StaleConfig:
    stop_hook: bool = True
    base: str = ""  # "" — 기본 브랜치 후보에서 구한다


@dataclass(frozen=True)
class Question:
    q: str
    page: str  # pages 디렉터리 기준 경로
    expect: str  # 정규식 — 본문 줄마다 search


@dataclass
class ForbidConfig:
    branch_names: bool = False
    plan_status: bool = False
    patterns: list[str] = field(default_factory=list)


@dataclass
class SmokeConfig:
    questions: list[Question] = field(default_factory=list)
    forbid: ForbidConfig = field(default_factory=ForbidConfig)


@dataclass
class Config:
    version: int = SUPPORTED_VERSION
    schema: SchemaConfig = field(default_factory=SchemaConfig)
    stale: StaleConfig = field(default_factory=StaleConfig)
    smoke: SmokeConfig | None = None  # None — [smoke] 없음(검사 대상 아님)


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
    _reject_unknown(data, ("version", "schema", "stale", "smoke"), "")
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
    schema_cfg = SchemaConfig(**kwargs)
    # 기본값까지 본다 — date_keys 에 남은 키는 date_prefixed_keys 의 접두 허용을 fullmatch 로 막는다.
    both = sorted(set(schema_cfg.date_keys) & set(schema_cfg.date_prefixed_keys))
    if both:
        current = ", ".join(schema_cfg.date_keys) + ("" if "date_keys" in schema else " — 적지 않아 기본값")
        raise ConfigError(
            f"schema.date_keys 와 schema.date_prefixed_keys 에 같은 키 — {', '.join(both)}"
            f"(date_keys 에서 뺀다. 지금 date_keys: {current})"
        )
    stale = _stale_config(data.get("stale", {}))
    smoke = _smoke_config(data["smoke"]) if "smoke" in data else None
    return Config(version=version, schema=schema_cfg, stale=stale, smoke=smoke)


def _stale_config(value) -> StaleConfig:
    stale = _table(value, "stale")
    _reject_unknown(stale, ("stop_hook", "base"), "stale.")
    if "stop_hook" in stale and type(stale["stop_hook"]) is not bool:
        raise ConfigError("stale.stop_hook 는 true 또는 false 여야 한다")
    if "base" in stale and not isinstance(stale["base"], str):
        raise ConfigError("stale.base 는 문자열이어야 한다")
    return StaleConfig(**stale)


def _smoke_config(value) -> SmokeConfig:
    smoke = _table(value, "smoke")
    _reject_unknown(smoke, ("questions", "forbid"), "smoke.")
    raw = smoke.get("questions", [])
    if not isinstance(raw, list):
        raise ConfigError("smoke.questions 는 [[smoke.questions]] 테이블 배열이어야 한다")
    questions = [_question(item, f"smoke.questions[{i}]") for i, item in enumerate(raw, 1)]
    forbid = _table(smoke.get("forbid", {}), "smoke.forbid")
    _reject_unknown(forbid, ("branch_names", "plan_status", "patterns"), "smoke.forbid.")
    for key in ("branch_names", "plan_status"):
        if key in forbid and type(forbid[key]) is not bool:
            raise ConfigError(f"smoke.forbid.{key} 는 true 또는 false 여야 한다")
    for i, pattern in enumerate(_str_list(forbid.get("patterns", []), "smoke.forbid.patterns"), 1):
        _check_regex(pattern, f"smoke.forbid.patterns[{i}]")
    return SmokeConfig(questions, ForbidConfig(**forbid))


def _question(value, name: str) -> Question:
    item = _table(value, name)
    keys = ("q", "page", "expect")
    _reject_unknown(item, keys, f"{name}.")
    bad = [key for key in keys if not isinstance(item.get(key), str) or not item[key]]
    if bad:
        raise ConfigError(f"{name} 의 {', '.join(bad)} 는 비지 않은 문자열이어야 한다")
    page = PurePosixPath(item["page"])
    if page.suffix != ".md" or page.is_absolute() or ".." in page.parts:
        raise ConfigError(f'{name}.page 는 pages 아래 .md 의 상대 경로여야 한다(예 "decision/x.md") — {item["page"]!r}')
    _check_regex(item["expect"], f"{name}.expect")
    return Question(item["q"], page.as_posix(), item["expect"])


def _check_regex(pattern: str, name: str) -> None:
    # grep -E 에서 옮긴 식이 조용히 뜻을 바꾸지 않게 한다 — Python re 는 [[:space:]] 를 문자 집합
    # `[[:space:]` 와 `]` 로 읽는다.
    dialect = _grep_dialect(pattern)
    if dialect == ":":
        raise ConfigError(f"{name}: POSIX 문자 클래스는 Python re 에 없다(\\s·[0-9] 등으로 바꾼다) — {pattern!r}")
    if dialect:
        raise ConfigError(
            f"{name}: GNU grep 의 \\<·\\>·[=…=]·[.….] 는 Python re 에서 뜻이 다르다(단어 경계는 \\b 로 쓴다) — {pattern!r}"
        )
    try:
        re.compile(pattern)
    except re.error as e:
        raise ConfigError(f"{name}: 정규식 오류 — {e} — {pattern!r}") from None


def _grep_dialect(pattern: str) -> str | None:
    """grep -E 와 Python re 가 다르게 읽는 구문의 표지(`:`·`=`·`.`·`<`)를 낸다. 문자 집합의 경계는
    Python re 로 가른다. grep 은 집합 안의 `\\` 를 문자로 읽으므로 `[\\[:space:]]` 의 클래스도 본다."""
    in_set = False
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\":
            if pattern[i + 1 : i + 2] in ("<", ">"):
                return "<"
            if in_set and BRACKET_ELEMENT.match(pattern, i + 1):
                return pattern[i + 2]
            i += 2
            continue
        if ch == "[":
            m = BRACKET_ELEMENT.match(pattern, i)
            if m and (in_set or pattern[i + 1] == ":"):
                return pattern[i + 1]
            if not in_set:
                in_set = True
                i += 1
                if pattern[i : i + 1] == "^":
                    i += 1
                if pattern[i : i + 1] == "]":
                    i += 1
                continue
        elif ch == "]":
            in_set = False
        i += 1
    return None


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
    if "" in value:
        raise ConfigError(f"{name} 에 빈 문자열이 있다")
    duplicates = sorted({v for v in value if value.count(v) > 1})
    if duplicates:
        raise ConfigError(f"{name} 에 중복 — {', '.join(duplicates)}")
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
    for key, cause in fm.unclosed_flow.items():
        yield "값 형식", f"{key} 의 {FLOW_CAUSES[cause][0]}"
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
    if category is not None and cfg.categories:
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
    if "covers" in fm.fields:
        yield from _covers_problems(fm.fields["covers"])


def _date_problems(key: str, value: str, match, rule: str, want: str):
    m = match(value)
    if m is None:
        yield rule, f"{key}={value} — {want}"
        return
    try:
        date.fromisoformat(m.group(0))
    except ValueError:
        yield "날짜 실재 안 함", f"{key}={value}"


def _covers_problems(value):
    """covers 는 git 최상위 기준 상대 경로의 fnmatch 패턴이다(SKILL.md 신선도 절)."""
    if is_empty(value):
        yield "covers 빈 값", "경로 패턴이 하나도 없다 — 채우거나 키를 지운다"
        return
    for item in value if isinstance(value, list) else [value]:
        if not item:
            yield "covers 빈 값", "빈 항목이 있다"
        elif item.startswith(("/", "./", "../")):
            yield "covers 형식", f"{item} — git 최상위 기준 상대 경로로 적는다"
        elif item.endswith("/"):
            yield "covers 형식", f"{item} — 디렉터리 아래 전부는 {item}* 로 적는다"
        elif "\\" in item:
            yield "covers 형식", f"{item} — 경로 구분자는 / 다"


# ---------- git 어댑터 (stale 만 쓴다 — schema 는 git 없이 돈다) ----------

GIT_TIMEOUT = 60.0  # 초, 닫힌 모드의 호출마다. hook 은 전체 예산의 남은 시간을 쓴다.
BASE_CANDIDATES = (
    "refs/remotes/origin/HEAD",
    "refs/remotes/origin/main",
    "refs/remotes/origin/master",
    "refs/heads/main",
    "refs/heads/master",
)


class GitError(Exception):
    """git 을 실행하지 못했거나 git 이 실패했다 — 닫힌 모드는 exit 2, hook 은 systemMessage."""


class OutOfTime(GitError):
    """시간 제한 안에 끝나지 않았다."""


class Git:
    """모든 호출에 GIT_OPTIONAL_LOCKS=0 과 GIT_LITERAL_PATHSPECS=1 을 준다. status 가 index 를 다시 쓰며
    잠금을 잡으면 같은 때의 git add·commit 과 부딪치고, 페이지 경로의 `[`·`:` 가 pathspec 문법으로 읽히면
    다른 파일을 가리킨다. 상속한 GLOB·NOGLOB·ICASE pathspec 변수는 끈다 — literal 과 함께 켜지면 git 이 호출을
    거부한다. deadline(time.monotonic 기준)이 있으면 남은 시간이 호출의 timeout 이다. config 는 호출마다
    붙이는 `-c` 설정이다."""

    def __init__(
        self,
        cwd,
        env=None,
        *,
        deadline: float | None = None,
        timeout: float = GIT_TIMEOUT,
        config: tuple[str, ...] = (),
    ):
        self.cwd = Path(cwd)
        base_env = os.environ if env is None else env
        self.env = {
            **base_env,
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_GLOB_PATHSPECS": "0",
            "GIT_NOGLOB_PATHSPECS": "0",
            "GIT_ICASE_PATHSPECS": "0",
        }
        self.deadline = deadline
        self.timeout = timeout
        self.config = config

    def derive(self, *config: str, **env: str) -> Git:
        """같은 repo·시간 제한에 `-c` 설정과 환경 변수를 더한 Git."""
        return Git(
            self.cwd,
            {**self.env, **env},
            deadline=self.deadline,
            timeout=self.timeout,
            config=(*self.config, *config),
        )

    def run(self, *args: str, input: bytes | None = None) -> subprocess.CompletedProcess:
        """exit code 는 호출자가 가른다 — merge-base 의 1 은 '공통 조상 없음' 이다."""
        limit = self.timeout
        if self.deadline is not None:
            limit = min(limit, self.deadline - time.monotonic())
            if limit <= 0:
                raise OutOfTime(f"git {args[0]} 전에 시간을 다 썼다")
        options = [part for item in self.config for part in ("-c", item)]
        try:
            proc = subprocess.Popen(
                ["git", *options, *args],
                cwd=self.cwd,
                env=self.env,
                stdin=None if input is None else subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=os.name != "nt",
            )
        except OSError as e:
            raise GitError(f"git 을 실행하지 못했다 — {e}") from None
        try:
            out, err = proc.communicate(input, timeout=limit)
        except BaseException as e:
            # git 이 띄운 fsmonitor hook 등도 함께 끝낸다 — git 만 죽이면 손자가 고아로 남는다. 새 세션이라
            # Ctrl-C·그룹에 온 SIGTERM·SIGHUP 이 git 에 닿지 않는다 — KeyboardInterrupt 와 __main__ 이 신호를
            # 바꾼 SystemExit 도 여기서 정리한다.
            _kill_group(proc)
            if isinstance(e, subprocess.TimeoutExpired):
                raise OutOfTime(f"git {args[0]} 가 {limit:.1f}초 안에 끝나지 않았다") from None
            raise
        return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)

    def out(self, *args: str, input: bytes | None = None) -> bytes:
        r = self.run(*args, input=input)
        if r.returncode != 0:
            detail = r.stderr.decode("utf-8", "replace").strip()[:500]
            raise GitError(f"git {args[0]} 실패(exit {r.returncode}) — {detail}")
        return r.stdout


def _kill_group(proc: subprocess.Popen) -> None:
    """communicate 로 pipe 를 끝까지 읽지 않는다 — 그룹 밖으로 떨어져 나간 데몬이 pipe 를 쥐고 있으면 막힌다."""
    with contextlib.suppress(OSError):
        if os.name == "nt":
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        if stream is not None:
            with contextlib.suppress(OSError):
                stream.close()


def _path(raw: bytes) -> str:
    """git 이 낸 경로 바이트. UTF-8 이 아니어도 surrogateescape 로 되돌릴 수 있게 든다 — 페이지 경로와 같은
    표기이고, 지문과 update-index 입력은 원래 바이트여야 한다."""
    return raw.decode("utf-8", "surrogateescape")


def _nul_paths(out: bytes) -> list[str]:
    return [_path(p) for p in out.split(b"\0") if p]


# repo·index 를 고르는 변수(`git rev-parse --local-env-vars` 가운데 config·replace 를 뺀 것) — 판정할 repo 는
# `.git` 탐색이 정한다(hook 은 입력 cwd). 물려받은 GIT_DIR 이 다른 repo 를 가리키면 그 repo 를 조용히 판정한다.
REPO_ENV = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_PREFIX",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_SHALLOW_FILE",
        "GIT_GRAFT_FILE",
    }
)


def open_repo(ctx: Context, env=None, *, deadline: float | None = None) -> Git:
    """시작점에서 git 최상위를 확인하고 최상위에서 부르는 Git 을 돌려준다. ls-files·diff 는 호출
    디렉터리 기준으로 낼 수 있어(diff.relative) 최상위에서만 부른다. 최상위가 탐색한 repo 루트 후보와
    다르거나, wiki 가 그 밖이거나, git 이 wiki 를 다른 repo(중첩 repo)나 다른 경로(대소문자만 다른 인자)로
    보면 GitError — 다른 repo 의 wiki 를 판정하면 결과가 그 안에서는 일관돼 오류가 숨는다."""
    env = {k: v for k, v in (os.environ if env is None else env).items() if k not in REPO_ENV}
    probe = Git(ctx.start, env, deadline=deadline)
    top = Path(os.fsdecode(probe.out("rev-parse", "--show-toplevel").rstrip(b"\r\n"))).resolve()
    if top != ctx.repo_root:
        raise GitError(f"git 최상위 {top} 가 탐색한 repo 루트 {ctx.repo_root} 와 다르다")
    if not ctx.wiki_root.is_relative_to(top):
        raise GitError(f"wiki {ctx.wiki_root} 가 repo {top} 밖이다")
    seen = Git(ctx.wiki_root, env, deadline=deadline).out("rev-parse", "--show-toplevel", "--show-prefix")
    wiki_top, prefix = (os.fsdecode(line.rstrip(b"\r")) for line in seen.split(b"\n")[:2])
    want = ctx.wiki_root.relative_to(top).as_posix()
    if Path(wiki_top).resolve() != top or prefix.rstrip("/") != ("" if want == "." else want):
        raise GitError(
            f"git 은 wiki {ctx.wiki_root} 를 repo {wiki_top} 의 '{prefix}' 로 본다 — 중첩 repo 이거나, 경로의 대소문자나"
            " 유니코드 정규화(macOS NFD)가 git 과 다르다. 뒤의 둘이면 wiki 경로를 git 이 낸 표기로 인자에 준다"
        )
    return Git(top, env, deadline=deadline)


def worktree_status(git: Git, *paths: str) -> dict[str, str]:
    """index·작업 트리의 변경 경로 → porcelain XY. untracked 는 디렉터리를 접지 않고 파일마다, rename 은
    옛 경로와 새 경로를 따로 낸다. ignored 는 빼고, status.showUntrackedFiles 설정은 인자가 덮는다. 중첩 repo 의
    `?? dir/` 는 끝의 `/` 를 떼 gitlink 경로로 내고, 같은 경로가 `D ` 와 `??` 로 둘 다 나오면 뒤의 `??` 가 남는다.
    diff.ignoreSubmodules 는 `git add` 가 따르지 않아 끈다(submodule 별 ignore 설정은 status 를 따른다)."""
    out = git.derive("diff.ignoreSubmodules=none").out(
        "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--", *paths
    )
    return {_path(entry[3:]).rstrip("/"): entry[:2].decode("ascii", "replace") for entry in out.split(b"\0") if entry}


def changed_files(git: Git, *, worktree: bool, base: str | None, others: tuple[str, ...] = ()) -> set[str]:
    """git 최상위 기준 변경 경로. worktree — index·작업 트리(untracked 포함), base — base..HEAD 의 commit.
    others 는 criss-cross 의 나머지 merge-base 다 — 모든 merge-base 에서 달라진 파일(교집합)만 센다. 어느
    merge-base 가 먼저 나오는지는 commit 날짜가 정해서, 하나만 보면 판정이 날짜에 따라 뒤바뀐다."""
    changed = set(worktree_status(git)) if worktree else set()
    if base is not None:
        diff = ("diff", "--name-only", "-z", "--no-renames", "--ignore-submodules=none")
        diffs = [set(_nul_paths(git.out(*diff, rev, "HEAD", "--"))) for rev in (base, *others)]
        changed.update(set.intersection(*diffs))
    return changed


def _behind_symlink(root: Path, path: str) -> bool:
    """앞 성분이 symlink 인 경로(git 의 has_symlink_leading_path 기준). git 은 작업 트리에 없는 것으로 보는데
    update-index 는 이름을 거부한다."""
    parent = root
    for part in path.split("/")[:-1]:
        parent = parent / part
        if parent.is_symlink():
            return True
    return False


def _stdin_paths(paths: list[str]) -> bytes:
    return b"".join(path.encode("utf-8", "surrogateescape") + b"\0" for path in paths)


def add_view(git: Git, status: Mapping[str, str], wanted: Callable[[str], bool]) -> dict[str, tuple[str, str]]:
    """wanted 인 경로 → 지금 `git add -A` 를 하면 index 에 기록될 (mode, blob). status(worktree_status)의 경로를 진짜
    index 의 사본에 `update-index --info-only` 로 반영해 git 자신의 add 경로(줄 끝 변환·symlink·종류 변경·
    intent-to-add·충돌 해소·submodule·중첩 repo)를 쓴다. `D ` 로만 남은 경로는 작업 트리에 없거나 ignored 라 add 가
    넣지 않고 사본에도 없어 넘기지 않는다(update-index 는 ignore 규칙을 보지 않는다). 사본은 mtime 을 지켜 racy
    판정을 진짜 index 와 같게 하고, split index 를 풀어 써 $GIT_DIR 에 shared index 를 쓰지 않게 하고, core.hooksPath 의
    hook 을 부르지 않는다(core.fsmonitor 는 status 처럼 돈다). object 를 만들지 않고 진짜 index 와 그 잠금은 건드리지 않는다."""
    paths = sorted(path for path, xy in status.items() if xy != "D " and wanted(path))
    index = git.cwd / os.fsdecode(git.out("rev-parse", "--git-path", "index").rstrip(b"\r\n"))
    with tempfile.TemporaryDirectory() as tmp:
        copy, hooks = Path(tmp, "index"), Path(tmp, "hooks")
        hooks.mkdir()
        if index.is_file():
            shutil.copy2(index, copy)
        temp = git.derive("core.splitIndex=false", f"core.hooksPath={hooks}", GIT_INDEX_FILE=str(copy))
        behind = [path for path in paths if _behind_symlink(git.cwd, path)]
        if behind:
            temp.out("update-index", "--force-remove", "-z", "--stdin", input=_stdin_paths(behind))
        rest = sorted(set(paths) - set(behind))
        if rest:
            temp.out(
                "update-index", "--add", "--remove", "--replace", "--info-only", "-z", "--stdin", input=_stdin_paths(rest)
            )
        out = temp.out("ls-files", "-s", "-z")
    view, unmerged = {}, set()
    for record in out.split(b"\0"):
        if not record:
            continue
        meta, _, raw = record.partition(b"\t")
        mode, blob, stage = meta.decode("ascii").split()
        path = _path(raw)
        if not wanted(path):
            continue
        if stage == "0":
            view[path] = (mode, blob)
        else:
            unmerged.add(path)
    if unmerged:
        raise GitError(f"충돌이 풀리지 않은 covers 경로 — {', '.join(sorted(unmerged)[:5])}")
    return view


@dataclass(frozen=True)
class Base:
    sha: str | None
    quiet: bool = False  # 범위를 정할 수 없는 정상 상태(unborn HEAD, 후보가 현재 브랜치뿐)
    reason: str = ""  # sha 가 None 일 때 — 조용하지 않으면 고치는 방법까지 담는다
    others: tuple[str, ...] = ()  # criss-cross 의 나머지 merge-base


def _verify(git: Git, rev: str) -> str | None:
    r = git.run("rev-parse", "--verify", "--quiet", "--end-of-options", rev)
    if r.returncode == 0:
        return r.stdout.decode("ascii").strip()
    if r.returncode == 1:
        return None
    raise GitError(f"git rev-parse 실패(exit {r.returncode}) — {r.stderr.decode('utf-8', 'replace').strip()}")


# git 의 ref_rev_parse_rules 가운데 refs/ 아래 것(git-rev-parse 문서 "<refname>" 순서).
DWIM_RULES = ("refs/{}", "refs/tags/{}", "refs/heads/{}", "refs/remotes/{}", "refs/remotes/{}/HEAD")


def resolve_base(git: Git, configured: str) -> Base:
    """merge-base(HEAD, base). configured 가 비면 기본 브랜치 후보 ref 가운데 지금 체크아웃한 브랜치를 뺀
    것들을 한꺼번에 넘긴다 — 여러 ref 의 merge-base 는 그 ref 들을 합친 가상 commit 과의 merge-base 라서,
    로컬 main 이 origin/main 보다 뒤처져도 가장 가까운 분기점이 나온다. 현재 브랜치를 빼는 것은 기본
    브랜치에서 직접 실행할 때 push 전 commit 을 범위에 넣기 위해서다. criss-cross 로 merge-base 가 여럿이면
    나머지를 others 에 담는다."""
    if _verify(git, "HEAD") is None:
        return Base(None, True, "HEAD 에 commit 이 없다")
    set_base = f"--base 또는 <wiki>/{CONFIG_NAME} 의 [stale] base 로 준다"
    if configured:
        if not configured.startswith("refs/"):
            # git 은 짧은 이름을 아래 순서의 첫 ref 로 풀고 --quiet 가 모호 경고를 삼킨다 — HEAD 의 태그면 범위가 빈다.
            names = [rule.format(configured) for rule in DWIM_RULES]
            listed = git.out("for-each-ref", "--format=%(refname)", *names).decode("utf-8", "replace").split("\n")
            found = [name for name in names if name in listed]
            if len(found) > 1:
                return Base(None, False, f"base '{configured}' 가 여러 ref({', '.join(found)})에 있다 — 그 가운데 하나의 전체 이름으로 준다")
        sha = _verify(git, f"{configured}^{{commit}}")
        if sha is None:
            return Base(None, False, f"base '{configured}' 를 찾지 못했다 — {set_base}")
        refs = [sha]
    else:
        listed = git.out("for-each-ref", "--format=%(HEAD)%(refname)", *BASE_CANDIDATES)
        # 패턴은 `/` 경계까지 앞부분 일치라 refs/heads/main/x 도 맞는다 — 정확히 같은 것만 남긴다.
        found = [line for line in listed.decode("utf-8", "replace").split("\n") if line[1:] in BASE_CANDIDATES]
        refs = [line[1:] for line in found if line[0] != "*"]
        if not refs:
            if found:
                return Base(None, True, "기본 브랜치 후보가 현재 브랜치뿐이다")
            names = ", ".join(ref.split("/", 2)[2] for ref in BASE_CANDIDATES)
            return Base(None, False, f"기본 브랜치 후보 ref({names})가 없다 — {set_base}")
    r = git.run("merge-base", "--all", "HEAD", *refs)
    if r.returncode == 1:
        if git.out("rev-parse", "--is-shallow-repository").strip() == b"true":
            return Base(None, False, "얕은 clone 이라 merge-base 를 구하지 못했다 — 이력을 더 받는다(CI 는 fetch-depth: 0)")
        return Base(None, False, f"HEAD 와 base 의 공통 조상(merge-base)이 없다 — {set_base}")
    if r.returncode != 0:
        raise GitError(f"git merge-base 실패(exit {r.returncode}) — {r.stderr.decode('utf-8', 'replace').strip()}")
    first, *others = r.stdout.decode("ascii").split()
    return Base(first, others=tuple(others))


# ---------- covers 판정 ----------


def covers_match(pattern: str, path: str) -> bool:
    """covers 문법의 유일한 정의 — fnmatch 규칙이고 대소문자를 가린다. `*` 는 `/` 를 넘는다(기존
    covers 를 고치지 않고 읽기 위해서다 — gitignore 식 `**` 가 아니다). 패턴과 똑같은 경로도 맞는다. 패턴 전체를
    한 번은 `[…]` 를 문자 집합으로, 한 번은 모든 `[` 를 문자 그대로 읽어 맞춘다 — `app/[id]/*` 가 `app/[id]/page.tsx`
    에 걸린다. 한 패턴에 리터럴 `[` 와 문자 집합을 섞으려면 리터럴 쪽을 `[[]` 로 쓴다. 매칭은 늘기만 한다."""
    if path == pattern or fnmatch.fnmatchcase(path, pattern):
        return True
    return "[" in pattern and fnmatch.fnmatchcase(path, pattern.replace("[", "[[]"))


@dataclass(frozen=True)
class CoversPage:
    rel: str  # git 최상위 기준
    patterns: tuple[str, ...]


def split_covers(pages: list[Page]) -> tuple[list[CoversPage], list[Page]]:
    """(covers 가 있는 페이지, covers 를 알 수 없는 페이지 — UTF-8 아님·frontmatter 닫힘 없음·covers 값이나 항목이
    `[` 로 시작해 `]` 로 끝나지 않음)."""
    covers, unreadable = [], []
    for page in pages:
        if page.fm is None or page.fm.status == "unclosed" or "covers" in page.fm.unclosed_flow:
            unreadable.append(page)
            continue
        value = page.fm.fields.get("covers", [])
        patterns = tuple(p for p in (value if isinstance(value, list) else [value]) if p)
        if patterns:
            covers.append(CoversPage(page.rel, patterns))
    return covers, unreadable


def stale_pages(
    covers: list[CoversPage], changed: set[str], deadline: float | None = None
) -> list[tuple[str, list[str]]]:
    """covers 에 걸린 변경이 있는데 페이지 자신은 변경 집합에 없는 페이지와 걸린 파일. 순서는 보지 않는다
    — 페이지를 한 번 고쳤으면 같은 범위의 다른 변경은 알리지 않는다(SKILL.md 신선도 절의 한계). 페이지 수 ×
    변경 수만큼 맞춰 보므로 hook 은 deadline 을 넘긴다. 패턴이 많은 페이지 하나로도 예산을 넘어 경로마다 본다."""
    stale = []
    for page in covers:
        if page.rel in changed:
            continue
        hits = []
        for path in changed:
            if deadline is not None and time.monotonic() >= deadline:
                raise OutOfTime("covers 를 맞춰 보는 중")
            if any(covers_match(p, path) for p in page.patterns):
                hits.append(path)
        if hits:
            stale.append((page.rel, sorted(hits)))
    return stale


def _unreadable_detail(page: Page) -> str:
    if page.fm is None:
        return "UTF-8 아님"
    if page.fm.status == "unclosed":
        return "frontmatter 닫힘 없음"
    return f"covers 의 {FLOW_CAUSES[page.fm.unclosed_flow['covers']][1]}"


# ---------- Stop hook 어댑터 ----------

HOOK_BUDGET = 15.0  # 초, stdin·페이지 읽기 포함 — hook 기본 timeout(600초)에 맡기지 않는다
STDIN_WAIT = 1.0  # EOF 까지. hook 이 stdin 을 기다리며 세션을 세우지 않게
STDIN_MAX = 1 << 24  # 바이트. Stop 입력은 작은 JSON 이다 — 끝없는 입력을 메모리에 쌓지 않는다
# 결과를 들고 이 세션으로 돌아올 background 작업(선례 dlc-early-stop.js) — 지금 판정하면 이르다.
WAIT_TYPES = ("subagent", "workflow")
CONTEXT_LIMIT = 10_000  # Stop additionalContext 상한(hooks 문서)
FILES_PER_PAGE = 10
HOOK_HINT = (
    "stale --stop-hook 은 Claude Code Stop hook 입력(JSON)을 stdin 으로 받는다."
    " 손으로 확인하려면 stale --branch 를 쓴다."
)
CONTEXT_HEAD = (
    "wiki 신선도: 아래 페이지의 covers 에 걸린 파일이 이 브랜치·작업 트리에서 바뀌었는데 페이지는"
    " 바뀌지 않았다. 페이지의 주장을 코드와 대조해 고치고, 변경이 주장과 무관하면 covers 를 좁힌다."
)
CONTEXT_TAIL = f"이 repo 에서 이 알림을 끄려면 <wiki>/{CONFIG_NAME} 에 [stale] stop_hook = false 를 둔다."


def _utf16_len(text: str) -> int:
    """Claude Code(JavaScript)가 세는 문자열 길이. surrogateescape 로 든 경로의 짝 없는 surrogate 도 한 단위다."""
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def render_context(stale: list[tuple[str, list[str]]]) -> str:
    """페이지마다 파일은 FILES_PER_PAGE 개까지, 전체는 CONTEXT_LIMIT 안으로 줄인다. 첫 페이지는 파일 경로를
    빼서라도 이름을 싣는다 — 어느 페이지인지 없는 알림은 고칠 곳을 가리키지 못한다."""
    lines = [CONTEXT_HEAD]
    # 줄바꿈과 "… 외 N개 페이지" 줄 몫을 남긴다.
    room = CONTEXT_LIMIT - _utf16_len(CONTEXT_HEAD) - _utf16_len(CONTEXT_TAIL) - 64
    for i, (rel, files) in enumerate(stale):
        more = f" 외 {len(files) - FILES_PER_PAGE}개" if len(files) > FILES_PER_PAGE else ""
        line = f"- {rel}: {', '.join(files[:FILES_PER_PAGE])}{more}"
        if i == 0 and _utf16_len(line) + 1 > room:
            line = f"- {rel}: 걸린 파일 {len(files)}개(경로가 길어 생략)"
        room -= _utf16_len(line) + 1
        if room < 0:
            lines.append(f"… 외 {len(stale) - i}개 페이지")
            break
        lines.append(line)
    lines.append(CONTEXT_TAIL)
    return "\n".join(lines)


def _read_in_thread(fd: int, wait: float) -> tuple[str, bytes]:
    """read_stdin 의 Windows 판 — select 가 소켓만 받아 막히는 읽기를 daemon 스레드에 맡기고 기다림에만 시한을
    둔다. timeout 이면 스레드는 읽기에 막힌 채 남아 프로세스와 함께 끝난다(daemon 이 아니면 종료가 그 스레드를
    기다려 멈춘다). sys.stdin.buffer 를 읽으면 종료 때 그 lock 을 쥔 스레드가 남는다."""
    done: queue.Queue = queue.Queue()

    def pump() -> None:
        chunks = []
        size = 0
        try:
            while True:
                chunk = os.read(fd, 1 << 16)
                if not chunk:
                    done.put(("eof", b"".join(chunks)))
                    return
                size += len(chunk)
                if size > STDIN_MAX:
                    done.put(("toolarge", b""))
                    return
                chunks.append(chunk)
        except BaseException as e:
            done.put(e)

    threading.Thread(target=pump, name="wiki_check-stdin", daemon=True).start()
    try:
        outcome = done.get(timeout=wait)
    except queue.Empty:
        return "timeout", b""
    if isinstance(outcome, BaseException):
        raise outcome
    return outcome


def read_stdin(wait: float) -> tuple[str, bytes]:
    """("tty" | "eof" | "timeout" | "toolarge", 읽은 바이트 — 입력으로 쓰는 것은 eof 일 때뿐이다). EOF 가 wait 초
    안에 오지 않으면 timeout, STDIN_MAX 바이트를 넘으면 toolarge 다. Windows 의 timeout 뒤에는 읽기 스레드가 stdin 을
    쥐고 있어, 쓰는 쪽이 닫을 때까지 fd 0 을 닫거나 stdin 을 물려받는 자식(git)을 띄우면 시한 없이 막힌다(실측) —
    timeout 이면 곧바로 끝낸다."""
    if sys.stdin is None:
        return "eof", b""
    fd = sys.stdin.fileno()
    if os.isatty(fd):
        return "tty", b""
    if os.name == "nt":
        return _read_in_thread(fd, wait)
    chunks = []
    size = 0
    deadline = time.monotonic() + wait
    while True:
        left = deadline - time.monotonic()
        if left <= 0 or not select.select([fd], [], [], left)[0]:
            return "timeout", b"".join(chunks)
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            return "eof", b"".join(chunks)
        size += len(chunk)
        if size > STDIN_MAX:
            return "toolarge", b""
        chunks.append(chunk)


def _warn(message: str) -> dict:
    return {"systemMessage": f"wiki_check stale: {message}"}


def _parse_hook_args(argv: list[str]):
    """(args, 오류 문구). argparse 는 오류를 stderr 에 쓰고 exit 2 로 끝내는데, Stop hook 의 exit 2 는
    종료 차단이다 — SystemExit 를 잡아 문구로 바꾼다. --help 면 (None, None)이고 도움말은 stdout(JSON
    자리)이 아니라 stderr 로 보낸다."""
    captured = io.StringIO()
    try:
        with contextlib.redirect_stderr(captured), contextlib.redirect_stdout(captured):
            return build_parser().parse_args(argv), None
    except SystemExit as e:
        text = captured.getvalue()
        sys.stderr.write(text)
        if not e.code:
            return None, None
        lines = text.strip().splitlines()
        return None, lines[-1] if lines else "인자를 읽지 못했다"


def run_stop_hook(argv: list[str], deadline: float) -> dict | None:
    """hook 분류표(plan # Decisions)의 순서대로 본다. None 이면 아무것도 내지 않는다."""
    args, arg_error = _parse_hook_args(argv)
    if arg_error is not None:
        return _warn(f"인자 오류 — {arg_error}")
    if args is None:
        return None
    state, raw = read_stdin(STDIN_WAIT)
    if state == "timeout":
        return _warn(f"stdin 이 {STDIN_WAIT:g}초 안에 끝나지 않았다")
    if state == "toolarge":
        return _warn(f"stdin 이 {STDIN_MAX}바이트를 넘는다")
    if state == "tty" or not raw.strip():
        print(HOOK_HINT, file=sys.stderr)
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return _warn("stdin 이 UTF-8 이 아니다")
    except ValueError as e:
        return _warn(f"stdin JSON 오류 — {e}")
    if not isinstance(data, dict):
        return _warn("stdin JSON 이 객체가 아니다")
    if data.get("stop_hook_active") is True:
        return None
    tasks = data.get("background_tasks")
    if isinstance(tasks, list) and any(isinstance(t, dict) and t.get("type") in WAIT_TYPES for t in tasks):
        return None
    cwd = data.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return _warn("입력 JSON 에 cwd 문자열이 없다")
    if not Path(cwd).is_dir():
        return None  # worktree 를 지운 뒤의 종료
    ctx = resolve_context(cwd, args.wiki_root, args.config, relative_to_repo=True)
    if ctx.repo_root is None:
        return None
    problem = missing_wiki(ctx)
    if problem is not None:
        # 탐색으로 못 찾은 것은 wiki 없는 repo 라 조용하다. 등록 명령에 적은 경로가 없는 것은 오타다.
        return _warn(problem) if args.wiki_root is not None else None
    covers, unreadable = split_covers(load_pages(ctx))
    if not covers:
        return None
    if time.monotonic() >= deadline:
        raise OutOfTime("페이지를 읽는 중")
    try:
        config = load_config(ctx.config_path)
    except ConfigError as e:
        return _warn(f"config 오류 — {e}")
    if not config.stale.stop_hook:
        return None

    git = open_repo(ctx, deadline=deadline)
    base = resolve_base(git, args.base or config.stale.base)
    notes = []
    if base.sha is None and not base.quiet:
        notes.append(f"작업 트리만 봤다: {base.reason}")
    changed = changed_files(git, worktree=True, base=base.sha, others=base.others)
    stale = stale_pages(covers, changed, deadline)
    if unreadable:
        listed = ", ".join(f"{p.rel}({_unreadable_detail(p)})" for p in unreadable[:5])
        more = f" 외 {len(unreadable) - 5}개" if len(unreadable) > 5 else ""
        notes.append(f"covers 를 읽지 못한 페이지 {len(unreadable)}개 — {listed}{more}")
    out = {}
    if notes:
        out["systemMessage"] = "wiki_check stale: " + " / ".join(notes)
    if stale:
        out["hookSpecificOutput"] = {"hookEventName": "Stop", "additionalContext": render_context(stale)}
    return out or None


def hook_main(argv: list[str]) -> int:
    """무엇이 일어나도 exit 0 이고 판정은 stdout JSON 한 줄로만 전한다 — Stop hook 의 exit 2 는 종료
    차단이고, 도구 실패를 무출력으로 끝내면 게이트가 꺼져도 드러나지 않는다."""
    deadline = time.monotonic() + HOOK_BUDGET
    try:
        out = run_stop_hook(argv, deadline)
    except OutOfTime as e:
        out = _warn(f"전체 시간 예산 {HOOK_BUDGET:g}초를 넘었다 — {e}")
    except GitError as e:
        out = _warn(str(e))
    except BaseException as e:
        traceback.print_exc()
        out = _warn(f"예상 밖 오류 — {type(e).__name__}: {e}")
    if out is not None:
        try:
            print(json.dumps(out))
            sys.stdout.flush()
        except BaseException:
            _discard(sys.stdout)
    return 0


def _discard(stream) -> None:
    """읽는 쪽이 닫은 표준 스트림을 devnull 로 돌린다 — 그대로 두면 종료 때의 flush 가 다시 실패해 exit 120 이다."""
    with contextlib.suppress(BaseException):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stream.fileno())
        os.close(devnull)


class _QuietStderr(io.TextIOWrapper):
    """쓰기가 실패하면 fd 를 devnull 로 돌리고 계속하는 stderr — 안내·traceback 을 전하지 못한 것이 판정·exit
    code 를 바꾸지 않게 한다. 버퍼에 남은 것은 다음 flush 때 devnull 로 간다."""

    def write(self, text):
        try:
            return super().write(text)
        except OSError:
            _discard(self)
            return len(text)

    def flush(self):
        try:
            super().flush()
        except OSError:
            _discard(self)
            with contextlib.suppress(OSError):
                super().flush()


class _Stdout(io.TextIOWrapper):
    """읽는 쪽이 닫은 pipe 에 쓰면 Windows 는 대개 BrokenPipeError 가 아니라 EINVAL 을 낸다 — CRT 가 ERROR_NO_DATA 를
    errno 로 옮기지 못한다(CPython gh-79935, 경합에 따라 EPIPE 일 때도 있다. subprocess 의 _stdin_write 도 EINVAL 을
    같은 뜻으로 본다). POSIX 와 같은 BrokenPipeError 로 바꿔 main 의 처리 한 곳으로 보낸다."""

    def write(self, text):
        try:
            return super().write(text)
        except OSError as e:
            _raise_if_closed_pipe(e)
            raise

    def flush(self):
        try:
            super().flush()
        except OSError as e:
            _raise_if_closed_pipe(e)
            raise


def _raise_if_closed_pipe(e: OSError) -> None:
    # POSIX 의 쓰기 EINVAL 은 다른 뜻이고, 닫힌 pipe 는 이미 BrokenPipeError 다.
    if os.name == "nt" and e.errno == errno.EINVAL:
        raise BrokenPipeError(errno.EPIPE, os.strerror(errno.EPIPE)) from e


def _rewrap(stream, cls):
    """같은 버퍼링으로 UTF-8·backslashreplace 인 cls 로 다시 감싼다."""
    buffering = {"line_buffering": stream.line_buffering, "write_through": stream.write_through}
    return cls(stream.detach(), encoding="utf-8", errors="backslashreplace", **buffering)


def setup_streams() -> None:
    """CLI 의 표준 스트림을 맞춘다 — `__main__` 에서 한 번 부른다(wiki_search 도 쓴다). stdout 은 닫힌 pipe 를
    `BrokenPipeError` 로 알리고, stderr 는 쓰기 실패를 삼키므로 main 이 받는 `BrokenPipeError` 는 stdout 의 것이다."""
    if sys.stderr is None:
        # 닫힌 stderr 는 None 이다 — 그대로 두면 오류 문구·traceback 을 쓰다 죽고, print(file=None) 은 stdout 으로 간다.
        sys.stderr = open(os.devnull, "w")
    # UTF-8 아닌 경로는 surrogateescape 로 들고 다닌다 — strict 면 출력에서 죽는다.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = _rewrap(sys.stdout, _Stdout)
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = _rewrap(sys.stderr, _QuietStderr)


# ---------- verified_at 지문 (--report) ----------

FP_VERSION = 1
FP_VALUE = re.compile(rf"fp{FP_VERSION}-[0-9a-f]{{16}}")
FP_ANY = re.compile(r"fp([1-9][0-9]*)-")
OLD_VALUE = re.compile(r"[0-9a-fA-F]{7,64}")  # 옛 형식 — commit 값


def fingerprint(entries: dict[str, tuple[str, str]]) -> str:
    """verified_at 값. 경로(git 최상위 기준)마다 `<mode> <blob> <경로>\\n` 을 경로 바이트 순으로 이은 sha256 의
    앞 16자다. 값은 consumer 페이지에 저장되는 계약이라 정의를 바꾸면 FP_VERSION 을 올린다."""
    digest = hashlib.sha256()
    rows = sorted((path.encode("utf-8", "surrogateescape"), mode, blob) for path, (mode, blob) in entries.items())
    for path, mode, blob in rows:
        digest.update(f"{mode} {blob} ".encode("ascii") + path + b"\n")
    return f"fp{FP_VERSION}-{digest.hexdigest()[:16]}"


def value_kind(value: str | list[str]) -> str:
    """none(없음) · future(이 스크립트가 모르는 판) · fp · old(commit 값) · bad."""
    if isinstance(value, list):
        return "bad"
    if value == "":
        return "none"
    m = FP_ANY.match(value)
    # 자릿수가 많으면 int() 없이 더 새 판이다 — 3.11+ 의 int() 는 4300 자리를 넘으면 ValueError 다.
    if m and (len(m.group(1)) > len(str(FP_VERSION)) or int(m.group(1)) > FP_VERSION):
        return "future"
    if FP_VALUE.fullmatch(value):
        return "fp"
    if OLD_VALUE.fullmatch(value):
        return "old"
    return "bad"


def _shown(value: str | list[str]) -> str:
    text = value if isinstance(value, str) else f"[{', '.join(value)}]"
    return text if len(text) <= 40 else text[:40] + "…"


def _confirm(basis: str, current: str) -> str:
    return f"{basis} 파일을 페이지 주장과 대조한 뒤에만 이 값을 verified_at 에 적는다: {current}"


def judge(
    value: str | list[str], patterns: tuple[str, ...] | None, view: dict[str, tuple[str, str]]
) -> tuple[str, str] | None:
    """(판정, 페이지 경로 뒤 문구). 판정할 것이 없으면 None. view 는 wiki 페이지를 뺀 add_view 다. STALE 의
    문구는 현재 값뿐이다 — 참고 표시를 붙여 cmd_report 가 줄을 만든다."""
    kind = value_kind(value)
    if kind == "future":
        return "판 모름", f"verified_at 판 모름 — {_shown(value)} — 이 스크립트는 fp{FP_VERSION} 까지 안다. 스크립트 갱신 필요"
    if patterns is None:
        if kind == "none":
            return None
        return "위반", "verified_at 만 있음 — covers 가 없어 판정할 파일이 없다 — covers 를 지웠거나 빠뜨렸다"
    matched = {path: entry for path, entry in view.items() if any(covers_match(p, path) for p in patterns)}
    if not matched:
        return "위반", f"covers 매칭 0건 — {', '.join(patterns)} 에 걸린 파일이 없다(wiki 페이지는 세지 않는다)"
    current = fingerprint(matched)
    if kind == "fp":
        return ("OK", "OK") if value == current else ("STALE", current)
    if kind == "none":
        return "미확인", f"미확인 — verified_at 이 없다 — {_confirm('covers', current)}"
    if kind == "old":
        return "위반", (
            f"verified_at 옛 형식 — {value} 는 옛 형식(16진수 7~64자 — commit 값)이다. 값은 이제 covers 파일 지문이다"
            f" — {_confirm('covers', current)}"
        )
    return "위반", (
        f"verified_at 형식 — {_shown(value)} — fp{FP_VERSION}- 와 소문자 16진수 16자여야 한다"
        f" — {_confirm('covers', current)}"
    )


def references(
    git: Git, pages: list[CoversPage], status: list[str], page_rels: set[str]
) -> dict[str, tuple[str, bool]]:
    """STALE 페이지 → (참고 문구, 파일을 보였나). 지문에는 어느 파일이 바뀌었는지가 없어 이력에서 추정한다 —
    판정과 무관하고, 얕은 clone 이거나 git 이 실패하면 생략 사유를 보인다."""
    try:
        shallow = git.out("rev-parse", "--is-shallow-repository").strip() == b"true"
    except GitError as e:
        return {page.rel: (f"참고 생략({e})", False) for page in pages}
    if shallow:
        return {page.rel: ("참고 생략(얕은 clone)", False) for page in pages}
    return {page.rel: _reference(git, page, status, page_rels) for page in pages}


def _reference(git: Git, page: CoversPage, status: list[str], page_rels: set[str]) -> tuple[str, bool]:
    """페이지를 마지막으로 바꾼 commit P 뒤 바뀐 covers 파일 — 트리끼리 `diff P HEAD`(작업 트리와 비교하는 diff 는
    index 를 다시 쓴다)와 작업 트리 변경의 합. 확인 없이 페이지를 고친 뒤라면 그 전 변경이 빠진다."""
    try:
        last = git.out("rev-list", "-1", "HEAD", "--", page.rel).decode("ascii").strip()
        if not last:
            return "참고 생략(페이지를 commit 한 적이 없다)", False
        changed = _nul_paths(
            git.out("diff", "--name-only", "-z", "--no-renames", "--ignore-submodules=none", last, "HEAD", "--")
        )
    except GitError as e:
        return f"참고 생략({e})", False
    files = sorted(
        path
        for path in {*changed, *status}
        if path not in page_rels and any(covers_match(p, path) for p in page.patterns)
    )
    more = f" 외 {len(files) - FILES_PER_PAGE}개" if len(files) > FILES_PER_PAGE else ""
    listed = f"{', '.join(files[:FILES_PER_PAGE])}{more}" if files else "없음"
    return f"참고(페이지를 마지막으로 바꾼 commit {last[:12]} 뒤 바뀐 covers 파일): {listed}", bool(files)


# ---------- smoke: 대표 질문과 금지 흔적 ----------

# 하이픈이 든 소문자 이름만 작업 브랜치로 본다 — main·master·HEAD 같은 한 낱말 이름은 빠진다.
WORK_BRANCH = re.compile(r"[a-z0-9]+(-[a-z0-9]+)+")
PLAN_STATUS = re.compile(r"status:\s*in_progress")


def text_lines(text: str) -> list[str]:
    """grep 과 같은 줄 — `\\n` 으로만 가르고, 끝 줄바꿈 뒤는 줄이 아니다."""
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def body_lines(text: str) -> list[str] | None:
    """frontmatter 뒤의 줄(parse_frontmatter 와 같은 경계). frontmatter 가 없으면 모든 줄, 닫히지 않았으면 None."""
    lines = text_lines(text)
    if not lines or lines[0].strip() != "---":
        return lines
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[i + 1 :]
    return None


def smoke_questions(questions: list[Question], texts: dict[str, str], index: str | None) -> list[str]:
    """질문마다 실패 이유("" 이면 통과). texts — pages 기준 경로 → 페이지 전문, index — index.md 전문(없으면 None).
    근거는 grep 처럼 줄마다 찾는다 — 부정 문자 집합이나 \\s 가 줄을 넘어 맞지 않는다."""
    reasons = []
    for question in questions:
        text = texts.get(question.page)
        stem = PurePosixPath(question.page).stem
        body = None if text is None else body_lines(text)
        if text is None:
            reasons.append("파일 없음")
        elif index is None:
            reasons.append("index.md 없음")
        elif f"[[{stem}]]" not in index:
            reasons.append(f"index.md 에 [[{stem}]] 등재 없음")
        elif body is None:
            reasons.append("frontmatter 가 닫히지 않아 본문을 가를 수 없다")
        elif not any(re.search(question.expect, line) for line in body):
            reasons.append(f"본문에 근거 없음: {question.expect}")
        else:
            reasons.append("")
    return reasons


def smoke_forbid(
    forbid: ForbidConfig, texts: dict[str, str], branches: list[str]
) -> list[tuple[str, list[tuple[str, int, str]]]]:
    """켠 금지 검사마다 (이름, 걸린 (pages 기준 경로, 줄 번호, 걸린 것)). 페이지 전문을 frontmatter 까지 본다 —
    plan frontmatter 를 옮겨 온 흔적이 그 자리에 남는다."""

    def matcher(rx: re.Pattern) -> Callable[[str], str | None]:
        def find(line: str) -> str | None:
            m = rx.search(line)
            return None if m is None else m.group(0)

        return find

    def find_branches(line: str) -> str | None:
        return ", ".join(b for b in branches if b in line) or None

    checks = []
    if forbid.branch_names:
        checks.append((f"작업 브랜치 이름 {len(branches)}개", find_branches))
    if forbid.plan_status:
        checks.append(("status: in_progress", matcher(PLAN_STATUS)))
    checks += [(f"패턴 {pattern}", matcher(re.compile(pattern))) for pattern in forbid.patterns]
    results = []
    for name, find in checks:
        hits = []
        for rel, text in texts.items():
            for n, line in enumerate(text_lines(text), 1):
                found = find(line)
                if found is not None:
                    hits.append((rel, n, found))
        results.append((name, hits))
    return results


def read_texts(pages_dir: Path) -> dict[str, str]:
    """pages 기준 경로 → 전문. UTF-8 이 아닌 바이트는 바꿔 읽고 나머지 줄은 검사한다(grep 처럼) — 형식 위반은
    schema 가 잡는다."""
    return {
        path.relative_to(pages_dir).as_posix(): normalize(path.read_bytes().decode("utf-8", "replace"))
        for path in sorted(pages_dir.rglob("*.md"))
        if path.is_file()
    }


def work_branches(git: Git) -> list[str]:
    """로컬·원격 추적 브랜치 가운데 작업 브랜치 이름. 원격 브랜치는 원격 이름을 뗀다."""
    names = set()
    out = git.out("for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")
    # splitlines 는 ref 이름에 들 수 있는 U+0085·U+2028 에서도 가른다.
    for ref in out.decode("utf-8", "replace").split("\n"):
        if ref.startswith("refs/heads/"):
            name = ref[len("refs/heads/") :]
        else:
            name = ref[len("refs/remotes/") :].partition("/")[2]
        if WORK_BRANCH.fullmatch(name):
            names.add(name)
    return sorted(names)


# ---------- CLI ----------


class UsageError(Exception):
    """인자·환경으로는 검사할 수 없다 — main 이 문구를 stderr 에 적고 exit 2."""


def missing_wiki(ctx: Context) -> str | None:
    """wiki 나 pages 디렉터리가 없을 때의 오류 문구."""
    if ctx.wiki_root is None:
        return (
            f"wiki 를 찾지 못했다 — {ctx.start} 에서 repo 루트까지 wiki/ 가 없다."
            " wiki 경로를 인자로 넘긴다"
        )
    pages_dir = ctx.wiki_root / "pages"
    if not pages_dir.is_dir():
        return f"wiki pages 디렉터리 없음: {pages_dir}"
    return None


def open_wiki(args: argparse.Namespace) -> Context:
    ctx = resolve_context(Path.cwd(), args.wiki_root, args.config)
    problem = missing_wiki(ctx)
    if problem:
        raise UsageError(problem)
    return ctx


def cmd_schema(args: argparse.Namespace) -> int:
    ctx = open_wiki(args)
    config = load_config(ctx.config_path)
    pages = load_pages(ctx)
    findings = check_schema(pages, config.schema, ctx.display(ctx.wiki_root / "pages"))
    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} 위반", file=sys.stderr)
        return 1
    print(f"wiki schema check: clean ({len(pages)} pages)")
    return 0


def _note_pending(count: int, scope: str) -> None:
    """닫힌 모드는 작업 트리를 읽지만 판정의 기준은 CI(깨끗한 checkout)다 — 출력 머리와 stderr 에 알린다."""
    if count:
        note = f"작업 트리 기준 — {scope} 미커밋 변경 {count}개 (CI 는 commit 된 내용으로 판정한다)"
        print(note)
        print(note, file=sys.stderr)


def cmd_stale(args: argparse.Namespace) -> int:
    """--branch·--report. --stop-hook 은 main 이 argparse 전에 hook_main 으로 넘긴다."""
    if args.report and args.base is not None:
        raise UsageError("--base 는 --branch·--stop-hook 의 비교 기준이다 — --report 는 이력을 보지 않는다")
    ctx = open_wiki(args)
    config = load_config(ctx.config_path)
    pages = load_pages(ctx)
    if args.report:
        return cmd_report(ctx, pages)
    covers, unreadable = split_covers(pages)
    # covers 를 알 수 없는 페이지가 있으면 "covers 페이지 0개" 라고 말할 수 없다.
    findings = [Finding(p.rel, "covers 읽기 실패", _unreadable_detail(p)) for p in unreadable]
    if not covers and not findings:
        print("wiki stale check: 검사 대상 아님 — covers 가 있는 페이지가 없다")
        return 0
    base = None
    if covers:
        if ctx.repo_root is None:
            raise UsageError(f"git repo 밖이다 — {ctx.start} 에서 위로 .git 을 찾지 못했다")
        git = open_repo(ctx)
        base = resolve_base(git, args.base or config.stale.base)
        if base.sha is None:
            raise UsageError(f"base 를 정하지 못했다: {base.reason}")
        wiki_rel = ctx.wiki_root.relative_to(git.cwd).as_posix()
        _note_pending(len(worktree_status(git, *(() if wiki_rel == "." else (wiki_rel,)))), "wiki")
        stale = stale_pages(covers, changed_files(git, worktree=False, base=base.sha, others=base.others))
        findings += [Finding(rel, "covers 변경", ", ".join(files)) for rel, files in stale]
    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} 위반", file=sys.stderr)
        return 1
    print(f"wiki stale check: clean (covers 페이지 {len(covers)}개, base {base.sha[:12]})")
    return 0


def cmd_report(ctx: Context, pages: list[Page]) -> int:
    """규칙 D — 이력을 보지 않고 페이지의 verified_at(대조한 때의 covers 파일 지문)을 지금 지문과 비교한다. 판정할
    페이지마다 한 줄을 내고 마지막 줄은 집계다."""
    covers, unreadable = split_covers(pages)
    patterns = {page.rel: page.patterns for page in covers}
    broken = {page.rel: _unreadable_detail(page) for page in unreadable}
    values = {page.rel: page.fm.fields.get("verified_at", "") for page in pages if page.rel not in broken}
    if not covers and not broken and all(value == "" for value in values.values()):
        print("wiki stale report: 검사 대상 아님 — covers·verified_at 이 있는 페이지가 없다")
        return 0
    page_rels = {page.rel for page in pages}
    git, status, view = None, {}, {}
    if covers:
        if ctx.repo_root is None:
            raise UsageError(f"git repo 밖이다 — {ctx.start} 에서 위로 .git 을 찾지 못했다")
        git = open_repo(ctx)
        status = worktree_status(git)
        every = [p for page in covers for p in page.patterns]

        def covered(path: str) -> bool:
            return any(covers_match(p, path) for p in every)

        view = add_view(git, status, lambda path: path not in page_rels and covered(path))
        wiki_rel = ctx.wiki_root.relative_to(git.cwd).as_posix()
        inside = "" if wiki_rel == "." else f"{wiki_rel}/"
        _note_pending(sum(1 for p in status if f"{p}/".startswith(inside) or covered(p)), "wiki·covers 파일의")
    rows = []
    for page in pages:
        if page.rel in broken:
            rows.append((page.rel, "위반", f"covers 읽기 실패 — {broken[page.rel]}"))
            continue
        row = judge(values[page.rel], patterns.get(page.rel), view)
        if row is not None:
            rows.append((page.rel, *row))
    stale = {rel for rel, verdict, _ in rows if verdict == "STALE"}
    refs = references(git, [page for page in covers if page.rel in stale], list(status), page_rels) if stale else {}
    counts = dict.fromkeys(("OK", "STALE", "미확인", "위반", "판 모름"), 0)
    for rel, verdict, text in rows:
        counts[verdict] += 1
        if verdict == "STALE":
            ref, listed = refs[rel]
            text = f"STALE — {ref} — {_confirm('참고' if listed else 'covers', text)}"
        print(f"{rel}: {text}")
    summary = f"OK {counts['OK']} · STALE {counts['STALE']} · 미확인 {counts['미확인']} · 그 밖의 위반 {counts['위반']}"
    if counts["판 모름"]:
        summary += f" · 판 모름 {counts['판 모름']}"
    print(f"wiki stale report: covers 페이지 {len(covers)}개 — {summary}")
    if counts["판 모름"]:
        print(f"\nverified_at 판 모름 {counts['판 모름']}개 — 스크립트 갱신 필요", file=sys.stderr)
        return 2
    violations = counts["STALE"] + counts["위반"]
    if violations:
        print(f"\n{violations} 위반", file=sys.stderr)
        return 1
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    ctx = open_wiki(args)
    smoke = load_config(ctx.config_path).smoke
    if smoke is None:
        print(f"wiki smoke check: 검사 대상 아님 — [smoke] 가 없다 (config: {ctx.config_path or '없음'})")
        return 0
    forbid = smoke.forbid
    if not (smoke.questions or forbid.branch_names or forbid.plan_status or forbid.patterns):
        # 선언했는데 비었다 — 오타로 검사가 꺼진 것을 통과로 보고하지 않는다.
        raise UsageError("[smoke] 가 있는데 검사가 0개다 — [[smoke.questions]] 나 [smoke.forbid] 를 채운다")
    branches = []
    if forbid.branch_names:
        if ctx.repo_root is None:
            raise UsageError(f"git repo 밖이다 — branch_names 는 브랜치 목록이 필요하다({ctx.start} 에서 위로 .git 을 찾지 못했다)")
        branches = work_branches(open_repo(ctx))
    pages_dir = ctx.wiki_root / "pages"
    texts = read_texts(pages_dir)
    index_path = ctx.wiki_root / "index.md"
    index = normalize(index_path.read_bytes().decode("utf-8", "replace")) if index_path.is_file() else None
    rows = []
    for question, reason in zip(smoke.questions, smoke_questions(smoke.questions, texts, index)):
        where = f"{question.q} → {ctx.display(pages_dir / question.page)}"
        rows.append(("FAIL", f"{where} — {reason}") if reason else ("PASS", where))
    for name, hits in smoke_forbid(forbid, texts, branches):
        rows += [("FAIL", f"금지 — {name} → {ctx.display(pages_dir / rel)}:{n} ({found})") for rel, n, found in hits]
        if not hits:
            rows.append(("PASS", f"금지 — {name}"))
    for verdict, text in rows:
        print(f"{verdict} | {text}")
    failed = sum(verdict == "FAIL" for verdict, _ in rows)
    print(f"wiki smoke check: PASS {len(rows) - failed} · FAIL {failed}")
    if failed:
        print(f"\n{failed} 위반", file=sys.stderr)
        return 1
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
    stale = commands.add_parser(
        "stale",
        # 약어를 받으면 --stop 이 --stop-hook 으로 풀려 hook 어댑터 없이 --branch 판정을 낸다. 접두 등록은 main 이 hook_main 으로 보낸다.
        allow_abbrev=False,
        help="covers 에 걸린 파일이 바뀌었는데 페이지는 그대로인지 검사",
        description=(
            "페이지 frontmatter covers(git 최상위 기준 fnmatch 패턴)에 걸린 파일이 바뀌었는데 페이지는"
            " 바뀌지 않은 것을 찾는다(--branch·--stop-hook). --report 는 verified_at(대조한 때의 covers 파일"
            " 지문)을 지금 지문과 비교한다. 규약은 SKILL.md 신선도 절."
        ),
    )
    stale.add_argument(
        "wiki_root",
        nargs="?",
        help="wiki 디렉터리 (생략하면 repo 루트까지 올라가며 찾는다. --stop-hook 이면 repo 루트 기준)",
    )
    stale.add_argument("--config", help=f"config 파일 (생략하면 <wiki>/{CONFIG_NAME})")
    mode = stale.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--branch", action="store_true", help="merge-base(HEAD, base)..HEAD 의 commit 만 본다 (CI·push 전)"
    )
    mode.add_argument(
        "--stop-hook",
        action="store_true",
        help="Claude Code Stop hook 어댑터 — stdin 의 hook 입력을 읽고 작업 트리까지 본다. 언제나 exit 0",
    )
    mode.add_argument(
        "--report",
        action="store_true",
        help="verified_at 을 작업 트리의 covers 파일 지문과 비교한다 — 이력을 보지 않는다 (감사·CI)",
    )
    stale.add_argument(
        "--base",
        help=(
            f"--branch·--stop-hook 의 비교 기준 ref (생략하면 <wiki>/{CONFIG_NAME} 의 [stale] base,"
            " 그것도 없으면 기본 브랜치 후보)"
        ),
    )
    stale.set_defaults(run=cmd_stale)
    smoke = commands.add_parser(
        "smoke",
        help="대표 질문마다 답할 페이지·index 등재·본문 근거와 금지 흔적 검사",
        description=(
            f"<wiki>/{CONFIG_NAME} 의 [[smoke.questions]] 마다 page(pages 기준 경로)가 있고 index.md 에"
            " [[stem]] 으로 등재됐고 본문(frontmatter 제외)의 어느 줄이 expect 정규식에 맞는지 본다."
            " [smoke.forbid] 는 pages 전문에서 작업 브랜치 이름·status: in_progress·사용자 패턴을 찾는다."
            " [smoke] 가 없으면 검사 대상 아님(exit 0)."
        ),
    )
    smoke.add_argument(
        "wiki_root", nargs="?", help="wiki 디렉터리 (생략하면 repo 루트까지 올라가며 찾는다)"
    )
    smoke.add_argument("--config", help=f"config 파일 (생략하면 <wiki>/{CONFIG_NAME})")
    smoke.set_defaults(run=cmd_smoke)
    return parser


# --stop-hook 의 접두(--st 부터)와 `=값` 꼴. argparse 로 가면 exit 2(Stop 종료 차단)라 hook 경로에서
# systemMessage 로 알린다.
HOOK_FLAG_FORMS = frozenset("--stop-hook"[:n] for n in range(len("--st"), len("--stop-hook") + 1))


def _wants_hook(argv: list[str]) -> bool:
    """`--` 앞에 hook 플래그 꼴이 있고 첫 위치 인자가 다른 서브커맨드가 아니다. schema·smoke 에 붙은 것과 `--`
    뒤의 것은 닫힌 모드의 사용 오류(exit 2)로 둔다. stale 의 오타는 hook 등록의 오타일 수 있어 hook 으로 보낸다."""
    head = argv[: argv.index("--")] if "--" in argv else argv
    names = [arg for arg in head if not arg.startswith("-")]
    if names and names[0] in ("schema", "smoke"):
        return False
    return any(arg.split("=", 1)[0] in HOOK_FLAG_FORMS for arg in head)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if _wants_hook(argv):
        return hook_main(argv)
    args = build_parser().parse_args(argv)
    try:
        code = args.run(args)
        if sys.stdout is not None:
            sys.stdout.flush()
        return code
    except UsageError as e:
        print(e, file=sys.stderr)
        return 2
    except ConfigError as e:
        print(f"config 오류: {e}", file=sys.stderr)
        return 2
    except GitError as e:
        print(f"git 오류: {e}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        # 결과를 끝까지 내지 못했으니 판정(0·1)이 아니다. stderr 는 _QuietStderr 라 여기 오는 것은 stdout 이다.
        _discard(sys.stdout)
        return 2
    except Exception:
        # 파이썬 기본 exit 1 은 "위반" 과 겹친다.
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    setup_streams()
    if os.name != "nt":
        for sig in (signal.SIGTERM, signal.SIGHUP):
            if signal.getsignal(sig) == signal.SIG_DFL:
                # git 은 새 세션이라 이 그룹에 온 신호를 받지 않는다 — 예외로 바꿔 Git.run 이 git 의 그룹을 정리하게 한다.
                signal.signal(sig, lambda signum, frame: sys.exit(128 + signum))
    sys.exit(main())
