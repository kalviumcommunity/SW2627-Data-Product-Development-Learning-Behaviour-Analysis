# LearnLens AI

> **Learning Behaviour Intelligence & Completion Prediction Platform**

LearnLens AI is an end-to-end data product designed to identify the
learning behaviours that distinguish students who successfully complete
courses from students who silently drop off.

An edtech platform already collects course completion records, quiz
performance, session activity, and enrollment data. LearnLens AI unifies
these sources, cleans and validates them, engineers behavioural
features, performs SQL/Pandas-based analysis, and presents actionable
insights through an interactive Streamlit dashboard.

## Problem

Traditional learning dashboards are largely descriptive: they show
completion percentages, quiz scores, or activity counts independently.

They do not answer:

-   Which behaviours are associated with successful completion?
-   Which students are silently disengaging?
-   At what stage do learners drop off?
-   Is the likely cause inactivity, poor quiz performance, or weak
    engagement?
-   Which students should an instructor intervene with first?

LearnLens AI addresses this gap with a behaviour intelligence layer.

## Objectives

1.  Build a unified student-level behavioural dataset.
2.  Identify patterns associated with course completion and drop-off.
3.  Segment learners by observable behaviour.
4.  Analyse completion funnels and drop-off points.
5.  Provide behaviour-specific intervention recommendations.
6.  Provide an optional completion-risk prediction model.
7.  Deliver all insights through a non-technical Streamlit dashboard.

## Core Features

### Data Pipeline

-   CSV ingestion for completion, quiz, session, and enrollment data
-   Schema and data-quality validation
-   Missing-value handling
-   Duplicate detection
-   Timestamp and data-type standardisation
-   Multi-source joins
-   Reusable feature-engineering pipeline

### Behavioural Analytics

-   Completion and drop-off rates
-   Funnel analysis
-   Session and engagement trends
-   Quiz-performance analysis
-   Correlation and relationship analysis
-   Behaviour segmentation
-   Root-cause analysis

### Behavioural Features

Examples include:

  Feature                    Purpose
  -------------------------- ---------------------------------------
  Total Study Hours          Measures overall learning effort
  Average Session Length     Measures depth of individual sessions
  Quiz Accuracy              Measures learning performance
  Quiz Frequency             Measures assessment engagement
  Days Since Last Activity   Detects inactivity
  Active Days                Measures consistency
  Learning Streak            Measures sustained engagement
  Weekly Sessions            Measures recurring engagement
  Completion Percentage      Measures course progress

## Dashboard

The Streamlit application is planned around the following views:

1.  **Home** --- completion rate, drop-off rate, average quiz score,
    active students
2.  **Student Explorer** --- individual session, quiz, completion, and
    risk information
3.  **Behaviour Analysis** --- distributions, trends, correlations, and
    behavioural patterns
4.  **Funnel** --- progression and drop-off by completion stage
5.  **Segments** --- learner behaviour cohorts and their trends
6.  **Recommendations** --- behaviour-specific intervention suggestions

## Architecture

``` text
                   ┌─────────────────────────┐
                   │       Raw CSV Data       │
                   │ Completion / Quiz /      │
                   │ Sessions / Enrollment    │
                   └────────────┬────────────┘
                                │
                                ▼
                   ┌─────────────────────────┐
                   │   Data Intake & Quality  │
                   │ Schema / Nulls / Dups /  │
                   │ Types / Validation       │
                   └────────────┬────────────┘
                                │
                                ▼
                   ┌─────────────────────────┐
                   │   Processing & Feature   │
                   │       Engineering       │
                   │ Behavioural Features    │
                   └────────────┬────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       ┌──────────────────┐          ┌──────────────────┐
       │ SQL Analytics     │          │ Pandas / NumPy   │
       │ KPIs / Funnel /   │          │ EDA / Segments / │
       │ Aggregations      │          │ Root Causes      │
       └────────┬─────────┘          └────────┬─────────┘
                └──────────────┬──────────────┘
                               ▼
                    ┌────────────────────────┐
                    │ Optional ML Layer      │
                    │ Completion Risk        │
                    │ Logistic Regression /  │
                    │ Random Forest          │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │     Streamlit App       │
                    │ KPIs / Charts / Filters │
                    │ Student Explorer /      │
                    │ Recommendations         │
                    └────────────────────────┘
```

