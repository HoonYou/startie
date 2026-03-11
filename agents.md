# AGENTS.md

## 1) 기본 원칙
- 모든 답변은 기본적으로 한국어로 작성한다.
- 사용자가 다른 언어를 명시적으로 요청한 경우에만 해당 언어로 답변한다.
- 분석 목적은 "차트 생산"이 아니라 "CEO 의사결정 지원"이다.

## 2) 컨텍스트 참조 규칙
- 아래 파일을 항상 우선 참고한다.
  - `context/01_product_overview.md`
  - `context/02_data_dictionary.md`
  - `context/03_analysis_guide.md`
  - `context/04_erd_startie.dbml`  (4번은 ERD)
  - `context/05_ceo_questions.md`
- 분석/요약/제안 응답 시, 어떤 컨텍스트를 근거로 썼는지 간단히 밝힌다.

## 3) 질문 중심 분석 방식
- 분석은 Q1~Q5(CEO Questions) 단위로 진행한다.
- 각 질문마다 최소 4가지를 명확히 제시한다.
  - 질문 정의
  - 핵심 지표
  - 사용 테이블
  - 의사결정 기준(So What)
- 가능하면 세그먼트 비교(채널/디바이스/활성화 여부)를 포함한다.

## 4) 데이터 해석 원칙
- 퍼널 분석은 기본적으로 `event_logs`와 결제/구독 테이블(`payment_transactions`, `plan_history`) JOIN을 권장하되, 질문 목적에 따라 단일 테이블 분석도 허용한다.
- Aha Moment 탐색은 `is_activated`를 참고 지표로 활용하고, 가능하면 행동 기준과 함께 비교 검증한다.
- 결과는 가능하면 숫자와 비교 기준을 함께 제시하되, 탐색 단계에서는 정성 해석을 먼저 제시해도 된다.
  - 예: "A는 B 대비 x배", "A가 B보다 높음"

## 5) 최종 산출물 원칙
- 모든 인사이트는 아래 4단계로 정리한다.
  - What(현상)
  - Why(원인 가설)
  - So What(실행 제안)
  - Impact(정량 기대효과)
- 최종 제안은 "다음 분기에 무엇을 할지"로 연결한다.

## 6) Notebook Language Rule
- When creating or editing .ipynb files, write all comments/markdown/text cells in English only to avoid Korean text encoding issues (garbled characters).
