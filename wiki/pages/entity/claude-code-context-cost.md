---
title: claude-code-context-cost
category: entity
created: 2026-09-28
updated: 2026-09-29
sources:
  - https://code.claude.com/docs/en/model-config (Context window and auto-compaction · Extended context, 2026-09-28 확인)
  - https://code.claude.com/docs/en/settings-reference (autoCompactWindow · promptCacheTtl)
  - https://code.claude.com/docs/en/env-vars (CLAUDE_CODE_AUTO_COMPACT_WINDOW · CLAUDE_AUTOCOMPACT_PCT_OVERRIDE)
  - https://code.claude.com/docs/en/prompt-caching (무효화 목록 · effort 변경 · TTL 기본값 · 디렉토리별 캐시 — 2026-09-29 재조회: effort 변경에 캐시가 유지되는 모델 목록)
  - Claude Code 2.1.283 bundled claude-api skill — shared/models.md · shared/prompt-caching.md (단가·캐시 배수)
  - 세션 실측 2026-09-28 — 한 사용자의 로컬 transcript 30일(Claude Code 2.1.239~2.1.283), 스크립트 plans/2026-09-28-wiki-context-cost-lessons/analysis/
---

# claude-code-context-cost

1M 컨텍스트 모델로 Claude Code 를 쓸 때 비용을 좌우하는 것은 **호출 1회의 컨텍스트 크기 × 호출 수**(cache read)와 **캐시 쓰기**(cache write — 긴 컨텍스트의 재작성 포함)다 — 아래 표본에서는 본 세션의 두 항목이 API 환산 비용의 약 3/4 이었다. CLAUDE.md 같은 고정 문서는 새 세션에서는 크게 보여도 긴 세션에서는 작은 몫이다([[ops-doc-slimming]] 2026-09-28 재검토).

## auto-compact 기본값과 설정 (공식 문서, 2026-09-28)
- Anthropic API 에서 native 1M 창으로 도는 모델(목록은 [[anthropic-claude-models]])은 **약 967K 토큰에서야** 자동 compaction 한다.
- `autoCompactWindow`: compaction 전에 컨텍스트가 얼마나 찰지. 어느 settings 파일에나 둘 수 있고(scope `Any file`) 값은 정수 `100000`~`1000000`, 모델 창으로 상한. `/autocompact 300k` 는 이 키를 **user settings** 에 쓰고 현재 세션에도 적용한다 — managed settings 처럼 상위 scope 가 같은 키를 정하면 세션은 그 값을 쓴다. 한 번만 바꾸려면 `--autocompact`, 되돌리기 `/autocompact auto`.
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW` 는 명령·flag·setting 보다 우선한다. **정수만 받는다** — `500k` 는 `500` 으로 읽혀 최솟값 100K 로 잘린다(명령·flag 는 `300k` 를 받지만 env 는 `300000` 으로 써야 한다).
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` 는 그 창의 몇 % 에서 compaction 할지 — 낮추기만 된다.
- `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` 이면 native 1M 모델도 200K 경계에서 compaction 한다.
- 1M 창은 **200K 초과분에 할증이 없다**(표준 단가).

## 단가와 캐시 TTL
- Opus 5.5: 입력 $4 · 출력 $20 / MTok, **cache read $0.20 = 입력의 0.05배**(다른 모델의 배수는 [[anthropic-claude-models]]). 캐시 쓰기는 5분 TTL 1.25배, 1시간 TTL 2배(bundled claude-api skill 2.1.283).
- Claude Code 는 **구독의 포함 사용량 안에서만** 본 대화를 1시간 TTL 로 요청한다. subagent·compaction·workflow 는 5분(서버가 정하는 일부 helper 만 1시간), 사용량 크레딧·API key·클라우드 공급자는 본 대화도 5분이다(`promptCacheTtl` 로 직접 고를 수 있음).
- 그래서 1시간 TTL 인 긴 본 대화에서는 한 번의 **재작성(2배)**이 여러 번의 읽기(0.05배)보다 비쌀 수 있다.

