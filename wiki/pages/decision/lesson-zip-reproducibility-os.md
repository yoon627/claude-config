---
title: lesson-zip-reproducibility-os
category: decision
created: 2026-09-22
updated: 2026-09-22
sources:
  - cstp_compliance CSTP1-3043-ai-agent-worker 커밋 a66bb98cf (agent/Scripts/ai_skill_package/build.py)
  - code-reviewer 실측 2026-09-22 (Windows 빌드에서 `create_system 0`·엔트리 순서 역전 확인)
---

# lesson-zip-reproducibility-os

"같은 입력이면 같은 zip" 을 약속하는 빌더는 **timestamp 만 고정해서는 재현되지 않는다.** Python `zipfile` 로 만든 아카이브는 빌드 호스트 OS 에 따라 바이트가 달라지는 축이 두 개 더 있고, 2026-09-22 AI skill 패키지 빌더(sha256 이 manager↔agent 계약의 checksum)에서 리뷰가 둘 다 실측으로 잡았다.

## 무엇이 달라지나

1. **`zipfile.ZipInfo.__init__` 이 `create_system` 을 OS 로 채운다** — win32 는 0, 그 외는 3. 중앙 디렉토리 헤더 바이트가 달라져 같은 내용도 sha256 이 갈린다.
2. **`sorted(Path)` 는 Windows 에서 case-fold 비교다** — `skills/a/references/x.md` 가 `skills/a/SKILL.md` 보다 앞에 오고, POSIX 에서는 `SKILL.md` 가 먼저다. 엔트리 순서 자체가 바뀐다.

결과: 운영자 PC(Windows)와 CI(Linux)가 같은 소스로 만든 패키지의 checksum 이 다르다. 재빌드로 검증·대조할 수 없고, checksum 을 캐시 키로 쓰는 저장소는 같은 내용을 중복 보관한다. 실행 경로는 멀쩡해서 **테스트도 통과한다** — 한 머신 안에서 두 번 빌드해 비교하는 테스트는 이 결함을 못 본다.

## 올바른 방법

```python
info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
info.create_system = 3          # 명시 — OS 기본값에 맡기지 않는다
info.external_attr = 0o644 << 16
entries = sorted(files, key=lambda p: p.relative_to(root).as_posix())  # 문자열 정렬
```

- 정렬 키는 `Path` 가 아니라 **posix 문자열**로.
- 회귀 테스트는 "두 번 빌드해 sha 가 같다" 로 끝내지 말고 **엔트리 순서**(`namelist()` 의 `SKILL.md` < `references/…`)와 **`create_system == 3`** 을 직접 assert 한다 — OS 가 하나뿐인 테스트 환경에서도 결정성의 *원인* 을 고정한다.

## 일반화

[[lesson-test-copies-artifact]] 와 같은 계열: "통과" 가 정보를 주지 않는 검증이 있다. 결정성처럼 *환경 축* 을 가진 성질은 한 환경에서의 반복 실행이 아니라 그 축을 고정했는지를 검사해야 한다. [[evidence-gate]] 의 "실행·관찰" 에서 관찰 대상은 결과 해시가 아니라 해시를 만드는 입력 축이다. 기록 경위는 [[workflow-failures]] 가 아니라 정상 리뷰 발굴이라 lesson 만 남긴다.
