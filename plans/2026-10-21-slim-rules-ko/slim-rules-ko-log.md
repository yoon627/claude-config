# Review Disposition
[묶음] plan-reviewer 묶음 모드 (2026-10-21, CONDITIONAL, Codex CLI 미설치):
- [묶음] 강한 S1, 표지 고정이 이 plan 의 § 번호에만 있다(skill 단계 번호·agent 항목 번호·인용된 라벨·hook 이 가리키는 제목이 빠짐) — fix: intent Constraints 에 표지 고정과 "바꾼 표지를 가리키는 곳 전부 검색" 을 넣음. 이 plan 의 Acceptance 3 도 인용된 라벨까지 넓힌다.
- [묶음] 강한 S2, slim-skills-ko·slim-agents-ko 가 이 plan 에 의존하는 것이 메모에 없고, 세부의 유일한 사본이 서로를 가리키며 사라질 수 있다 — fix: 두 단위 메모에 "slim-rules-ko 머지 뒤" 와 "유일한 사본 줄을 이어받는다", intent Constraints 에 같은 규칙.
- [묶음] 강한 S3, translate-en 이 쓰기 경로가 다른 셋(repo PR·공용 wiki main·머신별 memory)을 한 단위로 묶고 "파일별 머지" 와 어긋난다 — fix: translate-repo·translate-hooks·translate-wiki-docs·translate-memory 로 나눔.
- [묶음] 강한 S4, 언어 정책의 행동 규칙(subagent 지시·보고는 영어)을 맡은 단위가 없고 agents·Codex 프롬프트는 아직 한국어를 요구한다 — fix: language-policy 단위를 더하고, 그 전까지 영어 보고 요청은 사용자 지시에 따른 의도된 예외라고 intent 에 적음. 시점은 Open question.
- [묶음] 강한 S5, 진행 중인 `read-points`(skills/dlc·agents/code-reviewer·README)가 묶음과 같은 파일을 고친다 — fix: intent Constraints 에 순서 규칙(줄이기 단위 전에 머지 또는 그 위로 rebase, 번역 뒤 추가는 영어).
- [묶음] 약한 W1(a), remove-conclusion-block 의 [post-merge] 체크는 소급 생성 때 "intent: 1줄만" 을 넘는 본문 편집이고, plan-format 의 끝난 [post-merge] 는 그대로다 — fix: 체크는 사용자 지시("같이: … 체크")라 intent 소급과 별개의 기록 갱신으로 하고, plan-format 의 끝난 [post-merge](wiki 갱신, 0c6f7e2)도 같은 근거로 체크한다. Acceptance 6(/c 관찰)은 아직이라 그대로.
- [묶음] 약한 W1(b), intent Problem 에 결론 블록 제거의 목적이 없다 — fix: 한 줄 추가.
- [묶음] 약한 W2, 기각한 분할선 둘의 기술적 이유가 없고 rollback 이 단위 1 까지 되돌린다 — fix: intent Constraints 에 "manifest 는 같은 언어 안에서만" 이유, plan Decisions 에 "두 plan 으로 나누지 않은 이유는 plan 고정비와 커밋 단위가 이미 따로 리뷰된다는 것", rollback 에 단위 2 커밋만 되돌리는 선택지.
- [묶음] 약한 W3, 언어 정책의 범위가 다 덮이지 않는다(wiki/pages·repo wiki·plan log·intent·references·description) — fix: references·description 은 translate-repo 에, 나머지는 Open question.
- [묶음] 약한 W4, 모순 2 를 고쳐도 `skills/c/SKILL.md` 73·77행이 "머지" 를 그대로 멈춤 조건으로 둔다 — wontfix: `/c` 는 이어받은 흐름에서 사용자가 상태를 보지 않은 채 머지하지 않으려는 더 엄격한 규칙이고 §1 은 최소선이라 어긋나지 않는다.
- [묶음] 약한 W5, 사용자에게 보이는 hook 문구까지 번역하면 "보이는 것은 한국어" 와 어긋난다 — defer: Open question, translate-hooks 가 표시 방식을 확인한 뒤 정한다.
- [묶음] 약한 W6, Open questions 가 비어 있고 translate 단위가 줄이기 단위의 폐기에 막힐 수 있다 — fix: Open questions 4개, "done 또는 폐기 뒤".
- [묶음] 약한 W7, 단위별 규모 판정이 없다 — fix: translate-hooks 메모에 "코드라 medium 이상·TDD". 나머지는 각 단위가 착수 때 판정한다.
- [묶음] 약한 W8, "이력 메모 삭제" 를 다른 단위가 따라 하다 적용 시점 날짜까지 지울 수 있다 — fix: intent Constraints 로 옮기고 적용 시점 날짜는 규칙이라 남긴다고 적음.

