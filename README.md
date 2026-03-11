# 스타티 제품 분석 프로젝트

스타티(Startie)의 제품/수익화 데이터를 기반으로, 다음 분기 CEO 의사결정을 지원하기 위한 분석 프로젝트입니다.

이 저장소의 목적은 단순한 차트 생산이 아닙니다.  
핵심 목적은 `무엇을 해야 유료전환과 성장 지표가 개선되는가`를 Q1~Q5 질문 체계로 답하는 것입니다.

근거 컨텍스트:
- `context/01_product_overview.md`
- `context/02_data_dictionary.md`
- `context/03_analysis_guide.md`
- `context/04_erd_startie.dbml`
- `context/05_ceo_questions.md`

## 프로젝트 목적

스타티는 `7일 무료체험 -> 유료 구독 전환` 모델을 운영합니다.

- `Basic`: 월 `9,900원`
- `Pro`: 월 `19,900원`

현재 목표는 향후 6개월 내 핵심 지표를 개선해 투자자에게 성장성을 증명하는 것입니다.  
이 프로젝트는 그중에서도 `유료전환 최적화 전략`을 중심 주제로 삼아 CEO가 다음 분기에 실행할 우선순위를 제안하는 데 초점을 둡니다.

## CEO 질문 프레임워크

### Q1. 가치와 활성화
- 질문 정의:
  - 가입 후 어떤 초기 행동이 유저의 유료전환과 리텐션을 크게 높이는가?
- 핵심 지표:
  - 활성화율, Aha 도달률, 체험판 대비 유료전환율, D7/D30 리텐션
- 사용 테이블:
  - `users`, `event_logs`, `payment_transactions`, `plan_history`, `lessons`
- 의사결정 기준(So What):
  - Aha 행동이 강하면 온보딩과 초기 학습 경험 개선을 우선한다.

### Q2. 채널 품질
- 질문 정의:
  - 어떤 유입 채널에 예산을 늘리거나 줄여야 하는가?
- 핵심 지표:
  - CAC, LTV, LTV/CAC, 회수 기간, 채널별 리텐션
- 사용 테이블:
  - `users`, `campaigns`, `payment_transactions`, `plan_history`, `event_logs`
- 의사결정 기준(So What):
  - 전환 효율과 회수 효율이 낮은 채널은 축소하고 높은 채널은 확대한다.

### Q3. 이탈 분석
- 질문 정의:
  - 누가 왜 떠나는지, 어떤 시점에 조기 개입할 수 있는가?
- 핵심 지표:
  - 이탈률, 이탈까지 소요시간, 취소 사유 분포, 결제 실패 후 이탈률
- 사용 테이블:
  - `users`, `plan_history`, `payment_transactions`, `chat_events`, `push_events`, `event_logs`
- 의사결정 기준(So What):
  - 결제 실패 반복, 48시간 무활동 같은 조기 신호를 기반으로 자동 개입을 설계한다.

### Q4. A/B 테스트 평가
- 질문 정의:
  - 온보딩/가격 실험을 전체 적용할 것인가, 세그먼트 적용할 것인가?
- 핵심 지표:
  - uplift, p-value, 효과 크기, 세그먼트별 이질적 효과
- 사용 테이블:
  - `experiments`, `ab_assignment`, `event_logs`, `users`, `payment_transactions`
- 의사결정 기준(So What):
  - 통계적 유의성과 실용적 유의성을 함께 만족할 때 확대 적용한다.

### Q5. 다음 분기 전략 집중
- 질문 정의:
  - 다음 분기에 어떤 1~2개 전략을 최우선으로 실행해야 성장 임팩트가 큰가?
- 핵심 지표:
  - 예상 MRR 임팩트, 실행 난이도, 적용 속도, 리스크
- 사용 테이블:
  - Q1~Q4 종합 결과
- 의사결정 기준(So What):
  - `What -> Why -> So What -> Impact` 형식으로 최종 경영진 제안안을 정리한다.

## 분석 원칙

- 퍼널 분석은 기본적으로 `event_logs`와 `payment_transactions`, `plan_history`를 함께 본다.
- `is_activated`는 참고 지표로 사용하되, 실제 행동 로그 기준으로 반드시 검증한다.
- 가능한 한 채널, 디바이스, 활성화 여부 기준 세그먼트 비교를 포함한다.
- 모든 분석은 설명으로 끝내지 않고 반드시 의사결정으로 연결한다.

