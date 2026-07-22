---
title: subagent-model-effort — subagent별 model/effort 차등 + 메인 effort 하향으로 토큰 최적화
status: done
started: 2026-06-18
updated: 2026-06-19
---

# Goal

`~/.claude` 설정의 토큰 사용을 최적화하되 리뷰 품질은 보존한다. 핵심 두 레버:
1. 메인 세션 effort `max`→`high` (Anthropic 권장 기본값, thinking output 절감)
2. subagent별 model/effort 차등 — 리뷰는 opus+max(품질), 보조는 저단가 모델

요청 맥락: 사용자가 (1) 불필요 MCP/도구/subagent, (2) 토큰 낭비 지점, (3) headroom 실제 적용 여부, (4) 작업별 model 차등을 점검 요청 → 이 plan은 그중 **(4) model/effort 차등**의 구현분. 나머지(MCP 정리·headroom)는 아래 "이번 범위 밖" 참고.

> **plan 위치 주의**: 이 작업은 worktree `subagent-model-effort`에서 진행. plan 진실 소스는 이 worktree의 `plans/`(worktree-edit guard가 main plans/ 수정 차단). main `plans/2026-06-18-subagent-model-effort/`의 원본은 작업 시작 시점 스냅샷 → 완료(/e) 시 동기화.

# Progress
- 2026-06-19 PR #51 머지 완료 (main ccc1cc7). 검증 통과(diff plan 일치·settings valid JSON·User/Machine env 삭제 확인). status: done — worktree 정리.

- 2026-06-18: 환경 점검 + 설계 합의 완료(구현 미착수). codex(read-only) 교차검증 병행. claude-code-guide로 subagent effort frontmatter 지원 확인. 사용자가 "plan 저장 후 다음 세션에서 구현(B안)" 선택.
- 2026-06-18(이어서): `/wt subagent-model-effort` worktree 생성·진입(dlc). Explore 재확인 중 **중대 발견** — 메인 effort 레버가 plan 가정과 다름. subagent frontmatter 공식 지원 + **Haiku effort 미지원** 사실확정(claude-code-guide 2회). self-diagnosis 발동 → 사용자 결정 대기.
- 2026-06-18(구현): 사용자 결정 **"OS env 삭제 + high"**. 구현 완료 — Windows User env `CLAUDE_CODE_EFFORT_LEVEL` 삭제(확인=`''`) · `settings.json`(env `high`, `effortLevel` 제거) · agents 5개 frontmatter(reviewer 3개 opus+max, simplifier sonnet, researcher haiku). 검증: settings.json valid JSON, frontmatter 정확, **researcher=haiku effort smoke 통과**(haiku+세션effort max 상속 에러 없음 → researcher effort 명시·폴백 불필요). 메인 직접 리뷰 통과(로직 없는 설정 변경). **미적용**: 변경이 worktree에 있어 현재 세션 미반영 — main 머지+새 세션서 최종 적용.

# Next

1. (선택) worktree 브랜치 `subagent-model-effort` 커밋 — `settings.json` + agents 5개 (`plans/`는 gitignored라 제외). push/PR은 사용자 요청 시만(§8).
2. **머지 후 새 세션 검증(수동·필수)**: `/status`로 메인 effort=`high` 확인 / `/agents`로 5개 정의 로드(YAML 파싱 에러 없음) 확인 / researcher가 haiku로 실동작.
3. main 머지 시 worktree plan → main `plans/` 동기화(/e).

# Decisions

