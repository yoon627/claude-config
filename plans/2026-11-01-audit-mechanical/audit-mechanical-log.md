# Review Disposition
- code-reviewer(REQUEST CHANGES, 2026-11-01)
  - Major `guard-worktree-edit.js` end 핸들러 catch-all 이 모든 예외를 조용한 allow 로 바꿔 테스트 하네스의 크래시 감지를 끈다(변형 실험: HEAD 가드는 13건 crash 감지, 새 가드는 0건) — fix: catch-all 을 빼고 `JSON.parse` 뒤 비객체 타입 검사만. [plan 대비] 바뀐 쪽: 코드·plan(Task 8·Decisions).
  - Minor lint.yml `apt-get install` 앞에 `update` 없음(GitHub 문서: 색인이 낡으면 실패) — fix.
  - Minor `verify-changed.test.sh`:71 네 번째 bare `mktemp` — fix: `|| exit 1`.
  - Minor `verify.sh` skipped= 정규식이 CRLF 출력(Windows python)에 안 맞음 — fix: `tr -d '\r'`.
  - Minor README Node 바닥 근거 오류(verbatimSymlinks 는 v16.15.0/v17.6.0, Node 18 은 EOL) — fix: 문구. README Python 문구가 `wiki_check.py` 의 3.9 동작과 모순 — fix.
  - Minor [plan 대비] Acceptance 9 "도구 부재만" vs 새로 드러난 케이스 skip — fix(plan). lint.yml 이 Task·커밋 단위에 없음 + `⚠️ (구현)` 미신고(매 CI 실행 zsh 설치) — fix(plan): Task 2·커밋 단위 2·Decisions.
  - Minor 머지 뒤 Codex 머신의 TOML 머리말 drift — fix(plan): [post-merge] Task.
  - Minor CI FAIL·skip 노출에 자동 테스트 없음 — fix: verify-changed.test.sh 에 shellcheck 없는 PATH 로 `CI=1`(rc 1 + FAIL) / `CI=`(rc 0 + [skip]) 케이스. skipped= 노출 테스트는 Deferred(skip 하는 python 테스트 fixture 가 필요).
  - Nit null 케이스가 stdout 빈 것을 안 봄 — fix. Nit "1 unittest cases" 복수형 — wontfix: Acceptance 2 의 문구와 같고 기계가 읽는 줄. Nit `CI=false` 도 CI 로 봄 — wontfix: `record-verified.test.sh:9` 의 기존 관례.

- 재검토(NEEDS DISCUSSION): PATH 제한 케이스가 Git Bash 에서 `ln -s` 복사본의 DLL 미발견으로 깨질 수 있음 — fix: 절대경로 exec 래퍼(`test_launcher.sh` 방식)와 절대경로 `sh`. Nit 자기참조 `printf` 링크 — fix: 절대경로 도구만. Nit README "가장 낮은 LTS" — fix: "모든 릴리스가 담은 가장 낮은 LTS 라인".

# Deferred
- `verify.sh` 의 `OK (skipped=N)` → SKIP 노출을 테스트로 고정(skip 하는 작은 python 테스트 fixture 를 verify-changed.test.sh 에 두는 안) — 심각도 낮음
- 공용 wiki `docs/codex-review.md` §5 grep 의 `결론` 을 지우면 terms.md 의 `결론` 행이 낡는다 — rules-align [post-merge] 에서 그 grep 을 고칠 때 terms.md 행도 함께(code-reviewer 열린 질문)
- `.zsh` 2개(`scripts/gwl.zsh`·`install-gwl.zsh`)는 첫 CI 실행이 첫 `zsh -n` 이다 — 빨개지면 문법 수정은 별도 커밋
