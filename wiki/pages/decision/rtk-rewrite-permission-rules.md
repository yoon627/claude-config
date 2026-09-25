---
title: rtk-rewrite-permission-rules
category: decision
created: 2026-09-25
updated: 2026-09-25
sources:
  - https://code.claude.com/docs/en/hooks (PreToolUse updatedInput·permissionDecision)
  - https://code.claude.com/docs/en/permission-modes (auto 모드 평가 순서)
  - headless 실측 2026-09-25 (Claude Code 2.1.281~2.1.282, rtk 0.44.2)
  - plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md (감사 hooks-01~03)
---

# rtk-rewrite-permission-rules

**명령을 재작성하는 PreToolUse 훅이 있으면 권한 규칙은 재작성된 명령으로 평가된다.** 이 repo 는 rtk 훅이 git/gh 명령을 `rtk git …`·`rtk gh …` 로 바꾸므로, ask 규칙을 원래 형태로만 두면 한 번도 걸리지 않는다. 그래서 ask 규칙은 원래 형태와 `rtk ` 접두 형태를 함께 둔다(2026-09-25).

## 외부 사실 (✅ 공식 문서)

- hooks 문서: 훅이 `updatedInput` 을 돌려주면 Claude Code 는 *"evaluates permission rules … against the input your hook returns, not the input Claude sent"*. 훅의 `permissionDecision: "allow"` 는 확인 창을 건너뛰지만 *"Deny and ask rules are still evaluated"*.
- permission-modes 문서(auto 모드 평가 순서): 1단계에서 allow·ask·deny 규칙에 맞는 동작은 **분류기보다 먼저 즉시 결정**된다. ask 규칙은 auto 모드에서도 확인 창을 띄운다(*"If an explicit ask rule matches the command, Claude Code asks you even in auto mode"*). auto 모드에 들어갈 때 버려지는 allow 는 `Bash(*)`·와일드카드 인터프리터·패키지 매니저 run·Agent·Monitor 뿐이라, `Bash(rtk git *)` 같은 넓은 allow 는 그대로 살아 분류기 검토 없이 통과시킨다.
- 권한 규칙이 벗겨내는 래퍼(timeout·nice·nohup 등)에 `rtk` 는 없다.

## 무엇이 뚫려 있었나 (✅ 실측, 2026-09-25)

- `rtk hook claude` 에 payload 만 넣어 확인: `git push …`·`git branch -D`·`git checkout -- .`·`gh pr merge --delete-branch`·`gh api -X DELETE …`·`gh repo delete` 가 전부 `rtk …` 로 재작성됐다. push 를 뺀 나머지에는 rtk 가 `permissionDecision: "allow"` 까지 붙였다 — `settings.local.json` 의 allow 규칙(`git branch *`·`gh api *` 등)을 자체적으로 비춰 보는 것으로 보이며, home 파일(`~/.claude/settings.local.json`)의 `gh api *`·`gh repo *` 는 다른 repo 에서도 allow 가 나왔다.
- headless `claude -p --permission-mode default` 로 수정 전 세션에 `git push --dry-run origin main`·`git branch -D <없는 브랜치>`·`git checkout -- <없는 파일>` 을 시키면 **셋 다 확인 없이 실행**됐다(`permission_denials` 비어 있음). ask `Bash(git push * main*)` 대신 repo-local allow `Bash(rtk git *)` 가 맞았다.

## 결정

- `settings.json` ask 를 10건 → 72건. 파괴적 명령(원격 삭제·force·main push·`-D`·작업트리 폐기·토큰 출력)마다 원래 형태 + `rtk ` 형태. ask 는 allow 보다 먼저 평가되므로 넓은 `rtk git *` allow 는 일상 명령 편의를 위해 남겨 둬도 된다.
- gh 는 원격 쓰기가 많아 allow 자체를 읽기 전용(`gh pr view/list/checks/diff`, `gh repo view`, `gh run list/view`, `gh auth status`)으로 좁혔다. `gh auth *`·`env`(토큰 출력)는 allow 에서 뺐다.
- 기각: `rtk git *` allow 를 없애고 git 을 전부 분류기에 맡기기 — 파괴적 명령의 "항상 확인"(CLAUDE.md §8(b))은 분류기가 아니라 ask 로만 보장되므로 어차피 ask 목록이 필요하고, allow 를 지우면 일상 git 명령만 느려진다.
- 수정 후 같은 headless 실측: 파괴적 5종(`main` push·`HEAD:main` push·`-D`·`checkout --`·`gh api -X DELETE`)은 `permission_denials` 로 거부, 일상 4종(`git status`·`git branch -d`·`gh pr list`·기능 브랜치 dry-run push)은 통과. 대화형 auto 모드에서 main push 에 확인 창이 뜨는 것도 사용자가 확인했다.

## 남은 한계 (⚠️)

- `bash <script>` 로 실행하면 규칙은 `bash …` 만 본다 — 스크립트 안의 명령은 패턴에 보이지 않는다(CLAUDE.md §2 가 긴 명령을 스크립트로 빼라고 권하므로 흔한 경로다). auto 분류기가 스크립트 내용을 읽는지는 ❌모름.
- main 에서 `git push -u origin HEAD` 처럼 브랜치 이름이 없는 push 는 패턴으로 가를 수 없다.
- 규칙을 새로 만들 때 rtk 가 그 명령을 재작성하는지 `rtk hook claude` probe 로 먼저 본다. 재작성 대상 목록은 rtk 버전마다 바뀔 수 있다([[lesson-stale-tool-version]]).

## 연계

승인을 어디에 걸지는 [[risk-based-approval]], 훅 조건이 게이트가 아니라는 교훈은 [[lesson-agent-hook-if-best-effort]], worktree 세션의 git 명령 거부는 [[worktree-isolation-bash-guard]].
