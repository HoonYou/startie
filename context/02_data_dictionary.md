# 스타티 데이터 사전

## 데이터 기간
2025-01 ~ 2025-05

## 스키마 참고
- 전체 ERD(DBML): `context/04_erd_startie.dbml`
- 시각화: DBML을 `https://dbdiagram.io`에 붙여넣기

## 우선 분석 테이블

`users.csv`
- user_id
- signup_date
- acquisition_source
- device_type
- state
- current_plan
- is_activated
- activation_date
- churn_date
- total_sessions
- total_lessons_completed
- last_active_date

정의(현재 운영 기준):
- `is_activated`: 가입 후 7일 내 `lesson_started` 1회 이상 여부
- `activation_date`: 위 조건을 최초로 달성한 날짜

`event_logs.csv`
- user_id
- session_id
- event_name
- event_timestamp
- device_type
- event_sequence
- page_name
- course_id
- lesson_id
- event_properties

총 행 수(event_logs): 약 110만

## 수익화 관련 테이블

`payment_transactions.csv`
`plan_history.csv`

활용 목적:
- 매출
- 체험판 -> 유료 전환
- 요금제 업그레이드/다운그레이드
- LTV

## 실험 관련 테이블

`experiments.csv`
`ab_assignment.csv`

진행 실험:
- 온보딩 리디자인
- 가격 실험

## 마케팅 / CRM 테이블

`campaigns.csv`
`referral_events.csv`
`push_events.csv`
`chat_events.csv`

## 콘텐츠 테이블

`courses.csv`
`lessons.csv`

## 주요 조인 키
- user_id
- course_id
- lesson_id
- campaign_id
- experiment_id
- transaction_id

## 관계 요약
- 한 명의 유저는 여러 이벤트, 결제, 요금제 이력, 푸시 이벤트, 채팅 이벤트를 가질 수 있다.
- 하나의 코스는 여러 레슨을 가지며, 여러 이벤트 행에서 참조될 수 있다.
- 하나의 실험은 여러 유저 할당을 가진다.
- 하나의 캠페인은 유저 유입과 푸시 이벤트에 연결될 수 있다.
- 추천 이벤트에서는 한 유저가 추천인/피추천인 역할을 모두 가질 수 있다.