## 우리가 어떻게 일했는가

`docs/` 폴더를 중심으로 회의록, 작업 로그, 의사결정 기록, 분석 브리프를 쌓는 방식으로 작업했습니다.

- `docs/meetings/`
  - 회의 목적, 논의 내용, 결정 사항, 액션 아이템 정리
- `docs/worklog/`
  - 일자별 작업 내용, 확인한 데이터, 이슈, 다음 액션 기록
- `docs/decisions/`
  - 왜 그렇게 판단했는지 배경과 대안을 남기는 의사결정 로그
- `docs/analysis/`
  - Q1~Q5 분석 브리프, 유료전환 최적화 발표용 문서, 간트 차트 정리
- `docs/metrics/`
  - 발표/분석에 쓰는 지표 정의 관리
- `docs/templates/`
  - 회의록, 작업 로그, 의사결정, 분석 브리프 템플릿

## 작업 간트 차트

아래 간트 차트는 `docs` 기반으로 우리가 진행한 작업 흐름을 요약한 것입니다.

```mermaid
gantt
    title 스타티 유료전환 최적화 작업 흐름
    dateFormat  YYYY-MM-DD
    axisFormat  %m/%d

    section 문서 운영 체계 정리
    docs 구조 설계 및 README 정리          :done, d1, 2026-03-11, 1d
    회의록/작업로그/의사결정 템플릿 작성    :done, d2, 2026-03-11, 1d

    section 분석 방향 설정
    CEO 질문 프레임 정리                   :done, d3, 2026-03-11, 1d
    발표 주제 선정: 유료전환 최적화        :done, d4, 2026-03-11, 1d
    발표 브리프 작성                       :done, d5, 2026-03-11, 1d

    section 분석 설계
    퍼널 및 Activation/Aha 정의            :done, d6, 2026-03-12, 1d
    채널/디바이스 세그먼트 비교 설계       :done, d7, 2026-03-12, 1d
    리텐션/이탈/실험 분석 흐름 정리        :done, d8, 2026-03-12, 1d

    section 수익화 지표 확인
    ARPPU 계산 및 월별 확인                :active, d9, 2026-03-13, 1d
    유료전환 핵심 지표 해석 정리           :d10, 2026-03-13, 1d

    section CEO 제안 정리
    핵심 인사이트 구조화                   :d11, 2026-03-14, 1d
    다음 분기 실행안 연결                  :d12, 2026-03-14, 1d
```

## 저장소 구조

```text
context/         제품 개요, 데이터 사전, 분석 가이드, ERD, CEO 질문
data/raw/        원천 CSV 데이터
docs/            회의록, 작업 로그, 의사결정, 분석 브리프, 지표 정의
notebooks/       탐색 및 발표 보조 노트북
src/             Streamlit 앱과 분석/시각화 스크립트
outputs/         생성된 차트 및 요약 산출물
deliverables/    최종 발표 자료와 결과 파일
tests/           검증용 테스트 영역
```

## 주요 파일

- `src/app.py`
  - 세그먼트와 병목을 확인하는 Streamlit 대시보드
- `src/plot_actual_retention.py`
  - 실제 리텐션 커브 생성 스크립트
- `src/generate_ppt_visual_assets.py`
  - 발표용 슬라이드 시각 자산 생성 스크립트
- `docs/analysis/paid_conversion_presentation_brief.md`
  - 유료전환 최적화 발표 브리프
- `docs/analysis/gantt_plan.md`
  - 발표/작업 흐름용 간트 차트 문서

## 실행 방법

권장 환경:
- Python `3.11+`

필요 패키지 설치:

```bash
pip install pandas matplotlib numpy streamlit altair
```

대시보드 실행:

```bash
streamlit run src/app.py
```

리텐션 산출물 생성:

```bash
python src/plot_actual_retention.py
```

발표용 시각 자산 생성:

```bash
python src/generate_ppt_visual_assets.py
```

## 최종 산출물 원칙

모든 인사이트는 아래 구조를 따릅니다.

1. `What`
2. `Why`
3. `So What`
4. `Impact`

최종적으로는 `다음 분기에 무엇을 할지`를 CEO에게 제안하는 형태로 끝나야 합니다.
