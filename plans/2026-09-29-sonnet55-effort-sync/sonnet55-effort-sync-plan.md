---
title: sonnet55-effort-sync — 모델 버전 사실을 anthropic-claude-models 한 곳에 모으고 Sonnet 5.5·effort 저장값 제거를 반영
status: done
started: 2026-09-29
updated: 2026-09-29
---

# Goal
새 모델이 나오면 버전 *사실*은 wiki 한 페이지(`anthropic-claude-models`)와 index 요약 1줄만 고치고, 버전에 묶인 *결정*은 그 페이지의 "재평가할 결정" 목록을 보고 다시 판단하게 한다. 그 페이지에 Sonnet 5.5 출시를 반영하고, README·wiki 가 user settings 의 effort 저장값(2026-09-29 전부 제거)을 사실대로 적게 한다.

# Intent
- Problem: Sonnet 5.5 출시(2026-09-28)와 settings 의 `modelSettings` 제거(2026-09-29, 사용자 결정)로 README·wiki 가 낡았다. 원인은 "현재 별칭이 가리키는 버전"·"~만/~이상 모델 목록"을 여러 페이지가 반복해 적는 것 — 사용자 질문 "모델 새로 나올 때마다 갱신해야 하잖아?" 에 "한 곳에 모으기" 를 선택(2026-09-29).
- Constraints: 날짜 붙은 기록(`이후 변경(날짜)`·historical 콜아웃)과 lesson 페이지는 고치지 않는다. 기록·측정·결정 근거에서는 버전명을 별칭으로 바꾸지 않는다(별칭이 움직이면 무엇을 쟀는지 모호해진다). 외부 사실은 아래 `# Decisions` "원문 인용" 목록에 있는 것만 쓴다. M12 결정(`plans/2026-09-24-prompt-audit-apply`)의 존재·되돌리기 방법을 문서에서 지우지 않는다(lesson-verify-scaffold-purpose-before-removal 사례 2).
- Out of scope: `wiki/WIKI.md` 규칙 추가, README:506 `model` 키 서술, model-stage-tiering 본문 — 모두 `# Deferred`. settings.json 편집은 이미 완료(untracked — README:7, 이 브랜치 밖).
- Open questions: (열림) 세션 모델과 다른 모델로 고정된 subagent(researcher=sonnet·reviewer=opus)가 받는 effort 레벨 ❌ — 문서 없음, researcher 가 Sonnet 5.5(Claude Code 기본 `medium`, 레벨 재보정)로 바뀌어 무게가 커졌다. (열림) `switchModelsOnFlag: false` 에서 subagent 요청이 cybersecurity 플래그를 받으면 멈추는지·실패하는지 ❌ — researcher 는 CVE 조사 담당(`agents/researcher.md:3`). 둘 다 models 페이지 `[!open]` 으로 남긴다.
- 분할: 없음 — 목적 둘(Sonnet 5.5 반영·버전 사실 모으기 / effort 저장값 제거 반영)을 같은 문장이 함께 담는다: `README.md:285`·`effort-global-xhigh.md:21`·`claude-code-model-selection.md:40`·`index.md:40` 이 "Opus 5.5 `medium` 저장" 을 버전명과 함께 적어, 한쪽만 머지하면 그 문장이 버전명 제거 기준이나 설정 사실 중 하나와 어긋난다. models 페이지만 먼저 머지해도 다른 페이지가 "`sonnet` → Sonnet 5" 를 적어 wiki 가 서로 모순된다.

