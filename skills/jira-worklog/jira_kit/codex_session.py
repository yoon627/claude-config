"""Codex CLI 세션 로그 기반 시간 파서 (stdlib only).

Codex 는 세션을 ``~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`` 에 저장하고, 보관하면
``~/.codex/archived_sessions/rollout-*.jsonl`` (flat)로 옮긴다 — 둘 다 탐색해야 누락이 없다.
Claude 와 달리 cwd 별 폴더가 아니라 날짜 폴더에 여러 worktree 세션이 섞여 있어, 각 파일 첫 줄
``session_meta.payload.cwd`` 로 귀속을 정한다. **어느 worktree 인지 가리는 일은 여기서 하지
않는다** — 스캔은 (파일, cwd) 만 내놓고 분류는 호출자의 ``WorktreeIndex`` 가 맡는다. 필터를
여기 두면 Claude 경로(최장 prefix)와 규칙이 갈려, worktree **하위** 디렉토리에서 시작한
세션이 어느 버킷에도 못 가고 사라진다(실측 26건).

시간: timestamp 가 있는 모든 ``response_item`` 을 AI 작업 흐름(assistant)으로 쓰고, **진짜
사용자 입력은 ``event_msg``(``type=user_message``)로만 판별한다**(user). Codex 는
``<environment_context>``·``# AGENTS.md``·``[system instructions]`` 등 시스템 컨텍스트를
``response_item`` role=user 로 주입하므로 role/텍스트로는 진짜 입력을 가릴 수 없다.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, tzinfo
from pathlib import Path

from ._sessionio import iter_jsonl_timestamped, mtime

_Event = tuple[datetime, str]


def _sessions_roots(home: Path | None) -> list[Path]:
    """진행 중(sessions)과 보관됨(archived_sessions) 세션 루트 둘 다.

    보관된 대화의 rollout 은 ``archived_sessions`` 로 이동하므로, 여기를 빼면 보관 후 실행 시
    그 세션의 시간·토큰이 조용히 누락된다.
    """
    base = home or Path.home()
    return [base / ".codex" / "sessions", base / ".codex" / "archived_sessions"]


def _session_cwd(path: Path) -> str | None:
    """rollout 파일 **첫 줄**(session_meta)에서 cwd 만 읽는다(전체 read 회피)."""
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
    except OSError:
        return None
    try:
        obj = json.loads(first)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or obj.get("type") != "session_meta":
        return None
    payload = obj.get("payload")
    cwd = payload.get("cwd") if isinstance(payload, dict) else None
    return cwd if isinstance(cwd, str) else None


def find_codex_sessions(home: Path | None = None) -> list[tuple[Path, str]]:
    """cwd 를 읽어낸 rollout 전부를 ``(파일, cwd)`` 로 낸다 — worktree 당 한 번이 아니라 총 1회.

    진행 중·보관된 세션 루트를 모두 탐색한다(``**`` 가 archived 의 flat 구조도 매칭).
    cwd 를 못 읽은 파일(첫 줄이 session_meta 가 아니거나 깨진 경우)은 뺀다.
    """
    found: list[tuple[Path, str]] = []
    for root in _sessions_roots(home):
        if not root.is_dir():
            continue
        for path in root.glob("**/rollout-*.jsonl"):
            cwd = _session_cwd(path)
            if cwd is not None:
                found.append((path, cwd))
    found.sort(key=lambda entry: mtime(entry[0]))
    return found


def _iter_lines(path: Path, tz: tzinfo) -> Iterator[tuple[dict, datetime]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    yield from iter_jsonl_timestamped(text, tz)


def codex_events(files: list[Path], tz: tzinfo) -> list[_Event]:
    """Codex 세션들의 (시각, role) 이벤트를 시간순으로 뽑는다.

    진짜 사용자 입력은 ``event_msg``(``type=user_message``)로만 판별한다(user). 그 외 모든
    ``response_item``(message·reasoning·tool 등)은 AI 작업 흐름(assistant)으로 본다. Codex 는
    시스템 컨텍스트(``<environment_context>``·``# AGENTS.md``·``[system instructions]`` 등)도
    ``response_item`` role=user 로 주입하므로 role/텍스트는 진짜 입력의 신호가 못 된다.
    """
    events: list[_Event] = []
    for path in files:
        for obj, moment in _iter_lines(path, tz):
            kind = obj.get("type")
            if kind == "response_item":
                if isinstance(obj.get("payload"), dict):
                    events.append((moment, "assistant"))
            elif kind == "event_msg":
                payload = obj.get("payload")
                if isinstance(payload, dict) and payload.get("type") == "user_message":
                    events.append((moment, "user"))
    events.sort(key=lambda e: e[0])
    return events
