"""세션 로그(jsonl) 공통 IO 헬퍼 (Claude·Codex 파서 공유, stdlib only)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, tzinfo
from pathlib import Path


def mtime(path: Path) -> float:
    """파일 수정시각(정렬용). stat 실패 시 0.0."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def iter_jsonl_timestamped(text: str, tz: tzinfo) -> Iterator[tuple[dict, datetime]]:
    """jsonl 텍스트 각 줄에서 (파싱된 dict, tz 변환 timestamp) 를 뽑는다.

    빈 줄·bad json·비-dict·비-str/결측 timestamp·파싱 실패 줄은 건너뛴다. Claude(session_time)·
    Codex(codex_session) 파서가 공유해 파싱·방어 로직을 한 곳에 둔다.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        ts = obj.get("timestamp")
        if not isinstance(ts, str) or not ts:
            continue
        try:
            moment = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(tz)
        except ValueError:
            continue
        yield obj, moment
