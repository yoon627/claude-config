"""Codex CLI 세션 로그 기반 시간 파서 (stdlib only).

Codex 는 세션을 ``~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`` 에 저장하고, 보관하면
``~/.codex/archived_sessions/rollout-*.jsonl`` (flat)로 옮긴다 — 둘 다 탐색해야 누락이 없다.
Claude 와 달리 cwd 별 폴더가 아니라 날짜 폴더에 여러 worktree 세션이 섞여 있어, 각 파일 첫 줄
``session_meta.payload.cwd`` 로 귀속을 정한다. **어느 worktree 인지 가리는 일은 여기서 하지
않는다** — 스캔은 (파일, cwd) 만 내놓고 분류는 호출자의 ``WorktreeIndex`` 가 맡는다. 필터를
여기 두면 Claude 경로(최장 prefix)와 규칙이 갈려, worktree **하위** 디렉토리에서 시작한
세션이 어느 버킷에도 못 가고 사라진다(실측 26건).

시간: timestamp 가 있는 모든 ``response_item`` 을 AI 작업 흐름(assistant)으로 쓰고, **사용자
대기는 turn lifecycle 로 판정한다**. Codex 는 ``<environment_context>``·``# AGENTS.md`` 등
시스템 컨텍스트도 ``response_item`` role=user 로 주입해 role/텍스트로는 진짜 입력을 가릴 수
없고, ``event_msg`` ``user_message`` 도 2026-08 을 지나며 사라져(사용자 입력이 response_item
으로만 남는다) 그 이벤트만 보면 turn 사이 대기가 통째로 작업으로 잡힌다(실측 합계의 절반).
그래서 ``task_started`` 를 ``user``, ``task_complete``/``turn_aborted`` 를 ``await_user`` 로
번역해 ``_is_work_gap`` 의 기존 필터에 태운다 — 여기서 ``user`` 는 "진짜 사용자 입력"이 아니라
**"직전 gap 을 대기로 판정하라"는 표시**다(Claude 파서와 어휘는 같고 의미는 넓다).
``user_message`` 도 그대로 ``user`` 로 둔다 — 이 코퍼스에선 lifecycle 과 항상 함께 나와 결과를
바꾸지 않지만, 진짜 입력 직전 gap 을 대기로 보는 것은 형식과 무관하게 옳고 비용이 없다.
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


# 사용자가 답하기 전에는 output 이 오지 않는 도구 — Claude 의 ``_AWAIT_USER_TOOLS`` 대응.
_AWAIT_USER_CALLS = frozenset({"request_user_input"})
# 직전 gap 이 대기인 이벤트(turn 시작·진짜 입력) / 직후 gap 이 대기인 이벤트(turn 종료·중단).
_GAP_BEFORE_IS_WAIT = frozenset({"task_started", "user_message"})
_GAP_AFTER_IS_WAIT = frozenset({"task_complete", "turn_aborted"})


def _rollout_events(path: Path, tz: tzinfo) -> Iterator[_Event]:
    """rollout 한 파일의 (시각, role). 파일 = 세션이라 대기 상태(pending)도 파일 안에서만 산다.

    ``pending`` 은 답을 기다리는 ``request_user_input`` 의 call_id 들이다. 비어 있지 않은 동안
    오는 response_item 은 전부 대기다(사이에 reasoning 이 끼어도 새지 않게). turn 경계에서
    비운다 — output 없이 끊긴 call 이 실존해서, 안 비우면 그 뒤 세션 전체가 대기로 0 이 된다.
    """
    pending: set[str] = set()
    for obj, moment in _iter_lines(path, tz):
        kind = obj.get("type")
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            continue
        if kind == "response_item":
            item = payload.get("type")
            call_id = payload.get("call_id")
            # call_id 없는 call 을 넣으면 None 이 pending 에 남아 그 turn 전체가 대기로 사라진다.
            if (
                item == "function_call"
                and payload.get("name") in _AWAIT_USER_CALLS
                and isinstance(call_id, str)
            ):
                pending.add(call_id)
                yield moment, "await_user"
            elif item == "function_call_output" and call_id in pending:
                pending.discard(call_id)
                yield moment, "assistant"
            else:
                yield moment, "await_user" if pending else "assistant"
        elif kind == "event_msg":
            event = payload.get("type")
            if event in _GAP_BEFORE_IS_WAIT:
                pending.clear()
                yield moment, "user"
            elif event in _GAP_AFTER_IS_WAIT:
                pending.clear()
                yield moment, "await_user"


def codex_events(files: list[Path], tz: tzinfo) -> list[_Event]:
    """Codex 세션들의 (시각, role) 이벤트를 시간순으로 뽑는다(안정 정렬 — 같은 시각은 파일 순서).

    role 은 ``_is_work_gap`` 의 어휘다: ``user`` = 직전 gap 이 대기(turn 시작·진짜 입력),
    ``await_user`` = 직후 gap 이 대기(turn 종료·중단, ``request_user_input`` 대기 중),
    ``assistant`` = 그 외 모든 response_item.
    """
    events: list[_Event] = []
    for path in files:
        events.extend(_rollout_events(path, tz))
    events.sort(key=lambda e: e[0])
    return events
