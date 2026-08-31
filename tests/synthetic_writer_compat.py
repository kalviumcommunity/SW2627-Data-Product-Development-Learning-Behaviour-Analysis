"""Legacy test compatibility wrapper for synthetic dataset writing."""

from pipeline.synthetic_data import (
    SyntheticDataConfig,
    generate_synthetic_datasets,
    write_synthetic_snapshot,
)

from pathlib import Path


def write_datasets(
    output_dir,
    *,
    seed,
    students=100,
    courses=5,
    days=90,
    start_date="2024-01-01",
    force=False,
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    existing = list(output.glob("*.csv"))
    manifest = output / "manifest.json"

    if not force and (existing or manifest.exists()):
        raise FileExistsError(
            f"synthetic-data output already exists: {output}"
        )

    config = SyntheticDataConfig(
        seed=seed,
        students=students,
        courses=courses,
        days=days,
        start_date=start_date,
    )
    datasets = generate_synthetic_datasets(config)

    return write_synthetic_snapshot(
        output,
        datasets,
        seed=seed,
        config=config,
    )
