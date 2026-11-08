# Review Disposition
- plan-reviewer 1차(CONDITIONAL, 2026-11-07)
  - S1 2026-10-21 의 §8 이관 차단(ops-doc-slimming)을 plan 이 누락하고 같은 이관을 다시 계획 — fix: 이관 전부 기각, 자기 중복·절차 세부·이유 설명 삭제만.
  - S2 "절차 vs 규칙" 요지 판정은 검증 불가·오분류(L143·145-147·147 금지·L142·L50·§11 239-240·§5 78/81·wiki 목적지 행) — fix: 닫힌 검사 (a)~(d) + 로드 등급, 그 행들 keep.
  - S3 byte 게이트가 wiki 결정과 모순(14.6% > 11% 상한) — fix: 지표만(Acceptance 7).
  - S4 `rg` 검사의 거짓 통과 — fix: diff 기반 대응표 + 덮임 검사 + 변이 검사 + 독립 감사.
  - S5 세기 정의·판정자 없음 — fix: 정의(범위·양상·한정어·로드 등급)와 독립 subagent.
  - W1 고정 문구·hook 메시지 인용 — fix: Constraints 5. W2 README §5·§8 요약 — fix: 문서 Task. W3 분할 — fix: purpose-commit 2개(이관이 빠져 3→2). W4 가장 위험한 단계(이관) — 제거로 해소. W5 점검 3 양방향 — fix: `OK agent` 4줄 비교. W6 기각안 기록 — fix. W7 subagent 도 CLAUDE.md 소비자 — fix: (d) 에 포함. commit-check SKILL "91-99" 잘못된 범위 — fix: Task 에서 제거.
- plan-reviewer 재확인(CONDITIONAL, 2026-11-07)
  - 후보 행 판정: L49·L50 거짓양성 규칙·L78·L162·L182·L217 → keep(항상-켜짐 (c)/(d) 또는 §10 정본); L38·L134·L140·L145·L238·L265-266 → 괄호·세부만 축소; L22·L135·L141·L147·L160·L263·L264 → delete 가능 — fix: Task 2 재작성.
  - N1 인용 삭제 변이는 자명 통과 — fix: keep 목록 + 새 CLAUDE.md 재삭제 변이로 교체. N2 인용 줄 번호 오류 — fix: 대응표는 «인용» 으로. N3 커밋 2 가 작아진다 — accepted: 지표만, 사용자에게 미리 알림.
  - intra: 45↔250 형식 문자열 한 곳, 49 전부 유지(203 만 포인터), 184 의 PII 금지 유지 — fix.
- code-reviewer 1차(REQUEST CHANGES, 2026-11-07)
  - Major `check-dedupe.js` 가 "no/not/only/§숫자" 같은 짧은 단어 삭제를 못 잡음(≤2자 trivial, 행 원문의 부분 문자열 매칭) — fix: 줄마다 지워진 단어열과 그 줄 행들의 단어열의 정확 일치, trivial 은 문장부호만, 부정어·숫자 삭제 변이 72건.
  - PLAUSIBLE Major CLAUDE.md 커밋이 사용자 diff 확인보다 먼저 — 맞음(아래 Workflow Findings) — fix: 커밋을 패치로 보관하고 soft reset, 확인 뒤 재커밋.
  - Minor 203 "every item" 약화 — fix: "Done only when every item is met by evidence (§3-5, …)". Minor d5(대상 없음)·d10(로드 하강)·d2("expiry"·`bash <script>.sh` 누락) — fix(d5·d10 되살림, d2 문구). Minor plan Task 52행·Task 1 매핑 불일치 — fix. Minor 기본 base 를 merge-base 로 — fix. Nit 184 소문자 — fix(대시로 이어 붙임). Nit c:45 의 "CLAUDE.md §8(a)" 귀속은 설명이 빠진 뒤에도 규칙은 §8(a) 에 있어 무해 — wontfix.