## Tech Stack

  Layer                  Technology
  ---------------------- ---------------------------
  Language               Python 3.10+
  Data Processing        Pandas, NumPy
  Database / Analytics   SQLite or PostgreSQL, SQL
  Visualization          Plotly
  Dashboard              Streamlit
  Version Control        Git + GitHub
  CI                     GitHub Actions
  Optional ML            Scikit-learn

The stack is intentionally aligned with the available learning units
covering Python, Pandas, NumPy, SQL, business analytics, Plotly,
Streamlit, automation, GitHub workflows, and data-product delivery.

## Suggested Project Structure

``` text
learnlens-ai/
├── app/
│   ├── dashboard.py
│   ├── pages/
│   │   ├── home.py
│   │   ├── student_explorer.py
│   │   ├── behaviour_analysis.py
│   │   ├── funnel.py
│   │   ├── segments.py
│   │   └── recommendations.py
│   └── components/
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
├── pipeline/
│   ├── ingest.py
│   ├── validate.py
│   ├── clean.py
│   ├── transform.py
│   └── features.py
├── analytics/
│   ├── kpis.py
│   ├── funnel.py
│   ├── segmentation.py
│   ├── root_cause.py
│   └── sql_queries/
├── ml/
│   ├── train.py
│   ├── predict.py
│   └── evaluate.py
├── tests/
├── .github/
│   └── workflows/
├── requirements.txt
├── .env.example
├── README.md
└── PRD.md
```

## Data Sources

The MVP expects four datasets:

### Course Completion

`student_id`, `course_id`, `enrollment_date`, `completion_pct`, `status`

### Quiz Performance

`student_id`, `quiz_id`, `course_id`, `attempt_number`, `score_pct`,
`timestamp`

### Learning Sessions

`session_id`, `student_id`, `course_id`, `start_time`, `end_time`,
`duration_minutes`

### Enrollment

`student_id`, `course_id`, `enrollment_date`, `cohort`

No real student PII should be committed to the repository. Synthetic or
anonymised identifiers should be used for development and demonstration.

## MVP

### Included

-   CSV ingestion
-   Data validation and cleaning
-   Unified feature table
-   SQL-powered completion/funnel analysis
-   Rule-based behaviour segmentation
-   Root-cause analysis
-   Streamlit dashboard
-   CSV exports
-   Synthetic/sample data
-   GitHub Actions CI

### Deferred

-   Real-time streaming
-   Live LMS/API integration
-   Automated email/Slack alerts
-   Multi-tenant support
-   Dashboard authentication
-   ML completion prediction unless the core MVP is complete

## Optional Prediction Layer

If sufficient labelled data is available, LearnLens AI can train a
binary completion model using features such as:

-   study hours
-   session frequency
-   average session duration
-   quiz accuracy
-   days since last activity
-   active days
-   course progress

Possible models: - Logistic Regression - Random Forest

The model should be treated as a decision-support signal rather than
proof that a learner will drop out.

## Example Insight

``` text
Student: STU-1042

Behaviour:
- 8 days since last activity
- 3 sessions in the previous 14 days
- Average quiz score: 48%
- Completion: 37%

Likely driver:
Performance + Engagement

Suggested intervention:
Send a targeted revision/practice-quiz recommendation
before sending a generic inactivity reminder.
```

## Development Workflow

``` text
Issue
  ↓
Feature Branch
  ↓
Implementation
  ↓
Unit Tests + Validation
  ↓
Pull Request
  ↓
GitHub Actions
  ↓
Review
  ↓
Merge
```

## Quality Goals

-   100% schema validation for accepted processed datasets
-   ≥80% unit-test coverage
-   Dashboard load target \<3 seconds for sample data
-   Pipeline target \<5 minutes for one term of daily data
-   No silent dropping of malformed records
-   Reproducible environment through `requirements.txt`
## Team

| Member | Responsibility |
|---|---|
| Kushal | Data Pipeline |
| Niranjan | Analytics & Insights |
| Ruchitha | Dashboard & Reporting |

## Documentation

-   Product Requirements Document
-   Data dictionary and schema documentation
-   Pipeline documentation
-   Dashboard usage documentation

## Status

**Version:** 1.0.0\
**Status:** Draft / In Development