plan-reviewer (2026-10-21, CONDITIONAL, Codex CLI 미설치):
- 강한 S1, Tasks 순서가 커밋 단위 결정과 §8 검증 규칙에 어긋난다(단위 1 이 확인 없이 커밋되거나 단위 2 와 한 커밋으로 뭉친다) — fix: 단위 1 → 리뷰 → 사용자 확인 → 커밋 → 단위 2 순서로 Tasks 재배치.
- 강한 S2, "§8 세부는 이미 skills 에 있다" 가 커밋 게이트에는 거짓이다(dlc 16단계가 §8 을 단일 소스로 가리킨다) — fix: §8 은 §10 처럼 표현만 줄인다고 Decisions·manifest 에 적음, 게이트 조항을 manifest 에 조항별로.
- 강한 S3, §8(a)(b) 정리 조건은 절차 세부가 아니라 안전 게이트다 — fix: 인라인 유지, manifest 에 조건마다 한 줄.
- 강한 S4, Acceptance 가 긴 한 줄 불릿 안의 조항 손실을 못 잡고 같은 손이 채점한다 — fix: 조항 단위 manifest, 새 위치를 `«인용»` 으로 기계 확인, 핵심 문구를 단위 2 전에 고정(바꾸려면 승인), 단위 2·3 은 `--word-diff` 로 단위 1 뒤부터 대조, 새 subagent 독립 대조(Acceptance 4).
- 약한 W1, §5 code-reviewer "모든 흐름" vs dlc trivial, §3-5 Acceptance vs plan 없는 small — fix: 모순 8·9 로 추가.
- 약한 W2, 키워드로 이력을 지우면 규칙 속 "재현" 과 적용 시점 날짜가 걸린다 — fix: 이력을 괄호 안 근거 표시로만 정의.
- 약한 W3, §3 항목 번호와 인용된 구절이 고정 목록에 없다 — fix: Acceptance 3 과 manifest "표지" 절.
- 약한 W4, §5 effort 표는 CLAUDE.md 에만 있다 — fix: 인라인 유지, 포인터 형식 규칙을 Decisions 에.
- 약한 W5, 번복 규칙이 사용자 결정을 따르는 것까지 막을 수 있다 — fix: "사용자가 결정하면 따른다" 를 같은 문장에.
- 약한 W6, Tasks 를 처음부터 다 적으면 건너뛴 단계가 미완료로 남아 `/e merge` M1(5) 가 거부한다 — fix: "생략: <사유>" 와 날짜로 체크해 닫는다.
- 약한 W7, README 동기화가 단위 2 에 있다 — fix: 단위 1 로.
- 약한 W8, `@RTK.md`·굵은 agent 이름(improve.sh 3번 점검이 grep)이 핵심 문구에 없다 — fix: 추가(76개).
- 약한 W9, CLAUDE.md 는 Codex 의 AGENTS.md 이고 Codex 에 연결된 skill 은 7개뿐 — fix: Goal 델타에 "그 밖의 skill 포인터를 새로 더하지 않는다".
- 약한 W10, 공용 wiki risk-based-approval 17행이 "머지" 를 그대로 둔다 — fix: [post-merge] Task 와 Acceptance 9.
- 약한 W11, 선행 plan 본문 편집 — fix: Decisions 에 사용자 지시에 따른 별개의 기록 갱신이라고 적음.
- 약한 W12, "1회 원칙" 을 모두 "중복 질문 금지" 로 바꾸면 `skills/e` 82행과 뜻이 다르다 — fix: 82행은 인용을 지운다.
- 약한 W13, 머지 전에는 새 문구의 동작을 관찰할 수 없고 전체 diff 확인은 사용자 기억 규칙(짧은 확인)과 맞지 않는다 — fix: 단위 2·3 확인은 지운 조항과 등급·위치가 바뀐 조항만.
- 약한 W14, 모순 7 은 압축이다 — fix: 단위 2 로.
- 약한 W15, 모순 5 는 규칙 완화다 — fix: Decisions 에 완화라고 적음.
- rollback, 단위 2·3 만 되돌리는 선택지와 되돌린 뒤 각 머신의 pull·새 세션 — fix: Decisions.

