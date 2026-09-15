---
title: remove-codegraph-mcp — 성공 호출 0회인 codegraph MCP 와 그 자동화·문서 참조를 걷어낸다
status: in_progress
started: 2026-09-15
updated: 2026-09-15
---

# Goal
기록상 효용이 없는 codegraph MCP 를 Claude·Codex 양쪽에서 해제하고, 이 repo 의 자동화(wt init·bootstrap)와 문서에서 현재형 참조를 없앤다.

# Intent
- **Problem**: 매 세션 MCP 지침이 시스템 프롬프트에 주입되는 비용이 있는데, 보존된 로그상 성공 호출이 0회다 — Claude transcript 310개(2026-08-06~09-15, 그 이전 분은 보존기간으로 삭제) 실제 `tool_use` 7회 전부 `not initialized`/`No CodeGraph project is loaded` 에러, Codex 세션 627개(2026-06~07) 38회 중 결과 21건 전부 `user cancelled MCP tool call`·17건 결과 미기록. 2026-08-03 감사의 "30회 호출"(298 transcript)은 이 기간 밖이고 성공 여부를 세지 않았다 — "성공 0회"는 보존 기간 한정 사실이다. 현재 홈 depth 5 이내 어느 repo 에도 `.codegraph/` 가 없어 호출하면 반드시 실패한다. 사용자가 "제거"를 선택(2026-09-15).
- **Constraints**:
  - `settings.json` 은 `.gitignore` 로 추적 제외 → worktree 사본 없음. 허용목록 8줄 제거는 main 복귀 후 전역 파일 편집. main index 에 이 파일이 staged(`AM`)된 사용자 상태는 건드리지 않는다(`git restore --staged` 무확인 금지) — staged blob 에는 8줄이 남는다는 사실을 Report.
  - `~/.claude.json`·`~/.codex/config.toml`·`settings.json`·memory 는 git 밖 → **편집 전 `<scratch>/backup/` 에 백업**, 해제는 수동 편집 대신 CLI(`claude mcp remove codegraph -s user`, `codex mcp remove codegraph`).
  - memory `codegraph-projectpath-explicit` 은 gitignored 라 삭제 시 복구 불가 → 실측 근거를 retired wiki 본문으로 옮긴 뒤 삭제.
  - wiki 는 삭제가 아니라 retired 표기로 이력 보존([[headroom]] 2026-09-02 선례). `[[codegraph]]` 의 유일한 inbound 가 `headroom.md` 라 링크는 historical 형태로 남긴다(지우면 `check_links.py` orphan).
- **Out of scope**:
  - `plans/` 과거 plan 들의 codegraph 언급 — 당시 기록.
  - `scripts/session-brief.test.js` 의 slug fixture 문자열 `codegraph-wt-doc-fix` — 테스트 데이터.
  - `wiki/log.md` 과거 항목·`wiki/pages/decision/ops-doc-slimming.md` — 과거 기록.
  - 다른 머신(Windows 등)의 전역 등록 — 머신별 상태라 여기서 못 지운다. Report 에 수동 해제 명령만 안내.

# Progress
- 2026-09-15: 사용량 조사 → 사용자 "제거" 선택 → worktree 생성, Explore, draft plan → plan-reviewer CONDITIONAL(codex out of credits) → 지적 반영.
- 2026-09-15: 레포 내 편집 완료. Acceptance 1 통과(잔존 hit = retired codegraph.md·index:24·headroom:17,43), 2 는 retired 본문 59행에 삭제 파일명 1건 → 문장에서 파일명 제거 후 재확인 대기, 3 통과(임시 HOME 비교: 양쪽 exit 0, diff = codegraph 7줄 삭제뿐), 4 `ALL PASS`(skip 없음), 5 check_links clean. setup.ps1 은 pwsh 부재로 정적 대조만. code-reviewer 진행 중(codex out of credits).
- 2026-09-15: Acceptance 2 재확인 통과(0건). simplify 체크(diff 전체): `docs/worktree-lifecycle.md` §C 의 "idle 자동종료(~5분)"는 codegraph daemon 고유 성질이라 일반화된 점유 주체와 어긋나 "소유자 종료 안내"로 수정, rm-recovery §C 제목 "상세"→포인터 본문에 맞게 수정. §C 통째 삭제는 기각(파일 머리말·README 가 rm 실패 복구를 이 파일 내용으로 서술). 그 외 삭제 전용 diff 라 중복·죽은 코드 없음.
- 2026-09-15: code-reviewer(NEEDS DISCUSSION, blocker 0) 지적 전부 fix(1회차). 격리 runner 최종 검증 — Acceptance 1(잔존 hit = codegraph.md·index:24·headroom:17,43)·2(0건)·3(양쪽 exit 0, diff = codegraph 7줄 삭제)·4(`ALL PASS`, skip 없음)·5(check_links clean) 모두 관찰로 충족, 메인 판정과 불일치 없음. targeted 재리뷰(2회차) 진행 중.
- 2026-09-15: 2회차 APPROVE → Minor 1 fix(lifecycle §C "/e 한정·wt rm 제외" 구절), Nit 1 defer. 레포 변경분 evidence gate(Acceptance 1~5) 충족 → 커밋. Acceptance 6(전역)은 머지 후라 plan 은 in_progress 유지.

