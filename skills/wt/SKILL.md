---
name: wt
description: Git worktree 빠른 관리 — 목록/이동/생성+dlc/제거. `/wt <N>` 또는 기존 worktree 이름은 그 worktree 로 이동, 그 외 텍스트(요청사항)는 slug 확인 후 worktree 를 새로 만들고 그 안에서 `dlc` 로 작업. 접두 `?`(`/wt ? <막연한 설명>`)는 질문 모드 — AskUserQuestion 으로 요구사항을 구체화한 뒤 같은 생성 경로로 합류. 신규 생성 시 ignored `.env` 파일을 main worktree 에서 동일 상대경로로 자동 복사. `.claude/worktrees/<name>/` 에 prefix 없는 브랜치(`<name>`)로 생성하여 EnterWorktree 도구의 `worktree-` prefix 문제를 회피. 사용자가 `/wt`, `/wt <N>`, `/wt <기존이름>`, `/wt <요청사항>`, `/wt ? <막연한 설명>`, `/wt rm <name>` 형태로 호출할 때만 사용.
---

# wt — Git Worktree 관리

## 인자

`args` 를 다음 규칙으로 해석:

| 입력 | 동작 |
|---|---|
| (빈 인자) | list |
| `<정수 N>` | N번째 worktree 로 switch |
| `rm <name>` | remove |
| 기존 worktree branch 와 **정확일치** | 그 worktree 로 switch |
| 접두 `?` (`? <막연한 설명>`) | 질문 모드 — AskUserQuestion 으로 요구사항 구체화 후 '요청사항' 경로로 합류 |
| 그 외 모든 텍스트 (요청사항) | slug 파생 → 확인 → worktree 생성 → 그 안에서 `dlc` 로 작업 |

- **해석 순서** (위에서부터 평가, **첫 매치에서 확정** 후 이후 규칙은 보지 않는다 — 표 행 순서가 아니라 이 순서가 우선순위의 단일 소스): ① 빈 인자 → list. ② 첫 토큰 `rm` → remove (worktree 이름으로 `rm` 사용 금지). ②.5 첫 비공백 문자가 `?` → **질문 모드** (ask 섹션 — `?` 제거한 나머지를 seed 로 구체화 후 request 합류). `?rm foo`·`?123` 등 첫 문자가 `?` 면 토큰/정수/정확일치 여부와 무관하게 질문 모드. ③ 인자 전체가 정수 → switch (범위 밖이면 안내 + list). ④ 인자 전체가 기존 worktree branch 와 정확일치 → switch. ⑤ 그 외 전부 → **요청사항**으로 간주 (request 섹션).
- `rm` 뒤 인자 누락 등 형식 이상 → 위 표 출력 후 종료.
- **dlc 없는 단순 생성(빈 worktree 만 만들기)은 없다** — 정확일치하지 않는 텍스트는 항상 요청사항으로 처리된다.

> **참고**: 단순 list 만 보고 싶을 때는 사용자가 셸 `gwl` 함수(PowerShell 은 `scripts/gwl.ps1`, zsh 는 `scripts/gwl.zsh`)를 쓰는 것이 훨씬 빠름 (모델 왕복 없음). `/wt` 는 가공된 출력이나 후속 동작이 필요할 때만.

## 공통 규칙

- worktree path 는 항상 `.claude/worktrees/<name>` 으로 통일.
- 브랜치 이름 = worktree 이름 (1:1).
- **EnterWorktree 호출 시 항상 `path` 인자만 사용**. `name` 인자는 절대 쓰지 않는다 (prefix 자동 부착됨).
- 실행 전 git repo 안인지 확인 (`git rev-parse --show-toplevel`).
- 이름(slug·rm 대상) 검증: `^[a-zA-Z0-9._/-]+$`. 요청사항 원문은 검증 대상이 아니며, 그로부터 파생/입력된 slug 가 이 패턴을 만족해야 한다.

## list

`git worktree list` 결과를 `<path>  <sha>  [<branch>]` 형태로 인덱스(1-based) 와 함께 출력. 현재 cwd 와 일치하는 행 앞에 `→` 마커.

## switch

먼저 **대상 worktree 를 해석**한다 (경로 2가지):
1. `/wt <N>` (정수) — list N번째 worktree. 범위 밖이면 안내 + list.
2. `/wt <기존이름>` — `git worktree list` 의 branch 이름과 **정확일치**하는 worktree 1개. 정확일치 0개면 **request** (요청사항 → 생성 + dlc) 로 폴백.

부분일치/모호 매칭 없음. 정확일치만.

### 이동 방식 — 대상이 main 인지로 분기
worktree 세션 안에서 `EnterWorktree` 는 `.claude/worktrees/` 하위 대상만 받는다 (main = repo 루트는 못 들어간다). 그래서 대상이 어디냐로 도구를 가른다:

