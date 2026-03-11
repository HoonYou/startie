# PPT Metric Definitions

본 문서는 발표 자료에 사용한 주요 지표와 시각화의 계산 기준을 정리한 문서입니다.

- 근거 컨텍스트:
  - `context/01_product_overview.md`
  - `context/02_data_dictionary.md`
  - `context/03_analysis_guide.md`
  - `context/05_ceo_questions.md`
- 분석 목적:
  - 차트 생산이 아니라 CEO 의사결정 지원
- 재현 코드:
  - `src/generate_ppt_visual_assets.py`
  - `notebooks/startie_ppt_visual_assets.ipynb`
- 결과 시각화:
  - `deliverables/results/*.png`

## 공통 기준

### 데이터 기간
- `users`: 2024-03-01 ~ 2025-05-25
- `event_logs`: 2025-01-06 ~ 2025-05-26
- `payment_transactions`: 2025-01-06 ~ 2025-05-28
- `chat_events`: 2025-01-06 ~ 2025-05-25

### 해석 주의사항
- 이벤트 기반 시각화는 `event_logs` 관측 시작일이 2025-01-06이므로, 실질적으로 2025 cohort 기준 해석이 필요하다.
- `결제 완료`는 `event_logs`가 아니라 `payment_transactions.status = completed`를 사용한다.
- 발표용 기대효과 슬라이드의 일부 숫자는 실제 관측치가 아니라 deck scenario 숫자이며, 해당 항목은 별도로 명시한다.

## Q1. 가치와 활성화

### 1) Slide 07 - Value Gap Diagnostics

#### 질문 정의
- 유저가 제품 가치를 체감하기 전에 어디서 이탈하는가?

#### 핵심 지표
- `7-day quiz not submitted rate`
- `Churn rate by Aha status`
- `Churn timing spike`

#### 사용 테이블
- `users`
- `event_logs`

#### 계산 방식
- 분석 대상:
  - `signup_date >= 2025-01-06` 유저
- `7-day quiz not submitted rate`
  - 가입 후 0~6일 내 `quiz_submitted` 이벤트가 한 번도 없는 유저 비율
- `Aha`
  - 가입 후 0~6일 내 `lesson_completed >= 1` and `quiz_submitted >= 1`
- `Churned`
  - `users.churn_date is not null`
- `Churn rate by Aha status`
  - `Aha` 도달 여부별 `churned` 비율
- `Churn timing spike`
  - `churn_day = churn_date - signup_date`
  - 0~14일 구간의 이탈 분포 확인

#### 현재 사용 수치
- `7-day quiz not submitted rate = 83.4%`
- `Churn rate`
  - `Non-Aha = 53.93%`
  - `Aha = 34.89%`
  - `Non-Aha / Aha = 1.55x`
- `Churn timing`
  - 현재 데이터에서는 `Day 8` 이탈이 비정상적으로 집중되어 있어 운영 이벤트 또는 데이터 생성 로직 영향 가능성이 높음

#### So What
- Aha 도달 이전, 특히 퀴즈 미제출 단계에서 대규모 누수가 발생한다.
- Trial 종료 직전/직후 개입 설계가 핵심이다.

### 2) Slide 08 - Aha KPI

#### 질문 정의
- 가입 7일 내 어떤 행동 조합이 유료 전환을 가장 강하게 끌어올리는가?

#### 핵심 지표
- `7-day Aha distribution`
- `Paid conversion within 30 days by Aha status`

#### 사용 테이블
- `users`
- `event_logs`
- `payment_transactions`

#### 계산 방식
- 분석 대상:
  - `signup_date >= 2025-01-06` 유저
- 7일 행동 세그먼트
  - `Neither`: 7일 내 `lesson_completed = 0` and `quiz_submitted = 0`
  - `Lesson only`: 7일 내 `lesson_completed >= 1` and `quiz_submitted = 0`
  - `Aha`: 7일 내 `lesson_completed >= 1` and `quiz_submitted >= 1`
- `Paid conversion within 30 days`
  - 첫 `payment_transactions.status = completed` 날짜가 가입 후 0~30일 사이인 유저 비율

#### 현재 사용 수치
- `Neither = 28.53%`
- `Lesson only = 54.87%`
- `Aha = 16.60%`
- `Paid conversion within 30 days`
  - `Non-Aha = 20.58%`
  - `Aha = 39.18%`
  - `Gap = +18.60%p`
  - `Lift = 1.90x`

#### So What
- 핵심 KPI는 단순 학습 시작이 아니라 `강의 완료 + 퀴즈 제출`까지 도달한 Aha 행동이다.
- 온보딩과 Trial 경험은 이 행동의 도달률을 올리는 방향으로 설계해야 한다.

### 3) Slide 09 - Onboarding Improvement

#### 질문 정의
- 온보딩 개선이 실제로 Aha 도달을 가속화할 수 있는가?

#### 핵심 지표
- `Onboarding completion A/B uplift`
- `Aha rate by onboarding completion`

#### 사용 테이블
- `ab_assignment`
- `users`
- `event_logs`

#### 계산 방식
- 실험 대상:
  - `ab_assignment.experiment_id = exp_onboarding_v2`
- `Onboarding completion`
  - 가입 후 0~6일 내 `onboarding_completed >= 1`
- `Aha`
  - 가입 후 0~6일 내 `lesson_completed >= 1` and `quiz_submitted >= 1`
