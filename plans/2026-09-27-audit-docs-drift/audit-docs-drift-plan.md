---
title: audit-docs-drift — Codex effort 서술·README --no-verify·RTK import·권한 규칙 한계·모델 사실(wiki·README 비상 레버)을 현재 상태에 맞춤
status: in_progress
started: 2026-09-27
updated: 2026-09-27
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

2026-09-25 감사의 문서 drift 5건과, 조사에서 드러난 같은 사실의 README 사본(비상 레버)을 현재 사실에 맞춘다. 코드·설정 동작은 바꾸지 않는다.

# Intent

- 묶음: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `audit-docs-drift` 단위(사용자 "이어서해" 2026-09-27).
- Problem:
  1. `docs/codex-review.md:61` 이 Codex 기본 effort 를 `xhigh` 로 적었으나 이 머신 `~/.codex/config.toml` 은 `low` — 머신별 값이라 문서가 현재값을 단정하면 틀어진다.
  2. README 의 `--no-verify` 실행 안내(`README.md:127` 후반·`:724`)가 행위자를 한정하지 않아 CLAUDE.md §8 "훅 차단은 우회 금지"와 충돌해 읽힌다.
  3. CLAUDE.md 끝의 `@RTK.md` 는 gitignored 파일을 가리킨다 — 사용자 결정: import 는 두고 README 에 한 줄.
  4. wiki 모델 서술이 Opus 5·Fable 5 를 현재처럼 적고, subagent 모델 우선순위·비상 레버가 v2.1.251 변경 전 상태다. 같은 비상 레버가 `README.md:285` 에도 있다.
  5. push 권한 규칙의 한계 문장(`README.md:478`)이 실제 규칙 목록과 어긋난다(인자 없는 `git push` 는 걸림, `git -C`·`--mirror`·`--all`·`--prune` 빈틈 누락).
- 델타(이 plan 만의 제약):
  - 공용 wiki(공개 repo)에 쓰는 모델 사실은 공식 출처로 확인한 것만. 인용은 원문을 본 것만, 벤치 수치는 vendor 발표라고 표시. 이 repo 결정에 쓰이지 않는 세부(provider 별 해석 전체·벤치 표 전체·Mythos 5.1)는 넣지 않는다.
  - decision 페이지: **당시 근거**는 보존하고 인접 `> [!note] 이후 변경(2026-09-27)` 로 가리킨다. **현재 상태 callout**(`effort-global-xhigh` 의 `[!note] 현재 상태`)은 제자리에서 갱신하고, **지금 따를 절차**(비상 레버)는 바로 옆 callout 으로 정정한다(WIKI.md 불변 규칙 — 모순은 `[!conflict]`). `rtk-rewrite-permission-rules` 의 "남은 한계" 절은 판단이 아니라 현재 사실 목록이라 직접 갱신한다.
- Out of scope: `settings.json`·`~/.codex/config.toml`·`agents/*.md` 등 설정·운영 자산 변경, `scripts/pre-commit-check.*` 동작·메시지 변경, 모델 전략 memory 수정. 발견한 운영 영향은 `# Deferred` 와 Report 로.
- 분할: 없음 — README 와 wiki 가 같은 사실을 나눠 가진다(`README.md:478` ↔ `rtk-rewrite-permission-rules` 한계 절, `README.md:285` ↔ `claude-code-model-selection` 비상 레버). 따로 머지하면 그 사이 두 문서가 서로 다른 사실을 말한다.

# Acceptance

