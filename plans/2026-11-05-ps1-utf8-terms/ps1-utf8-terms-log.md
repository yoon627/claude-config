# Review Disposition
- code-reviewer(APPROVE, 2026-11-05)
  - Minor ps1 바이트 범위 계산과 `bad8` 경계를 고정하는 테스트가 없음(무 newline 마지막 줄의 잘린 시퀀스, overlong, U+10FFFF 초과, 올바른 4바이트 항목) — fix: `both` 케이스 4건. 리뷰어의 파이썬 모델 대조(3007 목록·426,149 시퀀스)는 불일치 0.
  - Nit ps1 주석이 "entry 를 다시 디코드" 라 했지만 실제로는 물리 줄 전체 — fix: 문구와, 떼어 내는 문자가 ASCII·BOM 이라 판정이 같다는 이유를 적음.
  - ⚠️ (구현) 엄격한 .NET 디코더 규칙에 맞춤 — accepted-risk(리뷰어 타당 판정).
  - ⚠️ (구현) NUL → `\001` — accepted-risk(리뷰어 타당 판정).
  - 열린 질문: 설치된 Windows hook 은 PowerShell 5.1 로 도는데 CI 는 pwsh 만 돈다 — 5.1 디코더 동작은 reference source 로만 확인(#190 의 Windows 전용 검증 대상).