# Acceptance
1. `anthropic-claude-models` 가 Sonnet 5.5 를 반영한다: 라인업(ID·출시일·가격·캐시 읽기·1M·최대 출력·기본 effort API/Claude Code·최소 버전·은퇴 하한), Sonnet 5 legacy(은퇴 하한), 별칭 해석 표(provider 별, "v2.1.284+" 조건), native 1M 목록("Sonnet 5 이상"), `/effort` 변경 시 캐시 유지 목록, Sonnet 5.5 안전 분류기 폴백, 최상위 `effortLevel` 예외 인용 갱신, Haiku 5.5 미출시(09-29), "버전 사실은 이 페이지에만" + "출시 시 재평가할 결정" 링크 목록, `[!open]` 은 researcher 가 Sonnet 5.5 로 도는 사실은 해소하고 위 두 ❌ 로 좁힘, 섹션별 조회일(09-29 재조회분 vs 09-27 유지분), frontmatter `sources` 09-29 조회분. 검증: 새로 쓴 사실 하나하나를 `# Decisions` "원문 인용" 항목과 대조. 통과: 인용 없는 수치·주장 0.
2. `anthropic-claude-models` 밖에서 현재 별칭 해석·모델 목록·저장된 모델별 레벨을 버전명으로 적는 문장이 없다. 검증: `rg -n --hidden -e 'Opus [0-9]' -e 'Sonnet [0-9]' -e 'Fable [0-9]' -e 'Haiku [0-9]' -e modelSettings -e effortLevel -g '!plans/**' -g '!wiki/log.md' -g '!projects/**' -g '!.git/**' -g '!wiki/pages/entity/anthropic-claude-models.md' .` 전수를 분류. 통과: 모든 줄이 (a) 날짜 붙은 기록·측정·결정 근거 (b) 한 모델에 대한 고정 사실(그 모델 단가 등) (c) 예시(statusline) (d) 설정 키 이름 자체의 설명 중 하나.
3. README:285·README:516·`effort-global-xhigh` 현재 상태·`claude-code-model-selection` effort 절·index 40행이 적는 것: user settings 에 effort 저장값 없음 → 모델 기본값 / `/effort` 는 `modelSettings` 에 모델별 저장(Enter), 슬라이더 `s` 는 세션 한정 / M12(Opus 5.5 `medium`, 2026-09-24)는 기본값과 같아 2026-09-29 키 제거, 되돌리기는 Opus 5.5 세션에서 `/effort high` 저장 / 고정 subagent 레벨 ❌ 유지. 검증: 해당 절 읽기 + `python3` 로 settings.json 에 `modelSettings`·`effortLevel`·env `CLAUDE_CODE_EFFORT_LEVEL` 없음 확인. 통과: 문서의 effort 서술과 실제 effort 키 일치.
4. 손댄 wiki 페이지 frontmatter `updated: 2026-09-29`·`sources` 갱신, `wiki/index.md` 18·31·32·40행 동기화, `wiki/log.md` 항목 2개(단위별). 검증: diff. 통과: 누락 0.
5. `bash scripts/verify.sh` 마지막 줄이 `ALL PASS` 또는 `ALL PASS (skip: install-codex-skill.test.ps1)` — 그 skip 은 이 Mac 에 PowerShell 이 없어서이고 이 변경은 ps1 을 건드리지 않으므로 그 한 건만 "미검증"으로 보고한다. `python3 skills/wiki/check_links.py wiki` 통과. 검증: 격리 runner. 통과: 둘 다.

# Progress
- 2026-09-29: worktree 생성(base main@28375dc). 사용자 질문으로 범위 재설정 — "각 곳에 Sonnet 5.5 추가" → "한 곳에 모으기". settings.json 의 남은 `modelSettings` 3키 제거(사용자 선택, M12 plan 확인 후 — 3키는 M12 와 무관·기본값과 동일). model-config·prompt-caching·advisor 재조회. plan-reviewer CONDITIONAL(Codex 미가용 — 크레딧 소진) → 전 항목 처분(아래).
- 2026-09-29: 단위 1·2 구현·커밋. check_links clean, verify.sh `ALL PASS (skip: install-codex-skill.test.ps1)`(단위별 각 1회). A2 rg 43건 전수 분류 — 42건 (a)~(d)(`effort-global-xhigh` precedence 절은 historical 콜아웃 아래라 (a)), `wiki/index.md:18` 1건은 models 페이지의 index 요약줄이라 Goal 이 models 페이지와 함께 고치도록 명시한 범위(아래 Decisions). code-reviewer REQUEST CHANGES(Major 1·Minor 13, Codex 미가용) → 처분(아래), 공식 문서(model-config·prompt-caching·pricing) 재조회로 사실 확인 후 수정.
- 2026-09-29(보충): `claude-opus-5-5`(당시 `xhigh`) 키 삭제는 이 plan 착수 전, 같은 세션에서 "xhigh 저장값과 M12 medium 중 어느 쪽이 의도인가" 질문에 대한 사용자 결정("기본값이 medium 이면 settings.json 에서 뺀다")으로 먼저 했다(백업 scratchpad `settings.json.bak-20260929` 로 `xhigh` 확인). 남은 3키 제거가 위 첫 줄이다 — 문서의 "4개 키" 는 둘을 합친 수.

