---
title: lesson-agent-hook-if-best-effort
category: decision
created: 2026-09-03
updated: 2026-09-03
sources:
  - coin-trading-bot PR #165 (`.claude/settings.json` agent hook 수정 + 민감파일 hook 교체)
  - https://code.claude.com/docs/en/hooks — `if` Bash 매칭 표("best-effort"), agent hook `ok`/`reason` 규약, `shell` 기본값
  - ~/.claude/projects/-Users-jongyoonlee-Repos-coin-trading-bot*/ 트랜스크립트 — 2026-08-04~09-03 agent hook 차단 40건(실제 `git commit` 3건), headless 검증 세션 hook stderr
---

# lesson-agent-hook-if-best-effort

Claude Code hook 의 `if` 필터는 **best-effort 매처라 게이트가 아니다**. `type: agent`/`prompt` hook 은 프롬프트 안에서 `tool_input` 을 보고 **자기 범위를 스스로 판정**해야 하고, 게이트 역할 hook 은 **플랫폼마다 실제 실행으로 fail-open 여부를 확인**해야 한다.

## 사례 (이 lesson 의 발단)
coin-trading-bot 의 커밋 전 6패턴 점검 hook(`type: agent`, `if: "Bash(git commit*)"`)이 2026-08-04~09-03 사이 40건을 차단했는데 실제 `git commit` 은 3건뿐이었다. 2026-09-02 code-reviewer 의 `codex exec` 병행 리뷰(전역 CLAUDE.md §9 필수)도 이 hook 이 "스테이징 diff 절차 밖"이라며 막았고, 그 빈자리를 pre-push codex 가 8라운드로 메웠다(가장 비싼 위치에서 나눠 잡음). 같은 파일의 민감파일 검사 hook 은 `shell: powershell` 이라 macOS 에서 `no PowerShell executable … found on PATH` 로 실패한 뒤 non-blocking 으로 **통과**하고 있었다 — `.pem`/`.env` staged 커밋을 아무것도 막지 않은 상태로 한 달.

## 근본 원인 (3 Whys)
1. **왜 커밋 아닌 명령에 발화?** docs 명시: 명령명 이상을 지정한 패턴(`git commit*`)은 `$VAR`·`$()`·backtick 이 든 명령에서 "판단 불가 → 보수적으로 실행"한다. heredoc 도 같은 취급이 실측됐다. `if` 는 프로세스 스폰을 아끼는 최적화지 hard gate 가 아니다("use the permission system rather than a hook to enforce a hard allow or deny").
2. **왜 발화가 차단으로?** 프롬프트가 "스테이징 .kt 없으면 빈 응답" 만 말하고 "이 명령이 커밋이 아니면 통과" 를 말하지 않아, agent 가 대기 중 명령을 절차 대비로 평가해 `ok:false` 를 냈다. 비결정적이라 같은 형태가 통과/차단 갈렸고, 그래서 "네이티브 worktree 가드" 로 오인됐다([[worktree-isolation-bash-guard]] 와 별개 기전).
3. **왜 fail-open 을 한 달 몰랐나?** hook 실패는 exit 1 = non-blocking error 로 조용히 지나가고, 커밋은 성공하므로 아무도 보지 않았다. PowerShell 포팅(Windows 에서 bash hook 이 안 돌아서)은 그 반대편 플랫폼에서 재실측되지 않았다.

## 올바른 방법
- `type: agent`/`prompt` hook 프롬프트의 **0단계는 항상 범위 자체 판정**: hook 입력(`$ARGUMENTS`)의 `tool_input.command` 가 대상 명령이면 점검, 아니면 즉시 `{"ok": true}` — "대상이 아닌 명령은 평가하지 말라" 를 명시. 출력은 docs 규약 `{"ok": true}` / `{"ok": false, "reason": "<한 줄>"}`(생 개행 금지).
- `if` 는 좁게 유지한다. `Bash(git *)` 처럼 넓히면 모든 git 명령마다 LLM 이 떠(명령당 +6초 실측) hook agent 의 `git diff` 가 자기 hook 을 재귀 발화시킨다. docs 표상 `cd x && git commit`·`$(git commit …)` 은 `git commit*` 도 서브커맨드로 잡는다.
- 게이트 hook(시크릿·파괴 명령 차단)은 **막혀야 할 케이스를 각 플랫폼에서 실제로 넣어 본다**(headless `claude -p --allowedTools Bash` 가 실제 트리거 경로). hook 실패는 통과다.
- `shell` 은 기본 bash, Windows 에서 Git Bash 미검출이면 PowerShell — 플랫폼 분기가 없으므로, 두 셸이 같은 문자열로 파싱하는 한 줄(`$`·backtick 없음)로 두고 로직은 `git -c alias.x='!…' x` 가 git 번들 sh 로 실행하게 하면 하나로 된다(PR #165, Windows 는 미실측).

## 연계
codex 병행 호출 규약은 [[codex-bash-invocation]], 격리 세션의 네이티브 거부는 [[worktree-isolation-bash-guard]], 반복 실패 추적은 [[workflow-failures]], 완료 게이트는 [[evidence-gate]].
