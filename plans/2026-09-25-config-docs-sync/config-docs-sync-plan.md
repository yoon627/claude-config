---
title: config-docs-sync — CLAUDE.md 가드 서술 정정 + 저장소 밖 설정 변경(autoMode·ruleset·Codex)의 문서화
status: done
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

intent `repo-audit-followups` 의 네 단위를 닫는다. CLAUDE.md §8 의 pre-push 서술과 §3-1 의 memory 참조를 사실에 맞추고, 2026-09-25 저장소 밖에서 적용한 세 가지(autoMode.environment 분리, GitHub ruleset, Codex 쪽 재정렬)를 README·wiki 에 남긴다.

# Intent

→ `plans/2026-09-25-repo-audit-followups/intent.md`.

델타:
- Problem:
  - CLAUDE.md §8 은 "다른 repo 의 main 푸시는 pre-push 훅이 하드 차단"이라고 적었지만 훅 설치는 repo 별 opt-in 이다. `~/Repos` 6개 중 설치된 곳은 0이다(감사 refs-01). §3-1 은 memory 적립 시점으로 `/e` 8단계를 가리키는데, 그 단계에는 memory 절차가 없다.
  - 저장소 밖 설정 세 가지는 파일이 untracked 거나 GitHub 쪽이라, 문서에 남기지 않으면 다음 세션·다른 머신이 이유를 모른다.
- 저장소 밖 적용 내역(2026-09-25, 사용자 선택):
  - autoMode.environment: user `settings.json` 의 visibility·default branch·source control·primary use·trusted repo 5개 항목을 repo 별 서술로 바꿨다. `claude auto-mode config` 에 반영된 것을 확인했다. 백업은 `backups/permissions-20260925/settings.before-automode-env.json`.
  - GitHub ruleset `main-guard`(id 23979698): `lint` 필수, `non_fast_forward`, `deletion`, admin bypass `always`. 첫 main push 에서 `Bypassed rule violations … lint` 를 관찰했다.
  - Codex:
    - `~/.codex/AGENTS.md` → `~/.claude/CLAUDE.md` 심링크(2026-06-10 `a3d7bdc` 결정 복원).
    - `~/.claude/AGENTS.md` 미러 제거.
    - `~/.agents/skills` 7개 심링크.
    - `~/.claude/.codex/config.toml`(serena·headroom) 제거, 전역 `[mcp_servers.headroom]` 제거.
    - 백업은 `backups/codex-resync-20260925/`.
- Constraints: CLAUDE.md 는 운영 자산이고, 사용자가 "CLAUDE.md 문구 정정"을 선택했다. 문장 사실 정정만 하고 규칙은 바꾸지 않는다.
- Out of scope: `~/.codex/agents/*.toml` 재생성, bootstrap 의 skill 심링크 일반화, Codex 훅 — intent `audit-low-batch` 로 넘긴다.
- 분할: 없음 — 네 단위 모두 문서 몇 줄이다. intent 의 `(미착수)` 네 줄이 같은 파일을 고치므로, 나누면 형제 브랜치끼리 intent.md 인접 줄에서 충돌한다.

# Acceptance

1. CLAUDE.md §8 에서 옛 표현 "pre-push` 훅이 계속 하드 차단" 0건, 새 서술(install-hooks 를 실행한 repo 한정·opt-in)이 있다. §3-1 은 "복귀는 `/e` 8단계, memory 적립은 복귀한 main 세션에서 직접"으로 읽힌다.
2. README:
   - deny 설명의 pre-push 서술이 1과 같다.
   - `autoMode.environment` 설명(repo 별 서술·`~/.claude` PUBLIC)이 있다.
   - GitHub ruleset `main-guard` 설명(규칙·관리자 bypass·실효 범위)이 있다.
   - Codex 쪽 연결 설명(심링크 단일 소스·import 재실행 주의·백업 경로)이 있다.