# Next
머지 경로 결정(사용자) → 머지 → 전역 단계(`<scratch>/global-backup.sh` → CLI 해제 → settings.json → memory → npm uninstall → `<scratch>/global-check.sh`).

# Decisions
- 2026-08-03 결정("이 repo `.codegraph/` 만 삭제, 전역 MCP 는 coin-trading-bot 실사용 70% 때문에 유지")을 **뒤집는다** (이유: 그 실사용처 coin-trading-bot 포함 어느 repo 에도 현재 `.codegraph/` 가 없고, 보존 로그상 호출은 전부 실패). 기각한 대안: (a) coin-trading-bot 프로젝트 scope 로만 MCP 유지 — 인덱스가 없어 여전히 실패하고 재인덱싱 의지도 기록에 없음 (b) 인덱스만 재생성하고 유지 — 코드 repo 에서 값을 한다는 증거가 0이라 비용만 되살림.
- wt 신규 생성 §3.6 셋업에서 codegraph init 단계를 없앤다.
- wt rm 파일 점유 분기를 lifecycle §C 회수 규칙 포인터로 바꾸던 결정을 "codegraph daemon 전제만 빼고 `wt rm` 은 자동 종료 안 함·안내 유지, 부분 성공만 lifecycle §C 포인터"로 변경 (이유: code-reviewer — `wt rm` 은 사용자가 직접 부르는 경로라 점유 프로세스를 이 세션이 띄웠는지 알 수 없고, lifecycle §C 의 식별 수단은 경로 필터뿐이라 사용자 서버를 확인 없이 죽일 수 있다. `/e` 7단계는 같은 세션이 띄운 프로세스라 회수 규칙이 성립). 원 결정: rm 실패 "파일 점유" 분기는 codegraph 문구만 빼지 않고 `docs/worktree-lifecycle.md` §C 규칙(내가 띄운 프로세스는 경로로 특정해 회수 / 남의 것은 자동 종료 안 함·안내)을 가리키도록 다시 쓴다 (이유: wt SKILL·rm-recovery §C 의 "자동 종료하지 않고 안내"는 점유 주체가 codegraph daemon(남의 것)이라는 전제의 규칙이라, 일반화하면 lifecycle §C 의 "내 것부터 회수"와 충돌한다. rm-recovery §C 는 본문이 전부 codegraph 라 포인터로 대체).
- `skills/wt/references/codegraph-worktree.md` 는 삭제한다(git 이 기억).
- bootstrap 은 codegraph 설치·MCP 등록·init 3단계와 그 판정 전용 변수(`mcp_list`/`$mcp`)를 제거하고, node 단계는 남긴다(hooks 가 `scripts/*.js` 로 node 의존 — 주석만 고친다).
- bootstrap 단계 번호는 재정렬하지 않는다 — 기각: 재정렬(diff 만 커짐). 번호를 참조하는 곳이 README·wiki 에 없어(grep 0건) 공백이 기능에 영향 없다.
- npm 전역 바이너리 `@colbymchenry/codegraph` 도 **전역 단계 마지막에 uninstall** 한다 (이유: 사용자 선택이 "제거"이고 `npm install -g` 한 줄로 복구 가능 — 처음 ⚠️추론으로 범위 밖에 둔 것은 의도를 좁게 해석한 것이라 변경). 이미 떠 있는 `serve --mcp` 프로세스는 세션 재시작 전까지 남는다.
- Acceptance 3 검증 방식을 실제 HOME dry-run → 임시 HOME 비교로 변경 (이유: 이 머신 baseline 이 exit=1 — `~/.agents/skills/jira-worklog` 가 링크가 아닌 실제 디렉터리라 3b 에서 조기 종료해 codegraph 단계(4·6·7)까지 도달하지 않는다. codegraph 무관한 기존 상태이며 고치지 않는다).
- 전역 단계 순서: 레포 머지 → 백업 → CLI 해제(Claude·Codex) → settings.json 허용목록 제거 → memory 근거 이관 확인 후 삭제·인덱스 줄 제거 → npm uninstall → Acceptance 6 → `status: done`.