- **메인 effort `max`→`high`**: Anthropic 공식 권장이 Opus는 high 기본, max는 "extremely hard, latency-insensitive" 한정(`shared/model-migration.md` Opus 4.8). max 전역은 전 작업 최대 thinking = 낭비 + 과사고. (이유: 토큰 절감 + 품질 유지)
- **[정정·중대 2026-06-18] 메인 effort 레버 — settings.json 만으론 불충분 (→ OS env 삭제로 해결)**: OS(Windows **User**) 환경변수에 `CLAUDE_CODE_EFFORT_LEVEL=max`가 **별도 존재**(settings.json `env`와 중복). 공식 문서상 **shell/OS env > settings.json `env`**(settings.md "shell variable takes precedence over the env block", env-vars.md) → settings.json만 high로 바꿔도 OS의 max가 이겨 메인은 max 유지. 진짜 레버는 OS env. **사용자 결정으로 OS env 삭제 + settings.json high 단일소스화**. plan의 "settings.json L3만 변경" 가정 폐기. (`CLAUDE_EFFORT`는 User/Machine 둘 다 빈값 → Claude Code 내부 파생 별칭, 공식 변수는 `CLAUDE_CODE_EFFORT_LEVEL` 뿐.)
- **리뷰 subagent = opus + effort:max**: 사용자 직관. 리뷰는 버그·보안·누락을 잡는 깊은 추론 단계라 thinking에 값을 치를 곳. 메인(high)과 분리해 비용을 리뷰에만 집중. (subagent `effort` frontmatter 공식 지원: sub-agents.md L283 — 세션 effort override, 미지정 시 상속. `model:` 별칭 opus/sonnet/haiku/fable·inherit·전체ID 유효.)
- **구현·plan = 메인 opus/high 유지**: dlc는 hub-and-spoke로 구현이 메인 직접(plan과 같은 에이전트). "구현만 sonnet"은 메인 model 하나라 구조상 분리 불가. 구현 전담 subagent 위임(경로 A)은 Sonnet이 40%만 싸고 메인 컨텍스트 복제 전달 오버헤드가 있어 무조건 이득 아님 → 대규모 보일러플레이트 구현만 케이스별 위임.
- **researcher=haiku, code-simplifier=sonnet**: researcher는 단순 검색(80%↓), simplifier는 기계적(40%↓). reviewer만 opus 유지.
- **[확정 2026-06-18] Haiku 4.5 effort 미지원 — 단 상속은 안전(smoke 확정)**: effort 파라미터는 Opus/Sonnet/Fable 전용, Haiku 제외(effort.md). **그러나** researcher=haiku에 세션 effort(max) 상속 상태 smoke 결과 **에러 없이 정상 응답** → Claude Code가 haiku에 effort를 무시/제거. researcher `effort` 명시·sonnet 폴백 불필요. (Haiku 4.5 extended thinking 자체는 budget_tokens 방식 지원, effort 파라미터만 미지원.)
- **가격 근거(claude-api / models.md, per 1M)**: Opus 4.8 $5/$25, Sonnet 4.6 $3/$15(40%↓), Haiku 4.5 $1/$5(80%↓). 캐시 read 0.1×.
- **정정 2건**(재논의 방지): (a) **opus[1m]은 long-context 프리미엄 없음**(models.md). (b) Sonnet은 Opus의 1/5 아니라 **40%만 싸다**(1/5은 Haiku).
- **effort 모델 제약**: Haiku 4.5는 effort 미지원. Sonnet 4.6·Opus는 max까지 지원.

# Key Files

- **Windows User 환경변수 `CLAUDE_CODE_EFFORT_LEVEL`** — 삭제 완료(=`''`). 메인 effort는 이제 settings.json `env`가 유일 소스.
- `settings.json` — `env.CLAUDE_CODE_EFFORT_LEVEL`(L3, **high**), ~~`effortLevel`(제거됨)~~, `model: opus[1m]`(L126)
- `agents/plan-reviewer.md` `agents/code-reviewer.md` `agents/architecture-reviewer.md` — `model: opus`+`effort: max` 추가 (본문 codex `model_reasoning_effort`는 별개 축 — 공존)
- `agents/code-simplifier.md` — `model: sonnet`
- `agents/researcher.md` — `model: haiku`
- `skills/dlc/SKILL.md` — hub-and-spoke 구조 근거: 구현=메인 hub, reviewer=격리 spoke

# Blockers

없음. (Windows User env 처리 사용자 결정 완료 → 삭제+high 적용. 남은 건 머지 후 새 세션 수동 검증 — blocker 아님.)

---

## 이번 범위 밖 (별도 작업 — 섞지 않음)

점검에서 함께 발견된 것들. model/effort와 무관하므로 분리:
- **serena MCP** 좀비 정리(`~/.claude.json` mcpServers에 정의 있으나 `claude mcp`가 인식 못 함, 프로세스 없음 — codegraph로 대체됨)
- **claude.ai Google Drive** MCP 미인증 → 안 쓰면 연결 해제
- **codegraph allow-list** stale 4개 제거(settings.json `codegraph_callees/impact/files/status` — 실제 노출 도구에 없음)
- **headroom**: `HEADROOM_MODE=cache`로 절약 $0(lifetime 4202req, tokens_saved 0). `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` 단일 프록시 경유(SPOF). token 모드 30s timeout 실패 이력 → 권장: chokepoint 제거, headroom opt-in
- **settings.local.json** allow 63개 광범위 — 토큰보다 보안/오작동 위험