- **main 판정 = path 기준** (브랜치명 아님 — main/master 무관): 대상 path == `git worktree list --porcelain` 첫 `worktree <path>`(= main checkout). `/wt 1`(정수 1) 과 `/wt <main브랜치명>`(정확일치) 양 경로 모두 이 판정을 탄다.
- **대상이 main 이면**:
  - 이미 cwd 가 main (= `git rev-parse --show-toplevel` 가 위 첫 porcelain worktree path 와 일치) → `ExitWorktree` 호출 없이 "이미 main" 보고.
  - 아니면 → **`ExitWorktree(action: keep)`** 로 세션을 원래(main) 위치로 복귀. 반환이 복귀 성공이면 완료. 반환이 "활성 worktree 세션 없음" no-op 이고 cwd 가 여전히 worktree 면(세션이 `/wt`/EnterWorktree 경유가 아니라 worktree 안에서 시작된 경우) → 자동 복귀 불가를 사용자에게 안내(새 세션에서 열거나 수동 이동). 세션 이력을 추측하지 말고 **툴 반환으로 판정**한다.
- **대상이 그 외(하위 worktree)면** → `EnterWorktree(path: <abs>)`.

## request (요청사항 → 생성 + dlc)

정수도 `rm` 도 아니고 기존 worktree branch 와 정확일치도 아닌 **모든 텍스트**는 요청사항으로 처리한다. 요청사항 원문은 worktree 생성 후 `dlc` 의 task 로 그대로 넘긴다.

### 1. slug 파생
- 요청사항에서 짧은 kebab-case slug 를 만든다: ASCII 소문자/숫자/`-`, ≤ ~30자, `^[a-zA-Z0-9._/-]+$` 만족.
- 한글·비ASCII 요청은 핵심 의미를 영문으로 요약해 slug 화 (예: "로그인 리다이렉트 버그 수정" → `login-redirect-fix`).
- 동사+대상 중심으로 간결하게, 불용어 제거.

### 2. 충돌 검사 (확인 전)
- 기존 브랜치(`git rev-parse --verify --quiet refs/heads/<slug>`) 또는 디렉토리(`.claude/worktrees/<slug>`) 존재 시 → `<slug>-2`, `<slug>-3` … 으로 비어있는 첫 후보를 제안값으로 사용하고, 충돌 사실을 확인 단계에 함께 표시.

### 3. 확인 (AskUserQuestion — "확인 후 생성")
- 파생 slug 와 요청사항 원문을 제시. 옵션: **"`<slug>` 로 생성 후 dlc"**(기본) / **"취소"**. 사용자는 Other 로 커스텀 slug 직접 입력 가능.
- 커스텀 slug 입력 시 동일 검증(`^[a-zA-Z0-9._/-]+$`) + 충돌 검사 재실행. 위반/충돌이면 다시 안내.
- "취소" 또는 거부 → 아무것도 만들지 않고 종료.

### 4. 생성 (확인된 slug 로)
1. base ref: `git symbolic-ref --short refs/remotes/origin/HEAD` → 실패 시 `origin/main` 폴백.
2. `git fetch origin <default>` (실패해도 경고만).
3. `git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default>`. (`--no-track` 이유·첫 push autoSetupRemote 는 `references/rm-recovery.md` §A.)
4. **`.env` 자동 복사** (옵트아웃 없음): **main worktree** 에서 basename 이 정확히 `.env` 인 ignored 파일을 **동일 상대경로**로 `.claude/worktrees/<slug>/` 안에 복사. **이미 있으면 skip(덮어쓰지 않음)**, 복사 실패(권한 등)는 경고만·worktree 유지. 후보 선정(`ls-files --others --ignored --exclude-standard`, basename `.env`)·제외 정규식은 `references/env-copy.md`.
5. `EnterWorktree(path: <repo-root>/.claude/worktrees/<slug>)`.
6. 새 cwd 에서 환경 셋업 (순서대로): **submodule self-heal**(`heal_submodules.py`) → **bootstrap**(`tools/bootstrap/bootstrap.py` 있으면, 없으면 skip) → **codegraph init**(조건부·백그라운드). heal 을 **bootstrap 보다 먼저**(중단 corrupt submodule 이 이후 단계를 죽이는 것 방지). 무엇이 실패해도 **worktree 유지·에러 그대로 보고**(사용자가 수동 재실행 결정). self-heal/bootstrap 상세는 `references/rm-recovery.md` §B, codegraph init 조건(PATH + **main** `.codegraph/`)·백그라운드·staleness·`projectPath` 지침은 `references/codegraph-worktree.md`.

### 5. dlc 작업
- 생성·진입 완료 후, 새 worktree(현재 cwd)에서 **`dlc` Skill 을 요청사항 원문을 인자로 invoke** (Skill 도구, `skill: dlc`, `args: <요청사항 원문>`). 이후는 dlc 가 규모 gate 부터 파이프라인까지 진행한다.
- dlc 시작 직전 한 줄 보고: "신규 생성: `<slug>`" + `.env: N copied, M skipped` (둘 다 0 이면 생략) + heal/bootstrap skip/실패 + "→ dlc 시작: <요청사항>".

## 질문 모드 (`?` 접두 → 구체화 → request)