- 2026-09-29: 리뷰 반영을 단위별 fixup 으로 커밋(models → 단위 1, 나머지 → 단위 2; index 18행은 단위 1 줄이지만 index.md 를 두 단위가 고쳐 단위 2 fixup 으로 — 귀속 예외). simplify 체크: 문서 서술만 바뀌어 줄일 중복 없음(수정 없음). 격리 runner: verify.sh `ALL PASS (skip: install-codex-skill.test.ps1)`, check_links clean, A2 hit 43곳(위치 불변), settings effort 키 `False False False`. evidence gate A1~A5 충족 → DONE(머지 전이라 status 는 in_progress 유지).
- 2026-09-29: commit-check 적용(사용자 승인) — fixup 을 두 단위에 합치고 두 단위 메시지를 정정(m8·"실효 레벨은 그대로" 오류). 재구성 전후 tree 동일. Report 후 사용자가 `/e merge` 선택.
- 2026-09-29: `/e merge` — origin/main(6커밋 앞섬)을 브랜치에 merge, `wiki/log.md` 끝 append 충돌은 양쪽 항목 모두 유지(main 쪽 먼저). merge 뒤 verify.sh `ALL PASS (skip: install-codex-skill.test.ps1)`·check_links clean. PR #211.

# Next


# Decisions
- decision 조회: [[effort-global-xhigh]]·M12(`plans/2026-09-24-prompt-audit-apply`) — 따른다. 착수 시 Opus 5.5 키는 `xhigh` 로 M12 와 어긋나 있었고, 사용자가 M12(`medium`)를 택해 키를 지웠다 — 새 Opus 5.5 세션은 `xhigh` → `medium`(= 모델 기본값)으로 바뀐다(2026-09-29 사용자 결정: `modelSettings` 전부 제거). 이 plan 은 처음에 "실효 레벨은 그대로" 라고 적었다가 백업 대조로 정정(2026-09-29). [[model-stage-tiering]] — 따른다(별칭 고정 불변, 본문 수정 없음). [[lesson-verify-scaffold-purpose-before-removal]] — 따랐다: 키 제거 전 M12 plan 을 읽었다(M12 는 `claude-opus-5-5` 키만 만들었고 "다른 키 무변경", 나머지 3키는 M12 와 무관).
- 범위 변경 (이유: 사용자 질문 "매번 적어줘야 해? 모델 새로 나올 때마다 갱신해야 하잖아?" → AskUserQuestion 에서 "한 곳에 모으기" 선택, 2026-09-29): "7개 파일마다 Sonnet 5.5 추가" → "버전 사실은 anthropic-claude-models 에만, 나머지는 버전명 없이 링크".
- 낡는 문장의 기준 (plan-review 반영으로 개정): "현재 별칭이 가리키는 버전", "~만/~이상/대부분 모델 목록"(비교 괄호 포함), "현재 라인업", "저장된 모델별 레벨" → models 페이지에만. 단 공식 문서가 완전한 표를 유지하는 목록(advisor 허용 조합 표)은 옮겨 적지 않고 공식 문서를 링크한다 — 사본이 하나 더 생기는 것보다 정본 링크가 낫다. 두는 것: 한 모델에 대한 고정 사실(그 모델 단가), 날짜 붙은 기록, 측정·결정 근거의 버전명(별칭으로 바꾸지 않는다).
- A2 해석(리뷰 m1): `wiki/index.md:18` 은 models 페이지의 index 요약줄이라 Goal("wiki 한 페이지와 index 요약 1줄만 고치고")이 models 페이지와 같은 단일 위치로 둔 줄이다 — (a)~(d) 분류 대상이 아니라 A2 의 "anthropic-claude-models" 범위에 속한다. 통과 기준을 바꾸는 것이 아니라 Goal 과 A2 문구의 어긋남을 해석으로 맞춘 것(acceptance 문구는 그대로 둔다).
- WIKI.md:17 "entity — 버전/날짜 포함" 해석: 그 사실이 유효한 버전·날짜를 적으라는 뜻이지 라인업을 페이지마다 반복하라는 뜻이 아니다. 규칙 명문화는 `# Deferred`.
- M12 (plan-review 반영): 되돌리기는 이제 "키만 `high` 로 복원" 이 아니라 Opus 5.5 세션에서 `/effort high` 를 Enter 로 저장(키가 새로 생김). M12 의 `medium` 은 Claude Code 모델 기본값에 기대므로 기본값이 바뀌면 강제되지 않고, `opus` 가 새 모델로 넘어가면 M12 는 끝나며 새 모델은 새 effort sweep 이 필요하다.
- ⚠️ M12 의도가 이제 모델 기본값에 기댄다 — "M12 레벨 강제" 와 "사용자 결정: 저장 키 제거" 가 상충 — 사용자 결정을 택했다(현재 값이 같아 실효 차이 없음, 기본값 변경은 models 페이지 재조회 때 드러난다).
- 기각: `claude-opus-5-5: medium` 키만 남기기 — 지금 기본값과 같아 효과가 없고 사용자가 제거를 택했다; 기본값이 바뀌는 경우만 의미가 있는데 그건 위 ⚠️ 로 감수. 모델 목록을 다른 페이지에도 날짜와 함께 복제 — 다음 출시 때 여러 곳을 다시 고쳐야 한다(사용자가 제기한 문제 그대로). advisor 조합 표를 models 페이지로 옮기기 — 공식 표가 완전하고 계속 갱신된다.
- rollback: 문서와 설정은 함께 유지하거나 함께 되돌린다(문서만 revert 하면 "저장돼 있다" 로 돌아가 설정과 어긋난다). 설정 되돌리기는 `/effort` 재저장 — scratchpad 백업(`settings.json.bak-20260929`·`-20260929b`)은 세션 임시 디렉토리라 휘발성이다.
- 커밋 단위: 1) `docs(wiki): add Sonnet 5.5 and hold model-version lists in anthropic-claude-models` — anthropic-claude-models, index 18행, log 항목 2) `docs: stop repeating model versions and saved effort outside the models page` — README.md(285·516), effort-global-xhigh, claude-code-model-selection(22·25·30·40·46), claude-code-context-cost(20·28·36·51), index 31·32·40행, log 항목. 순서: 단위 1 커밋 후 단위 2 편집.
- 원문 인용 (A1 대조 목록, 2026-09-29 조회):
  - model-config: alias 표 — Anthropic API `opus` Opus 5.5 / `sonnet` Sonnet 5.5; Claude Platform on AWS Opus 5.5 / Sonnet 4.6; Amazon Bedrock·Google Cloud's Agent Platform Opus 5.5 / Sonnet 4.5; Microsoft Foundry Opus 4.6 / Sonnet 4.5. "`default`: Special value that clears any model override and reverts to the runtime default for your account". "`best`: Uses the model the `fable` alias resolves to where Fable is available to you, otherwise the same model as `opus`".
  - model-config: "On the Anthropic API, Fable 5.1, Fable 5, Sonnet 5 and later, and Opus 4.7 and later run with the 1M window on every plan, including Pro."
  - model-config: "The model's default effort: `high` on every model that supports effort, except that Opus 5.5 and Sonnet 5.5 default to `medium`, Opus 4.7 defaults to `xhigh`…"
  - model-config (전문 — 리뷰 M1 반영, 앞 발췌가 적용 범위를 잘랐다): "A top-level `effortLevel` in your user settings file doesn't count for Opus 5.5. That key is the older form `/effort` wrote before Claude Code saved levels per model: it keeps applying where it applied before, on Opus 5, Fable 5.1, and earlier models, while Opus 5.5 and models released after it start at their own default until you choose a level for them with `/effort` or the `/model` picker. A top-level `effortLevel` in project, local, or managed settings, or one passed with `--settings`, applies to every model." model-config 에 v2.1.284 미만 클라이언트의 `sonnet` 해석 문장은 없다(2026-09-29 확인) — 그 서술은 2026-09-27 조회 기록으로만 쓴다.
  - pricing: "Cache read (hit) | 0.1x base input price (0.025x on Claude Fable 5.1 and Claude Mythos 5.1; 0.05x on Claude Opus 5.5)".
  - prompt-caching (예외 전문): "This doesn't apply on Amazon Bedrock, Google Cloud's Agent Platform, or a Claude apps gateway, or when you set `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` or your organization has a HIPAA configuration." "Before v2.1.260, changing effort on Fable 5.1 with an API key or a Claude subscription also invalidated the cache."
  - model-config: "Claude Code saves the level per model, under the `modelSettings` key in your user settings"; "`Enter` … save the level as your default and apply it in later sessions"; "`s` in the `/effort` slider or the `/model` picker: apply the level to this session only. Requires Claude Code v2.1.257 or later".
  - model-config: "Sonnet 5.5 requires Claude Code v2.1.284 or later, and Opus 5.5 requires v2.1.280 or later." "Sonnet 5.5: cybersecurity-flagged requests re-run on Sonnet 5. Biology-flagged requests end with a refusal instead, because Sonnet 5.5 has no biology fallback model."
  - prompt-caching: "On Opus 5.5, Sonnet 5.5, and Fable 5.1 with an API key or a Claude subscription, changing effort keeps the cache… This doesn't apply on Amazon Bedrock, Google Cloud's Agent Platform, or a Claude apps gateway…"
  - advisor: "The advisor must be at least as capable as the main model."; 표 행 "Sonnet 5.5 or Sonnet 5 | Fable, Opus 4.7 or later, Sonnet 5 or later".
  - CHANGELOG 2.1.284(2026-09-29 조회, 커밋 28375dc 의 `[!open]` 에 인용): "Added Claude Sonnet 5.5 (`claude-sonnet-5-5`), now the default Sonnet model on the Anthropic API".
  - researcher(platform docs models overview·sonnet-5-5 overview·pricing·effort·model-deprecations, 2026-09-29): `claude-sonnet-5-5`, 2026-09-28 출시, $2/$10, 캐시 읽기 $0.20, 1M, 최대 출력 128K, adaptive thinking; effort 다섯 단계 모두 지원(xhigh·max 포함); API 기본 effort `high`, Claude Code·앱 `medium`; "Its levels are recalibrated, so a level doesn't produce the same amount of thinking as the same level on Claude Sonnet 5. Run a fresh effort sweep…"; "Start with `high` unless your workload is agentic or latency-sensitive. For agentic coding and multistep tool use, start with `medium` for well-specified tasks and move to `high` for harder or longer ones"; 은퇴 "Not sooner than September 28, 2027"; Sonnet 5 legacy, 은퇴 "Not sooner than June 30, 2027"; Haiku 5.5 "in the coming weeks"(미출시).
  - 로컬: `plans/2026-09-28-wiki-context-cost-lessons/analysis/mdtok.sh:5` 가 `claude -p … --model sonnet` 으로 CLAUDE.md 토큰을 쟀다. 그 표본의 Claude Code 는 2.1.239~2.1.283(context-cost sources)이고 Sonnet 5.5 는 v2.1.284+ 라 측정 모델은 Sonnet 5 ⚠️추정(측정 시점 버전 기록 없음).

