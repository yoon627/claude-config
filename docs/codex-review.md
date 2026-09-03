# codex-review — codex 병행 검토 호출 공유 규약

reviewer subagent(plan-reviewer / code-reviewer / architecture-reviewer)와 dlc 파이프라인이 codex 병행 검토를 호출할 때 따르는 **단일 규약**. 각 agent 정의에 흩어진 codex 호출 블록을 대체한다. 글로벌 CLAUDE.md §9 기준.

> subagent 는 격리 컨텍스트라 이 파일을 자동으로 보지 않는다. 호출 측(agent 정의/dlc)이 이 절대경로를 명시 참조하거나 필요 시 Read 한다.

## 1. preflight

- `codex --version` 성공 시에만 호출. 실패·실행 오류(미설치 / PATH 없음 / 사용량 한도 / 환경 이슈: stdin·git-repo·sandbox)면 codex 병행을 **생략**하고 단독 진행, 출력에 `Codex 미가용: <사유>` 1줄. **agent 자체 검토는 계속**(non-blocking — codex 실패가 리뷰를 막지 않는다).

## 2. phase owner (중복 호출 방지)

- 한 phase 에 reviewer 가 여럿이면(예: 구현 후 `architecture-reviewer` + `code-reviewer` 병렬) 호출 측(dlc)이 **codex owner 1개만** 지정한다.
- owner 가 아닌 reviewer 는 환경변수 `CLAUDE_REVIEW_CODEX_MODE=external` 를 받아 자기 codex 호출을 생략하고, 출력에 "외부 codex owner 지정 — 병행 생략" 명시.
- owner 기본 선택: 변경이 버그/보안 위주면 `code-reviewer`, 구조 위주면 `architecture-reviewer`, 계획 단계는 `plan-reviewer`. **arch 의 planning 모드는 항상 codex off.**

## 3. 호출 명령 (Bash 도구 — 1차 경로)

**MUST — codex 는 Bash 도구로 호출한다.** `codex exec` 는 PROMPT 인자가 있어도 stdin 을 추가로 읽어, PowerShell 도구로 호출하면 stdin 이 안 닫혀 `Reading additional input from stdin...` 에서 무한 hang 한다(재현). 무거운 작업 전 짧은 smoke test(≤60s)로 응답부터 확인하고, hang/사용량 초과 시 즉시 중단하고 단독 진행 + 사유 명시. (PowerShell 만 가용한 환경의 폴백은 §4.)

read-only sandbox, ephemeral. **effort 는 작업 난이도별 차등**(아래 표). reasoning 로그 노이즈는 `-c hide_agent_reasoning=true` 로 억제(출력에서 결론 추출이 쉬워진다).

**프롬프트는 파일로, 명령은 짧게** — worktree 격리 세션의 네이티브 Bash 가드는 명령 텍스트에 `git` 이 들어간 형태(heredoc 본문의 `git diff` 언급, `--skip-git-repo-check` 플래그명 자체)를 거부하며 비결정적이다(wiki `worktree-isolation-bash-guard`, 2026-09-02 실측). 비trivial 리뷰는 항상 worktree 에서 돌므로 정본이 그 가드를 피해야 한다. `--skip-git-repo-check` 는 쓰지 않는다 — 리뷰는 git repo(worktree) 안에서 실행되므로 필요 없다. **cwd 는 repo(worktree) 루트여야 한다**(플래그를 뺐으므로 이 전제가 필수 — 메인 세션은 Bash cwd 가 유지되니 앞선 `cd` 를 확인).

절차 (`<scratch>` = 하네스가 시스템 프롬프트로 주는 세션 스크래치패드 절대경로 — 셸 변수가 아니다):
1. 프롬프트를 `<scratch>/codex-prompt.txt` 에 쓴다. **Write 도구가 있으면 Write**, reviewer subagent 처럼 없으면 Bash `cat > <scratch>/codex-prompt.txt <<'PROMPTEOF' … PROMPTEOF`. **Bash 로 만들 때는 본문에 `git` 토큰을 넣지 않는다**(가드는 Bash 명령 텍스트를 보므로 Write 로 쓴 파일 내용엔 제약 없음). 본문 골격:
   - `<도메인 특화 프롬프트>`
   - `변경 파일: <diff --stat 또는 명시 범위>` · `입력 번들: <호출부 / 생성 경로 / 의존 방향 / 테스트 fixture 요약>` · `검토 관점: <해당 agent 관점>`
   - `응답: 한국어. preamble 금지. Critical / Major / Minor 분류.`
2. 한 줄로 실행(2026-09-02·03 worktree 가드 활성 상태에서 통과 실증):

```bash
codex exec --sandbox read-only --ephemeral -c 'model_reasoning_effort="medium"' -c hide_agent_reasoning=true - < <scratch>/codex-prompt.txt > <scratch>/codex-review.txt 2>&1
```