3. wiki: `claude-code-agents-md-loading` 의 `[!open]` 이 해소되고, `claude-codex-collaboration` 에 심링크 단일 소스가 적혀 있다. `index.md`·`log.md` 가 동기화되고 `check_links.py` 가 clean 이다.
4. intent: `(미착수)` 네 줄이 이 plan 경로 한 줄로 바뀌고, Open question 이 `(해소)` 로 처분된다. `audit-low-batch` 에 새 잔여 항목(agents toml·bootstrap 심링크·Codex 훅)이 추가된다.
5. 전체: `bash scripts/verify.sh` → `ALL PASS`, 이 plan 의 plan-lint 가 통과한다(intent.md 는 plan-lint 대상이 아니다).

# Progress

- 2026-09-25: 착수. 저장소 밖 설정 세 가지는 이 plan 이전에 적용·확인했다(`# Intent` 델타).
- 2026-09-25: code-reviewer REQUEST CHANGES(Major 3) → fix loop 1: README deny 결론 문장, autoMode.environment 의 knowledge_base "local pre-push hook" 거짓 서술(저장소 밖 — 선택하신 범위 안의 내 오류 정정), intent 에서 빠진 SessionStart 무검증 ff 항목 복원. Minor·Nit 반영.

# Next

(없음 — 로컬 ff-merge 로 종료)

# Decisions

- 커밋 단위: 1개 — small 이고 문서만 바뀐다.
- ruleset 에 관리자 bypass 를 둔 이유: bypass 가 없으면 required status check 때문에 trivial·small 의 로컬 ff-merge 후 main 직접 push(CLAUDE.md §8)가 막힌다. 그만큼 소유자 본인의 실수는 막지 못한다 — README 에 실효 범위를 적는다. force push·삭제 차단은 CLAUDE.md §8 의 force push 금지와 같은 방향이라 함께 넣었다.
- Codex AGENTS.md 는 생성 스크립트가 아니라 심링크를 택했다. 2026-06-10 사용자 결정(`a3d7bdc`)이 이미 있고, 생성·별도 유지는 두 사본이 다시 갈라진다. 사용자가 고른 선택지 문구는 "현행 CLAUDE.md 기준 재생성"이었고, 심링크는 그 목적(항상 현행 CLAUDE.md)을 영구히 충족한다.
- `~/.codex/agents/*.toml` 은 재생성하지 않았다. 선택지 설명에 없었고, 그대로 옮기면 Codex 리뷰어가 "codex 병행 호출" 절 때문에 자기 자신을 다시 부른다 → `audit-low-batch`.

# Review Disposition

- [code] Major README:470 옛 결론 문장 — fix. Major autoMode.environment 의 knowledge_base pre-push hook 서술 — fix(`Default / protected branches` 항목, 백업 `settings.before-automode-fix2.json`). Major intent 에서 SessionStart 무검증 ff 유실 — fix(`autopull-verified-ff (미착수)`).
- [code] Minor wiki 한 페이지 안 모순 문장 — fix. Minor `core.hooksPath` 단서 — fix(CLAUDE.md·README). Minor Codex 확인 절차 보강 — fix. Minor bootstrap 이 AGENTS.md 심링크도 안 만듦 — fix(README·audit-low-batch). Nit skills 심링크 범위 표기·Codex bullet 위치(bootstrap 절로 이동)·wiki 시제·sources·claudeMdExcludes 후속 문장 — fix. Nit CLAUDE.md §3-1 의 7단계 삭제·harness 시작 경우 — wontfix(문구가 틀리지 않고, 경우 나열은 /e SKILL 이 단일 소스).

# Key Files

- `CLAUDE.md`(§3-1·§8), `README.md`(settings 키 목록·codex 절), `wiki/pages/entity/claude-code-agents-md-loading.md`, `wiki/pages/concept/claude-codex-collaboration.md`, `wiki/index.md`, `wiki/log.md`, `plans/2026-09-25-repo-audit-followups/intent.md`

# Blockers

없음.
