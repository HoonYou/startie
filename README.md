# Startie Product Analysis

CEO decision-support analysis project for Startie, an online education platform for career switchers in their 20s and 30s.

This repository is not organized around "making charts." It is organized around helping the CEO decide what to do next quarter by answering five business questions across activation, retention, churn, channel efficiency, and experiment rollout.

## Project Objective

Startie operates a `7-day free trial -> paid subscription` model with two plans:

- `Basic`: KRW 9,900 / month
- `Pro`: KRW 19,900 / month

The core business goal is to improve key product and revenue metrics within the next 6 months and present clear growth evidence to investors.

## CEO Question Framework

This project follows the Q1-Q5 framework defined in the context documents.

### Q1. Value and Activation
- What early behaviors increase paid conversion and retention?
- Key metrics: activation rate, trial-to-paid conversion, D7/D30 retention, time-to-paid after activation
- Main tables: `users`, `event_logs`, `payment_transactions`, `plan_history`, `lessons`

### Q2. Channel Quality
- Which acquisition channels deserve more or less budget?
- Key metrics: CAC, LTV, LTV/CAC, payback period, channel retention
- Main tables: `users`, `campaigns`, `payment_transactions`, `plan_history`, `event_logs`

### Q3. Churn Analysis
- Who leaves, why do they leave, and what signals appear before churn?
- Key metrics: churn rate, time-to-churn, cancellation reasons, post-payment-failure churn
- Main tables: `users`, `plan_history`, `payment_transactions`, `chat_events`, `push_events`, `event_logs`

### Q4. A/B Test Evaluation
- Should onboarding and pricing experiments be rolled out globally or by segment?
- Key metrics: lift, p-value, effect size, heterogeneous treatment effects
- Main tables: `experiments`, `ab_assignment`, `event_logs`, `users`, `payment_transactions`

### Q5. Next-Quarter Strategy
- Which 1-2 strategic bets should be prioritized next quarter?
- Output format: `What -> Why -> So What -> Impact`

## Analysis Principles

- Funnel analysis should combine `event_logs` with monetization tables such as `payment_transactions` and `plan_history`.
- Activation and Aha Moment analysis can use `is_activated`, but should be validated against concrete user behavior.
- Segment comparison matters. Preferred cuts include channel, device, and activation status.
- Every insight should connect to an executive decision, not stop at descriptive reporting.

## Repository Structure

```text
context/         Product overview, data dictionary, analysis guide, ERD, CEO questions
data/raw/        Source CSV files
docs/            Supporting documentation such as metric definitions
notebooks/       Exploratory and presentation-support notebooks
src/             Streamlit app and analysis/visual generation scripts
outputs/         Generated charts and summary CSV outputs
deliverables/    Final presentation assets and exported results
tests/           Test area for future validation work
```

## Main Files

- `src/app.py`: Streamlit funnel dashboard for segment and bottleneck analysis
- `src/plot_actual_retention.py`: Exact retention curve generation
- `src/generate_ppt_visual_assets.py`: Slide asset generation for the strategy deck
- `docs/metrics/ppt_metric_definitions.md`: Metric definitions used in presentation outputs

## How To Run

Recommended environment: Python 3.11+

Install dependencies manually based on the scripts in `src/`:

```bash
pip install pandas matplotlib numpy streamlit altair
```

Run the Streamlit dashboard:

```bash
streamlit run src/app.py
```

Generate retention outputs:

```bash
python src/plot_actual_retention.py
```

Generate presentation visual assets:

```bash
python src/generate_ppt_visual_assets.py
```

## Expected Deliverable Style

Insights should be expressed in the following structure:

1. `What`: What is happening?
2. `Why`: What is the likely reason?
3. `So What`: What should the company do next?
4. `Impact`: What quantified business improvement is expected?

The preferred endpoint is a next-quarter action recommendation for the CEO.

## Context Basis

This README is based on:

- `context/01_product_overview.md`
- `context/03_analysis_guide.md`
- `context/05_ceo_questions.md`

Those files define the business context, the analysis philosophy, and the Q1-Q5 decision framework used throughout this repository.