- A/B uplift
  - `treatment onboarding completion rate - control onboarding completion rate`

#### 현재 사용 수치
- `Onboarding completion`
  - `Control = 59.81%`
  - `Treatment = 68.12%`
  - `Uplift = +8.30%p`
- `Aha rate by onboarding completion`
  - `Not completed = 11.61%`
  - `Completed = 20.01%`
  - `Gap = +8.41%p`
  - `Lift = 1.72x`

#### So What
- 온보딩 자체는 개선 효과가 확인됐다.
- 다만 현재 실측 데이터 기준으로 treatment의 직접 Aha uplift는 아직 확인되지 않았으므로, 온보딩 완료 이후 행동 유도 설계까지 같이 봐야 한다.

## Q3. 이탈 분석

### 4) Slide 12 - Checkout Funnel Drop-off

#### 질문 정의
- 결제 직전 어느 단계에서 가장 큰 마찰이 발생하는가?

#### 핵심 지표
- `Pricing view -> Checkout start drop-off`
- `Checkout start -> Payment complete drop-off`

#### 사용 테이블
- `event_logs`
- `payment_transactions`

#### 계산 방식
- `Pricing view`
  - `event_logs.event_name = pricing_page_viewed`
- `Checkout start`
  - `event_logs.event_name = checkout_started`
- `Payment complete`
  - `payment_transactions.status = completed`
- 단위:
  - `unique user` 기준
- 식:
  - `Drop-off = 1 - (다음 단계 유저 수 / 현재 단계 유저 수)`

#### 현재 사용 수치
- `Pricing view -> Checkout start drop-off = 66.18%`
- `Checkout start -> Payment complete drop-off = 68.46%`

#### So What
- 가격 페이지 단계의 심리적 이탈과 결제 완료 직전 기술적 이탈을 분리해서 대응해야 한다.
- 결제 완료는 반드시 `payment_transactions`와 결합해 봐야 한다.

### 5) Slide 13 - CS Intervention Effect

#### 질문 정의
- 결제 실패 직후 CS 개입이 이탈 방지에 실제 도움이 되는가?

#### 핵심 지표
- `Churn rate with/without billing chat after failed payment`

#### 사용 테이블
- `payment_transactions`
- `chat_events`
- `users`

#### 계산 방식
- 분석 대상:
  - 첫 `status = failed` 결제를 가진 유저
- `CS contacted`
  - 실패 결제 후 7일 내 `chat_events.category = billing` 이 존재하는 경우
- `Churned`
  - `users.churn_date is not null`

#### 현재 사용 수치
- `No CS contact = 37.27%`
- `Billing chat within 7d = 4.17%`
- `Gap = -33.11%p`

#### So What
- 결제 실패는 방치보다 즉시 상담 연결이 훨씬 효과적이다.
- 리마인드와 CS 연결을 같은 플로우로 자동화할 근거가 된다.

## Q5. 다음 분기 전략 집중

### 6) Slide 14 - Expected Impact Summary

#### 질문 정의
- 다음 분기 우선 전략이 매출과 핵심 KPI에 어떤 임팩트를 주는가?

#### 핵심 지표
- `Extra monthly revenue`
- `Annualized value`
- `Onboarding completion increase`
- `Checkout efficiency increase`
- `Users retained / month`
- `7-day Aha reach increase`

#### 사용 테이블
- 실제 관측치 기반 항목:
  - `users`
  - `event_logs`
  - `payment_transactions`
  - `chat_events`
  - `ab_assignment`
- 시나리오 항목:
  - deck assumptions

#### 계산 방식
- 이 슬라이드는 실제값과 deck scenario 숫자가 혼합되어 있다.
- `7-day Aha reach +1.17%p`는 deck logic 기준 추정치:
  - `onboarding completion uplift (+8.3%p)` x `Aha gap from onboarding completion (+14.04%p in deck)`
- `MAU forecast 6M`
  - 최근 월별 MAU 추세 기반 baseline forecast
  - 개선 시나리오는 deck의 retained users uplift를 단순 가산한 illustrative chart

#### 현재 사용 수치
- `Extra monthly revenue = +1.54M KRW`
- `Annualized value = +185M KRW`
- `Onboarding completion = +1.36%p`
- `Checkout efficiency = +3.90%p`
- `Users retained / month = +7`
- `7-day Aha reach = +1.17%p`

#### So What
- 발표 마지막 장에서는 실데이터 근거와 경영 시나리오 숫자를 구분해 말해야 한다.
- CEO 의사결정 포인트는 “어느 KPI를 올릴 때 매출과 리텐션이 동시에 개선되는가”다.

## 결과 파일 매핑

- `slide03_overview_trend.png`
  - 가입자와 MAU 추세
- `slide07_value_gap_diagnostics.png`
  - 퀴즈 미제출, Aha 여부별 churn, churn timing
- `slide08_aha_kpi.png`
  - 7일 행동 분포, Aha 전환 uplift
- `slide09_onboarding_improvement.png`
  - 온보딩 A/B uplift, 온보딩 완료자의 Aha 우위
- `slide12_checkout_dropoff.png`
  - 가격 조회 -> 결제 시작, 결제 시작 -> 결제 완료 이탈률
- `slide13_cs_intervention_effect.png`
  - 결제 실패 후 CS 개입 효과
- `slide14_expected_impact_summary.png`
  - 발표용 기대효과 카드
- `slide14_mau_forecast_6m.png`
  - 6개월 MAU 시나리오
