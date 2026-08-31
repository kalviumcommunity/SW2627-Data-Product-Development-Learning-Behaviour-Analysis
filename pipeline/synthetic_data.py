"""Consistent synthetic raw-data generation for LearnLens."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SyntheticDataConfig:
    """Configuration for one synthetic-data generation run."""

    seed: int | None = None
    students: int = 100
    courses: int = 5
    days: int = 90
    start_date: str = "2024-01-01"


RAW_COLUMNS = {
    "completion": [
        "student_id",
        "course_id",
        "completion_pct",
        "status",
    ],
    "enrollment": [
        "student_id",
        "course_id",
        "enrollment_date",
        "cohort",
    ],
    "sessions": [
        "student_id",
        "course_id",
        "session_date",
        "duration_minutes",
    ],
    "quiz": [
        "student_id",
        "course_id",
        "quiz_id",
        "score",
        "attempt",
    ],
}


def _validate_config(config: SyntheticDataConfig) -> None:
    if config.students < 1:
        raise ValueError("students must be at least 1")
    if config.courses < 1:
        raise ValueError("courses must be at least 1")
    if config.days < 1:
        raise ValueError("days must be at least 1")


def _assignments(
    rng: np.random.Generator,
    students: int,
    courses: int,
) -> list[tuple[str, str]]:
    student_ids = [
        f"S{i:04d}"
        for i in range(1, students + 1)
    ]
    course_ids = [
        f"C{i:03d}"
        for i in range(1, courses + 1)
    ]

    assignments: list[tuple[str, str]] = []

    for student_id in student_ids:
        course_count = int(
            rng.integers(
                1,
                min(3, courses) + 1,
            )
        )

        selected = rng.choice(
            course_ids,
            size=course_count,
            replace=False,
        )

        assignments.extend(
            (student_id, str(course_id))
            for course_id in selected
        )

    return assignments


def generate_synthetic_datasets(
    config: SyntheticDataConfig | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate internally consistent raw datasets."""
    config = config or SyntheticDataConfig()
    _validate_config(config)

    rng = np.random.default_rng(config.seed)

    calendar = pd.date_range(
        start=config.start_date,
        periods=config.days,
        freq="D",
    )

    assignments = _assignments(
        rng,
        config.students,
        config.courses,
    )

    keys = pd.DataFrame(
        assignments,
        columns=["student_id", "course_id"],
    )

    # Enrollment is one row per student-course pair.
    enrollment = keys.copy()
    offsets = rng.integers(
        0,
        max(1, config.days // 3),
        size=len(enrollment),
    )
    enrollment["enrollment_date"] = [
        calendar[int(offset)]
        for offset in offsets
    ]
    enrollment["cohort"] = rng.choice(
        ["A", "B", "C"],
        size=len(enrollment),
    )

    # Completion is one row per student-course pair.
    progress = (
        rng.beta(
            5,
            2,
            size=len(keys),
        )
        * 100
    )

    completion = keys.copy()
    completion["completion_pct"] = np.round(
        progress,
        2,
    )
    completion["status"] = pd.cut(
        completion["completion_pct"],
        bins=[-np.inf, 25, 85, np.inf],
        labels=[
            "dropped",
            "in_progress",
            "completed",
        ],
        right=False,
    ).astype(str)

    # Sessions contain real source timestamps and are event-level rows.
    session_rows: list[dict[str, object]] = []

    for student_id, course_id in assignments:
        count = int(
            rng.integers(1, 5)
        )

        for _ in range(count):
            day_index = int(
                rng.integers(
                    0,
                    config.days,
                )
            )

            session_rows.append(
                {
                    "student_id": student_id,
                    "course_id": course_id,
                    "session_date": calendar[day_index],
                    "duration_minutes": int(
                        rng.integers(
                            15,
                            121,
                        )
                    ),
                }
            )

    sessions = pd.DataFrame(
        session_rows,
        columns=RAW_COLUMNS["sessions"],
    )

    # Quiz attempts are correlated loosely with completion to provide useful
    # demo analytics without hardcoded learner records.
    quiz_rows: list[dict[str, object]] = []

    for index, (student_id, course_id) in enumerate(
        assignments
    ):
        attempt_count = int(
            rng.integers(1, 4)
        )
        base_score = float(
            completion.iloc[index]["completion_pct"]
        )

        for attempt in range(1, attempt_count + 1):
            score = np.clip(
                base_score
                + rng.normal(0, 10),
                0,
                100,
            )

            quiz_rows.append(
                {
                    "student_id": student_id,
                    "course_id": course_id,
                    "quiz_id": "Q1",
                    "score": round(
                        float(score),
                        2,
                    ),
                    "attempt": attempt,
                }
            )

    quiz = pd.DataFrame(
        quiz_rows,
        columns=RAW_COLUMNS["quiz"],
    )

    result = {
        "completion": completion,
        "enrollment": enrollment,
        "sessions": sessions,
        "quiz": quiz,
    }

    validate_generated_datasets(result)
    return result


def validate_generated_datasets(
    datasets: dict[str, pd.DataFrame],
) -> None:
    """Validate generator output before it reaches the production pipeline."""
    expected = set(RAW_COLUMNS)

    if set(datasets) != expected:
        raise ValueError(
            "synthetic generator produced unexpected datasets"
        )

    for name, expected_columns in RAW_COLUMNS.items():
        frame = datasets[name]

        if frame.empty:
            raise ValueError(
                f"synthetic {name} dataset must not be empty"
            )

        if list(frame.columns) != expected_columns:
            raise ValueError(
                f"synthetic {name} schema does not match raw contract"
            )

        if frame[
            ["student_id", "course_id"]
        ].isna().any().any():
            raise ValueError(
                f"synthetic {name} contains missing identifiers"
            )

    completion = datasets["completion"]
    if not completion["completion_pct"].between(
        0,
        100,
    ).all():
        raise ValueError(
            "synthetic completion values are outside 0-100"
        )

    sessions = datasets["sessions"]
    if not sessions["duration_minutes"].ge(
        0
    ).all():
        raise ValueError(
            "synthetic session durations cannot be negative"
        )

    if not pd.api.types.is_datetime64_any_dtype(
        sessions["session_date"]
    ):
        raise ValueError(
            "synthetic session_date must be datetime-like"
        )

    quiz = datasets["quiz"]
    if not quiz["score"].between(
        0,
        100,
    ).all():
        raise ValueError(
            "synthetic quiz scores are outside 0-100"
        )

    if not quiz["attempt"].ge(1).all():
        raise ValueError(
            "synthetic quiz attempts must be >= 1"
        )


def write_synthetic_snapshot(
    output_dir: str | Path,
    datasets: dict[str, pd.DataFrame],
    *,
    seed: int | None,
    config: SyntheticDataConfig,
) -> dict[str, Path]:
    """Persist an optional auditable snapshot of a generated run."""
    output = Path(output_dir)
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    validate_generated_datasets(datasets)

    paths: dict[str, Path] = {}

    for name, frame in datasets.items():
        path = output / f"{name}.csv"
        frame.to_csv(
            path,
            index=False,
        )
        paths[name] = path

    manifest = {
        "seed": seed,
        "students": config.students,
        "courses": config.courses,
        "days": config.days,
        "start_date": config.start_date,
        "datasets": {
            name: {
                "file": path.name,
                "rows": int(len(datasets[name])),
            }
            for name, path in paths.items()
        },
    }

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["manifest"] = manifest_path

    return paths