## 실측 — 한 사용자의 30일 표본 (2026-08-29~09-28)
표본이다(한 사용자·한 머신·1M 모델 위주). 수치는 비율과 토큰 수만 적는다.
- 본 세션 API 호출 1회 평균 컨텍스트 **457,867 토큰**(중앙 428,465), **81% 가 200K 초과**. 세션별 최대 컨텍스트는 중앙 67K 지만 p90 960K — 기본 창에서는 소수의 긴 세션이 80~96만까지 자라 사용량을 지배한다. 본 세션 137개 중 compaction 이 일어난 세션은 15개.
- API 단가 환산 비용 구성: 본 세션 cache read 47.5% · cache write 28.6% · output 9.1% · subagent 약 15%. 아래 버전 문제가 사라진 뒤 14일은 46.4% · 19.7% · 11.4% · 22.6%.
- CLAUDE.md(43,079B, 한글 위주, import 하는 RTK.md 961B 포함)는 약 2만 토큰(`claude -p --model sonnet` 으로 측정 — 당시 Claude Code 2.1.283 이하라 Sonnet 5 로 추정 ⚠️, Opus 토크나이저와 다를 수 있음 ⚠️). 새 세션 기본 컨텍스트(약 5.5만)의 36% 다. 실사용 몫은 **계산값**이다: `2만 × 호출 수 ÷ 전체 호출 컨텍스트 합(본 세션+subagent)` = 3.6%(본 세션에만 실린다고 볼 때)~6.6%(subagent 에도 실린다고 볼 때). 본 세션 호출 1회 평균 대비로는 약 4.4%. 2026-09-27 전까지 worktree 세션은 CLAUDE.md 를 이중 주입했으므로([[claude-code-agents-md-loading]]) 그 기간의 실제 몫은 이보다 컸다.
- auto-compact 창 재생 시뮬레이션(**본 세션 비용 기준**, 호출 기록에 창을 적용, compaction 직후 크기 중앙 119,010 은 실측, 요약 출력 1.2만은 가정): 300K −38.9%(세션당 1.4회), 400K −32.7%, 500K −27.8%, 200K −38.0%(세션당 3.7회 — compaction 직후가 12만이라 여유가 없다). 요약 손실로 대화가 달라지는 효과는 반영하지 않는다 — 적용 후 재측정이 필요하다.

## 캐시 재작성의 원인
재작성 = 컨텍스트 60K 초과이면서 캐시 쓰기가 그 호출 컨텍스트의 50% 초과(휴리스틱). 직전 호출 이후 무엇이 있었는지로 나눈 재작성률(같은 표본, 재작성/호출):

| 직전 신호 | 재작성률 | 해석 |
|---|---|---|
| 없음(기준선) | 0.7% (140/19,982) | |
| 1시간 넘게 휴식 | 80% (115/144) | 1시간 TTL 만료 |
| 5~60분 휴식 | 7.6% (53/696) | 5분 TTL 로 요청된 구간(크레딧 사용 등)이나 다른 무효화와 겹친 경우로 보임 ⚠️ |
| `/model` 명령 | 87.5% (14/16) | 캐시는 모델별 |
| 응답 모델이 바뀜(폴백 포함) | 37.1% (46/124) | |
| compaction | 100% (30/30) | 컨텍스트가 작아진 뒤라 비용은 작다 |
| 세션 중 cwd 변경(worktree 이동) | 0.9% (11/1,285) | 원인 아님 — 단 **세션끼리는** 디렉토리별로 캐시가 나뉘어 worktree 마다 연 세션은 서로의 캐시를 못 쓴다(공식) |
| `/effort` 변경 | — | 공식: **대부분 모델은 무효화**, 일부 모델은 API key·구독에서 유지(모델 목록·예외 환경은 [[anthropic-claude-models]]). 이 표본의 Opus 5.5·2.1.283 관찰 1회도 유지(직후 호출 cache read 415,606·쓰기 2,043) |

신호 없는 재작성은 이 표본에서 **Claude Code 2.1.239~2.1.247 에 4~9%**, 2.1.248~2.1.259 약 0.5%, **2.1.260(2026-09-04) 이후 약 0%**(2.1.283 에서 2/2,352)였다. 같은 날짜에도 버전에 따라 갈려 클라이언트 쪽 원인으로 보이지만 무엇인지는 모른다 ⚠️ — 신호표가 보지 못한 공식 무효화(MCP 서버 연결·제거, plugin 토글, 도구 전체 deny, fast mode, 이미지 누적, Claude Code 업그레이드)나 세션 안의 effort 변경이 후보다.

## 집계 방법 (재사용)
- 위치: 본 세션 `~/.claude/projects/<project>/*.jsonl`, subagent `…/<session>/subagents/*.jsonl`.
- **usage 는 content block 마다 같은 `message.id` 로 반복 기록된다.** `message.id`(없으면 `requestId`)로 전역 중복을 제거한다 — 이 표본에서는 안 하면 합계가 약 2.4배 부풀었다(배수는 응답당 줄 수에 따라 표본마다 다르다). 중복 줄의 usage 는 같은 값이라 비중은 거의 그대로다([[lesson-grep-absence-not-proof]] 사례 7).
- 컨텍스트 = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. 캐시 쓰기 TTL 구분은 `usage.cache_creation.ephemeral_1h_input_tokens`·`ephemeral_5m_input_tokens`.
- CLAUDE.md 의 토큰은 headless 로 `--settings '{"claudeMdExcludes":["<경로>"]}'` 포함·제외 두 번 돌린 차이로 잰다([[claude-code-agents-md-loading]] 의 측정 방식). 빈 디렉토리 headless 세션은 새 세션 기본만 보여 주므로 실사용 비중으로 옮기지 않는다.
- 파일 mtime 으로 기간을 거르면 경계가 세션 단위라 대략적이다.

## 연계
모델·1M 선택은 [[claude-code-model-selection]], 고정 문서 슬림화의 기대효과는 [[ops-doc-slimming]].