# Key Files
- `wiki/pages/entity/anthropic-claude-models.md` — 버전 사실의 단일 위치(라인업·별칭 표·1M·캐시 유지·기본 effort·폴백·재평가할 결정)
- `wiki/pages/decision/effort-global-xhigh.md` — 현재 상태 콜아웃: 저장값 없음·M12 경위·되돌리기
- `wiki/pages/entity/claude-code-model-selection.md` — 22·25·30·40·46행
- `wiki/pages/entity/claude-code-context-cost.md` — 20·28·36·51행
- `README.md` — 285행(agents effort 해석)·516행(`/effort` 가 쓰는 키)
- `wiki/index.md`·`wiki/log.md` — 동기화

# Blockers
없음

# Review Disposition
- plan-reviewer 2026-09-29 (CONDITIONAL, Codex 미가용):
  - [강1] README:516 `/effort`→`effortLevel` 서술 누락 — fix(Key Files·A3 추가).
  - [강2] A2 검증 범위·방법 불일치 — fix(저장소 전체 rg 패턴·제외 경로 고정).
  - [강3] `[!open]` researcher 영향 처분 누락 — fix(사실 부분 해소, ❌ 두 개로 좁혀 `[!open]` 유지 + Intent Open questions).
  - [강4] A5 skip 없음 통과 불가(pwsh 부재) — fix(ps1 1건 skip 은 미검증으로 보고).
  - [강5] 기준 예외 모순(model-selection:30 advisor, context-cost:28 배수 괄호) — fix(advisor 는 공식 표 링크, 배수 괄호는 models 페이지 링크, 기준 개정).
  - [강6] A1 대조 원문 미보존 — fix(Decisions "원문 인용" 목록).
  - [약] 분할 근거·커밋 순서·M12 되돌리기·기각안·❌ 유지·A3 범위·sources·WIKI.md:17·Goal 과장·기록의 버전명 유지·Open questions·백업 휘발성·alias v2.1.284+ 조건 — fix(각 섹션 반영).
  - [약] 기준일 페이지 전체 과장 — fix(섹션별 조회일).
  - [약] README:506 `model` 키 서술과 실제 `"model": "opus"` 불일치 — defer(`# Deferred`).
  - ⚠️ self-flag(M12 가 기본값에 기댐) — accepted-risk(현재 값 동일, 사용자 결정).