code-reviewer 단위 1 (2026-10-21, REQUEST CHANGES — 막는 것은 manifest, 단위 1 diff 는 Minor 만, Codex CLI 미설치):
- Major M1, manifest "표지" 에 다른 파일이 인용하는 이름이 빠졌다(«중복 질문 금지»·«대응표»·**한계**·트리거 번호·«공개 점검»·improve 가 인용하는 셋·«force push»·§8 의 worktree 규칙 위치) — fix: 표지 절과 핵심 문구에 추가.
- Major M2, manifest 의 몇 줄이 여러 조항을 한 줄에 담거나(10.16·10.20·10.25·10.28) 내용이 없다(10.27) — fix: §10 을 조항 단위로 다시 나누고 10.13·11.7·7.2 도 나눔.
- Major M3, §4 "임계값을 의식적으로 낮춘다" 가 지워도 되는 이유로 분류돼 있었다 — fix: 4.1b 인라인, 영역 단서는 4.2 로.
- Minor A [plan 대비, 바뀐 쪽: 둘 다], `agents/code-reviewer.md` 와 README agents 표가 "모든 흐름" 을 그대로 둔다 — fix: 단위 1 Tasks 에 경로를 더하고 고침.
- Minor B [plan 대비, 바뀐 쪽: 둘 다], §3-5 를 "plan 이 있는 비trivial" 로 바꾸면 plan 을 빠뜨린 medium 이상이 빠진다 — fix: 원래 문장 + "(plan 없이 가는 small 은 검증 결과로)".
- Minor C, "PR 머지" 는 로컬 non-ff 머지를 확인 목록에서 빼고 (a) 정리를 "데이터를 지우지 않는" 괄호에 넣는다 — fix: "머지" 유지, 목록 밖에 예외 문장.
- Minor D, "사용자가 결정하면 따른다" 에 한계가 없다 — fix: "(§8 의 금지는 그대로), 새 근거 없이 내 추천이 바뀐 것처럼 말하지 않는다".
- Minor E, trivial 의 뜻이 CLAUDE.md 에 없다(§7 "1줄 수정" 보다 좁다) — fix: §5 첫 언급에 dlc 규모표 정의.
- Minor G, 생략을 누가 정하는지 없다 — fix: "조건부 단계가 해당 없거나 사용자가 생략을 정한 단계".
- Nit F, `(날짜)` 표기 — fix: `(YYYY-MM-DD)`. "나중에 더하는 Task 는 이유" 와 급한 일 추가의 관계 — wontfix: 리뷰 반영·재실행처럼 급한 일도 이유가 한 구절이면 된다.
- M4, 3.1.m1 "사본은 없다" 는 잘못된 거부 메시지를 바로잡는 규칙이다 — fix: 인라인(짧게).
- M5, 3.1.3 의 중복 대상 번호 — fix: 8.32.
- M6, §8 "core.hooksPath 가 있으면 설치해도 무효" 가 `scripts/install-hooks.sh` 와 다르다(설치 거부) — fix: 모순 10 으로 단위 1 에서 고침, manifest 위치는 줄 번호 대신 인용.
- M7, 8.m1 등급 — fix: 이유.
- M8, 핵심 문구에 안전 문구가 빠졌고 여러 번 나오는 문구는 약한 검사다 — fix: 21개 추가(97개), 약한 문구는 Acceptance 1 의 조항별 인용이 지킨다고 manifest 에 적음. 횟수 검사는 하지 않는다(중복 정리로 정당하게 줄어든다).
- Nit, manifest 에 없던 조항(§12 "인덱스는 직접 갱신", §6 출력 토큰 기준, §8 상세 포인터, §0·§2 이유) — fix: 추가.
- Open question, 단위 2·3 의 README 요약 동기화 — fix: 단위 2·3 리뷰 때 README 요약(271~284행)이 맞는지 함께 본다.

독립 대조 (2026-10-21, 새 subagent — 새 CLAUDE.md 와 인라인 조항 293개만 읽음, Acceptance 4): missing 0 · weakened 0 · misplaced 0 · contradicted 2.
- 3.6.2 vs 8.24·1.20b, §3-6 이 모든 코드 작업의 마무리로 `/e merge`(push·PR)를 내놓아 §8 의 trivial·small 로컬 ff-merge 와 어긋난다(원래 문구부터) — fix: §3-6 에 "(trivial·small 은 §8 의 로컬 ff-merge)". 동작 변경이라 단위 1 의 fixup 커밋으로(모순 11).
- 8.23c vs 8.7·8.24, "미커밋 plan·log 변경은 삭제 전 커밋·push 로 보존" 이 "push 는 요청 시만" 과 로컬 ff 흐름에 어긋난다(원래 문구부터) — fix: "커밋으로 보존(push 는 요청 시만)". 보존은 커밋이면 되고, 미머지 브랜치는 `git branch -d` 가 지우지 않는다. 단위 1 의 fixup 커밋으로(모순 12).

