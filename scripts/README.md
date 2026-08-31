# Automatic synthetic source data

The pipeline now generates internally consistent synthetic raw data by
default. The committed `data/raw/*.csv` fixtures are no longer required for
normal development/demo execution.

Run the normal pipeline:

```bash
python run_pipeline.py
```

By default:

```text
LEARNLENS_DATA_SOURCE=synthetic
```

Every run gets a fresh dataset because the default seed is unset.

For reproducible runs:

```bash
LEARNLENS_SYNTHETIC_SEED=42 python run_pipeline.py
```

Useful controls:

```text
LEARNLENS_SYNTHETIC_STUDENTS=500
LEARNLENS_SYNTHETIC_COURSES=10
LEARNLENS_SYNTHETIC_DAYS=180
LEARNLENS_SYNTHETIC_START_DATE=2024-01-01
```

To keep an auditable generated snapshot:

```bash
LEARNLENS_SYNTHETIC_PERSIST=true python run_pipeline.py
```

Snapshots are written under `data/generated/`.

The production pipeline can still explicitly ingest external CSVs:

```bash
LEARNLENS_DATA_SOURCE=csv python run_pipeline.py
```

This separation makes synthetic generation the default application path while
keeping external-data ingestion available for a real deployment.
