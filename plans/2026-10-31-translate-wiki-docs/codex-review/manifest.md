# wiki docs/codex-review 규칙 목록 (translate-wiki-docs)

공용 wiki 3eaa4f4 의 `docs/codex-review.md`(90줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다. 제목 줄은 check.json `headings` 가 고정한다.

## 머리말
- P.1 reviewer subagent(plan-reviewer / code-reviewer / architecture-reviewer)와 dlc 파이프라인이 codex 병행 검토를 호출할 때 따르는 단일 규약
- P.2 각 agent 정의에 흩어진 codex 호출 블록을 대체, 글로벌 CLAUDE.md §9 기준
- P.3 subagent 는 격리 컨텍스트라 이 파일을 자동으로 보지 않는다, 호출 측(agent 정의/dlc)이 절대경로를 명시 참조하거나 필요 시 Read

## 1. preflight
- A.1 순서대로 본다, 어느 단계든 생략이 결정되면 codex 병행을 생략하고 단독 진행, 출력에 `Codex 미가용: <사유>` 1줄
- A.2 agent 자체 검토는 계속(non-blocking — codex 실패가 리뷰를 막지 않는다)
- A.3 세션 마커 `<scratch>/codex-unavailable` 이 있으면 호출하지 않는다 — 사유는 파일 내용 그대로(`Codex 미가용: <내용> (세션 캐시)`)
- A.4 `<scratch>` 는 §3 의 세션 스크래치패드 절대경로(메인·subagent 가 같은 경로를 받는다)
- A.5 `codex --version` 실패(미설치 / PATH 없음)면 생략
- A.6 호출 뒤 출력이 한도·과금 오류면 마커를 쓰고 생략 — 한 세션 안에서 저절로 풀리지 않아 다음 reviewer 가 반복해 기다릴 이유 없음(2026-09-10 실측: plan-reviewer 가 `out of credits` 보고 뒤 같은 세션 code-reviewer 재시도), 마커 작성 명령(`printf … "workspace out of credits" > "<scratch>/codex-unavailable"`)
- A.7 한도 오류로 보는 출력(대소문자 무시, 하나라도 포함): `out of credits` · `insufficient_quota` · `usage limit` · `rate limit` · `429`
- A.8 환경 이슈(stdin hang·git-repo·sandbox)는 마커를 쓰지 않는다 — 다음 reviewer 는 다른 cwd·방식으로 성공할 수 있다
- A.9 마커는 스크래치패드와 함께 세션이 끝나면 사라진다(다음 세션은 다시 시도)
- A.10 사용자가 크레딧을 채웠으면 파일을 지우면 그 세션 안에서도 재시도
- A.11 호출 측(dlc)이 마커를 보면 reviewer 에게 §7 의 외부 codex 모드 문구를 주어 시도 자체를 건너뛴다

## 2. phase owner
- B.1 한 phase 에 reviewer 가 여럿이면(예: 구현 후 architecture-reviewer + code-reviewer 병렬) 호출 측(dlc)이 codex owner 1개만 지정
- B.2 owner 아닌 reviewer 에게는 호출 측이 프롬프트에 §7 문구("Codex review is already running externally. Do not invoke Codex.")를 넣는다
- B.3 그 reviewer 는 자기 codex 호출을 생략하고 출력에 "외부 codex owner 지정 — 병행 생략" 명시
- B.4 owner 기본 선택: 버그/보안 위주면 code-reviewer, 구조 위주면 architecture-reviewer, 계획 단계는 plan-reviewer
- B.5 arch 의 planning 모드는 항상 codex off

## 3. 호출 명령
- C.1 MUST — codex 는 Bash 도구로 호출
- C.2 `codex exec` 는 PROMPT 인자가 있어도 stdin 을 추가로 읽어 PowerShell 도구로 호출하면 `Reading additional input from stdin...` 에서 무한 hang(재현)
- C.3 무거운 작업 전 짧은 smoke test(≤60s)로 응답부터 확인, hang/사용량 초과 시 즉시 중단하고 단독 진행(출력에 `Codex 미가용: <사유>` 1줄)
- C.4 PowerShell 만 가용한 환경의 폴백은 §4
- C.5 read-only sandbox, ephemeral
- C.6 effort 는 작업 난이도별 차등(아래 표)
- C.7 reasoning 로그 노이즈는 `-c hide_agent_reasoning=true` 로 억제(결론 추출이 쉬워진다)
- C.8 프롬프트는 파일로, 명령은 짧게 — worktree 격리 세션의 네이티브 Bash 가드가 명령 텍스트에 `git` 이 들어간 형태(heredoc 본문의 `git diff`, `--skip-git-repo-check` 플래그명)를 거부하며 비결정적(wiki `worktree-isolation-bash-guard`, 2026-09-02 실측)
- C.9 비trivial 리뷰는 항상 worktree 에서 돌므로 정본이 그 가드를 피해야 한다
- C.10 `--skip-git-repo-check` 는 쓰지 않는다 — 리뷰는 git repo(worktree) 안에서 실행되므로 필요 없다
- C.11 cwd 는 repo(worktree) 루트여야 한다(플래그를 뺐으므로 필수 — 메인 세션은 Bash cwd 가 유지되니 앞선 `cd` 확인)
- C.12 절차의 `<scratch>` = 하네스가 시스템 프롬프트로 주는 세션 스크래치패드 절대경로 — 셸 변수가 아니다
- C.13 1 프롬프트를 `<scratch>/codex-prompt.txt` 에 쓴다
- C.14 Write 도구가 있으면 Write, reviewer subagent 처럼 없으면 Bash heredoc(`cat > … <<'PROMPTEOF' … PROMPTEOF`)
- C.15 Bash 로 만들 때는 본문에 `git` 토큰을 넣지 않는다(가드는 Bash 명령 텍스트를 보므로 Write 로 쓴 파일 내용엔 제약 없음)
- C.16 본문 골격: 도메인 특화 프롬프트 / 변경 파일·입력 번들·검토 관점 / 응답 영어·preamble 금지·Critical / Major / Minor 분류
- C.17 2 한 줄로 실행(2026-09-02·03 worktree 가드 활성 상태에서 통과 실증) — `codex exec --sandbox read-only --ephemeral -c 'model_reasoning_effort="medium"' -c hide_agent_reasoning=true - < … > … 2>&1`
- C.18 비-git 디렉토리가 대상이면 codex 가 뜨지 않는다(`--skip-git-repo-check` 는 그 경우를 여는 플래그지만 worktree 세션에선 플래그명이 가드에 걸린다) → §1 preflight 대로 병행 생략(출력 1줄)
- C.19 effort 차등은 호출 측이 phase 난이도로 지정
- C.20 표: 논의·질의·소규모 diff·문서·설정 검토 → `low`
- C.21 표: plan 리뷰 · 소규모 코드 리뷰 → `medium`
- C.22 표: 구현 후 code-reviewer 병행(브랜치 전체 diff) → `high` (2026-09-03 부터 repo pre-push codex 게이트를 대체하는 유일한 codex 코드 리뷰 — coin-trading-bot 은 게이트 제거)
- C.23 표: 보안·동시성·복잡 버그·대규모 구조 검토 → `high`
- C.24 표: 최심층(지원 모델 한정) → `xhigh`
- C.25 구현 후 리뷰의 범위는 브랜치 전체 diff — 프롬프트에 `git diff <base>...HEAD`(base = `origin/<default>` 또는 호출 측이 준 sha)를 명시하고 codex 가 read-only sandbox 안에서 직접 실행(번들 파일 목록만 주면 pre-push 가 잡던 범위 밖 결함을 놓친다)
- C.26 P0/P1 급(돈·데이터·보안) 결함을 먼저 보고하게 한다
- C.27 effort 는 항상 `-c model_reasoning_effort=...` 로 명시 — 생략하면 머신마다 다른 `~/.codex/config.toml` 값(없으면 codex 내장 기본값)이 적용돼 차등이 무너진다(높으면 토큰 샘, 낮으면 깊이 부족)
- C.28 `minimal` 은 일부 모델(gpt-5.5 등)에서 `web_search`/`image_gen` 툴과 충돌(400) → 실질 최저는 `low`
- C.29 `xhigh` 는 지원 모델(gpt-5.1-codex-max / gpt-5.2-codex / gpt-5.5 등) 한정, 미지원 모델은 자동 폴백 안 됨 → 호출 전 모델 확인
- C.30 `hide_agent_reasoning=true` 는 출력 노이즈 억제용 — reasoning 토큰은 줄지 않는다(과금 동일), 실제 절감은 effort 차등과 글로벌 AGENTS.md 슬림화 두 축뿐
- C.31 일부 codex 버전에서 무시될 수 있어(openai/codex#7090) 결론 추출은 §5 의 grep/tail 로 보장
- C.32 background 금지: 항상 foreground — background 실행이 메인 대화의 thinking block 을 손상시켜 `thinking blocks ... cannot be modified` API 400 을 유발한 전례
- C.33 도메인 특화 유지: 범용 "이 변경을 검토하라" 대신 해당 agent 의 검토 관점을 프롬프트에 박는다(codex 가 경고한 handoff drift 회피)

## 4. Windows / PowerShell fallback
- D.1 §3 의 Bash MUST 는 Bash 도구가 있을 때 전제 — 아래는 Bash 도구가 없고 PowerShell 만 가용한 환경 한정 폴백(§3 강제와 모순 아니라 양립)
- D.2 1차 폴백 — 파일 stdin: `Get-Content -Raw <file> | codex exec [opts] -`, PowerShell 은 `<` 입력 리다이렉션 미지원(about_redirection, PowerShell#1629)
- D.3 ⚠️ 파이프가 stdin 을 닫아 §3 의 hang 을 피하는지는 미검증(Windows 환경 미보유) — 첫 사용 시 smoke ≤60s 로 확인
- D.4 프롬프트 파일은 단일 인용 here-string `@'` … `'@`(closing `'@` 는 column 0)을 `Set-Content` 로
- D.5 출력 리다이렉트 `> file 2>&1` → `| Out-File -Encoding utf8 <file>`, stderr 는 별도, native exe stderr 를 `2>&1` 로 합치지 말 것(PowerShell 5.1 NativeCommandError)
- D.6 결론 추출 `grep` / `tail` → `Select-String` / `Select-Object -Last <N>`

## 5. 출력 처리
- E.1 codex 출력이 크면 결론부만 추출: `grep -E '^##? (Critical|Major|Minor|결론)' -A 30` 또는 `tail -300`
- E.2 raw 전체를 메인 컨텍스트에 넣지 않는다
- E.3 grep 결과에 같은 블록이 두 번 나오면(스트림 출력 + 최종 메시지 중복, 2026-09-03 실측) 뒤쪽 블록만
- E.4 출력 파일은 세션 스크래치패드(권장, §3 의 `<scratch>`) 또는 `/tmp`·`$env:TEMP`, repo 안에 쓰지 않는다(dirty 방지)
- E.5 codex 출력엔 reasoning/tool 로그가 섞일 수 있다, 최종 메시지 블록(마지막 `codex` 화자 이후)만

## 6. 통합
- G.1 codex 결과와 자체 검토를 "합의 / Codex 만 잡은 것 / 메인만 잡은 것" 으로 정리
- G.2 심각도 충돌 시 더 높은 쪽 채택 + 양쪽 근거 명시

## 7. 외부 codex 모드
- H.1 호출 측이 프롬프트에 "Codex review is already running externally. Do not invoke Codex." 를 넣으면 자체 codex 호출 생략
- H.2 이 문구가 유일한 방식 — 환경변수 경로(`CLAUDE_REVIEW_CODEX_MODE=external`)는 2026-09-26 폐기: Agent 도구는 subagent 에 환경변수를 넘기지 못하고 그 변수를 읽는 코드도 없었다
- H.3 호출 측이 §1 세션 마커를 이미 봤으면 프롬프트에 "Codex is unavailable in this session (<사유>). Do not invoke Codex." — reviewer 는 preflight 없이 생략, 출력엔 `Codex 미가용: <사유> (세션 캐시)`

## 다른 파일이 가리키는 표지
- 절 번호 §1~§7 — `agents/architecture-reviewer.md`(§1 preflight·§2·§3·§5·§7), `agents/plan-reviewer.md`·`agents/code-reviewer.md`("§7 문구"·"공통 규약 §3"·"§3 차등 표"), `skills/dlc/SKILL.md`("§7 문구"·"규약 §1"), CLAUDE.md §9(파일 이름). 번호·순서 그대로, 제목만 영어.
- §7 의 두 프롬프트 문구 "Codex review is already running externally. Do not invoke Codex." · "Codex is unavailable in this session" — dlc·agent 가 글자로 인용. 원래 영어, 그대로.
- 출력 줄 `Codex 미가용: <사유>` — dlc(한국어, 번역 중)가 reviewer 보고에서 `Codex 미가용: … out of credits` 를 찾는다. `Codex 미가용` 은 원문 유지, `<사유>`·`(세션 캐시)` 만 영어.
- 마커 파일 `<scratch>/codex-unavailable`·`<scratch>/codex-prompt.txt`·`<scratch>/codex-review.txt` — dlc·architecture-reviewer·README 가 이름으로. 그대로.
- §5 추출 명령 `grep -E '^##? (Critical|Major|Minor|결론)' -A 30` — 명령이라 글자 그대로(`결론` 포함).
- 본문 골격의 Codex 프롬프트 줄 — architecture-reviewer 의 영어 프롬프트("Changed files:"·"Input bundle:"·"Review checklist:"·"Reply: English. No preamble. Classify as Critical / Major / Minor.")와 같은 말로.
- §6 세 분류 — agent 출력 템플릿 필드(terms.md "Agreed items / Found only by Codex / Found only by this review")와 같은 말로.

## 핵심 문구
`<scratch>/codex-unavailable` · `codex --version` · `out of credits` · `insufficient_quota` · `usage limit` · `rate limit` · `429` · `Codex 미가용: <reason>` · (session cache) · "Codex review is already running externally. Do not invoke Codex." · "Codex is unavailable in this session (<reason>). Do not invoke Codex." · `CLAUDE_REVIEW_CODEX_MODE=external` · 2026-09-26 · `Reading additional input from stdin...` · ≤60s · `-c hide_agent_reasoning=true` · `--skip-git-repo-check` · `worktree-isolation-bash-guard` · `<scratch>/codex-prompt.txt` · <<'PROMPTEOF' … PROMPTEOF · `Reply: English. No preamble. Classify as Critical / Major / Minor.` · codex exec --sandbox read-only --ephemeral -c 'model_reasoning_effort="medium"' -c hide_agent_reasoning=true - < "<scratch>/codex-prompt.txt" > "<scratch>/codex-review.txt" 2>&1 · `git diff <base>...HEAD` · `origin/<default>` · `-c model_reasoning_effort=...` · `~/.codex/config.toml` · `minimal` · `web_search`/`image_gen` · gpt-5.1-codex-max / gpt-5.2-codex / gpt-5.5 · openai/codex#7090 · `thinking blocks ... cannot be modified` · `Get-Content -Raw <file> | codex exec [opts] -` · about_redirection, PowerShell#1629 · `| Out-File -Encoding utf8 <file>` · NativeCommandError · `Select-Object -Last <N>` · `grep -E '^##? (Critical|Major|Minor|결론)' -A 30` · `tail -300` · `$env:TEMP` · Agreed items · Found only by Codex · Found only by this review · CLAUDE.md §9
