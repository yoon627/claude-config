# Review Disposition
- code-reviewer Major — status 항목을 `createdAt` 으로 정렬하라 했으나 `gh pr view --json statusCheckRollup` 은 그 키가 없고 생성 시각을 `startedAt` 으로 내보낸다(`api/export_pr.go`) — fix: `--jq` 식이 모든 항목을 `startedAt` 으로 정렬
- code-reviewer Major — 이름만으로 중복을 묶어 gh(check run 은 이름+workflow+event, status 는 따로)보다 느슨했다 — 다른 workflow 의 cancel 된 같은 이름 run 이 가려져 M6 로 갈 수 있었다 — fix: 키를 `[__typename, 이름 또는 context, workflowName]` 으로. event 는 `gh pr view` 가 내보내지 않아 맞출 수 없음을 규칙에 적었다
- code-reviewer Minor — check run 과 status 가 한 이름 공간으로 읽힐 수 있음 — fix: 키에 `__typename`
- code-reviewer 권고 — 문장 규칙 대신 결정적인 `--jq` 식 — fix(채택), 가짜 rollup 9개로 시험
- code-reviewer Minor — `--watch` exit 0 뒤 재조회에 `pending` 이 남는 경우가 주 경로 규칙에 없고(원래부터), 대체 경로는 그것을 일반 REJECTED 로 보내 "checks 대기" Task 대신 `# Blockers` 가 된다 — defer: 원래 있던 빈틈이라 이 수정 범위 밖, `# Deferred` 에
- code-reviewer Minor — 닫힌 목록의 ` / ` 구분이 새 문장에도 깨지지 않는가 — false-positive: 식 안의 `//` 는 ` / ` 와 다르고 코드 span 안이다. "the way gh computes buckets" 는 식 문장으로 바꾸며 없어졌다
- code-reviewer Minor — Acceptance 5 검색이 `index.md` 35줄("`--json` 재조회")을 놓친다 — fix: post-merge Task·Acceptance 5 에 추가
- code-reviewer Nit — 원문 표 파싱을 기각한 사유가 실제보다 강하다(`rtk proxy` 로 원문을 볼 수 있다) — wontfix: rtk 가 없는 머신에서는 `rtk proxy` 가 없어 분기가 생긴다. 구조화된 JSON 한 경로가 단순하다는 이유가 남는다
- code-reviewer Nit — README 350줄 "(exit code + bucket 재조회)" — wontfix: 여전히 맞는 요약

# Deferred
- `/e merge` M5 주 경로: `--watch` exit 0 뒤 재조회에 `pending` bucket 이 남는 경우(그 사이 새 check 가 등록됨)가 닫힌 목록에 없다 — "REJECTED (timeout)" 로 보내는 안(심각도 낮음, `skills/e/SKILL.md` M5) — code-reviewer
- rtk 가 있는 머신에서 `gh pr view <N> --json statusCheckRollup --jq …` 출력을 rtk 가 바꾸는지 미확인(이 머신에 rtk 없음) — rtk 머신에서 한 번 관찰(심각도 낮음 — 실패하면 REJECTED 로 안전하게 멈춘다)