# Workflow Findings
- 2026-11-07 CLAUDE.md 변경(규칙 문구)을 사용자 word-diff 확인 **전에** 커밋했다(7e14e80·db31bb9). §8 "확인·검증 안 된 변경은 커밋하지 않는다" 와 plan 의 "확인 → 커밋" 순서를 어겼다. 왜: 다른 단위에서 code-reviewer 승인 뒤 커밋하던 흐름을 그대로 탔고, CLAUDE.md 는 위임 예외 밖이라 확인이 먼저라는 것을 커밋 시점에 다시 보지 않았다. 처리: 커밋을 `git format-patch` 로 보관하고 `git reset --soft` 로 풀어 확인 뒤 재커밋. push 전이라 외부 영향 없음.

# Deferred

# Rule manifest
`check-dedupe.js --table` 출력(2026-11-07, 커밋 1·2 뒤). 남는 자리의 «인용» 은 스크립트가 파일에서 그대로 찾는다; keep.json 23구절은 새 CLAUDE.md 에 원문 그대로 있어야 하고 하나씩 지우면 검사가 FAIL 이어야 한다(변이 40건 중 생존 0).

| id | § | 옛 줄 | 지운 절 | 종류 | 남는 자리 «인용» | 남긴 포인터 |
|---|---|---|---|---|---|---|
| i1 | 8 | 133 | gitignored global state and non-git directories are excluded | intra | CLAUDE.md: «**Exception — global state with no worktree copy** (`projects/…/memory/`, `MEMORY.md`, `FE» | (exceptions — §3-1) |
| i2 | 11 | 230 | `rg`/Grep run from the `~/.claude` root skip this folder, so name the path | intra | CLAUDE.md: «`wiki/` in `~/.claude` (including the harness reference docs `wiki/docs/`) is ignored as w» | Read it by the absolute path `~/.claude/wiki` (§2). |
| i3 | 13 | 265 | The wiki is not injected automatically; the injected paths are the global feedback files (every repo's session | intra | CLAUDE.md: «Feedback lines and `MEMORY.md` index lines are injected every session (memory bodies are r» | in the layer §12 judges |
| i4 | 10 | 203 | Done only when every item is satisfied by evidence (run, observation, pass) (dlc evidence gate). | intra | CLAUDE.md: «**Non-trivial work is done only after the plan's `# Acceptance` items (§10) are checked ag» | Done only by evidence (§3-5, the dlc evidence gate). |
| i5 | 10 | 184 | pre-commit-check scans staged `plans/*.md` for tokens (+ the §8 rule against printing raw secrets) | intra | CLAUDE.md: «the `pre-commit-check` secret scan only looks at `settings.json` and `plans/*.md`» | (§8 — the pre-commit-check secret scan reads staged plans) |
| d1 | 1 | 22 | it picks axes from the changed files and skips unrelated slow tests, shown as `[slow]`; the full run is for CI | detail | skills/dlc/SKILL.md: «If the repo provides a command that picks axes from the changed files, use it (`bash scrip» | **`bash scripts/verify.sh changed`** |
| d2 | 2 | 38 | on Windows, `bash <script>.sh` detaches from the harness process tree and survives expiry and TaskStop | reason | /root/.claude/wiki/pages/entity/windows-bash-tool-orphan-processes.md: «Windows 에서 Claude Code Bash 도구의 작업을 시간 제한이나 TaskStop 으로 멈춰도, Git Bash(MSYS) 자식 프로세스는 끝나지 않» | (Windows: it survives TaskStop — [[windows-bash-tool-orphan-processes]]) |
| d3 | 3 | 50 | written in a main session; from a worktree session, after returning; from another repo's session, as a §11 pro | intra | CLAUDE.md: «Writes happen in a main session and are committed directly to that repo's main (§8 excepti» | (when it accumulates, to the shared wiki `workflow-failures.md` — §11) |
| d4 | 8 | 135 | since its purpose is to keep everything | detail | skills/e/SKILL.md: «- **Commit**: if safe, `git add -A`, then `git commit`. Message `wip: <one-line summary of» | The `/e` WIP checkpoint is the exception. |
| d5 | 8 | 140 | it is a plumbing reassembly, not a hook bypass with `--no-verify` | reason | (이유 설명 — 명령문은 그대로) | unpublished commits only, after user approval, code content unchanged. |
| d6 | 8 | 141 | work time is split by per-line `cwd`, so passing the name as an argument after returning to main also works | detail | skills/e/SKILL.md: «Attribution is by per-line cwd, so **even run after returning to main, the time of that wo» | So run `/e` step 6 before the step 7 deletion. |
| d7 | 8 | 145 | In a workflow that does not push, checking only against `origin/<default>` misjudges it as unmerged forever. | detail | skills/e/SKILL.md: «in a workflow that does not push, `inBase`, based on `origin/<default>`, stays false/unkno» | **a merge into local main counts too** |
| d8 | 8 | 147 | it bundles local and remote deletion and so bypasses the separate approval of (b), and where a worktree holds  | reason | skills/e/SKILL.md: «**No `--delete-branch`** (CLAUDE.md §8 — it bypasses the separate approval of remote delet» | **Do not use** `gh pr merge --delete-branch` **as a command**. |
| d9 | 9 | 160 | in PowerShell, stdin never closes and it hangs forever | reason | /root/.claude/wiki/docs/codex-review.md: «when it is called with the PowerShell tool, stdin never closes and it hangs forever» | **Always call codex with the Bash tool**. |
| d10 | 11 | 238 | the first line gives the wikis found and their page counts; on exit 2, read the reason on stderr | detail | skills/wiki/SKILL.md: «The first line lists the wikis found and their page counts; use it to confirm where it sea» | searches the shared wiki (regardless of cwd) and the current repo's wiki together. If there are no results or they miss, read the two `index.md` files directly |
| d11 | 13 | 263 | the same gate as "a voluntary recording trigger without approval was not adopted" in [[self-diagnosis-and-impr | reason | CLAUDE.md: «If it is a target, propose `/wiki ingest` (not automatic).» | (the same gate as the wiki ingest proposal of §11) |
| d12 | 13 | 264 | Comes with an `index.md` and `log.md` sync. | detail | skills/wiki/SKILL.md: «9. Register in `index.md` + append to `log.md` (`## [YYYY-MM-DD] ingest \| <title>`).» | **Details = a lesson page in the target layer's wiki (§11)** |


# Audit
- 독립 감사(2026-11-07, 17행): OK 15 · WEAKER 1(d5 — "plumbing 재조립, `--no-verify` 우회가 아님" 조정 문장이 어디에도 없어짐) · LOAD-DOWNGRADE 1(d10 — §11 이 skill 없이 돌리라는 `wiki_search.py` 의 첫 줄·exit 2 안내가 skill 에만 남음) · 미덮임 삭제 0 · keep 23구절 모두 있음 — 처분: d5·d10 되살림(대응표에서 제거, 15행), 184행 문장 첫 글자 대문자, d2 포인터에 "expiry" 복원.
- code-reviewer 재확인(APPROVE, 2026-11-07): 1차 항목 전부 종결, 탐침 6건 모두 FAIL. Minor 추가 단어 미검사 — fix: 바뀐 줄에 더해진 단어는 그 줄 행들의 포인터 단어 집합 안에 있어야 함(탐침 "push only on request, or when convenient" FAIL 확인). PLAUSIBLE 비슷한 두 줄의 짝짓기 오류 — accepted-risk(현재 바뀐 줄들은 서로 다르고, 짝 점수 하한 0.3; 재현 없음). Nit 변이 표본이 옛 줄 번호를 새 본문에 씀 — accepted-risk(줄 수가 같을 때만 정확 — 이번은 270/270; 줄이 늘고 줄면 표본이 어긋날 뿐 검사는 안 약해짐).
