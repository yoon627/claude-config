---
title: subagent-model-pinning — agents/*.md model 을 inherit 에서 단계별 고정으로 전환
status: in_progress
started: 2026-08-06
updated: 2026-08-11
---

# Goal

`agents/*.md` frontmatter 의 `model: inherit` 를 단계별로 고정한다 — reviewer 3종(plan/code/architecture)은 `opus`, researcher 는 `sonnet`. 근거는 [[model-stage-tiering]](2026-08-05 승인). README·wiki(`effort-global-xhigh`·`index`·`log`·`model-stage-tiering` 의 `[!open]`)를 같은 브랜치에서 동기화한다.

# Progress

- 2026-08-06: worktree `subagent-model-pinning` 생성(base d7cfba1) → main 이 4커밋 앞서 있어 `git merge --ff-only origin/main`(7c977c8)로 정합. 근거 페이지 `model-stage-tiering.md` 가 브랜치에 편입되어 dead-link 우려 해소.
- 2026-08-06: 편집 대상 8곳 확정, 검증 명령 식별(`.github/workflows/lint.yml`).
- 2026-08-06: plan-reviewer(+codex 병행) CONDITIONAL — 지적 11건 전부 처분(`# Review Disposition`). researcher 조사로 `[1m]` 판정 확정(미문서화 + stripping 버그 #45169 → 미사용; Opus 4.7+ 는 API/Max 에서 자동 1M 이라 불필요). **구현 완료** — agents 4파일 + README + wiki 5페이지 + index/log.
- 2026-08-06: Acceptance #1~#5 통과, 레포 검증 전량 PASS(node --check 23 / unit 9 / python 3 / JSON / shellcheck), `plan-lint` exit 0.
- 2026-08-11: simplify 체크(중복 없음) + 최종 재검증 전량 PASS(node --check 23 / unit 9 / python 3 / JSON / shellcheck, dead link 0, plan-lint 0). Acceptance #1~#6 충족, #7 은 머지 후 새 세션 몫.
- 2026-08-11: code-reviewer REQUEST CHANGES(Major 6·Minor 7) → 전부 검증 후 반영. **08-06 교정의 오류 정정**: "런타임 effort=high" 는 tool 셸 `printenv` 만 본 오판이었고 실제 claude 프로세스는 `max`(`ps eww` 실측). 근본원인 `scripts/bootstrap/setup.sh:118`·`setup.ps1:156` 확정. `effort-os-env-single-source` 의 동일 stale 도 교정. wiki 5페이지 `updated`/`sources` 보강.

# Next

**머지 후 새 세션에서 Acceptance #7(런타임 smoke) 수행** — reviewer 3종·researcher 를 각 1회 spawn 해 자기 exact model ID 를 보고시켜 opus/sonnet 반영을 확인한다. 이 worktree 에서는 원리적으로 불가했다(라이브 정의는 `~/.claude/agents/`). 실패 시 되돌리기는 `# Rollback`.

그 다음(선택): `# Deferred` 의 bootstrap effort 재주입 문제(심각도 중) 처리 여부 결정.

# Decisions

- **inherit → 명시 고정**: 2026-07-04 `effort-global-xhigh` 의 inherit 결정 전제("Fable 가용성 변동 대비, 세대 교체 시 수정 지점 0")가 Fable 기본모델 + 주간 50% 캡 시대엔 역효과 — 세션이 Fable 이면 리뷰·조사까지 Fable 캡을 소모한다. 리뷰 품질 병목엔 opus, 검색·요약엔 sonnet 이 맞다([[model-stage-tiering]]).
- **별칭 사용(모델 ID 아님)**: `opus`/`sonnet` 별칭은 세대를 따라가므로([[claude-code-subagent-config]]) inherit 결정이 지키려던 "세대 교체 시 수정 지점 0" 속성은 대부분 보존된다 — 잃는 것은 *세션 모델 추종*뿐이고, 그게 이번에 의도적으로 끊는 대상이다.
- **effort 는 불변**: 전역 단일 레버 유지([[effort-global-xhigh]] precedence). frontmatter 에 `effort` 를 되살리지 않는다 — env 가 override 라 죽은 설정이 된다.
- **effort 실측값 교정 (plan-review 반영)**: 문서가 주장하는 `xhigh` 는 사실이 아니다 — 실측 `printenv CLAUDE_CODE_EFFORT_LEVEL` = `high`, `settings.json:3`·`:244` 모두 `high`. 커밋 `78a6715 fix(settings): effort xhigh→high (웹툴 400 해소)` 에서 **의도적으로 하향**됐는데 wiki 만 갱신되지 않았다. `effort-global-xhigh.md` 를 어차피 개정하므로 그 안의 사실오류는 같이 바로잡는다(내가 편집하는 파일에 알면서 거짓 서술을 남기지 않는다). 단 **페이지명 자체(`effort-global-xhigh`)가 현재값과 어긋나는 문제는 rename·링크 전수 수정이라 스코프 밖 → `# Deferred`**.
- **1M context 트레이드오프 (plan-review 반영)**: 세션은 `ANTHROPIC_MODEL=opus[1m]`(실측). `model: opus` 로 박으면 세션 추종이 끊기며 1M 옵트인도 함께 잃을 개연이 있다. `opus[1m]` 이 frontmatter 에서 유효하면 그걸로 고정하고, 아니면 200k 수용을 명시 결정한다(researcher 대기).
- **`subagent-model-effort-tiering` 배너 처리**: `[!conflict]` 배너(:14)는 *현재 상태를 가리키는 포인터*이지 역사 본문이 아니다. 이번 변경이 model 차등을 부분 복원하므로 배너의 "차등 폐기" 단정은 stale → 배너에 한 줄만 덧붙이고 본문 차등 기록은 역사로 보존. (Codex 는 "역사 문서 불가침"으로 반대했으나, lint 의 '모순' 점검 대상은 배너 쪽이라 갱신을 택함.)
- **범위 밖(의도)**: dlc 최종 검증 runner 는 빌트인 `general-purpose` 라 `agents/` 에 없어 pinning 대상이 아니다 — [[model-stage-tiering]] 의 "simplify·verify = 세션 모델 그대로" 와 일치하므로 변경하지 않는다.
- **wiki 정합 방식**: main 미커밋 문제는 rebase(ff)로 해소 — 사용자 확인 결과 wiki 작업이 `531bf06` 으로 이미 push 되어 있었다. 따라서 `[[model-stage-tiering]]` 링크를 정상 사용하고, 같은 파일의 `[!open] 구현 대기` 블록도 이 브랜치에서 해소 표시로 갱신한다(문서가 현재 상태와 어긋나지 않게 — CLAUDE.md §3-5).

# Key Files

- `agents/{plan-reviewer,code-reviewer,architecture-reviewer}.md:5` — `model: opus`
- `agents/researcher.md:5` — `model: sonnet`
- `agents/code-reviewer.md:25` — 본문의 `model: inherit` 근거 서술(drift 대상)
- `README.md:265` — agents/ 절 frontmatter 설명
- `wiki/pages/decision/effort-global-xhigh.md:21` — 2026-07-04 inherit 결정의 개정 기록
- `wiki/pages/decision/model-stage-tiering.md:38` — `[!open] 구현 대기` 해소
- `wiki/index.md:26` — effort-global-xhigh 요약줄 동기화 (`:29` subagent-model-effort-tiering, `:20` claude-code-model-selection 도 대조)
- `wiki/pages/decision/subagent-model-effort-tiering.md:14` — `[!conflict]` 배너에 부분 복원 한 줄
- `wiki/log.md` — 변경 append(WIKI.md 규약 5)

# Rollback

- **되돌리기**: md·frontmatter 만이라 스키마·마이그레이션 없음 → 머지 커밋 단일 `git revert <merge-sha>` 로 전 파일 동시 복원.
- **비상 레버(revert 없이 즉시 무력화)**: `CLAUDE_CODE_SUBAGENT_MODEL=<alias>` env 가 frontmatter 보다 우선([[claude-code-model-selection]]:32) — 단 전 subagent 일괄이라 티어링은 사라진다. 현재 미설정(실측).
- **롤백 트리거**: 모델 선택은 로그·statusline 에 안 남아 관측 경로가 없다 → 아래 smoke 가 사실상 유일한 관측 수단.
- **반영 시점 주의**: 라이브 정의는 `~/.claude/agents/` 라 **머지 전엔 런타임 효과 0**, 반영 확인·롤백 확인 모두 **새 세션**에서 해야 한다(핫리로드 여부 미확인).

# Acceptance

| # | 충족 조건 | 검증 방법 | 통과 기준 |
|---|---|---|---|
| 1 | agents 4파일 frontmatter 가 의도한 모델로 고정 | `grep -n '^model:' agents/*.md` | reviewer 3종 `opus`, researcher `sonnet`, `inherit` 0건 |
| 2 | frontmatter 가 유효한 YAML·별칭 | `claude-code-subagent-config` 의 허용 별칭 대조 | `opus`/`sonnet` 은 문서상 유효 별칭 |
| 3 | 문서에 stale `inherit` 서술 없음 | `grep -rn 'model: inherit' README.md agents/ wiki/` | **현재 정책을 서술하는 문장에 0건**. 역사 문맥 1건만 잔존 허용: `effort-global-xhigh.md`(2026-07-04 결정 기록) |
| 4 | wiki 링크 무결 | 신규 `[[...]]` 대상 파일 존재 확인 | dead link 0건 |
| 5 | wiki index·log 동기화 | `grep` index:20/26/29 · log tail | 3개 요약줄이 현재 정책 반영, log 에 이번 변경 append(WIKI.md 규약 5 형식) |
| 6 | 레포 검증 통과 | `.github/workflows/lint.yml` 의 node --check / unit tests / python test 전량 | 전부 통과(이번 변경은 md 만 건드리므로 회귀 없어야 함) |
| 7 | **런타임 반영 smoke** (머지 후) | main 머지 후 **새 세션**에서 각 subagent 를 1회 spawn 해 자기 exact model ID 를 보고시킴 | reviewer 3종 = Opus 계열, researcher = Sonnet 계열. ⚠️ **이 worktree 에서는 원리적으로 불가**(라이브 정의는 `~/.claude/agents/`) → 머지 전 Report 에서는 "미검증"으로 명시, 완료 선언에 쓰지 않는다 |

# Blockers

(없음)

# Review Disposition

plan-reviewer(+codex 병행, 2026-08-06) — CONDITIONAL:
- `opus[1m]` 1M 상실 → **fix** (researcher 확인 후 결정, Decisions 반영)
- effort xhigh 사실오류 → **fix** (페이지 내 교정) + 페이지명 drift 는 **defer**(`# Deferred`)
- Acceptance 정적 grep 뿐 → **fix** (#7 런타임 smoke 추가, 머지 전 미검증 명시)
- `subagent-model-effort-tiering.md:14` 배너 누락 → **fix**
- Acceptance #3 "0건" 달성 불가 → **fix** (allowlist 기준으로 재작성)
- `index.md:24`→`:26` 오기 → **fix**
- rollback 절차 부재 → **fix** (`# Rollback` 신설)
- Opus 한도 소진 시 동작 ❌모름 → **fix** (researcher 조사 항목 4에 포함)
- dlc 검증 runner 커버리지 → **wontfix** (의도된 범위 밖 — Decisions 에 명시)
- `code-reviewer.md:25` 최소 수정 권고 → **fix** (문장 통째 교체 대신 `inherit`→`opus 별칭` 최소 수정)
- Codex: 정책 문장 4곳 동일 문구 통일 → **fix**

code-reviewer(2026-08-11) — REQUEST CHANGES, Major 6 / Minor 7:
- `effort-os-env-single-source.md:15` 동일 stale(`xhigh`·"OS env 없음") → **fix**
- `effort-global-xhigh.md` "런타임 모두 high" 반례(프로세스 실측 `max`) + 근본원인 미기록 → **fix** (문장 재작성 + `ps eww` 판정법 명시), bootstrap 스크립트 수정은 **defer**(운영 자산, `# Deferred`)
- wiki 편집 페이지 `updated`/`sources` 미갱신 → **fix** (5개 페이지)
- plan `# Next`/`# Progress`/`updated` stale → **fix**
- `CLAUDE_CODE_SUBAGENT_MODEL=inherit` no-op 함정 미기재 → **fix** (README + wiki 2곳)
- Opus 한도 소진 시 게이트 정지 경고가 자동 로드 표면에 부재 → **fix** (README 에 경고 절), CLAUDE.md §9 절차 추가는 **defer**(운영 자산 — 제안만)
- Minor: "위 warning"→"아래", availableModels 버전 조건, haiku 모순 전파 제거 + `[!conflict]` flag, `code-reviewer.md:25` 자기참조 제거, README 밀도 축약, 표기 통일 → 전부 **fix**
- Minor: researcher context 창 축소 우려(PLAUSIBLE) → **false-positive**. 근거: 2026-08-06 조사에 "On the Anthropic API, Fable 5, **Sonnet 5**, and Opus 4.7 and later always run with the 1M window" — Sonnet 5 도 네이티브 1M 이라 축소되지 않는다(`sonnet[1m]` 별칭이 따로 있는 것은 구세대 호환 표기).
- Minor: Acceptance #3 allowlist 과다 열거 → **fix** (실측 1건으로 정정)

# Deferred

- **wiki `effort-global-xhigh` 페이지명이 실제값과 어긋남** — 심각도 낮음(내용은 이번에 교정, 파일명만 잔존). rename 은 `wiki/index.md`·`log.md`·타 페이지의 `[[effort-global-xhigh]]` 링크 전수 수정을 동반해 별도 작업. 파일: `wiki/pages/decision/effort-global-xhigh.md`
- **`scripts/bootstrap/setup.sh:118`·`setup.ps1:156` 이 effort 단일소스를 깨뜨림** — **심각도 중**. 두 스크립트가 shell/User env 에 `CLAUDE_CODE_EFFORT_LEVEL=max` 를 심어 `settings.json`(`high`)을 이긴다(실측: claude 프로세스 env=`max`). [[effort-os-env-single-source]] 가 적립한 실패의 재발이고 **bootstrap 재실행마다 재주입**된다. 운영 자산 수정이라 별도 승인 필요(§1). 결정 필요: settings.json 을 진짜 단일 소스로 둘지(bootstrap 의 export 제거), 아니면 `max` 를 의도된 값으로 인정하고 settings.json·wiki 를 그쪽에 맞출지.
- **[[model-stage-tiering]] 의 haiku 배제 사유가 오류** — 심각도 낮음. "haiku 는 effort 미지원이라 제외"라 적었으나 [[claude-code-subagent-config]] 의 smoke 결과 Claude Code 가 haiku 의 effort 를 무시/제거해 정상 동작한다. sonnet 선택 자체는 조사 품질 근거로 별도 성립하므로 결론은 불변. 이번엔 `subagent-model-effort-tiering` 에 `[!conflict]` flag 만 걸고 원 페이지 수정은 미룸(사용자 승인 결정문). 파일: `wiki/pages/decision/model-stage-tiering.md:20`
- **CLAUDE.md §5/§9 에 "리뷰 게이트 모델 불가" 절차 부재** — 심각도 중. §9 는 Codex 미가용 시 생략만 규정하고, Opus 한도 소진으로 plan-reviewer/code-reviewer 자체가 실패할 때의 절차가 없다(이번 pin 이 새로 만든 리스크). README 에 비상 레버는 명시했으나 CLAUDE.md 는 운영 자산이라 자가 수정하지 않음(§1) — **제안만**: §9 에 "필수 게이트 subagent 가 API 오류로 실패하면 `CLAUDE_CODE_SUBAGENT_MODEL=<별칭>` 로 우회하고 그 사실을 Report/plan 에 기록" 한 줄.

# Workflow Findings

(없음)