# Acceptance
1. **현재형 참조 0**: `git grep -n -i codegraph -- . ':!plans' ':!wiki/log.md' ':!wiki/pages/decision/ops-doc-slimming.md' ':!scripts/session-brief.test.js'` 의 hit 이 다음만 남는다 — `wiki/pages/entity/codegraph.md`(retired 본문 전체), `wiki/index.md` 의 codegraph 요약 1줄(retired 표기), `wiki/pages/entity/headroom.md` 의 `[[codegraph]]` historical 링크(과거형 문장). 그 외 hit 0.
2. **삭제 파일 링크 무결**: `git grep -n 'codegraph-worktree.md' -- . ':!plans' ':!wiki/log.md'` 0건.
3. **bootstrap 동작**: `<scratch>/compare-setup.sh` — origin/main 판과 수정판 `setup.sh --dry-run` 을 같은 임시 HOME 에서 실행해 exit code 가 같고, 출력 diff 가 codegraph 3단계 줄 삭제뿐이며, 수정판 출력(`repo:` 줄 제외)에 `codegraph` 0건. `setup.ps1` 은 Windows 실행 불가 → 정적 대조만(미검증 명시).
4. **repo 검증**: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 있으면 그 축 명시).
5. **wiki 동기화·무결**: `entity/codegraph.md` 상단 `> [!note] Retired (2026-09-15)` + 근거 수치 + memory 실측 근거 이관, `wiki/index.md` 요약 retired, `wiki/log.md` 항목 추가, `uv run --no-project python skills/wiki/check_links.py wiki` 가 baseline 과 같이 clean.
6. **전역 해제(main 복귀 후)**: 백업 4종 존재, `claude mcp list` 에 codegraph 없음, `codex mcp list` 에 codegraph 없음, `~/.claude/settings.json` 에 `mcp__codegraph__` 0건 + `jq . ` 파싱 성공, memory 파일 부재 + `MEMORY.md` 에 codegraph 줄 0건, `command -v codegraph` 없음. 절감은 다음 세션부터(실행 중 세션엔 지침이 계속 주입).

# Key Files
- `skills/wt/SKILL.md` — 76행 §3.6 셋업 단계, 118행 rm §6 점유 분기
- `skills/wt/references/codegraph-worktree.md` — 삭제
- `skills/wt/references/rm-recovery.md` — 18행 §B 3단계, 20-22행 §C
- `skills/e/SKILL.md` — 112행 제거 실패 분기 요약
- `docs/worktree-lifecycle.md` — 47행 §C 점유 분기(정본)
- `scripts/bootstrap/setup.sh`(11·58·88-111행)·`scripts/bootstrap/setup.ps1`(27·69·103-129행)
- `scripts/bootstrap/README.md` — 60·62·63행 재현 대상 표
- 루트 `README.md` — 332(wt references)·381(bootstrap)·620(트리 주석)행
- `wiki/pages/entity/codegraph.md`·`wiki/index.md`·`wiki/log.md`·`wiki/pages/concept/worktree-per-task.md`(20·28행)·`wiki/pages/entity/headroom.md`(17·43행)
- 전역(백업 대상): `~/.claude.json`, `~/.codex/config.toml`, `~/.claude/settings.json`, `~/.claude/projects/-Users-jongyoonlee--claude/memory/{codegraph-projectpath-explicit.md,MEMORY.md}`

# Blockers