요청이 막연해 바로 slug 로 굳히기 이른 경우, 접두 `?` 로 **요구사항을 먼저 대화로 좁힌 뒤** request 경로에 합류시킨다. 접미 `?` 는 쓰지 않는다 (일반 의문형 요청과 충돌하므로 접두만 트리거).

### 1. seed 추출
- `args` 에서 맨 앞 `?` 와 뒤따르는 공백을 제거한 나머지를 seed(막연한 설명)로 본다. `/wt ?` 처럼 seed 가 비어도 된다.

### 2. 구체화 (AskUserQuestion)
- seed 를 바탕으로 **무엇을 / 어디를 / 어떤 결과로** 끝낼지 좁히는 질문을 한다. seed 가 비면 "무엇을 하려는지"부터 묻는다.
- 한 번에 안 좁혀지면 추가로 물어 작업 범위·대상·완료 기준을 확정한다. `?` 를 붙였다는 것 자체가 "대화로 좁히고 싶다"는 신호이므로 최소 1회는 묻는다.
- 사용자가 취소/거부하면 아무것도 만들지 않고 종료.
- 추가로 물어도 범위·대상·완료 기준이 확정되지 않으면 request 로 넘기지 않는다 — 더 묻거나 종료한다 (모호한 채 §3 으로 넘기면 slug 파생·dlc task 가 부실해진다).

### 3. request 합류
- 확정된 요구사항을 **요청사항 원문으로 삼아** 위 request 섹션 §1(slug 파생) → §5(dlc) 를 그대로 수행한다. 질문 모드는 이 앞단(요구사항 확정)만 더할 뿐, slug·충돌검사·생성·`.env` 복사·dlc 로직은 재사용한다.

## rm `<name>`

1. `<name>` 미지정 → 사용법 안내 + list.
2. 매칭: 정수면 list N번째, 아니면 branch 이름 **정확일치** 1개.
3. 0개 → 안내 + list. (정확일치만 하므로 2개+ 모호 케이스 없음.)
4. 안전 검사:
   - 메인 worktree 거부.
   - cwd 가 대상 하위면 거부 + 다른 worktree 로 switch 안내.
   - 대상에서 `git status --porcelain` 비어있지 않으면 경고.
   - unpushed 커밋 있으면 경고 (`git log origin/<branch>..<branch>` 또는 upstream 없으면 `git log <branch> --not --remotes`).
   - **미머지 탐지 (옵션 3 원격 삭제 판단 근거)**: `git branch --merged origin/<default>` 에 대상 branch 가 없거나 `git log origin/<default>..<branch>` 가 비어있지 않으면 **미머지** — 원격 삭제(옵션 3)는 데이터 유실 위험이므로 이 사실을 옵션 3 경고에 명시(e 는 조건5 게이트로 차단하나 wt 는 수동이라 사용자 판단; 미탐지 시 삭제 안 함 전제). `<default>` = `git symbolic-ref --short refs/remotes/origin/HEAD` (실패 시 `origin/main`).
5. AskUserQuestion (옵션 1: worktree 만 / 옵션 2: worktree + 로컬 브랜치 / 옵션 3: worktree + 로컬·원격 브랜치 / 옵션 4: 취소). 경고(특히 unpushed·미머지)는 question 본문에 명시 — 원격 삭제(옵션 3)는 그 경고를 본 사용자가 택할 때만.
6. 실행: `git worktree remove <path>`. 실패 시 stderr 원인으로 분기:
   - **"modified or untracked files"/"use --force" 류**(변경·untracked 잔존): `--force` 적용 여부는 **별도 AskUserQuestion 후에만**(절대 묻지 않고 강제 실행 금지).
   - **파일 점유 류**(OS 삭제 실패 — "Access is denied"·"being used"·"Directory not empty"): codegraph daemon 이 그 worktree `.codegraph/` 를 잡았을 수 있음. **자동 종료하지 않고 안내** 후 재시도(`--force` 는 OS 점유엔 무효). 상세·조건은 `references/rm-recovery.md` §C.
   - 옵션 2·3(로컬 브랜치 삭제): **remove 성공 후에만** `git branch -D <branch>` (remove 실패·거부 시 브랜치 보존).
   - 옵션 3(원격도 삭제): 로컬 삭제 후 `git push origin --delete <branch>` (원격 ref 부재면 no-op·경고만).
7. 한 줄 보고.

## 주의

- `git worktree remove --force`, `git branch -D`, 원격 브랜치 삭제(`git push origin --delete`)는 사용자 명시 확인 없이 실행 금지.
- 정확일치하지 않는 텍스트는 요청사항으로 간주해 worktree 를 새로 만든다 — 이름 오타로 의도치 않은 생성을 막기 위해 **생성 전 slug 확인(AskUserQuestion)** 을 반드시 거친다.
- 요청사항 path 는 생성 후 `dlc` 를 자동 실행한다. worktree 를 만들 필요가 없는 단순 질문·탐색·읽기 전용 작업이면 `/wt` 대신 현재 worktree 에서 직접 처리.
- EnterWorktree 후 후속 명령은 새 cwd 기준.