1. codex effort: `docs/codex-review.md` 의 "effort 명시" 줄이 머신별 기본값을 단정하지 않고, 명시해야 하는 이유(phase 별 차등이 무너짐 — 높으면 토큰, 낮으면 리뷰 깊이)를 적는다. 검증: `grep -n "현재 \`xhigh\`" docs/codex-review.md` 0건, effort 표·모델 조건 줄은 그대로.
2. `--no-verify`: README 에서 실행을 안내하는 두 곳에 "사용자가 확인·판단한 뒤 터미널에서 직접 하는 복구이고 Claude 는 우회하지 않고 원인을 고치거나 보고 후 멈춘다(CLAUDE.md §8)" 단언이 있다. 부수 drift: 훅 경로는 `$(git rev-parse --git-path hooks)/pre-push`, 가드는 `.sh`/`.ps1` 둘 다, 검사 대상은 `plans/*.md`(다시 추적되면 `settings.json`). 같은 절의 `.ps1` 전용 서술(`README.md:114`·`:122`)도 맞춘다. 설명만 하는 언급(`:118`·`:306`·`:433`)은 그대로. 검증: 내용 단언(`grep -c "CLAUDE.md §8" README.md` 증가, 두 문단에 행위자 문구), `.git/hooks/pre-push` 리터럴 0건.
3. RTK: README CLAUDE.md 절 끝에 한 문단 — `RTK.md` 는 gitignored 라 rtk 를 설치한 머신의 main checkout 에만 있다. worktree 의 CLAUDE.md 사본에서는 import 가 비지만 사용자 전역 `~/.claude/CLAUDE.md` 가 같은 파일을 불러와 세션 효과는 같다. 빠지는 건 rtk 미설치 머신뿐(안내할 rtk 도 없다). 그래서 RTK.md 를 추적·복사할 필요가 없다. 검증: 문단에 이 세 단언이 있다.
4. 권한 한계: `README.md:478` 의 한계 문장을 실제 대조 결과로 교체한다 — `bash <script>`(재작성 없음), 대상 브랜치 이름 없는 push(인자 없는 `git push` 는 정확 일치 규칙에 걸리고 `git push origin`·`-u origin HEAD` 는 안 걸림), `git -C <dir> push`(rtk 0.44.2 가 `rtk git -C … push` 로 재작성 — 어떤 `rtk git push …` 규칙에도 안 맞음, 로컬 `Bash(rtk git *)` allow 가 있으면 그대로 통과), `--mirror`·`--all`·`--prune`(ask 없음). 백스톱: pre-push 가드(설치한 repo 만, `~/.claude` 면제, `--no-verify` 로 건너뜀), GitHub `main-guard`(관리자 bypass — 소유자 push 는 통과 표시만). `rtk-rewrite-permission-rules` 한계 절도 같은 내용으로. 검증: `~/.claude/settings.json` push ask 규칙 문자열 대조(값 출력 없음) + `rtk rewrite` 실측 기록.
5. 모델 사실(wiki): 교차 검증 결과(`wf_83e9d53b-c4e` journal 마지막 모델 결과의 `stale_claims`) 25건 — `anthropic-claude-models` 18·19·20·21·24·29·32·35·43, `claude-code-model-selection` 21·24·27·30·34·38·40·41, `model-stage-tiering` 24·26·38·42, `effort-global-xhigh` 21·46·47·50 — 을 정정·주석·기각 중 하나로 처분해 `# Review Disposition` 에 남긴다. 페이지 기준일 2026-09-27. Fable 5.1 최소 버전 불일치(2.1.255 대 2.1.257)는 `[!conflict]`. `/usage` 라벨 문장은 현 문서에 없어 삭제. Haiku 4.5 은퇴 하한(2026-10-15 이후) 한 줄. Sonnet/Haiku 5.5 는 "발표만, 2026-09-27 미출시" 한 줄 이하. index 요약 줄(`wiki/index.md` 의 해당 페이지 줄)도 재작성. 검증: 각 페이지 sources 에 공식 URL, `check_links.py wiki` clean, 공개 점검 스캔, log 항목.
6. README 비상 레버: `README.md:285` 를 v2.1.251 이후 사실로 — `CLAUDE_CODE_SUBAGENT_MODEL=<별칭>` 만으로는 frontmatter pin 을 못 덮고 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`(v2.1.257+)을 함께 줘야 하며, FORCE 는 researcher·빌트인 Explore/Plan 까지 덮는다. 또는 `agents/*.md` frontmatter 편집. 검증: 문단에 두 변수와 부작용 단언.
7. 검증: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), `node scripts/plan-lint.js <이 plan>` 통과, `bash skills/improve/improve.sh --ci` error 0.

# Progress

- 2026-09-27: 착수. 이해 단계 workflow `wf_83e9d53b-c4e`(모델 사실 조사 2갈래 → 교차 검증 1, 문서 항목 3갈래, 에이전트 6·오류 0). 모델: Opus 5.5(2026-09-22, $4/$20, 기본 effort medium)·Fable 5.1(2026-09-01)이 현재, Opus 5·Fable 5 는 legacy, Sonnet 5 가격 인상 취소($2/$10 확정), Haiku 4.5 은퇴는 2026-10-15 이후. 문서: 권한 한계 문장은 이미 있으나 부정확, `:127` 훅 경로가 linked worktree 에서 틀림.
- 2026-09-27: plan-reviewer(Codex 생략) CONDITIONAL — 강 5(README:285 범위 추가, RTK 문안, Deferred 신설, 25건 열거, decision 규칙 분리)·약 다수 반영. 핵심 사실 3개를 편집 전에 공식 문서 원문으로 재확인(subagent 모델 순위·FORCE·subagent effort 상속, Opus 5.5 기본 medium·Claude Code 의 `effortLevel` 미적용, Fable 5.1 v2.1.257 / Opus 5.5 v2.1.280). `rtk rewrite` 로 push 형태별 재작성 실측(rtk 0.44.2).
- 2026-09-27: 커밋 A `34e89fb`(README 가드·RTK·권한 한계, codex-review, rtk-rewrite 한계 절) · 커밋 B `776c40c`(wiki 모델 페이지 4개·index·log, README 비상 레버). 가격·라인업·권장 문구·advisor 는 편집 전 원문 재확인. verify ALL PASS·check_links clean.
- 2026-09-27: 리뷰 workflow `wf_9da65693-33d`(code-reviewer + 사실 반박 5묶음, 에이전트 6·오류 0) — code-reviewer REQUEST CHANGES: Major 1(리뷰어 effort 를 미결 회귀로 적음 — 실제로는 2026-09-24 M12 결정으로 `modelSettings` Opus 5.5 `medium` 이 저장돼 있음, settings 직접 확인) + Minor 다수. 사실 검증 61건 중 과장 8·반박 1(원문에 없는 인용). 전부 반영(아래 Disposition), `--hook-only` 의미와 전역 옵션 재작성은 실측으로 확인.

# Next

리뷰 반영분을 fixup 으로 커밋(README·index·log 는 두 단위가 함께 고친 파일이라 B fixup, codex-review·rtk-rewrite 페이지는 A fixup) → commit-check 로 합치고 B 메시지 정정 → 머지 방식 확인(`/e merge`).

# Decisions

- 커밋 단위: 2개(목적 기준) — 1) `docs: align README and codex-review with current guard and permission behaviour` — `docs/codex-review.md`, README 의 `--no-verify`·RTK·권한 한계 부분, `wiki/pages/decision/rtk-rewrite-permission-rules.md` 2) `docs(wiki): update model facts to the Opus 5.5 / Fable 5.1 lineup` — wiki 모델 페이지 4개·index·log, README 비상 레버(`:283-285`). 같은 README 파일을 두 커밋이 나눠 고치므로 README 는 부분 stage(`git add -p` 대신 편집 순서로 분리 — 커밋 A 편집을 먼저 끝내고 커밋한 뒤 B 편집). plan·intent 는 마지막 커밋에.
- 모델 사실은 교차 검증 결과 중 confirmed 이면서 편집 전 재확인한 원문을 우선한다. 공식 출처끼리 어긋나는 값(Fable 5.1 최소 버전)은 `[!conflict]` 로 둘 다.
- 결정의 재평가(리뷰어 effort, Fable advisor, 모델 배치 근거)는 사용자 결정 사항이라 이 plan 에서 하지 않는다(`# Deferred`, Report 질문).
- ⚠️ `git push origin`·`-u origin HEAD` 가 ask 에 안 걸린다는 판단은 규칙 문자열과 문서의 매칭 규칙(와일드카드·정확 일치)에서 추론했고 headless 실측은 없다 — README 에 "규칙 문자열 대조 기준" 으로 적는다. 재작성 형태는 `rtk rewrite` 로 실측.
- 기각한 대안: codex-review 에 "현재 `low`" 로 값만 고치기(머신마다 달라 다시 낡는다) · README 에서 `--no-verify` 안내를 삭제(fail-closed 가드의 사람 복구 절차가 사라진다) · RTK.md 를 whitelist 로 추적(rtk 가 다시 쓰면 diff, 사용자 결정으로 기각) · import 제거(rtk 설치 머신의 안내가 사라짐) · decision 페이지 본문 재작성(당시 판단의 근거가 지워져 재논의를 부른다).

# Key Files

- `docs/codex-review.md` — effort 명시 줄
- `README.md` — `:114`·`:122`·`:127`·`:249` 뒤·`:283-285`·`:478`·`:724`
- `wiki/pages/entity/anthropic-claude-models.md`, `wiki/pages/entity/claude-code-model-selection.md`
- `wiki/pages/decision/model-stage-tiering.md`, `wiki/pages/decision/effort-global-xhigh.md`, `wiki/pages/decision/rtk-rewrite-permission-rules.md`
- `wiki/index.md`, `wiki/log.md`
- `plans/2026-09-25-repo-audit-followups/intent.md` — `# Plans`

# Blockers

# Review Disposition

- [plan] 강 README:285 비상 레버 범위 밖 — fix(Acceptance 6).
- [plan] 강 RTK 문안이 세션 로딩과 어긋남 — fix(전역 CLAUDE.md 경유 로드, 빠지는 건 rtk 미설치 머신뿐).
- [plan] 강 `# Deferred` 없음·운영 영향 무음 — fix(아래 Deferred, Report 질문).
- [plan] 강 stale claim 25건 미열거·advisor 누락 — fix(Acceptance 5 열거, 처분은 편집 후 이 절에).
- [plan] 강 decision 규칙이 당시 근거와 현재 절차를 섞음 — fix(델타에 세 부류 구분, rtk-rewrite 한계 절은 직접 갱신).
- [plan] 약 Acceptance 2·4 의 `--no-verify` 개수 충돌·줄번호 밀림 — fix(내용 단언).
- [plan] 약 권한 빈틈 불완전(`--mirror`·`--all`·`--prune`, `git -C` 재작성) — fix(`rtk rewrite` 실측 포함).
- [plan] 약 커밋 분할이 디렉토리 기준 — fix(목적 기준 재배정).
- [plan] 약 `분할:` 근거·기각 대안 누락 — fix.
- [plan] 약 README:114·122 `.ps1` 전용 서술 — fix(Acceptance 2).
- [plan] 약 index 요약 줄 stale — fix(Acceptance 5).
- [plan] 약 공개 wiki 외부 사실 위험 — fix(델타: 원문 인용만·vendor 표시·Mythos 제외·`[!conflict]`·`/usage` 삭제·기준일).
- [plan] 약 핵심 사실 재검증을 편집 뒤에 둠 — fix(편집 전 원문 재확인 완료).
- [plan] 약 Haiku — fix(은퇴 하한 한 줄, pin 없음 확인). `claude-code-subagent-config` 의 Haiku effort 절 — defer.
- [stale 25] `anthropic-claude-models` 18·19·20·21·24 — fix(현재 라인업·legacy 로 재작성) · 29 — fix(Fable 5 v2.1.170 유지, 5.1 은 `[!conflict]`, `/usage` 라벨 삭제) · 32 — fix(2026-08 구도를 역사 기록으로, 현재 구도 추가) · 35 — fix(폴백 대상·`switchModelsOnFlag`) · 43 — fix(모델별 권장, 옛 인용 정정).
- [stale 25] `claude-code-model-selection` 21·24 — fix(alias·해석) · 27 — fix(Fable advisor 가능) · 30 — fix(우선순위 5단계 + project/managed·조직 기본값) · 34 — fix(v2.1.251 순서) · 38 — fix(native 1M 전 플랜) · 40·41 — fix(비상 레버 callout·FORCE).
- [stale 25] `model-stage-tiering` 24·26 — 주석(이후 변경 note, 결정 보존) · 38 — 주석(트리거 충족) · 42 — 주석(인접 note).
- [stale 25] `effort-global-xhigh` 21 — fix(현재 상태 callout 제자리 갱신 + M12) · 46·47·50 — 주석(인접 note).
- [code] Major 리뷰어 effort 를 미결 회귀로 적음(M12 누락) — fix(M12 결정·근거·되돌리기 기준을 effort-global-xhigh·README·index·log 에, 남은 ❌ 만 미확인으로).
- [code] 원문에 없는 인용("A subagent inherits the session effort level by default") — fix(frontmatter 표 원문으로).
- [code] effort 상속과 모델 기본값을 섞음 — fix(세션 모델이 Opus 5.5 일 때만 medium, 다른 세션 모델은 ❌).
- [code] RTK 조건(rtk 설치 머신) 틀림 — fix(`rtk init -g` 가 만든 경우만, bootstrap 의 `--hook-only` 는 RTK.md 없음 — `rtk init --help` 확인).
- [code] rtk-rewrite sources 항목이 backtick 으로 시작해 YAML 파싱 실패 — fix(따옴표, PyYAML 파싱 확인).
- [code] 빈틈을 `git -C` 로만 적음 — fix(전역 옵션 `-C`·`-c`·`--git-dir`·`--no-pager`, `rtk rewrite` 실측).
- [code] allow 통과가 wiki 에서 `git -C` 에만 적힘 — fix(백스톱 bullet 에 일반 문장).
- [code] README:290 inherit 문장 모순 — fix(FORCE 단독 = 메인 모델, inherit = 효과 없음).
- [code] README D 절: Windows 절에 macOS 블록을 넣고 macOS 절은 옛 경로·복구 안내 없음 — fix(Windows 절 원복, macOS 절에 훅 경로·사람 복구 안내).
- [code] plan 처분·Progress·Next 미기록 — fix.
- [code] nit Claude Code 에서 Opus 4.7 기본 `xhigh` — fix · nit sources 의 로컬 workflow ID — wontfix("researcher 조사(본 세션)" 선례와 같은 출처 표기, 비밀 아님) · nit codex config 키가 없을 때 — fix.
- [facts] 과장 8·반박 1(다른 모델 `high`, FORCE 단독의 Explore 상한, inherit 문장, 조직 기본값, effort 순서의 ultracode 전제, frontmatter effort 의 env·상한 제약, 원문 없는 인용, 리뷰어 medium 범위 2곳) — fix 전부.

# Deferred

- (확인 필요) 리뷰어 effort 는 2026-09-24 M12 결정(user settings `modelSettings` — Opus 5.5 `medium`, 나머지 `high`)의 범위 안이다. 남은 것은 M12 plan 이 ❌ 로 남긴 "세션 모델과 다른 모델로 고정된 subagent(예: Fable 세션의 opus 리뷰어)가 어떤 레벨을 받는가" — 문서에 없어 실측이 필요하다(`/tasks` 는 definition 이 `effort` 를 둘 때만 레벨을 표시). frontmatter `effort:` 를 둘지는 그 결과를 본 뒤 사용자 결정.
- (결정 필요) Fable-as-advisor 재평가 트리거 충족(`model-stage-tiering`), "Fable 이 확실히 이기는 구간" 근거 약화 — 모델 배치 결정과 모델 전략 memory 의 전제 재검토.
- (제안) CLAUDE.md §8 "main/master push 는 전역 `ask` — 매번 확인이 뜬다" 는 브랜치 이름 없는 push·`git -C`·`--mirror` 빈틈 때문에 과장 — 운영 자산이라 제안만.
- (제안) `scripts/pre-commit-check.sh:41,190`·`.ps1:69,212` 의 stderr `--no-verify` 우회 힌트 — 차단 시 Claude 가 읽는 문구라 §8 충돌 표면. 바꾸면 `pre-commit-check.test.sh:76,100` 도 함께.
- (낮음) README settings 절에 `switchModelsOnFlag` 미기재(사용자 settings 는 `false`) — README:472 규약상 drift.
- (낮음) `claude-code-subagent-config` 의 Haiku effort 절 — Haiku 4.5 은퇴(2026-10-15 이후) 뒤 낡을 후보.