- code-reviewer 2026-09-29 (REQUEST CHANGES, blocker 0, Codex 미가용):
  - [M1] models 의 최상위 `effortLevel` 서술에서 user settings 한정 누락(README:516 동일) — fix(원문 전문 재조회, project·local·managed·`--settings` 는 모든 모델 적용 인용 추가, README·effort-global-xhigh 의 "모든 모델이 기본값" 에 조건).
  - [m1] index:18 이 A2 (a)~(d) 밖 — fix(Decisions 에 Goal 기준 해석, Progress 정정).
  - [m2] "버전명 없이 링크" 규칙의 예외 누락 — fix(models 도입부·index 18).
  - [m3] "대부분 모델 0.1배" 소실 — fix(pricing 재조회 인용을 models 에 추가).
  - [m4] advisor 공식 표 링크가 본문에 없음 — fix(model-selection:30 에 URL).
  - [m5] index:40 되돌리기에 "Opus 5.5 세션에서" 누락 — fix.
  - [m6] models:32 "다른 현재 모델은 high" 기준 미표기 — fix("API 기준").
  - [m7] sources 가 가리키는 plan 이 untracked — fix(마무리 fixup 에 plan 포함).
  - [m8] 5ed1427 메시지 "holds those facts alone" 과장 — fix(commit-check 에서 reword 제안).
  - [m9] log 헤딩에 페이지명 없음 — fix.
  - [m10] "v2.1.284 미만 클라이언트 → Sonnet 5" 범위 과대·원문 없음 — fix(2026-09-27 조회 당시 v2.1.283 이하 기록으로 좁힘).
  - [m11] effort 캐시 유지 예외 불완전 — fix(예외 전문·v2.1.260 조건을 models 로, context-cost 괄호는 링크만).
  - [m12] "옛 저장 형식" 인용 미기재 — fix(원문 인용 목록·models 에 인용).
  - [m13] effort-global-xhigh precedence 절(historical)에 이후 변경 표기 없음 — defer(`# Deferred`).
  - [Nit] context-cost:51 "Bedrock 등 제외" 역해석 — fix(괄호 정리). effort-global-xhigh:25 "문서만 되돌리면" 모호 — fix. model-selection:20 `best` 서술 — fix(`opus` 와 같은 모델). index:18 조회일 — fix.
  - [Open] 3키 대 4키 — fix(Progress 보충: Opus 5.5 키는 착수 전 별도 결정). 이 확인 중 메인이 "실효 레벨은 그대로" 오류를 발견(백업상 제거 직전 `xhigh`) — effort-global-xhigh·log·plan 정정, 24828b9 메시지도 commit-check reword 대상.

