# Reproducible synthetic data

This generator creates development/demo data for the four raw datasets used by
the LearnLens pipeline.

It is intentionally **not imported or executed by the production pipeline**.

## Usage

```bash
python scripts/generate_synthetic_data.py   --seed 42   --students 100   --courses 5   --days 90   --output-dir data/generated
```

To replace an existing generated dataset:

```bash
python scripts/generate_synthetic_data.py   --seed 42   --output-dir data/generated   --force
```

The output contains:

```text
completion.csv
enrollment.csv
sessions.csv
quiz.csv
manifest.json
```

The generator is deterministic for a given seed and produces internally
consistent student/course relationships. It does not write into `data/raw`
unless a developer explicitly passes that directory as `--output-dir`.
