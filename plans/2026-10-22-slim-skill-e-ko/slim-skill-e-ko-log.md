# Review Disposition
plan-reviewer (2026-10-24, CONDITIONAL, Codex CLI 미설치) — 리뷰 뒤 사용자가 압축을 폐기해(2026-10-24) 대부분은 번역 단계로 넘긴다:
- 강한 S1, 계획한 R.7 수정이 "merged 는 확정이 아니니 근거를 보여 주고 택하게" 라는, 이 줄에만 있는 규칙을 지운다(e230de0 이전 목록의 조건5 = merged 신호) — fix: Decisions 에 새 문장을 적고 그대로 고침.
- 강한 S2, manifest 가 한정어를 빠뜨렸다(7.2 "경로 표기는 2단계와 같다", M2 "외부 쓰기 없음", M4 "전부", B.5 "git/파일로 확인된 것만", T.4 "안전하면", MM.4c "Skill 도구로", 6.4 PowerShell 형태) — defer: 압축 폐기로 이 PR 에선 조항이 바뀌지 않는다. 번역 단위(translate-repo)가 이 manifest 를 대조표로 쓸 때 보강한다.
- 강한 S3, 표지 목록이 인용하는 파일·글자 그대로 라벨을 빠뜨렸다(jira-worklog SKILL 103행 "6단계", test_exit_contract.py 의 «등록 불가», worktree-lifecycle 7·35행, bash-guard wiki, README 353·354행, skills/c 60·74행) — defer: 번역 단위에서 보강(이 PR 은 한 줄만 바꾸고 그 줄을 인용하는 곳은 없다).
- 강한 S4, 파일 안의 상호 참조(약 30개)를 검사하지 않는다 — defer: 번역 단위의 Acceptance 에 "내부 참조가 그대로 풀린다" 를 넣는다(intent Open question 이 아니라 각 translate-repo plan 의 항목).
- 약한 W1, 핵심 문구 세트에 안전 문구가 빠졌다 — defer: 번역 단위.
- 약한 W2, 6.3c "유일한 사본" 전제가 틀렸다(slim-rules-ko 의 최종 locations.txt 는 8.m5 를 CLAUDE.md §8 에 남겼다) — fix: plan 에서 그 전제를 뺐다.
- 약한 W3, README 판단이 없다 — fix: Decisions 에 "바꿀 것 없음" 과 doc-drift 경고 처리.
- 약한 W4, ①②③ 을 1)2)3) 으로 — wontfix: 이 PR 범위 밖, 번역 단위가 다시 쓴다.
- 약한 W5, 경계 절에만 있는 조항 — defer: 번역 단위.
- 약한 W6, "짧게 유지" 이유 줄이 위치 검사 밖 — defer: 번역 단위.
- 약한 W7, 가장 위험한 구간(MM·7·R)의 게이트 문장 — fix: 압축 폐기로 해당 없음. 번역 단위에 "게이트 문장은 뜻 대조를 줄 단위로" 를 넘긴다.
- 약한 W8, `worktree-lifecycle.md` §B 의 조건 번호(4·5 merged, 6 산출물)가 SKILL 의 조건 1~6 과 다르다 — defer: 아래 Deferred.
- 약한 W9, Goal 의 "7월 PR #89~92 로 §E" 사실 오류·intent `updated`·선행 plan 체크의 Decisions 줄 — fix: Goal 을 고쳐 쓰며 그 문장을 뺐고, intent `updated` 갱신, Decisions 에 선행 plan 체크 근거.
- 약한 W10, skills/e 본문을 읽는 테스트 없음 — 확인만(조치 없음).

# Deferred
- [post-merge] 공용 wiki `docs/worktree-lifecycle.md` §B 의 조건 번호를 skills/e 7단계의 조건 1~6 과 맞춘다(§B 는 4·5 를 merged, 6 을 미보존 산출물로 세고 점유 프로세스 조건이 없다) — main 세션에서(plan-reviewer W8).
- 번역 단위(translate-repo)에 넘길 것: 이 plan 의 manifest(+ 리뷰 S2·S3·W1·W5·W6 보강), 내부 상호 참조 검사(S4), 게이트 구간(머지 모드·7단계·정리 규칙)은 뜻 대조를 줄 단위로(W7).