# Deferred
- `wiki/WIKI.md` 에 "모델 버전·별칭 해석·모델 목록은 `anthropic-claude-models` 에만 적고 다른 페이지는 링크(공식 문서가 완전한 표를 유지하면 그 문서를 링크)" 규칙 + WIKI.md:17 해석 추가 제안 — 규칙이 없으면 다음 세션이 다시 복제한다(심각도 중, 운영 자산 성격이라 승인 후 별도 작업).
- README:506 이 settings `model` 을 "키 없음(핀 해제)" 으로 적지만 실제 `~/.claude/settings.json` 에는 `"model": "opus"` 가 있다(2026-09-29 확인) — 어느 쪽이 의도인지 확인 필요(심각도 하, README.md:506).
- `wiki/pages/decision/effort-global-xhigh.md` "## precedence" 절(2026-08-12 historical)은 현재형 문장인데 `modelSettings`·scope 별 `effortLevel` 적용 범위가 없고 인라인 "이후 변경" 표기도 없다 — 현재 precedence 는 models 페이지 effort 절 링크로 바꾸는 이후 변경 노트 제안(심각도 하, 리뷰 m13).
- 공용 wiki `worktree-isolation-bash-guard` 에 관찰 추가 제안: worktree 세션에서 rtk 가 재작성한 `git status`/`git add` 는 거부되고 `/usr/bin/git <cmd>` 단일 명령은 통과(2026-09-29, 심각도 하).
- §13 교훈 적립 제안(공용 wiki, 승인 후): (1) 설정 키를 지우며 "실효 레벨은 그대로" 라고 적기 전에 제거 직전 실제 값을 백업으로 확인한다 — 이 작업에서 요약만 보고 단정했다가 백업(`xhigh`)으로 정정. (2) 공식 문서를 발췌 인용하면 적용 범위 문장이 잘린다 — 사실 대조는 원문 전문으로(리뷰 M1). 기존 lesson 페이지에 사례로 붙일지 판정 필요(심각도 중).