비-git 디렉토리가 대상이면 codex 자체가 뜨지 않는다(`--skip-git-repo-check` 는 그 경우를 여는 플래그인데 worktree 세션에선 플래그명이 가드에 걸린다) → §1 preflight 대로 **병행 생략 + 사유 기록**으로 결론짓는다.

- **effort 차등** (호출 측이 phase 난이도로 지정):

  | 작업 | effort |
  |---|---|
  | 논의·질의·소규모 diff·문서·설정 검토 | `low` |
  | 일반 코드 리뷰 · plan 리뷰 | `medium` |
  | 보안·동시성·복잡 버그·대규모 구조 검토 | `high` |
  | 최심층 (지원 모델 한정) | `xhigh` |

- **effort 는 항상 `-c model_reasoning_effort=...` 로 명시한다.** 생략하면 `~/.codex/config.toml` 기본값(현재 `xhigh`)이 적용돼 토큰이 최대로 샌다.
- `minimal` 은 일부 모델(gpt-5.5 등)에서 `web_search`/`image_gen` 툴과 충돌(400)하니 실질 최저는 `low`.
- `xhigh` 는 지원 모델(gpt-5.1-codex-max / gpt-5.2-codex / gpt-5.5 등) 한정. 미지원 모델은 자동 폴백되지 않으니 호출 전 모델 확인.
- `hide_agent_reasoning=true` 는 **출력 노이즈 억제용** — reasoning 토큰 자체는 줄지 않는다(과금 동일). 실제 토큰 절감은 effort 차등과 글로벌 AGENTS.md 슬림화 두 축뿐이다. 일부 codex 버전에서 무시될 수 있어(openai/codex#7090) 결론 추출은 §5 의 grep/tail 로 보장한다.
- **background 금지**: 항상 foreground 로 호출. background 실행은 메인 대화의 thinking block 을 손상시켜 `thinking blocks ... cannot be modified` API 400 을 유발한 전례가 있다.
- 도메인 특화 유지: 범용 "이 변경을 검토하라" 대신 해당 agent 의 검토 관점을 프롬프트에 박는다(codex 가 경고한 handoff drift 회피).

## 4. Windows / PowerShell fallback

§3 의 Bash MUST 는 **Bash 도구가 있을 때** 전제 — 아래는 Bash 도구 자체가 없고 PowerShell 만 가용한 환경 한정 폴백이다(§3 강제와 모순 아니라 양립):

- **1차 폴백 — 파일 stdin**: 프롬프트 파일을 만든 뒤 `Get-Content -Raw <file> | codex exec [opts] -`. PowerShell 은 `<` 입력 리다이렉션을 지원하지 않는다(파서가 예약어로 거부 — about_redirection, PowerShell#1629). ⚠️ 파이프가 stdin 을 닫아 §3 의 hang 을 피하는지는 **미검증**(Windows 환경 미보유) — 첫 사용 시 smoke ≤60s 로 확인.
- 프롬프트 파일을 PowerShell 로 만들 땐 단일 인용 here-string `@'` … `'@`(closing `'@` 는 반드시 column 0)을 `Set-Content` 로.
- 출력 리다이렉트 `> file 2>&1` → `| Out-File -Encoding utf8 <file>` (stderr 는 별도 처리; native exe stderr 를 `2>&1` 로 합치지 말 것 — PowerShell 5.1 은 NativeCommandError 로 감싼다).
- 결론 추출 `grep` / `tail` → `Select-String` / `Select-Object -Last <N>`.

## 5. 출력 처리

- codex 출력이 크면 결론부만 추출: `grep -E '^##? (Critical|Major|Minor|결론)' -A 30` 또는 `tail -300`. **raw 전체를 메인 컨텍스트에 넣지 않는다.** grep 결과에 같은 블록이 두 번 나오면(스트림 출력 + 최종 메시지 중복, 2026-09-03 실측) 뒤쪽 블록만 취한다.
- 출력 파일은 세션 스크래치패드(권장, §3 의 `<scratch>`) 또는 `/tmp`·`$env:TEMP`. repo 안에 쓰지 않는다(dirty 방지).
- codex 출력엔 reasoning/tool 로그가 섞일 수 있다. 최종 메시지 블록(마지막 `codex` 화자 이후)만 취한다.

## 6. 통합

- codex 결과와 자체 검토를 **"합의 / Codex 만 잡은 것 / 메인만 잡은 것"** 으로 정리. 심각도 충돌 시 더 높은 쪽 채택 + 양쪽 근거 명시.

## 7. 외부 codex 모드

- 호출 측이 `CLAUDE_REVIEW_CODEX_MODE=external` 설정 또는 프롬프트에 "Codex review is already running externally. Do not invoke Codex." 포함 시 자체 codex 호출 생략.
