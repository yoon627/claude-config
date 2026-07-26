"""jira-kit 설정 로드 (repo 비종속, stdlib only).

민감정보(JIRA_BASE_URL/EMAIL/API_TOKEN)는 환경변수 또는 .env 로,
비민감 설정(ticket_pattern/timezone/추정 파라미터)은 jira-kit.toml 로 둔다.
우선순위: 환경변수 > .env > jira-kit.toml > 기본값.
API_TOKEN 은 toml 에서 읽지 않는다(커밋 위험) — 환경변수/.env 전용.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .jira_client import JiraConfig, api_base_for, fetch_cloud_id

_DEFAULT_TICKET_PATTERN = r"[A-Z][A-Z0-9]+-\d+"  # 범용 Jira 키(CSTP1-2251 등도 매칭)
_DEFAULT_TIMEZONE = "Asia/Seoul"
_DEFAULT_MAX_GAP = 60


class ConfigError(RuntimeError):
    """설정 파일(.env / jira-kit.toml) 로드·파싱 실패 (CLI 는 이를 잡아 exit code 로 처리)."""


@dataclass(frozen=True)
class Config:
    jira: JiraConfig | None  # 자격증명 3개가 모두 있을 때만 non-None
    ticket_pattern: str
    timezone_name: str
    max_gap_minutes: int


def package_root() -> Path:
    """jira-kit 패키지 루트(scripts/jira_kit/config.py → jira-kit/). activate 가 skills/ 를 찾는 데 쓴다."""
    return Path(__file__).resolve().parents[2]


def parse_env(text: str) -> dict[str, str]:
    """단순 ``KEY=VALUE`` .env 파서(주석·빈 줄 무시, 양끝 따옴표 제거)."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def flatten_toml(data: dict) -> dict[str, str]:
    """jira-kit.toml 구조를 env 키 평면 dict 로 변환(토큰은 제외)."""
    jira = data.get("jira", {}) if isinstance(data.get("jira"), dict) else {}
    worklog = data.get("worklog", {}) if isinstance(data.get("worklog"), dict) else {}
    raw = {
        "JIRA_BASE_URL": jira.get("base_url"),
        "JIRA_EMAIL": jira.get("email"),
        "JIRA_CLOUD_ID": jira.get("cloud_id"),
        "JIRA_TICKET_PATTERN": worklog.get("ticket_pattern"),
        "JIRA_TIMEZONE": worklog.get("timezone"),
        "JIRA_MAX_GAP_MINUTES": worklog.get("max_gap_minutes"),
    }
    return {k: str(v) for k, v in raw.items() if v is not None}


def _int_or(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def resolve_config(
    environ: dict[str, str],
    env_file: dict[str, str],
    toml_flat: dict[str, str],
) -> Config:
    """세 소스(환경변수 > .env > toml)를 병합해 Config 를 만든다. 순수 함수(테스트 용이)."""

    def pick(key: str) -> str | None:
        for source in (environ, env_file, toml_flat):
            value = source.get(key)
            if value:
                return value
        return None

    base_url = pick("JIRA_BASE_URL")
    email = pick("JIRA_EMAIL")
    # 토큰은 민감정보 — 환경변수/.env 만(toml 제외)
    token = environ.get("JIRA_API_TOKEN") or env_file.get("JIRA_API_TOKEN")
    jira = JiraConfig(base_url, email, token) if (base_url and email and token) else None

    return Config(
        jira=jira,
        ticket_pattern=pick("JIRA_TICKET_PATTERN") or _DEFAULT_TICKET_PATTERN,
        timezone_name=pick("JIRA_TIMEZONE") or _DEFAULT_TIMEZONE,
        max_gap_minutes=_int_or(pick("JIRA_MAX_GAP_MINUTES"), _DEFAULT_MAX_GAP),
    )


def resolve_timezone(name: str) -> tzinfo:
    """IANA 이름으로 tzinfo 를 만든다. tzdata 없으면(Windows 등) 시스템 로컬로 fallback.

    Windows 는 IANA tz DB 를 내장하지 않아 ``ZoneInfo`` 가 실패할 수 있다. 정확한 IANA
    타임존이 필요하면 ``pip install tzdata``. fallback 여부는 반환 타입이 ZoneInfo 인지로
    호출부가 판정한다(ZoneInfo 아니면 로컬 fallback).
    """
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ModuleNotFoundError):
        local = datetime.now().astimezone().tzinfo
        return local if local is not None else timezone.utc


def find_upwards(name: str, start: Path) -> Path | None:
    """start 부터 상위로 올라가며 name 파일을 찾는다(repo root/홈까지)."""
    for directory in [start, *start.parents]:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def global_config_dir() -> Path:
    """홈 전역 jira-kit 설정 디렉토리(``~/.jira-kit``).

    skill 이 여러 repo/worktree/AI 에서 토큰·설정을 한 곳에서 읽게 하는 위치.
    """
    return Path.home() / ".jira-kit"


def _read_env_file(path: Path, label: str) -> dict[str, str]:
    try:
        return parse_env(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"{label} 읽기 실패 ({path}): {exc}") from None


def _read_toml_file(path: Path) -> dict[str, str]:
    try:
        return flatten_toml(tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"jira-kit.toml 파싱 실패 ({path}): {exc}") from None
    except OSError as exc:
        raise ConfigError(f"jira-kit.toml 읽기 실패 ({path}): {exc}") from None


def load_config(
    start_dir: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
    global_dir: Path | None = None,
    cloud_id_fetcher: Callable[[str], str | None] | None = None,
) -> Config:
    """실제 파일/환경에서 설정을 읽어 Config 를 만든다.

    우선순위: 환경변수 > 프로젝트 .env(cwd 상위) > 홈 전역 ``~/.jira-kit/`` > 기본값.
    홈 전역 소스는 skill 이 여러 repo 에서 토큰을 한 곳에서 읽게 한다(프로젝트별 override 가능).
    """
    environ = dict(os.environ) if environ is None else environ
    start = (start_dir or Path.cwd()).resolve()
    home = global_dir if global_dir is not None else global_config_dir()

    # .env: 홈 전역(<) → 프로젝트(cwd 상위)(>). 프로젝트가 전역을 override.
    env_file: dict[str, str] = {}
    global_env = home / ".env"
    if global_env.is_file():
        env_file.update(_read_env_file(global_env, "전역 .env"))
    project_env = find_upwards(".env", start)
    if project_env:
        env_file.update(_read_env_file(project_env, ".env"))

    # jira-kit.toml: 프로젝트 우선, 없으면 홈 전역.
    global_toml = home / "jira-kit.toml"
    toml_path = find_upwards("jira-kit.toml", start) or (
        global_toml if global_toml.is_file() else None
    )
    toml_flat = _read_toml_file(toml_path) if toml_path else {}

    config = resolve_config(environ, env_file, toml_flat)
    if config.jira is not None:
        # scoped API token 은 api.atlassian.com/ex/jira/{cloudId} 경로 필요.
        # cloudId 는 설정값 우선, 없으면 site 의 _edge/tenant_info 로 조회(오프라인/unscoped 면 None → site 경로).
        cloud_id = (
            environ.get("JIRA_CLOUD_ID")
            or env_file.get("JIRA_CLOUD_ID")
            or toml_flat.get("JIRA_CLOUD_ID")
        )
        if not cloud_id:
            fetcher = fetch_cloud_id if cloud_id_fetcher is None else cloud_id_fetcher
            cloud_id = fetcher(config.jira.base_url)
        api_base = api_base_for(config.jira.base_url, cloud_id)
        config = replace(config, jira=replace(config.jira, api_base=api_base))
    return config
