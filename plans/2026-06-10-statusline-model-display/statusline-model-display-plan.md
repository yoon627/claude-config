---
title: statusline-model-display — statusline claude/codex 조각을 모델명+사용량 병기로
status: done
started: 2026-06-10
updated: 2026-06-10
---

# Goal
`statusline.js` 의 claude/codex 사용량 조각에서 'claude'/'codex' 레이블 단어를 제거하고, 그 자리에 각 도구의 모델명을 넣어 '모델명 + 사용량' 병기로 만든다. 예: `claude 53%(20:30) | codex 70%(15:00)` → `Opus 53%(20:30) | gpt-5.4 70%(15:00)`.

# Progress
- 2026-06-10: `/wt ?` 질문 모드로 요구사항 구체화(병기 / 레이블 제거 / codex=config 기본값). worktree 생성.
- 2026-06-10: Explore — statusline.js(claude 35-39행, codex 89-93행), codex-quota-refresh.js, ~/.codex/config.toml(`model="gpt-5.4"`), 공식 statusline 문서(`model.display_name` 확인). 테스트 인프라 없음→수동 검증. subagent-statusline.js는 사용량 미표시→변경 불필요.
- 2026-06-10: 구현 완료 — readCodexModel() 헬퍼 + claude/codex 레이블 변수화, README 동기화. 수동 검증 통과(모델명 표시·claude폴백·readCodexModel→gpt-5.4·codex캐시). code-reviewer+codex 병행 리뷰 → Major 1건 합의.
- 2026-06-10: Major fix — readCodexModel 정규식이 top-level 미보장(`/m`의 ^는 줄 시작이라 [profiles.x] 안 model 오매칭). `cfg.split(/^\s*\[/m)[0]` 로 첫 [table] 헤더 이전만 매칭. edge case 재검증 통과(섹션 model 차단·top우선·주석 스킵, 실제 config gpt-5.4 유지), node --check OK.
- 2026-06-10: 커밋 `2bc2518` → push → PR #30 머지(merge commit `1c6e7d3`) → main worktree ff 적용(`~/.claude/statusline.js` 갱신, status line 2초 후 자동 반영, 세션 재시작 불필요) → origin 브랜치 삭제. 실제 출력 확인: `Opus 4.8 53%(...) | gpt-5.4 98%(...) | ctx 12%`. → **done**.

# Next
- (없음 — 머지·실제 적용 완료)
- 마무리(/e): 이 plan 을 main `plans/` 로 이전 + worktree 정리 + 세션 main 복귀.

# Decisions
- 표시 = 사용량+모델 **병기**(완전 대체 X). 이유: 사용량(%·리셋)은 한도 소진 시점 정보라 유용. (사용자 결정)
- 레이블 단어 'claude'/'codex' **제거** — 모델명이 도구 구분 역할 대신. (사용자 결정)
- claude 모델 출처 = statusLine stdin `input.model.display_name` (공식 문서 159행, 이미 들어옴, 실시간·정확).
- codex 모델 출처 = `~/.codex/config.toml` 의 `model` 값. 이유: quota refresh가 쓰는 `account/rateLimits/read`는 모델 미제공. 한계: 설정 기본값이라 codex 세션 `/model` 변경과 어긋날 수 있음(사용자 감수).
- codex config는 statusline.js가 **직접 동기 읽기**(매 호출). 이유: config.toml 작고 로컬, 2초 간격에 부담 무시. 캐시 경유(codex-quota-refresh)보다 단순.
- fallback: claude display_name 없으면 `'claude'` 유지, codex config/model 못 읽으면 `'codex'` 유지 — 조각 정체성 보존, statusline은 절대 안 깨지게(기존 try/catch 패턴 승계).

# Key Files
- `statusline.js` — claude 조각(35-39행)·codex 조각(89-93행) 레이블 변경 + codex model 읽기 헬퍼.
- `README.md` — 187행 예시, 197-198행 "Codex quota 표시" 형식 동기화.
- `~/.codex/config.toml` — codex model 읽기 대상(읽기 전용, 변경 안 함).

# Review Disposition
code-reviewer(REQUEST CHANGES) + codex(중간) 병행, Major 1건 합의:
- **Major** (readCodexModel 정규식 top-level 미보장 → 섹션 내 model 오매칭) — **fix**: `cfg.split(/^\s*\[/m)[0]` 로 첫 [table] 헤더 이전만 매칭. 재검증으로 섹션 model 차단 확인.
- **Minor** (매 호출 readFileSync, 2초 간격) — **defer**: statusline은 매 렌더 새 프로세스라 메모이즈 무효, 진짜 절감은 codex-quota.json에 model 동봉(codex-quota-refresh.js 변경, 별도 범위). config 수백 바이트 <1ms라 허용.
- **Minor** (bare 따옴표 없는 값 미매칭) — **wontfix**: TOML 문자열 따옴표 필수, 정상 config 무관.
- **Nit** (label 스코프 충돌 / display_name 빈문자열 폴백) — 통과: 블록 스코프 분리·falsy `||` 폴백 정상.

# Blockers
(없음)
