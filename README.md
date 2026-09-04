# LearnLens AI

LearnLens AI is a Streamlit-based learning analytics application that turns
learner activity data into actionable course, completion, quiz, engagement,
and student-behaviour insights.

The project is built around a production-oriented data pipeline with:

- automatic synthetic data generation for normal development/demo runs
- explicit CSV ingestion for external datasets
- source-schema validation
- data-quality gates
- reproducible synthetic runs
- student-course analytics
- Streamlit dashboards
- automated regression tests

---

## Table of Contents

1. [Architecture](#architecture)
2. [Project Structure](#project-structure)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Running the Pipeline](#running-the-pipeline)
6. [Synthetic Data](#synthetic-data)
7. [Running the Frontend](#running-the-frontend)
8. [CSV / External Data Mode](#csv--external-data-mode)
9. [Pipeline Outputs](#pipeline-outputs)
10. [Testing](#testing)
11. [Development Workflow](#development-workflow)
12. [Environment Variables](#environment-variables)
13. [Troubleshooting](#troubleshooting)
14. [Production Readiness Checklist](#production-readiness-checklist)

---

# Architecture

The normal application flow is:

```text
                    ┌──────────────────────┐
                    │  Synthetic Generator │
                    └──────────┬───────────┘
                               │
                               ▼
                     ┌─────────────────┐
                     │    Ingestion    │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │     Cleaning    │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │    Validation   │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  Transformation │
                     └────────┬────────┘
                              │
                              ▼
                  ┌─────────────────────────┐
                  │ Student-course metrics  │
                  └────────────┬────────────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ Quality Gate  │
                       └───────┬───────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Processed Artifacts │
                    └──────────┬──────────┘
                               │
                               ▼
                       ┌─────────────┐
                       │ Streamlit UI│
                       └─────────────┘
```

Synthetic data is the default source for a normal run.

Explicit external CSV data remains available when a path or CSV mode is
specified.

The source-selection contract is:

```text
No explicit data path
        ↓
Configured source mode
        ↓
Synthetic by default
```

and:

```text
Explicit data path
        ↓
CSV source
```

---

# Project Structure

A simplified project layout:

```text
SW2627-Data-Product-Development-Learning-Behaviour-Analysis/
│
├── app/
│   └── dashboard.py
│
├── analytics/
│   ├── funnel.py
│   ├── kpis.py
│   ├── segmentation.py
│   └── ...
│
├── components/
│   ├── charts.py
│   ├── filters.py
│   ├── insight_card.py
│   ├── kpi_card.py
│   └── ...
│
├── pipeline/
│   ├── clean.py
│   ├── config.py
│   ├── ingest.py
│   ├── join.py
│   ├── pipeline.py
│   ├── quality.py
│   ├── quality_gate.py
│   ├── synthetic_data.py
│   ├── transform.py
│   └── validate.py
│
├── services/
│   └── analytics_service.py
│
├── views/
│   ├── overview.py
│   ├── student_behaviour.py
│   ├── course_performance.py
│   └── reports_insights.py
│
├── tests/
│   └── ...
│
├── data/
│   ├── raw/
│   ├── generated/
│   └── processed/
│
├── run_pipeline.py
├── requirements.txt
└── README.md
```

---

# Requirements

Recommended environment:

```text
Python 3.13
```

You also need:

- `pip`
- `venv`
- Git

All Python dependencies are listed in:

```text
requirements.txt
```

---

# Installation

## Clone the repository

```bash
git clone <repository-url>
cd SW2627-Data-Product-Development-Learning-Behaviour-Analysis
```

Replace `<repository-url>` with the repository URL.

## Create a virtual environment

### Linux / macOS

```bash
python3.13 -m venv venv
source venv/bin/activate
```

### Windows PowerShell

```powershell
py -3.13 -m venv venv
venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
py -3.13 -m venv venv
venv\Scripts\activate.bat
```

Verify the interpreter:

```bash
python --version
```

Expected:

```text
Python 3.13.x
```

## Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

# Running the Pipeline

The main pipeline entrypoint is:

```bash
python run_pipeline.py
```

The default behavior is to generate synthetic data automatically and pass it
through the complete production pipeline.

```text
python run_pipeline.py
        ↓
Generate synthetic data
        ↓
Clean
        ↓
Validate
        ↓
Transform
        ↓
Join
        ↓
Quality gate
        ↓
Write processed artifacts
```

## Reproducible pipeline run

Use a fixed synthetic seed:

```bash
LEARNLENS_SYNTHETIC_SEED=43 python run_pipeline.py
```

A fixed seed makes the generated dataset reproducible for the same
configuration.

This is useful when:

- debugging
- reviewing pull requests
- comparing changes
- preparing demos
- reproducing a reported result

---

# Synthetic Data

The normal project workflow does not require manually maintained raw CSV
fixtures.

Synthetic source data is generated programmatically by:

```text
pipeline/synthetic_data.py
```

The generated source datasets are:

```text
completion
enrollment
sessions
quiz
```

The generator is designed to produce internally consistent relationships
between students and courses.

It also validates generated records before they enter the production
pipeline.

## Fresh random data

Run:

```bash
python run_pipeline.py
```

Without a seed, different runs may produce different generated data.

## Reproducible data

Run:

```bash
LEARNLENS_SYNTHETIC_SEED=43 python run_pipeline.py
```

## Generate a larger dataset

500 learners:

```bash
LEARNLENS_SYNTHETIC_STUDENTS=500 \
LEARNLENS_SYNTHETIC_SEED=43 \
python run_pipeline.py
```

10 courses:

```bash
LEARNLENS_SYNTHETIC_COURSES=10 \
LEARNLENS_SYNTHETIC_SEED=43 \
python run_pipeline.py
```

500 students and 10 courses:

```bash
LEARNLENS_SYNTHETIC_STUDENTS=500 \
LEARNLENS_SYNTHETIC_COURSES=10 \
LEARNLENS_SYNTHETIC_SEED=43 \
python run_pipeline.py
```

Generate a 180-day synthetic calendar:

```bash
LEARNLENS_SYNTHETIC_DAYS=180 \
LEARNLENS_SYNTHETIC_SEED=43 \
python run_pipeline.py
```

Change the synthetic start date:

```bash
LEARNLENS_SYNTHETIC_START_DATE=2024-01-01 \
LEARNLENS_SYNTHETIC_SEED=43 \
python run_pipeline.py
```

## Combine configuration

Example:

```bash
LEARNLENS_SYNTHETIC_STUDENTS=500 \
LEARNLENS_SYNTHETIC_COURSES=10 \
LEARNLENS_SYNTHETIC_DAYS=180 \
LEARNLENS_SYNTHETIC_START_DATE=2024-01-01 \
LEARNLENS_SYNTHETIC_SEED=43 \
python run_pipeline.py
```

---

# Persist Synthetic Source Data

Normally synthetic source data is generated in memory and immediately consumed
by the pipeline.

To keep a snapshot of the generated source datasets:

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
LEARNLENS_SYNTHETIC_PERSIST=true \
python run_pipeline.py
```

The snapshot is written under:

```text
data/generated/
```

Typical output:

```text
data/generated/
├── completion.csv
├── enrollment.csv
├── sessions.csv
├── quiz.csv
└── manifest.json
```

The manifest records the seed, generator settings, dataset files, and row
counts.

---

# Running the Frontend

The Streamlit dashboard entrypoint is:

```bash
python -m streamlit run app/dashboard.py
```

You can also use:

```bash
streamlit run app/dashboard.py
```

The application is normally available at:

```text
http://localhost:8501
```

## Run frontend with reproducible synthetic data

Use the same seed when demonstrating or debugging a specific dataset:

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
python -m streamlit run app/dashboard.py
```

The frontend should then consume the synthetic source generated through the
shared ingestion/analytics path.

The main dashboard areas include:

```text
Overview
Student Behaviour
Course Performance
Reports & Insights
```

---

# CSV / External Data Mode

Synthetic data is the default, but external CSV input is supported.

Set:

```bash
LEARNLENS_DATA_SOURCE=csv
```

Then run:

```bash
LEARNLENS_DATA_SOURCE=csv python run_pipeline.py
```

The default CSV directory is:

```text
data/raw/
```

Expected datasets:

```text
data/raw/completion.csv
data/raw/enrollment.csv
data/raw/sessions.csv
data/raw/quiz.csv
```

## Custom raw-data directory

Set:

```bash
LEARNLENS_RAW_DATA_PATH=/path/to/raw
```

Example:

```bash
LEARNLENS_DATA_SOURCE=csv \
LEARNLENS_RAW_DATA_PATH=/tmp/learnlens/raw \
python run_pipeline.py
```

## Explicit paths in application code

Passing an explicit data directory to the analytics service is treated as an
external CSV source.

This is useful for:

- integration tests
- fixture-based tests
- local experiments
- external data
- deployment-specific datasets

---

# Pipeline Outputs

Processed artifacts are written to:

```text
data/processed/
```

Important outputs include:

```text
data/processed/
├── student_course.csv
├── quality_report.csv
└── pipeline_manifest.json
```

## `student_course.csv`

This is the main aggregated learner/course analytics table.

It contains fields such as:

```text
student_id
course_id
enrollment_date
cohort
completion_pct
status
total_duration
session_count
avg_quiz_score
quiz_attempts
```

## `quality_report.csv`

Contains data-quality results for the source datasets.

The quality gate is intentionally strict and is designed to stop invalid source
data before it becomes a production artifact.

## `pipeline_manifest.json`

Contains reproducibility and artifact metadata, including:

- schema version
- row count
- quality-report location
- student-course artifact location
- source schema metadata

---

# Testing

Always run the complete test suite before pushing production-impacting
changes:

```bash
python -m pytest -q
```

This is the primary project validation command.

Do not use only one focused test file to decide whether the application is
production-ready.

## Run pipeline tests

```bash
python -m pytest tests/test_pipeline.py -q
```

## Run quality-gate tests

```bash
python -m pytest tests/test_quality_gate.py -q
```

## Run synthetic-data tests

```bash
python -m pytest tests/test_generate_synthetic_data.py -q
```

## Run dashboard integration tests

```bash
python -m pytest tests/test_dashboard_analytics_integration.py -q
```

## Run frontend/source integration tests

```bash
python -m pytest tests/test_frontend_synthetic_runtime.py -q
```

The actual filename may differ if the test has been moved or renamed; prefer
the complete suite for final validation.

---

# Development Workflow

A normal development cycle:

```bash
git pull
python -m pytest -q
python run_pipeline.py
python -m streamlit run app/dashboard.py
```

For a reproducible development cycle:

```bash
LEARNLENS_SYNTHETIC_SEED=43 python run_pipeline.py
```

Then:

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
python -m streamlit run app/dashboard.py
```

Check the repository:

```bash
git status
```

Review modifications:

```bash
git diff
```

Stage:

```bash
git add .
```

Commit:

```bash
git commit -m "describe the change"
```

Push:

```bash
git push
```

---

# Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `LEARNLENS_DATA_SOURCE` | `synthetic` | Select synthetic or CSV source mode |
| `LEARNLENS_RAW_DATA_PATH` | `data/raw` | External CSV input directory |
| `LEARNLENS_PROCESSED_PATH` | `data/processed` | Processed output directory |
| `LEARNLENS_SYNTHETIC_SEED` | unset | Fixed seed for reproducible generation |
| `LEARNLENS_SYNTHETIC_STUDENTS` | `100` | Number of generated students |
| `LEARNLENS_SYNTHETIC_COURSES` | `5` | Number of generated courses |
| `LEARNLENS_SYNTHETIC_DAYS` | `90` | Number of generated calendar days |
| `LEARNLENS_SYNTHETIC_START_DATE` | `2024-01-01` | Synthetic calendar start date |
| `LEARNLENS_SYNTHETIC_PERSIST` | `false` | Save generated source snapshots |

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'app'`

Make sure commands are being executed from the repository root.

Check:

```bash
pwd
```

Then:

```bash
python -c "import app; print(app.__file__)"
```

The path should belong to the current checkout.

Also verify:

```bash
python -c "import pipeline; print(pipeline.__file__)"
```

Both application and pipeline imports should resolve to the same project.

---

## Python is importing another checkout

This can happen when a different project has previously been installed into
the virtual environment.

Check:

```bash
python -c "import app, pipeline; print(app.__file__); print(pipeline.__file__)"
```

If the paths point to different project directories, recreate the virtual
environment:

```bash
deactivate
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Frontend displays old data

Clear Streamlit's cache:

```bash
streamlit cache clear
```

Restart the application:

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
python -m streamlit run app/dashboard.py
```

You can also use a different seed to verify that the displayed values change:

```bash
LEARNLENS_SYNTHETIC_SEED=99 \
python -m streamlit run app/dashboard.py
```

---

## Frontend reports `Path(None)` / `NoneType` errors

This indicates that `None` is being passed into a CSV path conversion instead
of reaching the synthetic/default source-selection branch.

Check that:

```text
AnalyticsService()
```

means "use the configured source".

An explicit path should only be used when CSV data is intended.

---

## Pipeline fails the quality gate

Run:

```bash
python -m pytest -q
```

Then reproduce with:

```bash
LEARNLENS_SYNTHETIC_SEED=43 python run_pipeline.py
```

Do not weaken the quality gate simply to make a generated dataset pass.

If the generator violates a source contract, fix the generator.

---

## Synthetic sessions contain duplicate rows

The synthetic generator is expected to produce data that satisfies the source
quality contract.

Run:

```bash
python -m pytest tests/test_synthetic_session_quality.py -q
```

The generator samples session dates uniquely per student/course so exact source
row duplicates are not created.

---

## Streamlit warnings

Some Streamlit versions emit deprecation warnings for UI API arguments such as
`use_container_width`.

Warnings do not necessarily indicate a pipeline or data-source failure.

For the actual application state, prioritize:

```bash
python -m pytest -q
```

and successful pipeline/frontend execution.

---

# Production Readiness Checklist

Before merging a production-impacting change, run:

```bash
python -m pytest -q
```

Then run the pipeline:

```bash
LEARNLENS_SYNTHETIC_SEED=43 python run_pipeline.py
```

Verify that:

```text
data/processed/student_course.csv
data/processed/quality_report.csv
data/processed/pipeline_manifest.json
```

exist and are non-empty.

Then run the actual frontend:

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
python -m streamlit run app/dashboard.py
```

Verify:

```text
☐ Overview loads
☐ Student Behaviour loads
☐ Course Performance loads
☐ Reports & Insights loads
☐ KPIs populate
☐ Charts render
☐ Course filters work
☐ Status filters work
☐ Report export works
☐ No hardcoded raw CSV dependency is required for the default run
☐ Pipeline artifacts are generated
☐ Quality gate passes
☐ Full test suite passes
```

---

# Quick Start

For most developers, these are the only commands required.

## Install

```bash
python3.13 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Run reproducible pipeline

```bash
LEARNLENS_SYNTHETIC_SEED=43 python run_pipeline.py
```

## Run frontend

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
python -m streamlit run app/dashboard.py
```

## Run tests

```bash
python -m pytest -q
```

## Run with a larger synthetic dataset

```bash
LEARNLENS_SYNTHETIC_SEED=43 \
LEARNLENS_SYNTHETIC_STUDENTS=500 \
LEARNLENS_SYNTHETIC_COURSES=10 \
python run_pipeline.py
```

## Use external CSV data

```bash
LEARNLENS_DATA_SOURCE=csv python run_pipeline.py
```

---

# Data-source contract

The most important runtime rule is:

```text
                    LearnLens
                       │
          ┌────────────┴────────────┐
          │                         │
   No explicit path          Explicit path
          │                         │
          ▼                         ▼
 configured source             CSV source
          │
          ▼
 synthetic by default
```

This keeps the project self-contained and repeatable for development and demos,
while retaining a clear path for external or real-world datasets.
