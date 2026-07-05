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

read-only sandbox, ephemeral, git repo 체크 skip. **effort 는 작업 난이도별 차등**(아래 표). reasoning 로그 노이즈는 `-c hide_agent_reasoning=true` 로 억제(출력에서 결론 추출이 쉬워진다).

```bash
cd "<repo-root>" && codex exec --sandbox read-only --skip-git-repo-check --ephemeral \
  -c 'model_reasoning_effort="medium"' -c hide_agent_reasoning=true - > /tmp/codex-review.txt 2>&1 <<'CDXPROMPT'
<도메인 특화 프롬프트>
- 변경 파일: <git diff --stat 또는 명시 범위>
- 입력 번들: <호출부 / 생성 경로 / 의존 방향 / 테스트 fixture 요약>
- 검토 관점: <해당 agent 관점>
- 응답: 한국어. preamble 금지. Critical / Major / Minor 분류.
CDXPROMPT
```

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

- heredoc `<<'CDXPROMPT'` → 단일 인용 here-string `@'` … `'@` (closing `'@` 는 반드시 column 0).
- 출력 리다이렉트 `> file 2>&1` → `| Out-File -Encoding utf8 <file>` (stderr 는 별도 처리; native exe stderr 를 `2>&1` 로 합치지 말 것 — PowerShell 5.1 은 NativeCommandError 로 감싼다).
- 결론 추출 `grep` / `tail` → `Select-String` / `Select-Object -Last <N>`.
- 또는 프롬프트를 파일로 저장 후 `codex exec [opts] - < prompt.txt`.

## 5. 출력 처리

- codex 출력이 크면 결론부만 추출: `grep -E '^##? (Critical|Major|Minor|결론)' -A 30` 또는 `tail -300`. **raw 전체를 메인 컨텍스트에 넣지 않는다.**
- 출력 파일은 임시 위치(`/tmp/...` 또는 `$env:TEMP`). repo 안에 쓰지 않는다(dirty 방지).
- codex 출력엔 reasoning/tool 로그가 섞일 수 있다. 최종 메시지 블록(마지막 `codex` 화자 이후)만 취한다.

## 6. 통합

- codex 결과와 자체 검토를 **"합의 / Codex 만 잡은 것 / 메인만 잡은 것"** 으로 정리. 심각도 충돌 시 더 높은 쪽 채택 + 양쪽 근거 명시.

## 7. 외부 codex 모드

- 호출 측이 `CLAUDE_REVIEW_CODEX_MODE=external` 설정 또는 프롬프트에 "Codex review is already running externally. Do not invoke Codex." 포함 시 자체 codex 호출 생략.
