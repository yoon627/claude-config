---
title: lesson-test-copies-artifact
category: decision
created: 2026-08-12
updated: 2026-08-12
sources:
  - 커밋 bde82de (테스트를 settings.json 직독으로 전환)
  - 실측 2026-08-12 (거짓 통과 1회 발생 → 분기 마커로 재검증)
---

# lesson-test-copies-artifact

검증 스크립트에 **배포물의 사본을 복붙**하면 원본이 바뀌는 순간 테스트와 배포물이 갈라진다. 그때 테스트는 실패하지 않고 **통과한다** — 더 이상 아무것도 검증하지 않으면서. 2026-08-12 에 실제로 한 번 당해서 적립한다.

## 무슨 일이었나

`settings.json` 의 훅 명령을 검증하려고 테스트 스크립트에 그 명령을 문자열로 복붙해 뒀다. 이후 명령을 `$HOME` → `~` 로 바꾸면서 테스트 쪽은 `sed` 로 치환했는데, 치환 결과가 이렇게 됐다:

```sh
HOOK='c="~/.orca/agent-hooks/claude-hook.cmd"; …'   # 큰따옴표 안의 ~
```

`~` 는 큰따옴표 안에서 **확장되지 않는다.** `[ -f "$c" ]` 가 리터럴 `~/…` 를 보므로 항상 거짓이고, 세 케이스(.cmd 존재 / .sh 존재 / 둘 다 없음)가 전부 `else` fallback 으로 샜다. fallback 은 stdin 을 삼키고 `exit 0` 이라 **3케이스 모두 exit 0** — 완벽한 초록불이었다.

실제 `settings.json` 은 올바른 무따옴표 형태였다. 즉 배포물은 정상인데 테스트만 죽어 있었고, 그 사실을 알려주는 신호가 하나도 없었다.

## 왜 놓쳤나 (3 Whys)

1. **왜 거짓 통과를 못 알아챘나** — exit code 만 봤다. 세 케이스가 *서로 다른 분기*를 타야 한다는 것을 확인하지 않았다.
2. **왜 exit code 만 봤나** — fallback 이 성공(`exit 0`)으로 설계돼 있어서, "실패 경로도 0" 이라는 사실이 검증을 무의미하게 만든다는 점을 계산에 넣지 않았다.
3. **왜 테스트와 배포물이 갈라졌나** — 명령을 두 곳(설정 파일 · 테스트)에 두고 손으로 동기화했다. 단일 소스가 아니었다.

## 올바른 방법

- **테스트는 배포물에서 직접 읽는다.** 복붙 금지.
  ```sh
  HOOK=$(node -e 'JSON.parse(fs.readFileSync("…/settings.json"))… print(h.command)')
  ```
  이러면 배포물이 바뀌어도 테스트가 자동으로 따라오고, 갈라질 수가 없다.
- **exit code 로 끝내지 말고 "어느 분기를 탔는지" 관측한다.** 각 분기에 고유 마커를 심고 그 마커를 assert:
  ```sh
  [ "$OUT" = "SH_BRANCH_TAKEN" ] && echo OK || echo "FAIL: fallback 으로 샜다"
  ```
- **성공이 기본값인 코드(fail-open fallback·`|| true`·무음 degrade)를 검증할 때는 특히 그렇다.** 그런 코드에서 "통과"는 정보가 없다 — 무엇이 *일어났는지*를 봐야 한다.

## 일반화

이건 [[lesson-grep-absence-not-proof]] 와 같은 계열이다: **부정적 관측(매칭 없음 · 에러 없음)을 근거로 쓰면 안 된다.** grep 무매칭이 부재의 증거가 아니듯, exit 0 은 검증의 증거가 아니다. 둘 다 "무엇을 확인했는지"를 긍정형으로 말할 수 있어야 한다.

[[evidence-gate]] 의 "실행·관찰로 검증" 에서 *관찰* 이 exit code 를 뜻하지 않는다는 구체화이기도 하다. 발단이 된 변경은 [[lesson-tracked-config-machine-paths]].
