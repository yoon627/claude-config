"""Jira Cloud REST API v3 클라이언트 (stdlib urllib 만).

worklog 등록/조회/갱신을 제공한다. 인증은 Basic(email:API token).

worklog started 포맷·query param 위치는 Jira 의 까다로운 검증을 통과하도록 고정한다:
- started 는 ``yyyy-MM-ddTHH:mm:ss.SSS±HHMM`` — 밀리초 필수, offset 은 콜론 없음.
  ``datetime.isoformat()`` 의 ``+09:00`` 은 400 을 부르므로 ``%z`` 로 만든다.
- notifyUsers/adjustEstimate 는 query string 으로만 — body 에 넣으면 400.
- 성공 상태는 endpoint 별로 고정한다(worklog 등록 201, 조회/갱신/사용자 조회 200). 그 외 상태·빈 응답은 실패로 본다.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import quote

# notifyUsers=false: 자동 등록이라 watcher 이메일 알림 억제.
# adjustEstimate=leave: 남은 추정치(remaining estimate)를 건드리지 않음(기본 auto 는 자동 차감).
_WORKLOG_QUERY = "?notifyUsers=false&adjustEstimate=leave"


@dataclass(frozen=True)
class JiraConfig:
    base_url: str  # site: https://<site>.atlassian.net (표시·cloudId 조회용)
    email: str = field(repr=False)  # PII — repr 제외
    token: str = field(repr=False)  # 토큰 — repr 제외(로그·예외 노출 방지)
    api_base: str = ""  # REST 호출 base(빈값이면 base_url). scoped token 은 api.atlassian.com/ex/jira/{cloudId}

    def rest_base(self) -> str:
        return (self.api_base or self.base_url).rstrip("/")


class JiraError(RuntimeError):
    """Jira API 호출 실패. 메시지·체인에 토큰을 절대 포함하지 않는다."""


def fetch_cloud_id(site_url: str, *, timeout: float = 10.0) -> str | None:
    """site 의 ``_edge/tenant_info`` 에서 cloudId 를 조회한다(인증 불필요).

    scoped API token 은 ``mysite.atlassian.net`` 직접 호출 시 401(익명 처리)이므로, 이
    cloudId 로 ``api.atlassian.com/ex/jira/{cloudId}`` 경로를 만들어야 Basic auth 가 인증된다.
    """
    url = f"{site_url.rstrip('/')}/_edge/tenant_info"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None
    cloud_id = data.get("cloudId")
    return cloud_id if isinstance(cloud_id, str) and cloud_id else None


def api_base_for(site_url: str, cloud_id: str | None) -> str:
    """REST 호출 base. cloudId 있으면 scoped/OAuth 경로, 없으면 site 경로(unscoped)."""
    if cloud_id:
        return f"https://api.atlassian.com/ex/jira/{cloud_id}"
    return site_url.rstrip("/")


def format_started(dt: datetime) -> str:
    """Jira worklog 의 ``started`` 문자열을 만든다 (콜론 없는 offset + 밀리초 3자리)."""
    if dt.tzinfo is None:
        raise ValueError("started 는 tz-aware datetime 이어야 합니다 (offset 누락 시 Jira 400)")
    return (
        dt.strftime("%Y-%m-%dT%H:%M:%S.")
        + f"{dt.microsecond // 1000:03d}"
        + dt.strftime("%z")
    )


def adf_from_text(text: str) -> dict[str, Any]:
    """plain text 를 최소 유효 ADF(Atlassian Document Format) 문서로 감싼다.

    여러 줄(``\\n``)은 각각 별도 paragraph 로 분리한다(빈 줄 포함, 문단 보존).
    """
    lines = text.split("\n")
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": line}]}
            if line
            else {"type": "paragraph", "content": []}
            for line in lines
        ],
    }


def _auth_header(config: JiraConfig) -> str:
    raw = base64.b64encode(f"{config.email}:{config.token}".encode()).decode("ascii")
    return f"Basic {raw}"


def _request(
    config: JiraConfig,
    method: str,
    path_with_query: str,
    body: dict[str, Any] | None,
    *,
    timeout: float,
    expect_status: int,
    what: str,
) -> dict[str, Any]:
    """Jira REST 호출 공통 경로. 성공 시 파싱된 JSON, 실패 시 JiraError(토큰 미노출)."""
    url = f"{config.rest_base()}{path_with_query}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", _auth_header(config))
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        hint = ""
        if exc.code == 401 and "api.atlassian.com" not in url:
            hint = " (scoped token 은 api.atlassian.com/ex/jira/{cloudId} 경로 필요 — JIRA_CLOUD_ID 설정/cloudId 조회 확인)"
        raise JiraError(f"{what} 실패 ({exc.code}): {detail}{hint}") from None
    except urllib.error.URLError as exc:
        raise JiraError(f"Jira 연결 실패 ({what}): {exc.reason}") from None

    if status != expect_status:
        raise JiraError(f"{what} 실패: 예상 {expect_status}, 받음 {status}")
    if not raw:
        if status == 204:
            return {}  # No Content (PUT 등 성공, 본문 없음)
        raise JiraError(f"{what} 실패: 빈 응답 (status {status})")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise JiraError(f"{what} 응답 파싱 실패: 비-JSON 응답 (status {status})") from None


def add_worklog(
    config: JiraConfig,
    issue_key: str,
    time_spent_seconds: int,
    started: datetime,
    comment: str | None = None,
    *,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """worklog 1건을 등록한다. 성공(201) 시 응답 JSON, 실패 시 JiraError."""
    body: dict[str, Any] = {
        "timeSpentSeconds": int(time_spent_seconds),
        "started": format_started(started),
    }
    if comment:
        body["comment"] = adf_from_text(comment)
    path = f"/rest/api/3/issue/{quote(issue_key, safe='')}/worklog{_WORKLOG_QUERY}"
    return _request(
        config, "POST", path, body,
        timeout=timeout, expect_status=201, what=f"worklog 등록 {issue_key}",
    )


def get_worklogs(
    config: JiraConfig, issue_key: str, *, timeout: float = 15.0
) -> list[dict[str, Any]]:
    """이슈의 기존 worklog 를 pagination 을 따라 전부 반환한다(중복 등록 방지용).

    ``GET issue worklogs`` 는 ``PageOfWorklogs`` — startAt/maxResults/total 이 있다.
    한 페이지만 보면 마커가 뒤 페이지에 있을 때 '미등록' 으로 오판해 중복 POST 가 난다.
    """
    worklogs: list[dict[str, Any]] = []
    start_at = 0
    encoded = quote(issue_key, safe="")
    while True:
        path = f"/rest/api/3/issue/{encoded}/worklog?startAt={start_at}&maxResults=1000"
        result = _request(
            config, "GET", path, None,
            timeout=timeout, expect_status=200, what=f"worklog 조회 {issue_key}",
        )
        batch = result.get("worklogs")
        batch = batch if isinstance(batch, list) else []
        worklogs.extend(batch)
        total = result.get("total")
        start_at += len(batch)
        if not batch or not isinstance(total, int) or start_at >= total:
            break
    return worklogs


def update_worklog(
    config: JiraConfig,
    issue_key: str,
    worklog_id: str,
    time_spent_seconds: int,
    started: datetime,
    comment_adf: dict[str, Any] | None = None,
    *,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """기존 worklog 의 시간을 갱신한다(PUT). 성공 200.

    ``comment_adf`` 는 이미 조립된 ADF(기존 worklog comment 재전송용)라 그대로 넣는다 —
    마커·수동편집을 보존하려 text 재래핑을 하지 않는다. None 이면 comment 필드를 생략한다.
    """
    body: dict[str, Any] = {
        "timeSpentSeconds": int(time_spent_seconds),
        "started": format_started(started),
    }
    if comment_adf is not None:
        body["comment"] = comment_adf
    path = (
        f"/rest/api/3/issue/{quote(issue_key, safe='')}"
        f"/worklog/{quote(str(worklog_id), safe='')}{_WORKLOG_QUERY}"
    )
    return _request(
        config, "PUT", path, body,
        timeout=timeout, expect_status=200, what=f"worklog 갱신 {issue_key}/{worklog_id}",
    )


def get_myself(config: JiraConfig, *, timeout: float = 15.0) -> dict[str, Any]:
    """현재 인증 사용자 정보(``accountId`` 등). worklog author 대조로 타인 worklog 보호."""
    return _request(
        config, "GET", "/rest/api/3/myself", None,
        timeout=timeout, expect_status=200, what="현재 사용자 조회",
    )