# Review Disposition
- plan-reviewer 2026-09-15 (codex: out of credits, 마커 기록)
  - Acceptance 2 제외 목록 오류(log.md:65) — fix
  - Acceptance 3 `repo:` 경로 오탐 + baseline 부재 — fix
  - wiki orphan 위험 + check_links 가 verify.sh 밖 — fix(Acceptance 5, headroom historical 링크 유지)
  - memory 복구 불가 — fix(근거 wiki 이관 후 삭제, 백업)
  - 전역 상태 rollback 부재 — fix(백업 + CLI)
  - 점유 분기 일반화 충돌 — fix(lifecycle §C 포인터)
  - 2026-08-03 결정 번복 사유·기각 대안 누락 — fix
  - bootstrap 부수 변수·node 주석 — fix
  - Key Files README 모호 — fix
  - staged settings.json 보고 — fix(Report 항목)
  - Acceptance 1 주관 판정 — fix(잔존 hit 열거)
  - 다른 머신·실행 중 세션 시나리오 — fix(Out of scope + Report 안내, Acceptance 6 명시)
- code-reviewer 2026-09-15 (codex: out of credits) — NEEDS DISCUSSION, blocker 0
  - Major(PLAUSIBLE) wt rm 에 "내가 띄운 것 회수"가 들어와 경로 필터만으로 사용자 서버를 확인 없이 종료 가능 — fix(wt rm 은 "자동 종료 안 함·안내" 유지, 부분 성공만 lifecycle §C 포인터)
  - Minor lifecycle:47 idle 자동종료 잔존 — fix(simplify 체크에서 선반영)
  - Minor wt SKILL·rm-recovery stderr 목록에 Windows "Invalid argument" 누락 — fix
  - Minor wiki "홈 아래 어느 repo 에도" 범위 과장 — fix("홈 depth 5 이내 탐색")
  - Minor wiki 가 머지 전 전역 조치를 완료형 서술 — fix("머지 후 전역 단계", Acceptance 6 참조)
  - Nit worktree-per-task `updated` 미갱신 — fix
  - Nit rm-recovery §C 제목·부분 성공 분기 혼입 — fix
  - Nit `[!open]` 조용한 삭제 — fix("측정 없이 retire 로 종결" 명시)
  - Open README bootstrap 도구 목록 jq 누락 — defer(# Deferred, 기존 drift)
- code-reviewer 2회차 targeted 2026-09-15 — APPROVE, 1회차 6건 resolved
  - Minor(PLAUSIBLE) lifecycle §C:47 회수 규칙에 "/e 한정·wt rm 제외" 명시 없음 — fix(한 구절 추가; fix loop 상한 도달이라 재리뷰 없이 메인 확인)
  - Nit(PLAUSIBLE) /e 도 경로 필터뿐이라 사용자 서버와 구분 한계 — defer(# Deferred, 이번 diff 이전부터)
- ⚠️ self-flag: 번호 재정렬 안 함 — resolved(기각 사유를 "참조처 없음"으로 정정). npm 바이너리 범위 밖 — resolved(마지막에 uninstall 로 변경).

# Workflow Findings
- 2026-09-15 `dlc-early-stop` doc-drift 경고 오탐: README.md·wiki/index.md 를 이 브랜치에서 이미 갱신했는데(`diff-stat` 에 둘 다 포함) "갱신되지 않았다"고 경고. 원인 미조사(⚠️추정: worktree 세션에서 판정 기준 경로가 main checkout 이거나, `rm`·Write 경로 편집이 ledger 에 안 잡힘).

# Deferred
- `scripts/bootstrap/README.md` 66행 "settings.json | repo 추적 파일이라 git clone 으로 따라옴" — `.gitignore` 로 추적 제외된 현재와 어긋남(문서 drift, 중). 이번 범위 밖.
- `/e` 7단계 점유 프로세스 회수가 경로 필터로만 대상을 식별 — 같은 worktree 에서 사용자가 띄운 서버와 세션이 띄운 서버를 구분할 수단이 "세션 기억"뿐이고, 점유 프로세스를 알리는 수단(Windows handle 도구 등)도 미서술(중). `docs/worktree-lifecycle.md` §C·`skills/e/SKILL.md`. code-reviewer 2회차 발견, 이번 diff 이전부터.
- 루트 `README.md` 381행 bootstrap 설명 도구 목록에 jq 누락(`setup.sh` 2b 단계는 설치) — 이번 변경 전부터의 drift(하). code-reviewer 발견.