code-reviewer 단위 2·3 (2026-10-21, NEEDS DISCUSSION — Critical·Major 0, Codex CLI 미설치):
- Minor 1, §3-1 의 "`.env`/key/token/cert 원문 출력 금지" 를 §8(8.32)로 합쳤더니 대상 목록(답변·로그·fixture·snapshot)이 붙어 범위가 좁아졌다(도구 출력) — fix: §3-1 에 원래 문장을 되살림.
- Minor 2, §11 "경로를 명시한다" 가 §2 의 "영향 범위 조사에서는" 으로만 남았다 — fix: §11 에 "건너뛰므로 경로를 명시한다 — §2".
- Minor 3 [plan 대비, 바뀐 쪽: plan], 리뷰 단락을 §10 → §9 로 옮겨 공용 wiki native-overlap-ledger 51행 인용이 낡았다 — fix: Deferred 에 [post-merge] 줄.
- Minor 4, §3-4 의 "기록 후 진행" 의 "진행" 이 빠졌다(manifest 도 빠뜨림) — fix: "로 남기고 진행한다", manifest 3.4.2 도.
- Minor 5, §7 예외 목록을 한 줄로 합쳐 뒤 불릿까지 예외처럼 읽힌다 — fix: 3항목 목록과 **기타** 라벨을 되살림.
- Nit 0.4 "문자 그대로의 표현이 있으면 그것을 쓴다" — fix: 되살림. Nit 8.29d "보고"(report 와 헷갈림) — fix: "여기고". Nit 8.9b 포인터 — fix: "절차는". Nit 8.10b "`~/.claude` 에서" — fix: 되살림. Nit 9.6 라벨 — fix: **리뷰 시점**. Nit 동사 빠진 문장 2곳·조사 1곳 — fix. Nit 2.9 rtk 가 `rtk grep` 으로 바꾼다 — fix. Nit manifest 1.18·3.5.4 와 Acceptance 8 의 기준점 — fix: manifest 수정, 크기는 5555fc6 기준과 단위 1 뒤 기준을 둘 다 적음.
- 반영분은 재리뷰 없이 — 모두 리뷰가 지목한 원래 문구를 되살리는 것이고, 위치 검사 317개·핵심 문구 97개를 다시 돌려 통과(2026-10-21).
- Open question, 옛 §3-1 의 원문 출력 금지가 도구 출력까지 덮었는지 — 해소: 되살렸으니 옛 범위 그대로.

# Deferred
- [post-merge] 공용 wiki `pages/decision/ops-doc-slimming.md` 에 2026-10-21 결과 — 규칙 손실 0·§8·§10 이관 없음으로 CLAUDE.md 49,942B → 48,170B(−3.5%), 방법(조항 단위 manifest 317개·`«인용»` 위치 기계 검사·새 CLAUDE.md 만 읽는 독립 대조가 모순 2개를 찾음). 공개 출처(이 repo PR) — main 세션에서 `/wiki ingest`.
- ⚠️ 확인 필요: compaction 뒤 "다시 읽은 지시 파일" 로 주입된 CLAUDE.md 가 #239 머지 전 내용(결론 블록 규칙)이었다 — 그때 main 파일에는 `## 결론` 이 0건이었다(2026-10-21 `grep -c`). 원인 모름 ❌. 재현되면 공용 wiki 에 적는다.
- [post-merge] 공용 wiki `pages/decision/native-overlap-ledger.md` 51행의 "CLAUDE.md §10 이 이미 … /code-review 수동 사용" → §9(리뷰 단락이 §9 로 옮겨짐) — main 세션에서.

# Workflow Findings
- remove-conclusion-block 은 plan-format log 의 Deferred "다음 작업" 에서 시작했는데 그때 §10 intent 트리거 3(소급 생성)이 걸리지 않았다 — 이 plan 에서 묶음을 만들며 소급했다(2026-10-21, plan-reviewer 묶음 리뷰 W1 지적).
